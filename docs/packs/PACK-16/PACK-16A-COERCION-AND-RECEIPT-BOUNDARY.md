# PACK-16A — Coercion Resistance and Receipt Reality Boundary

**Round:** PACK-16A — Verifiable Voting Protocol and Ballot Model Selection. **Specification and ADR only. No code. Not implemented. Not an implementation candidate. Not a PASS.**
**Repository version:** unchanged at `0.15.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-099`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

This is the document most likely to be quoted out of context, so it says
the difficult things first and the reassuring things second.

---

## 1. The boundary, stated once

> **Coercion resistance for remote voting is not a cryptographic property.
> It is a conditional property that depends on the voter having an interval
> in which nobody is watching. A polling booth manufactures that interval by
> physical enforcement. Remote voting can only assume it.**

The authoritative formulation:

> _"Because remote systems enable voters to fill out their ballots outside a
> controlled environment, anyone can watch over the voter's shoulder while
> she fills out her ballot… Note that if the coercer can monitor the voter
> throughout the vote casting period, then resistance is futile … For remote
> voting, we need to assume that voters will have some time when they can
> interact with the voting system unobserved."_ `[E-46]`

Every coercion-resistant scheme in the literature **relocates** this
assumption rather than removing it: JCJ to postal credential delivery
`[E-34]`, Civitas to in-person registration `[E-35]`, Selene to unmonitored
tracker delivery `[E-38]`, VoteAgain to an anonymous channel `[E-43]`.
**None removes it, and EPD² will not be the first.**

---

## 2. Six layers, and what each can actually do

The single most common error in this field is attributing a guarantee to
the wrong layer. The layers are listed with what they **do** guarantee,
what they **cannot**, and who owns the remainder.

### 2.1 Cryptographic guarantees

| Guarantees                                                                             | Cannot guarantee                                                      |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| No individual ballot is decrypted in `EPD2-HOM-1`                                      | That the client encrypted what the voter chose                        |
| The aggregate cannot be decrypted below a trustee quorum                               | That a quorum will not collude                                        |
| A published ballot cannot be altered without detection from the record                 | That anyone will check                                                |
| A malformed or out-of-range ballot is rejected by proof verification                   | That the implementation verifies proofs correctly (`F-INF-2`)         |
| The confirmation code reveals nothing about the choice `[E-05]`                        | That the **fact of participation** is not itself coercive information |
| A copied ciphertext cannot be resubmitted without knowledge of its plaintext (`BM-14`) | Anything about the voter's physical surroundings                      |

**Owner of the remainder:** PACK-16B (parameters, ceremony), PACK-16D
(implementation correctness).

### 2.2 Client guarantees

| Guarantees                                                                              | Cannot guarantee                               |
| --------------------------------------------------------------------------------------- | ---------------------------------------------- |
| No persistent storage, no analytics, no third-party origin, no fingerprinting (ADR-096) | That the browser or operating system is honest |
| No credential or ballot material survives the visit (PACK-15 §13.3)                     | That an extension is not reading the page      |
| Challenge/spoil is offered on equal footing with casting (`BM-11`)                      | That the voter uses it, or understands it      |
| Randomness self-test refuses to encrypt on failure (`T-P16A-35`)                        | The quality of browser entropy in general      |

**Owner of the remainder:** out of scope for every candidate system
assessed; stated as `RR-05`, and **not** claimed to be solved.

### 2.3 Controlled-environment guarantees

Available only where a physical channel exists.

| Guarantees                                           | Cannot guarantee                                   |
| ---------------------------------------------------- | -------------------------------------------------- |
| An unobserved interval, physically enforced          | That the voter can reach the location              |
| A device the organisation controls                   | That the organisation is trustworthy               |
| Assistance under supervision by more than one person | That an assisted voter is not pressured beforehand |

**This is the only layer that addresses `T-P16A-26` and `T-P16A-30` at
all.** Every other layer treats them as unmitigated.

### 2.4 Remote-device limitations

Stated as findings, not as risks to be managed away:

```text
A screenshot of any screen the voter sees is transferable.
A screen recording of the whole session is transferable.
A browser extension can observe everything the page renders.
A co-present observer sees the selection before it is encrypted.
Remote desktop and screen sharing reproduce the observer at a distance.
A device the coercer supplied is a device the coercer controls.
```

**None of these is addressed by cryptography, and none is addressed by the
selected profile.** They are addressed, partially, by prohibition and
guidance (§6) and, properly, only by changing the channel.

### 2.5 Organizational controls

| Control                                                                | Effect                                                      |
| ---------------------------------------------------------------------- | ----------------------------------------------------------- |
| Separation of duties across election roles                             | Prevents insider concentration; does nothing about coercion |
| Trustees from independent organisations                                | Raises the cost of collusion                                |
| Independent Auditor concurrence for exclusions and aborts              | Prevents unilateral outcome changes                         |
| A long voting window                                                   | Increases the chance an unobserved interval exists          |
| Governed content telling participants to vote in private               | Informs; enforces nothing                                   |
| **A governance decision not to hold a high-coercion-risk vote online** | **The only organizational control that actually works**     |

### 2.6 Legal and governance controls

| Control                                                       | Effect                                                                |
| ------------------------------------------------------------- | --------------------------------------------------------------------- |
| Election-specific authorization before activation             | Forces a per-context decision rather than a default                   |
| Prohibition of public-election activation by default          | Removes the highest-coercion class from scope entirely                |
| Offence and complaint procedures for coercion and vote buying | Deterrent; after the fact                                             |
| A declaration that the vote was cast freely and in secret     | ODIHR recommends one for Estonia `[E-40]`; evidential, not preventive |

---

## 3. What the ballot tracker is, and what it is not

The `EPD2-HOM-1` receipt is a **confirmation code** derived entirely from
the encryptions of the ballot and the election's extended base hash
(`BM-03`, `[E-05]`).

| The confirmation code **is**                               | The confirmation code **is not**                                 |
| ---------------------------------------------------------- | ---------------------------------------------------------------- |
| A pointer to an entry on the bulletin board                | A proof of which option was selected                             |
| Evidence that a ballot with these encryptions was recorded | Evidence of what those encryptions contain                       |
| Checkable by anyone holding the code                       | Decryptable by anyone, including its holder                      |
| Evidence that the holder **participated**                  | — and this is the residual: participation itself can be coercive |

**Why a receipt must not reveal the choice.** If it did, it would be a
transferable proof of vote, saleable and demandable. Council of Europe
Standard 23 states the requirement directly: _"An e-voting system shall not
provide the voter with proof of the content of the vote cast for use by
third parties"_ `[E-56]`.

**Why verifiability must not become transferable proof.** Standard 15
requires the voter to be able to verify; Standard 23 forbids giving her
proof usable by a third party; Standard 25 requires that superseded choices
remain secret `[E-56]`. **These three standards are in tension, and that
tension is the entire field.** Every scheme in the comparison is a
different attempted resolution, and every one of them pays for it
somewhere. `EPD2-HOM-1`'s resolution is the narrowest available: the voter
can check **presence**, and nobody — including her — can check **content**.

**The residual, stated:** a confirmation code proves participation. In a
context where a coercer demands proof that someone voted at all — a
turnout-buying attack, or forced participation — the code is usable against
its holder. This cannot be removed without removing verifiability.
`T-P16A-25` records it.

---

## 4. Cast-as-intended, in the words a participant should be told

The challenge mechanism is the only cast-as-intended control in this
profile. Its honest description:

> When you finish choosing, the app locks in a code for your ballot. You
> can then either cast it, or open it up to check that the app encrypted
> what you actually chose. If you open it, that ballot is thrown away and
> you start again — that is the point: a ballot that has been opened cannot
> be counted, so the app cannot know in advance whether you will check it.
>
> If enough people check, a dishonest app is caught. If you check once and
> it is correct, that tells you the app was honest **that time**. It does
> not prove it will be honest next time, and it does not prove it is honest
> for everyone else.

That last paragraph is the part usually omitted. **Challenge detects a
cheating device probabilistically and in aggregate.** A device that cheats
on one ballot in a hundred is likely to be caught across an electorate and
unlikely to be caught by any individual voter.

**And the empirical limit:** in the most mature remote-voting deployment in
the world, the share of voters who verified peaked at **9.9 %** `[E-29]`.
A verification mechanism used by one voter in ten is a real control, and it
is not the control most descriptions imply.

---

## 5. Does revoting help against coercion?

**Sometimes, under assumptions that often fail, and at a cost.**

| Question                               | Answer                                                                                                                                                                                                                                 |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Does revoting help?                    | Only if the coercer **cannot occupy the last moment** of the voting window. Its guarantee is temporal, not cryptographic                                                                                                               |
| Under what assumptions does it help?   | The coercer leaves before the window closes; cannot observe _whether_ a revote happened; and does not simply supervise until closing time                                                                                              |
| What does it not solve?                | **Forced abstention.** Household and workplace coercion spanning the whole window. A coercer who returns at the end                                                                                                                    |
| What does it cost?                     | Belenios caveat #1 — an undetectable server-side rollback of the latest ballot `[E-15]`; and in Estonia, a device attack that defeats individual verifiability by exploiting revoting `[E-28a]`                                        |
| Was it made to work cryptographically? | It was attempted (VoteAgain) and **broken**, with no fix proposed `[E-44]`                                                                                                                                                             |
| Official assessments                   | Belenios calls it _"a (moderate) protection against coercion"_ `[E-14]`; Springall et al. call Estonia's _"relatively strong protection against in-person, individual coercion… More sophisticated attacks remain possible"_ `[E-28b]` |

**EPD²'s decision: no revoting in `EPD2-HOM-1`.**
`PACK-16A-REVOTING-AND-BALLOT-LIFECYCLE.md` §2 is the reasoning and §2.4 is
the honest account of what that costs.

### 5.1 In-person override

Assessed as the **strongest available** coercion control, because it
changes the environment rather than adding a second chance inside a
compromised one. Not adopted in this round, because reconciling two
channels requires knowing which participants voted in person — a
per-participant fact that PACK-15's boundary forbids from reaching the
tally. Estonia solves it by keeping the identity binding `[E-24]`, and that
route is closed here. `OD-P16A-09` carries a scope-level variant.

### 5.2 Paper override

**Available today, and it is not a technical feature.** For any context
where coercion risk is judged material, governance may decide to hold the
vote on paper. `PACK-16A-GERMAN-LEGAL-BOUNDARY.md` §8 makes this an
explicit permitted outcome of the activation gate. For statutory candidate
nominations it is not merely permitted but **required** `[E-51]`.

---

## 6. How verification can become a coercion instrument

Verification is usually presented as protective. It has an attack surface.

| Path                                                                     | Control                                                                                                         | Residual                                                          |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A coercer compels a verification session and reads the choice off screen | **Verification shows presence of a code on the board, never a choice.** No operation reveals a choice post-cast | A coercer present during **casting** already has the choice       |
| A fake verification interface reassures a voter whose ballot was dropped | Published board and mirror addresses; the whole board is independently downloadable (`BB-09`)                   | A voter who uses only the handed-to-them interface is unprotected |
| A fake interface shows the coercer what he wants                         | Same                                                                                                            | Same                                                              |
| The verification origin is the casting origin                            | **Separate origin, mandatory** (`BB-14`)                                                                        | —                                                                 |
| Verification timing identifies the voter's board entry                   | Board reads unauthenticated and not logged per entry; full-board download available (`BB-09`)                   | A mirror operator can observe fetches                             |
| A coercer demands the confirmation code                                  | The code reveals nothing about the choice                                                                       | **It proves participation** — unavoidable                         |

---

## 7. Permitted claims registry

**These may be stated, in these words, with these qualifications.**

| ID      | Permitted claim                                                                         | Required qualification                                                         |
| ------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `PC-01` | "No individual ballot is decrypted."                                                    | Add: "in this election profile"                                                |
| `PC-02` | "The result cannot be decrypted without a quorum of trustees."                          | Add: "acting together"                                                         |
| `PC-03` | "Your receipt does not show how you voted."                                             | none                                                                           |
| `PC-04` | "You can check that your ballot is on the public list."                                 | none                                                                           |
| `PC-05` | "Anyone can check that the published result matches the published ballots."             | Add: "using an independent verifier"                                           |
| `PC-06` | "No result, partial result or turnout figure is available before the vote closes."      | none                                                                           |
| `PC-07` | "You can check that the app encrypted what you chose, before you cast."                 | Add: "the ballot you check is discarded"                                       |
| `PC-08` | "The system cannot tell anyone how you voted."                                          | Add: "and cannot tell anyone whether a particular person voted"                |
| `PC-09` | "Ballots cannot be altered or removed without this being visible in the public record." | Add: "provided the record is checked"                                          |
| `PC-10` | "The system is designed so that no single administrator can decrypt anything."          | none                                                                           |
| `PC-11` | "This design has been specified and is awaiting external review."                       | Required whenever the architecture is described at all, until review completes |

**Every claim above is conditional on the assumptions in
`PACK-16A-BALLOT-MODEL-SPECIFICATION.md` §3.4.** A claim quoted without its
qualification is a prohibited claim.

---

## 8. Prohibited claims registry

**These may not be used, in any document, interface, notification, press
statement, grant application or handover, unless and until a specific
proof is produced and cited.**

| Prohibited                                        | Why                                                                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `coercion-proof`                                  | No remote system is; `[E-46]`                                                                                 |
| `fully coercion-resistant`                        | Not claimed by any candidate; JCJ's own property is contested `[E-37]`                                        |
| `impossible to buy votes`                         | Turnout buying and forced participation remain                                                                |
| `impossible to force a voter`                     | `T-P16A-26`, `T-P16A-30` are unmitigated                                                                      |
| `absolute ballot secrecy`                         | Secrecy is conditional on trustee non-collusion and on client honesty                                         |
| `unhackable`                                      | Meaningless and false                                                                                         |
| `fraud-proof`                                     | Detection is not prevention                                                                                   |
| `mathematically impossible to manipulate`         | The mathematics is conditional on parameters, implementation and quorum                                       |
| `end-to-end verifiable` **without qualification** | Requires a board, mirrors, an independent verifier and take-up — none of which exists yet                     |
| `anonymous`                                       | Unlinkable under stated assumptions ≠ anonymous                                                               |
| `BSI certified`                                   | The current BSI protection profile is scoped to **non-political** elections and nothing is certified `[E-53]` |
| `BVerfG compliant`                                | The Court has never ruled on cryptographic verifiability; any such claim is an extrapolation `[E-41]`         |
| `legally compliant` / `legally ready`             | No legal assessment has been performed                                                                        |
| `approved for public elections`                   | Prohibited by default                                                                                         |
| `production ready`                                | It is not                                                                                                     |
| `implemented` / `implementation complete`         | Nothing is implemented                                                                                        |
| `external CI pass` / `final pass` for this tree   | Not claimed                                                                                                   |

### 8.1 Required alternatives

```text
SPECIFIED
ASSESSED
PROPOSED
SELECTED FOR ARCHITECTURAL REVIEW
REQUIRES EXTERNAL REVIEW
REQUIRES LEGAL ASSESSMENT
DEFERRED TO PACK-16B / PACK-16C / PACK-16D
NOT PRODUCTION READY
NOT LEGALLY ACTIVATED
PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT
```

### 8.2 Enforcement

`PACK-16A-ACCEPTANCE-MATRIX.md` `AC-P16A-071` … `AC-P16A-074` make the
registries checkable: a prohibited-phrase scan over repository
documentation and over governed participant-facing content is an
implementation-stage obligation, and a violation is a **PASS blocker**.
`PACK-16A-REASON-CODE-SPECIFICATION.md` §9 forbids reason-code text from
carrying a prohibited claim.

---

## 9. The paragraph this document exists to make possible

When someone asks whether EPD² voting is secret, the correct answer is:

> The system is designed so that no component and no combination of two
> components can connect a person to a ballot, and so that no individual
> ballot is ever decrypted. That design has been specified and has not yet
> been built, reviewed or legally assessed. It does not protect you from
> someone standing behind you while you vote, and no online voting system
> anywhere does. If that is a risk for you, vote in person where that is
> offered, and tell us if it is not.

Every clause is defensible from a cited source. **That is the standard.**

**SPECIFIED. ASSESSED. REQUIRES EXTERNAL REVIEW. REQUIRES LEGAL
ASSESSMENT. NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
