# Finance ledger model

Status: implemented for CLAUDE-PACK-10. This document describes
`services/finance-service/src/epd2_finance_service/ledger.py` and the
parts of `storage.py` that support it: exact money, per-currency
balancing, the immutability of a posted entry and the two routes around
it, accounting periods and their lock, the transaction register with its
provenance and import batches, and inter-unit transfers. The layering
decision is `docs/adr/ADR-049-authoritative-finance-ledger-and-correction-model.md`.

`ledger.py` is pure. It performs no I/O, reads no clock, opens no
storage and imports from no other service; every identifier, every
timestamp and every sequence number is passed in by the application
layer.

## 1. `Money`, and why there is no float

`domain.Money` carries integer `minor_units`, an explicit `currency`, an
explicit `scale` and a `RoundingRule`. The constructor refuses a
non-integer `minor_units` outright, and refuses `bool` as well, since
`True` is an `int` in Python and a boolean amount is not a defect anyone
would notice downstream. There is no float in the finance domain: not in
the constructor, not in arithmetic, not in `to_payload()` (`ФИН-08`).

The refusal that matters more is the currency one. `Money.__add__` and
`__sub__` call `_assert_same_currency` and raise
`FINANCE_CURRENCY_UNSUPPORTED` when the currencies differ, so two
amounts in different currencies never net silently: cross-currency
arithmetic requires a recorded conversion, and no conversion is recorded
by this module (`ФИН-09`). `sum_money` accumulates per currency into a
mapping and never collapses it. `assert_non_zero` refuses a zero-value
posting, because a zero posting is the wrong tool for a non-monetary
fact — canon 19f.4 wants a typed non-monetary record instead.

`GOVERNED_CURRENCIES` is `{"EUR"}` and `CURRENCY_SCALE` is `{"EUR": 2}`.
These are the reference seed the in-memory adapters start from, not a
statement about which currencies a party may hold: extending the set is
a `FinancePolicy(currency)` decision under canon 19f.20, and no
`FinancePolicy` aggregate exists this round. Until one does, any
currency other than EUR is refused at construction, which is stricter
than the canon requires and is a limitation rather than a rule.

## 2. Balancing, per currency

`assert_balanced` runs twice: once in the `JournalEntry` constructor, so
an unbalanced entry cannot exist even as a draft, and once inside `post`
— the constructor guarantee is about the object, and the second is about
the act (`ФИН-07`).

Four things it refuses:

- an empty line set, which would balance vacuously;
- a zero-value line, through `Money.assert_non_zero`;
- a negative magnitude, because direction is carried by `PostingSide`
  and a "negative debit" would be a second, undeclared way of expressing
  a credit;
- a per-currency mismatch, with the offending currency named. Debit and
  credit totals are accumulated separately per currency and compared per
  currency; nothing is ever netted across currencies, since no
  conversion has been recorded (`ФИН-09`).

`PostingLine` is a value object with no identity: lines are not
addressable, not individually versioned and never edited. Changing one
means drafting a new entry. `dimension_references` carries opaque
analytical dimensions — cost centre, campaign, project — as references
only, and no dimension is ever a party.

## 3. A posted entry is content-immutable

`amend_draft` is the only edit path in the module and it calls
`assert_entry_mutable`, which refuses anything that is not a draft with
`FINANCE_IMMUTABLE_RECORD_MODIFICATION_ATTEMPTED`. "Editing any field of
a posted entry" therefore raises by construction rather than by a
per-field check (`ФИН-05`). The refusal names immutability rather than a
forbidden transition, because editing a posted entry is not a
disallowed transition — it is an attempt to rewrite an authoritative
record. `post` refuses an already-posted entry for the same reason and
with the same code.

`entry_sequence` is assigned at posting, per (scope, period), and never
reused — not even by an entry that replaces a reversed one. A draft
carries `None`, and the constructor refuses a draft that carries a
sequence as firmly as a posted entry that does not.

### The two correction routes

Canon 19f.6 permits exactly two ways to change monetary effect after
posting, and `ledger.py` implements them as two functions that produce
different links.

`reverse(entry, ...)` returns a tuple: the original marked `reversed`
and a new draft reversal entry. Returning both halves of one act is
deliberate — a caller cannot record the reversal while leaving the
original still reversible. The reversal carries equal and opposite lines
built by `PostingLine.opposite()`, which flips the side and leaves the
amount unchanged; reversal by negation would produce a second
representation of the same effect. It sets `reverses_entry_id`, carries
its own reason code, and is posted through the ordinary `post` command
with its own never-reused sequence.

`correct(entry, replacement_lines, ...)` returns a single new draft
entry carrying `corrects_entry_id`. The original stays `posted` and
untouched. A correction is not a reversal: it states that a further,
differently-shaped booking belongs with the original, whose own effect
stands until separately reversed. `replacement_lines` is balanced in its
own right by the constructor, not against the original, and an optional
`period` lets the correction be booked into a later reporting period
when the original's has closed.

Both go through `assert_correction_target`, which refuses four things
with `FINANCE_CORRECTION_TARGET_INVALID`: an unresolved target (`None` —
modelled explicitly so a caller who could not resolve the original gets
the same refusal as one who named a draft, disclosing nothing about
another scope), a draft (no monetary effect to correct), an
already-reversed entry, and — through the `JournalEntry` constructor —
an entry that reverses or corrects itself.

Re-posting after a reversal has no special API. The corrected effect is
booked as an ordinary new entry through the same `post` command, without
reusing the reversed entry's sequence and without a
`reverses_entry_id`. Modelling it as a distinct operation would create a
second write path into the register, which is precisely the bypass canon
19f.4 forbids.

### The chain-cycle refusal

`correction_chain` orders a set of linked records from the origin
through its corrections and reversals. It reads only each record's
identity and its single backward link, so it is total over its input and
usable on a scope-filtered slice — a predecessor id absent from the
input means "outside this chain" rather than "missing", which is what
keeps it from leaking records in another scope (`ФИН-03`).

It refuses four shapes, all with `FINANCE_CORRECTION_TARGET_INVALID`:

- a cycle. `_assert_chain_acyclic` walks every backward link to its
  origin and refuses any revisit; a `settled` set guarantees each node is
  resolved at most once, so the walk is provably bounded. A cycle in an
  append-only chain is not a data curiosity — it is a set of records each
  claiming to correct the other, with no origin and no answer to "what
  actually happened first";
- a duplicate identity in the presented set;
- more than one origin, or a set that does not form a single connected
  chain;
- a branch, where one record is corrected or reversed by two others.
  Canon 19f.4 describes a chain, not a tree, and silently picking one
  branch would hide the other.

`_record_predecessor` also refuses a record that sets both
`corrects_*_id` and `reverses_*_id`: "which original does this correct"
would have two answers.

## 4. Accounting periods

`AccountingPeriod` carries an explicit named IANA timezone, resolved
through `resolve_period_timezone`, which refuses an empty, missing or
unknown name rather than falling back to UTC. Period boundaries are
civil-calendar facts, and a silent UTC default would move them by an
hour twice a year (`ФИН-39`). `domain.require_timezone` refuses a naive
datetime anywhere in the domain and raises
`FINANCE_ACCOUNTING_PERIOD_UNDETERMINED` rather than a monetary code —
canon section 24 gives that code the meaning "no period, or no
timezone-explicit period, could be determined", which is exactly what a
naive instant leaves behind. The function's docstring records that an
earlier draft raised a money code here, which would have reported a time
defect as a money defect.

The lifecycle is `open`, `closing`, `closed`, `reopened`. `closing` is a
real, storable state and not a transient: it freezes new postings while
corrections already in flight settle, and it denies
`assert_open_for_posting` exactly as `closed` does.
`_POSTABLE_PERIOD_STATUSES` is an enumerated set of `{open, reopened}`
rather than the negation "not closed", so `closing` denies and any
future status denies by default (`ФИН-10`).

### Why the command re-checks the lock

`ledger.post` takes `period` as a required keyword-only argument and
calls `period.assert_open_for_posting()` itself. There is deliberately
no overload that posts without a period. Canon 19f.5 states that the
closed-period block is re-checked inside each posting command, and an
overload without one would be exactly the bypass `ФИН-10` forbids: a
caller could hold a stale period object, or none, and the write would
land. `post` also re-asserts that the entry's `ReportingPeriodRef`
matches the `AccountingPeriod` presented, so a caller cannot satisfy the
lock check with an open period while booking into a closed one.

The order of checks in `post` is fixed and each step has its own code:
draft status first (posting a posted entry is an immutability violation,
not a transition error), then scope, then the period lock, then balance.

### Dual-controlled reopening

Reopening is two acts. `request_reopening` builds a create-once
`PeriodReopeningRecord` — and building it is what performs the checks,
because the record is the evidence that dual control happened. It runs
only on a `closed` period, asserts both authorities' scopes, refuses an
approval timestamped before its request, and snapshots the period's
`state_digest()` into `closed_state_digest`.

`assert_reopening_dual_control` compares two things, not one. Distinct
`authority_id` values are not enough if the same natural actor holds
both assignments, so `actor_reference` is compared too wherever both
sides carry one: a dual-control rule one person can satisfy alone is not
one (`ФИН-11`, `ФИН-32`).

`reopen(record, at=...)` then refuses a record belonging to another
period and refuses a record whose `closed_state_digest` no longer
matches the period's current digest, so a stale approval cannot be
replayed against a period that has moved on since. It re-runs the
dual-control assertion rather than trusting that the record was built
correctly. `reopening_records` is append-only; nothing is ever
rewritten, and there is no silent reopening path at all.

## 5. The transaction register

`FinancialTransaction` is the authoritative record of a business fact:
the dates, the origin, the policy version that classified it, the
evidence cited, the purpose-scoped handle it touched and the posted
entry realising its money. Its constructor refuses:

- `IMPORTED` provenance with no `import_batch_reference` — an imported
  fact whose batch cannot be named cannot be audited (`ФИН-38`);
- a status at or beyond `classified` with no classification code or no
  bound `PolicyBinding` — classification is never inferred from the
  amount and never resolved at read time, because a decision that
  resolves its policy at read time can be silently rewritten by a later
  policy change (`ФИН-23`);
- a status asserting completed monetary effect (`posted`, `corrected`,
  `reversed`) with no `journal_entry_id` — the incomplete state canon
  19f.6 says must fail closed;
- a party in any shape other than the opaque `fph:` handle reference;
- a transaction that corrects or reverses itself.

Every transition runs through `_transition`, which applies one
enumerated edge, bumps `version`, and then calls
`assert_provenance_unchanged` — so a future transition cannot forget it.
`transaction_date`, `provenance` and `import_batch_reference` are frozen
once the fact is recorded: they are the audit trail's anchor, and
changing where a fact came from would rewrite that anchor while leaving
every downstream reference intact (`ФИН-40`).

`version` is an explicit field here, unlike the nine aggregates whose
version is the length of their append-only history, and `_check_version`
enforces it on every mutating method so two concurrent classifications
cannot both land.

### Provenance and import batches

`domain.Provenance` records the kind (`manual_entry`, `imported`,
`derived_correction`, `derived_reversal`), the source system reference,
the recording authority, and optionally the batch and external
references. `Provenance.to_payload()` deliberately omits
`recorded_by_authority`, which is correct for a wire payload and wrong
for a hash — which is why the state payloads in `events.py` use their
own complete serialisers instead.

`storage.ImportBatchRecord` records one ingestion act:
`registered -> applied | rejected`, with a fingerprint the ingestion
adapter computed over the source file or feed window. The batch is
registered before anything is booked from it, so a crash between
registration and application leaves a `registered` row rather than a
silently re-appliable file. The counts on the record are what the
adapter reported and are authoritative for nothing; the transaction
register is.

The store refuses a fingerprint that already reached `applied`
(`FINANCE_DUPLICATE_IMPORT`), and re-registering the same batch id with
identical content is an idempotent replay that returns the stored
record. The fingerprint index is scoped, because two organizations may
legitimately import byte-identical files — the same published funding
statement, say — and one unit's ingestion must never block another's
(`ФИН-03`). `find_by_fingerprint` prefers an `applied` batch over the
earliest registered one, so a rejected first attempt cannot mask an
applied second. `mark_applied` refuses a second application, since
applying a batch twice would re-book every transaction it carried.

None of these guarantees survives concurrency. The adapter's own
docstring says a durable backend would carry a unique index on
`(organization_id, fingerprint)` where status is `applied`; this
in-memory check does not survive two workers racing.

### What the transaction fingerprint cannot distinguish

`storage.transaction_fingerprint` digests the scope, the source system
reference, the external reference, the import-batch reference, the
transaction date and the posting date. Two limits are honest and are
stated in the code:

- The amount is not in the digest. Under the single authoritative money
  layer (ADR-049) monetary effect lives on the `JournalEntry`, not on
  the transaction, so the transaction alone cannot fingerprint it. Two
  intakes for different amounts, same source, same external reference,
  same dates, produce the same digest.
- For a `MANUAL_ENTRY` with no `external_reference`, two genuinely
  distinct same-day intakes in one scope produce the same digest. The
  digest is built from `provenance.external_reference or ""`, so an
  absent reference contributes an empty string rather than distinguishing
  anything.

The function therefore answers "has something already arrived under this
identity?" and never "is this a duplicate?". The second question belongs
to the command layer and to `FINANCE_DUPLICATE_TRANSACTION`. A durable
backend would carry a unique index only where `external_reference` is
present, because that is the only case where uniqueness is a fact rather
than a guess. A caller that treats a fingerprint match as proof of
duplication will suppress legitimate same-day manual entries; a caller
that treats a non-match as proof of novelty will accept a re-keyed
duplicate with a different date.

The posting-sequence allocator has a parallel honesty note.
`InMemoryJournalEntryStore.next_sequence` is monotonic and gap-free per
(scope, period), takes its high-water mark from the stored entries as
well as from its counter so a re-hydrated store does not re-issue a
number, and is explicitly not concurrency-safe. It is also only gap-free
in effect if the command layer allocates last: a number handed out and
then discarded because the posting was refused leaves a hole, and a hole
in a posting sequence is what an auditor reads as a removed entry.

## 6. Inter-unit transfers and the double-counting refusal

A `GovernedTransfer` is two `TransferLeg`s bound by one
`internal_transfer_reference`. The shared reference is the whole point:
it lets consolidation recognise the pair and eliminate it exactly once,
without a higher scope ever writing into a lower one (`ФИН-37`).

`assert_transfer_pair_resolvable` refuses four shapes, all with
`FINANCE_TRANSFER_PAIR_UNRESOLVED`, and the pair is validated in
`GovernedTransfer.__post_init__` so an incomplete transfer cannot be
stored and discovered later:

- not exactly two legs. One leg is a half-recorded movement that
  consolidation would either double-count or drop;
- both legs in the same scope. A movement inside one unit is not a
  transfer, and pairing a scope with itself would let the record be
  eliminated against itself;
- not one outgoing and one incoming leg;
- unequal amounts. A transfer that changes value in flight is two facts,
  not one.

The rule behind all four is canon 19f.6's: a contribution is income to
exactly one unit, and any onward movement is a transfer and never new
income. Without the pairing, a donation received centrally and passed to
a regional unit would appear as income twice, and the party's
consolidated income figure would be wrong in the direction that
flatters it.

Consolidation itself is not implemented this round. There is no
consolidation command, no `finance_report.consolidated` emission path
and no `GovernedTransferStore` reference in `application.py`; the
elimination the pairing exists to enable has to be performed by a caller
using the domain module directly.
