# PACK-16D — Canonical Encoding Specification (`EPD2-ENC-1`)

**Round:** PACK-16D — Cryptographic Implementation Architecture, Reference
Components, Atomic Persistence, Test Vectors and Verification Harness.
**Reference implementation. Not production code. Not certified. Not a PASS.**
**Repository version:** unchanged at `0.16.0` · **Canon version:** unchanged at `0.8.0`
**ADR:** `ADR-102`, status `proposed`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED. PUBLIC-ELECTION ACTIVATION PROHIBITED BY DEFAULT.**

---

## 1. The grammar

`ENCODING_VERSION = "EPD2-ENC-1"`, defined in
`services/voting-service/src/epd2_voting_service/reference/crypto/encoding.py`.
All lengths are big-endian.

```text
UINT(n, width)  fixed-width big-endian; no short form, no leading-zero elision
BYTES(b)        = UINT(len(b), 4) || b
TEXT(s)         = BYTES(NFC(s).encode("utf-8"))
SEQ(xs)         = UINT(len(xs), 4) || BYTES(x0) || BYTES(x1) || ...
FIELD(name, v)  = TEXT(name) || BYTES(v)
STRUCT(fields)  = UINT(len(fields), 4) || FIELD... ; ordered, NEVER sorted
```

| ID      | Rule                                                                                                                                                                               |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-01` | **Hashes and signatures are computed over these bytes and over nothing else.** There is no second serialisation of any artefact anywhere in the reference implementation           |
| `CE-02` | Every length prefix is exactly 4 bytes. A count and a length are the same width everywhere, so no reader needs to know which one it is looking at to advance                       |
| `CE-03` | Group elements are always the full `\|p\|` bytes and scalars always the full `\|q\|` bytes (`encode_group_element`, `encode_scalar`). There is **no short form to disagree about** |

## 2. Why a binary tuple encoding and not canonical JSON

The reference implementation deliberately does not use "JSON that happens
to look stable". The module docstring gives the reason and it is the whole
argument: **ordinary JSON is not canonical.**

| ID      | JSON property                                                     | Consequence for a digest                                              |
| ------- | ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| `CE-04` | Object key order is unspecified                                   | Two conforming encoders produce different bytes for the same value    |
| `CE-05` | Integer and float are not distinguished at the syntax level       | `1` and `1.0` are the same number and different bytes                 |
| `CE-06` | Unicode escaping is optional and multi-form                       | `"é"`, `"é"` and a decomposed `"é"` are three encodings of one string |
| `CE-07` | Whitespace is insignificant to a parser and significant to a hash | Pretty-printing an artefact changes its digest                        |

A canonical-JSON _profile_ can pin all of these, but it does so by adding
rules on top of a format whose default behaviour violates them. Every
consumer must then implement the profile correctly, and a consumer that
merely implements JSON correctly produces wrong digests while looking
right. `EPD2-ENC-1` inverts that: the encoding has no free choices to get
wrong. There is no whitespace, no escaping, no number syntax, and no key
ordering, because none of those concepts exist in it.

| ID      | Rule                                                                                                                                                                                                                            |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-08` | **Canonical form is a property of the format here, not a discipline layered on it.** A conforming encoder cannot produce a non-canonical `EPD2-ENC-1` byte string, because the format admits exactly one encoding of each value |

## 3. Field order is normative; maps are prohibited

`encode_struct(fields)` takes an **ordered sequence** of
`(name, encoded_value)` pairs and emits them in that order.

| ID      | Rule                                                                                                                                                                                                                                                                  |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-09` | **`encode_struct` never sorts.** Declaration order in the source is the wire order and is normative. Reordering the fields of a struct is a breaking change to every digest derived from it                                                                           |
| `CE-10` | **Maps are prohibited outright as an input type.** A map has no order, so an encoder that accepted one would have to invent an ordering rule — and that rule would then be the thing implementations disagree about. Removing the input type removes the disagreement |
| `CE-11` | Field names are themselves `TEXT`, so they are length-prefixed and NFC-normalised like any other string. A field name cannot run into its value                                                                                                                       |
| `CE-12` | `test_canonical_struct_field_order_is_normative` in `tests/reference/test_crypto_units.py` asserts that `[("a",1),("b",2)]` and `[("b",2),("a",1)]` encode to different bytes — the property is pinned, not merely intended                                           |

### 3.1 Duplicate field names are rejected

`encode_struct` tracks the names it has seen and raises
`CanonicalEncodingError` (`reason_code = "INVALID_CANONICAL_ENCODING"`) on
the second occurrence of a name.

| ID      | Rule                                                                                                                                                                                     |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-13` | A duplicate field is **rejected, never deduplicated and never last-wins**. Both of those resolutions are silent, and a silent resolution is a place where two implementations can differ |
| `CE-14` | `test_canonical_struct_rejects_duplicate_fields` pins this, matching on the message `duplicate field`                                                                                    |

## 4. Text is NFC-normalised

`normalize_text(s)` is `unicodedata.normalize("NFC", s)`, applied by
`encode_text` before UTF-8 encoding.

| ID      | Rule                                                                                                                                                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CE-15` | **NFC is the single permitted normalisation form.** Two Unicode spellings of the same string — a precomposed `é` and an `e` followed by a combining acute — encode to identical bytes and therefore to identical digests |
| `CE-16` | Without this rule, an artefact could be re-serialised by a client on a platform with different default normalisation and stop matching its own digest. That failure would look like tampering                            |
| `CE-17` | `test_text_is_nfc_normalised` asserts both that the two source strings differ and that their encodings are equal, so the test cannot pass vacuously                                                                      |
| `CE-18` | Normalisation is applied on **encode only**. `EPD2-ENC-1` does not preserve the caller's original spelling, and this is intentional: the encoding's job is to make the two indistinguishable                             |

## 5. Fixed width, and the rejection of short forms

| ID      | Rule                                                                                                                                                                                                                       |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-19` | `encode_uint(value, width)` emits exactly `width` bytes. It **raises rather than truncates** if the value does not fit, and **raises on a negative value** — negative integers are not canonically encodable at all        |
| `CE-20` | `decode_uint(raw, width)` **rejects an input of the wrong width rather than padding it**. `decode_uint(b"\x01", 4)` is an error, not the integer 1                                                                         |
| `CE-21` | A group element carries the modulus width and a scalar the order width regardless of magnitude, so a small value and a large value of the same kind are the same size. A length is never a channel for a value's magnitude |
| `CE-22` | `test_canonical_encoding_is_fixed_width_and_rejects_short_forms` pins all four behaviours: the fixed-width encoding of 1, its round trip, the short-form rejection, the negative rejection and the overflow rejection      |

### 5.1 Declared limits

| Constant        | Value     | Applies to                                                    |
| --------------- | --------- | ------------------------------------------------------------- |
| `MAX_BYTES_LEN` | `1 << 24` | `encode_bytes`                                                |
| `MAX_SEQ_LEN`   | `1 << 20` | `encode_seq`                                                  |
| `MAX_TEXT_LEN`  | `1 << 16` | `encode_text` (measured in characters, before UTF-8 encoding) |

| ID      | Rule                                                                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-23` | Exceeding a limit raises `CanonicalEncodingError`. The limits exist so that a hostile input cannot force an unbounded allocation inside a hash preimage |

## 6. Length ambiguity: why `("ab","c")` and `("a","bc")` cannot collide

A length-ambiguous encoding is one where the boundary between two
adjacent values can be moved without changing the byte string. It is the
classic way a hash over concatenated fields is attacked: if `A || B` is
just the concatenation of two variable-length strings, then `("ab","c")`
and `("a","bc")` produce identical preimages, and a signature over one is
a signature over the other.

`EPD2-ENC-1` prevents this structurally. Each `TEXT` value carries its own
4-byte length before its bytes, so the two cases differ in the length
prefix long before the payload:

```text
("ab","c")   ... UINT(2,4) || "ab" || ... UINT(1,4) || "c"
("a","bc")   ... UINT(1,4) || "a"  || ... UINT(2,4) || "bc"
```

| ID      | Rule                                                                                                                                                                                                                                   |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-24` | **Every variable-length value is length-prefixed before its content.** The boundary between adjacent values is carried in the bytes, not inferred from them                                                                            |
| `CE-25` | `test_p05b_struct_is_not_length_ambiguous` in `tests/reference/test_property.py` pins exactly this pair: it encodes `[("f", TEXT("ab")), ("g", TEXT("c"))]` and `[("f", TEXT("a")), ("g", TEXT("bc"))]` and asserts the results differ |
| `CE-26` | The struct's leading field count is a second, independent boundary: a struct of `n` fields cannot be reinterpreted as a struct of `n ± 1` fields without changing its first four bytes                                                 |

## 7. The gap that was here, and how it was found

This section used to record a caller obligation: `encode_struct` and
`encode_seq` appended the bytes they were handed **verbatim**, adding only
the field name and the element count, so non-ambiguity held only if every
caller passed an already-canonical value. That was not a caller obligation.
It was a defect, and it made the encoding ambiguous:

```text
SEQ([b"ab", b"c"])   and   SEQ([b"a", b"bc"])
```

both flattened to `UINT(2,4) || "abc"` — **two different sequences sharing
one digest**, which is exactly the length-ambiguity §6 says the format
prevents. `encode_struct` appended field values raw for the same reason.

**Both functions now length-prefix.** `encode_seq` emits
`UINT(len, 4) || BYTES(item)…` and `encode_struct` emits
`UINT(len, 4) || TEXT(name) || BYTES(value)…`, which is what the grammar in
§1 always said.

| ID      | Rule                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-27` | **`BYTES(v)` in `FIELD(name, v)` and `BYTES(x)` in `SEQ` are emitted by the encoder itself**, not supplied by the caller. A caller passes a value; the encoder adds its length. There is no longer a class of call site that can weaken the guarantee by passing an unwrapped blob                                                                                                                                     |
| `CE-28` | **Non-ambiguity of a struct or sequence therefore holds unconditionally**, for any byte values whatsoever. The boundary between adjacent items and between a field name and its value is carried in the bytes in every case, not inferred from a schema the reader is assumed to share                                                                                                                                 |
| `CE-29` | **The defect was found by an independent implementation, not by review and not by a self-generated vector.** `tests/reference/crossimpl/independent_verifier.mjs` — a Node.js program that re-derives the encoding from the _written grammar_ of §1 rather than from `encoding.py` — disagreed with the Python output. The document and the code had diverged, and only something built from the document could see it |
| `CE-30` | **Every digest in the round changed as a result**, because every artefact digest is taken over a struct. The internal stability vectors caught the change, which is the one thing stability vectors are for: they cannot tell you the old value was wrong, but they will not let it change quietly                                                                                                                     |
| `CE-31` | This is the round's clearest evidence for why self-generated vectors are not conformance evidence. **An error made consistently by one implementation is invisible to that implementation's own vectors**, however many of them there are                                                                                                                                                                              |

## 8. What is not implemented

| ID      | Limitation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CE-32` | **There is no general decoder.** `encoding.py` exports `decode_uint` and nothing else. `EPD2-ENC-1` is a one-way encoding this round: the verifier re-encodes artefacts it has parsed from a transport format and compares digests, rather than parsing canonical bytes directly. A conformance decoder is unfinished work                                                                                                                                                                                                                                                                                                                         |
| `CE-33` | **`EPD2-ENC-1` is an EPD² decision with no external counterpart, so no published external vector for it exists** — that absence is declared by name in `PRIMARY_SOURCE_UNAVAILABLE` in `reference/testing/conformance.py` rather than filled with a self-generated value. What does exist is cross-implementation evidence: the Node.js oracle of `CE-29` encodes independently and agrees byte-for-byte. The 23 internal stability vectors keep their `stability-only (interoperability NOT established)` status and prove stability, not agreement. Full interoperability with any other implementation remains **unestablished** (`OD-P16D-02`) |
| `CE-34` | Canonicality is enforced on the encode path only. Bytes that arrive from outside and claim to be `EPD2-ENC-1` are not validated as canonical, because there is nothing to validate them with (see `CE-32`)                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `CE-35` | `MAX_TEXT_LEN` bounds characters, while `MAX_BYTES_LEN` bounds bytes; a string of `MAX_TEXT_LEN` multi-byte characters is larger than its character count suggests. Both bounds hold, but they are not the same bound                                                                                                                                                                                                                                                                                                                                                                                                                              |

## 9. What this document does not decide

```text
A general EPD2-ENC-1 decoder               → PACK-17
A second complete independent
  implementation                           → OD-P16D-02, PACK-17
Transport / at-rest serialisation format   → out of scope; digests are over EPD2-ENC-1 only
Schema evolution and migration             → EPD2-SCHEMA-1; migration is never silent
Constant-time encoding behaviour           → OD-P16D-05; not claimed
```

**REFERENCE IMPLEMENTATION. REQUIRES EXTERNAL REVIEW. NOT PRODUCTION READY.
NOT LEGALLY ACTIVATED.**
