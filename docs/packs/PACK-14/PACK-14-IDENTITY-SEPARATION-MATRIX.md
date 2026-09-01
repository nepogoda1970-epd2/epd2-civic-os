# PACK-14 — Identity Separation Matrix

**Round:** PACK-14 — specification and ADR only. **No code. Not implemented. Not a candidate. Not a PASS.**
**Repository version:** unchanged at `0.13.0` · **Canon version:** unchanged at `0.8.0`
**NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.**
**Architecture correction applied (2026-07-30).**

The single table this pack exists to protect. Each row is an identifier
space; the columns say what it is, who owns it, where it may appear and —
most importantly — where it may not.

## 1. Identifier spaces

| Identifier                 | Owner                             | Purpose                                | May appear in                                                | May **never** appear in                                                                                    | Optional? |
| -------------------------- | --------------------------------- | -------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | --------- |
| `account_id`               | Account Registry                  | Authentication and session subject     | Account Registry, Authentication, Session, Recovery contexts | Any other domain's records or events; any projection; any voting-side artifact; any public surface         | no        |
| `person_record_id`         | Identity Verification (canon 7.3) | Subject of identity proofing           | Identity proofing case and its evidence                      | Integration keys; membership records; finance records; events outside proofing; any join with `account_id` | **yes**   |
| `membership_id`            | Membership domain                 | The governed relationship              | Membership domain records and decisions                      | Login; authentication; session; voting-side artifacts                                                      | yes       |
| `member_number`            | Membership domain                 | Visible organizational number          | Organizational documents, member-facing display              | Login identifier; correlation key; authentication input; voting handoff                                    | yes       |
| applicant reference        | Membership application            | An application in progress             | `MembershipApplication` and its decision record              | Anything implying membership before canon 19d.9 stage B                                                    | yes       |
| `communication_persona_id` | Communication domain              | Permitted internal appearance          | Communication surfaces                                       | Authentication; membership decisions; voting linkage; identity proofing                                    | yes       |
| voting credential          | **PACK-15/16**                    | Voting                                 | Voting domain only                                           | Everywhere else. Not specified by PACK-14                                                                  | n/a       |
| scoped actor reference     | Derived per purpose               | What domains and events actually carry | Any domain, scoped to its purpose and organizational scope   | Being reused across purposes; being reversed to `account_id` without a governed mapping                    | no        |

## 2. Identifiers explicitly forbidden as universal keys

`email`, `phone`, `member_number`, `account_id`, `person_record_id`,
national ID, eID subject identifier, device identifier,
`communication_persona_id`, and any provider-issued stable subject claim.

None of these may be used as a join key between two domains, as a
correlation key, or as a login identifier where the table above says
otherwise.

## 3. Permitted correlation — the mapping boundary

A correlation between two identifier spaces exists only through an explicit
governed mapping boundary carrying **all** of:

| Property                                | Why it is mandatory                                                      |
| --------------------------------------- | ------------------------------------------------------------------------ |
| purpose                                 | A mapping without a purpose is a general-purpose mapping                 |
| organizational scope                    | `FIR-INV-013`: Bund/Land/Kreis isolation applies to mappings too         |
| domain owner                            | Someone must be answerable for it                                        |
| access policy                           | Otherwise "governed" means "documented"                                  |
| retention                               | A mapping that never expires becomes the global identifier by longevity  |
| audit evidence                          | An unobserved correlation is an unaccountable one                        |
| prohibition on uncontrolled correlation | Stated in the boundary itself, so a later reader cannot infer permission |

**A mapping boundary is not a table anyone may join.** It is a governed
operation with a reason code, and its absence is a refusal.

## 4. Lifecycle independence

| Situation                                          | Permitted? | Note                                                        |
| -------------------------------------------------- | ---------- | ----------------------------------------------------------- |
| Account with no person record and no membership    | yes        | The common case at registration                             |
| Account closed, membership continues               | yes        | Membership is a legal relationship, not a login             |
| Membership terminated, account continues           | yes        | The person may still be an applicant, a citizen, a claimant |
| Member with no account at all                      | yes        | Assisted and offline channels (`FIR-INCLUSION-001`)         |
| Applicant automatically becoming a member          | **no**     | Canon 19d.9 stage B requires a human decision               |
| Account ID used to log in as a member number       | **no**     | §2                                                          |
| Two accounts merged by matching email              | **no**     | ADR-080; duplicate handling is a reviewed decision          |
| Provider subject claim stored as the account's key | **no**     | ADR-079 §3                                                  |

## 5. Four concepts that are never equivalent

```text
authentication          — who is operating this session, and how strongly
identity proofing       — whether a claimed real-world identity was verified
membership eligibility  — whether the party's rules admit this person
authorization           — whether this actor may perform this act now
```

Authentication does not prove legal identity. Identity proofing does not
approve membership. Membership does not create a voting credential.
Authorization is decided per act, not per login.
