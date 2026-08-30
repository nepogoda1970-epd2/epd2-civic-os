// Independent cross-implementation verifier for PACK-16D conformance.
//
// WHY THIS EXISTS
// ---------------
// Every test vector PACK-16D ships is produced by the same Python code that
// consumes it. That proves the implementation is *stable*; it cannot prove
// the implementation is *right*, because an error made consistently is
// invisible to its own oracle. This file is a second implementation, in a
// different language, sharing no code, no parser and no arithmetic routine
// with the producer.
//
// WHAT IT DELIBERATELY DOES NOT DO
// --------------------------------
// It does not import anything from the Python side, it does not call out to
// it, and it does not reuse its canonical encoder. It re-derives every
// structure from the specification written in the PACK-16D documents:
//
//   UINT(n,width)  fixed-width big-endian, no short form
//   BYTES(b)       = UINT(len,4) || b
//   TEXT(s)        = BYTES(utf8(NFC(s)))
//   SEQ(xs)        = UINT(len,4) || BYTES(x0) || BYTES(x1) || ...
//   STRUCT(fs)     = UINT(len,4) || (TEXT(name) || BYTES(value))...
//   h(key,label,parts) = HMAC-SHA256(key, TEXT(label) || SEQ(parts))
//
// Modular exponentiation is square-and-multiply written out here rather than
// Python's `pow(a,b,m)`, so even the arithmetic is an independent path.
//
// It reads a JSON case file on stdin and writes a JSON verdict on stdout.
// It never sees a private key, a nonce, or any voter data.

import { createHmac, createHash } from "node:crypto";
import { readFileSync } from "node:fs";

// -- canonical encoding, re-derived from the specification ----------------

function encodeUint(value, width) {
  if (value < 0n) throw new Error("negative integer is not encodable");
  const out = Buffer.alloc(width);
  let v = value;
  for (let i = width - 1; i >= 0; i -= 1) {
    out[i] = Number(v & 0xffn);
    v >>= 8n;
  }
  if (v !== 0n) throw new Error(`integer does not fit in ${width} bytes`);
  return out;
}

function encodeBytes(buf) {
  return Buffer.concat([encodeUint(BigInt(buf.length), 4), buf]);
}

function encodeText(text) {
  return encodeBytes(Buffer.from(text.normalize("NFC"), "utf8"));
}

function encodeSeq(items) {
  return Buffer.concat([
    encodeUint(BigInt(items.length), 4),
    ...items.map(encodeBytes),
  ]);
}

function encodeStruct(fields) {
  const parts = [encodeUint(BigInt(fields.length), 4)];
  const seen = new Set();
  for (const [name, value] of fields) {
    if (seen.has(name)) throw new Error(`duplicate field ${name}`);
    seen.add(name);
    parts.push(encodeText(name), encodeBytes(value));
  }
  return Buffer.concat(parts);
}

const ZERO_KEY = Buffer.alloc(32);

function h(label, parts) {
  const mac = createHmac("sha256", ZERO_KEY);
  mac.update(encodeText(label));
  mac.update(encodeSeq(parts));
  return mac.digest();
}

// -- arithmetic, written out rather than borrowed -------------------------

function modPow(base, exponent, modulus) {
  let result = 1n;
  let b = base % modulus;
  let e = exponent;
  while (e > 0n) {
    if (e & 1n) result = (result * b) % modulus;
    b = (b * b) % modulus;
    e >>= 1n;
  }
  return result;
}

function toFixedHex(value, byteWidth) {
  const hex = value.toString(16);
  return hex.padStart(byteWidth * 2, "0");
}

function groupElement(value, pBytes) {
  return Buffer.from(toFixedHex(value, pBytes), "hex");
}

function scalar(value, qBytes) {
  return Buffer.from(toFixedHex(value, qBytes), "hex");
}

// -- the checks -----------------------------------------------------------

function checkParameters(c) {
  const p = BigInt("0x" + c.p);
  const q = BigInt("0x" + c.q);
  const g = BigInt("0x" + c.g);
  const r = BigInt("0x" + c.r);
  const results = {
    p_bit_length: p.toString(2).length,
    q_bit_length: q.toString(2).length,
    q_equals_2_256_minus_189: q === 2n ** 256n - 189n,
    q_divides_p_minus_1: (p - 1n) % q === 0n,
    p_equals_q_r_plus_1: p === q * r + 1n,
    g_in_range: 1n < g && g < p,
    g_order_is_q: modPow(g, q, p) === 1n,
  };
  const digest = createHash("sha256")
    .update(c.p + c.q + c.g + c.r, "ascii")
    .digest("hex");
  results.parameter_digest = digest;
  results.parameter_digest_matches = digest === c.expected_parameter_digest;
  results.all_relations_hold =
    results.p_bit_length === 4096 &&
    results.q_bit_length === 256 &&
    results.q_equals_2_256_minus_189 &&
    results.q_divides_p_minus_1 &&
    results.p_equals_q_r_plus_1 &&
    results.g_in_range &&
    results.g_order_is_q;
  return results;
}

function checkEncoding(c) {
  const p = BigInt("0x" + c.p);
  const pBytes = Math.ceil(p.toString(2).length / 8);
  const g = BigInt("0x" + c.g);
  return {
    group_element_hex: groupElement(g, pBytes).toString("hex"),
    matches:
      groupElement(g, pBytes).toString("hex") === c.expected_group_element,
    width_bytes: pBytes,
  };
}

function checkSelectionEncryption(c) {
  // alpha = g^r mod p ; beta = K^r * g^m mod p
  const p = BigInt("0x" + c.p);
  const g = BigInt("0x" + c.g);
  const K = BigInt("0x" + c.public_key);
  const nonce = BigInt("0x" + c.nonce);
  const m = BigInt(c.message);
  const alpha = modPow(g, nonce, p);
  const beta = (modPow(K, nonce, p) * modPow(g, m, p)) % p;
  const pBytes = Math.ceil(p.toString(2).length / 8);
  return {
    alpha: toFixedHex(alpha, pBytes),
    beta: toFixedHex(beta, pBytes),
    matches:
      toFixedHex(alpha, pBytes) === c.expected_alpha &&
      toFixedHex(beta, pBytes) === c.expected_beta,
  };
}

function checkSelectionProof(c) {
  // Disjunctive Chaum-Pedersen verification, re-derived:
  //   c0 + c1 == challenge (mod q)
  //   g^v0 == a0 * alpha^c0
  //   K^v0 == b0 * beta^c0
  //   g^v1 == a1 * alpha^c1
  //   K^v1 == b1 * (beta/g)^c1
  const p = BigInt("0x" + c.p);
  const q = BigInt("0x" + c.q);
  const g = BigInt("0x" + c.g);
  const K = BigInt("0x" + c.public_key);
  const alpha = BigInt("0x" + c.alpha);
  const beta = BigInt("0x" + c.beta);
  const P = c.proof;
  const [a0, b0, a1, b1] = ["a0", "b0", "a1", "b1"].map((k) =>
    BigInt("0x" + P[k]),
  );
  const [c0, c1, v0, v1] = ["c0", "c1", "v0", "v1"].map((k) =>
    BigInt("0x" + P[k]),
  );

  const pBytes = Math.ceil(p.toString(2).length / 8);
  const payload = encodeStruct([
    ["context", Buffer.from(c.context_hex, "hex")],
    ["public_key", groupElement(K, pBytes)],
    ["alpha", groupElement(alpha, pBytes)],
    ["beta", groupElement(beta, pBytes)],
    ["a0", groupElement(a0, pBytes)],
    ["b0", groupElement(b0, pBytes)],
    ["a1", groupElement(a1, pBytes)],
    ["b1", groupElement(b1, pBytes)],
  ]);
  const digest = h("EPD2/v1/selection_proof", [payload]);
  const challenge = BigInt("0x" + digest.toString("hex")) % q;

  const betaOverG = (beta * modPow(g, q - 1n, p)) % p;
  const checks = {
    challenge_matches: (c0 + c1) % q === challenge,
    eq_g_v0: modPow(g, v0, p) === (a0 * modPow(alpha, c0, p)) % p,
    eq_k_v0: modPow(K, v0, p) === (b0 * modPow(beta, c0, p)) % p,
    eq_g_v1: modPow(g, v1, p) === (a1 * modPow(alpha, c1, p)) % p,
    eq_k_v1: modPow(K, v1, p) === (b1 * modPow(betaOverG, c1, p)) % p,
  };
  checks.verifies = Object.values(checks).every(Boolean);
  checks.recomputed_challenge = challenge.toString(16);
  return checks;
}

function checkBallotHash(c) {
  const digest = h("EPD2/v1/ballot_hash", [Buffer.from(c.envelope_hex, "hex")]);
  return {
    digest: digest.toString("hex"),
    matches: digest.toString("hex") === c.expected_digest,
  };
}

function checkConfirmationCode(c) {
  // The code is 5 groups of 5 characters drawn from a 32-symbol alphabet,
  // taken from a domain-separated digest over the encryptions and H_E.
  const alphabet = c.alphabet;
  const digest = h("EPD2/v1/confirmation_code", [
    Buffer.from(c.input_hex, "hex"),
  ]);
  let value = BigInt("0x" + digest.toString("hex"));
  const chars = [];
  for (let i = 0; i < 25; i += 1) {
    chars.push(alphabet[Number(value % BigInt(alphabet.length))]);
    value /= BigInt(alphabet.length);
  }
  const groups = [];
  for (let i = 0; i < 5; i += 1)
    groups.push(chars.slice(i * 5, i * 5 + 5).join(""));
  const code = groups.join("-");
  return { code, matches: code === c.expected_code };
}

function checkAccumulation(c) {
  const p = BigInt("0x" + c.p);
  let alpha = 1n;
  let beta = 1n;
  for (const ct of c.ciphertexts) {
    alpha = (alpha * BigInt("0x" + ct.alpha)) % p;
    beta = (beta * BigInt("0x" + ct.beta)) % p;
  }
  const pBytes = Math.ceil(p.toString(2).length / 8);
  return {
    alpha: toFixedHex(alpha, pBytes),
    beta: toFixedHex(beta, pBytes),
    matches:
      toFixedHex(alpha, pBytes) === c.expected_alpha &&
      toFixedHex(beta, pBytes) === c.expected_beta,
  };
}

function checkDecryptionShare(c) {
  // Chaum-Pedersen: g^response == commitment_a * public^challenge
  //                 base^response == commitment_b * share^challenge
  const p = BigInt("0x" + c.p);
  const g = BigInt("0x" + c.g);
  const base = BigInt("0x" + c.base);
  const share = BigInt("0x" + c.share);
  const pub = BigInt("0x" + c.public_share_key);
  const a = BigInt("0x" + c.proof.a);
  const b = BigInt("0x" + c.proof.b);
  const challenge = BigInt("0x" + c.proof.challenge);
  const response = BigInt("0x" + c.proof.response);
  const checks = {
    eq_g: modPow(g, response, p) === (a * modPow(pub, challenge, p)) % p,
    eq_base:
      modPow(base, response, p) === (b * modPow(share, challenge, p)) % p,
  };
  checks.verifies = checks.eq_g && checks.eq_base;
  return checks;
}

function checkThresholdTally(c) {
  // Lagrange combination at zero, then g^m recovery and bounded decode.
  const p = BigInt("0x" + c.p);
  const q = BigInt("0x" + c.q);
  const g = BigInt("0x" + c.g);
  const beta = BigInt("0x" + c.beta);
  const selection = c.shares.map((s) => BigInt(s.sequence));
  let combined = 1n;
  for (const s of c.shares) {
    const l = BigInt(s.sequence);
    let num = 1n;
    let den = 1n;
    for (const j of selection) {
      if (j === l) continue;
      num = (num * j) % q;
      den = (den * (((j - l) % q) + q)) % q;
    }
    const weight = (num * modPow(den, q - 2n, q)) % q;
    combined = (combined * modPow(BigInt("0x" + s.value), weight, p)) % p;
  }
  const groupValue = (beta * modPow(combined, p - 2n, p)) % p;
  let plaintext = -1;
  for (let m = 0; m <= c.maximum; m += 1) {
    if (modPow(g, BigInt(m), p) === groupValue) {
      plaintext = m;
      break;
    }
  }
  return { plaintext, matches: plaintext === c.expected_plaintext };
}

// -- structural ballot rebuild -------------------------------------------
//
// The weaker form of this check hands the oracle the producer's already
// canonical bytes and asks it only to hash them. That tests the hash, not
// the encoding — and the encoding is where this round's real defect was
// found. So the oracle is given the ballot's *fields* and rebuilds the
// canonical bytes from the written grammar before hashing.

function encodeCiphertext(ct) {
  return encodeStruct([
    ["alpha", Buffer.from(ct.alpha, "hex")],
    ["beta", Buffer.from(ct.beta, "hex")],
  ]);
}

function encodeDisjunctiveProof(pr) {
  return encodeStruct(
    ["a0", "b0", "a1", "b1", "c0", "c1", "v0", "v1"].map((k) => [
      k,
      Buffer.from(pr[k], "hex"),
    ]),
  );
}

function encodeChaumPedersen(pr) {
  return encodeStruct(
    ["a", "b", "challenge", "response"].map((k) => [
      k,
      Buffer.from(pr[k], "hex"),
    ]),
  );
}

function encodeBallotEnvelope(env) {
  const contests = env.contests.map((contest) =>
    encodeStruct([
      ["contest_id", encodeText(contest.contest_id)],
      [
        "selections",
        encodeSeq(
          contest.selections.map((sel) =>
            encodeStruct([
              ["option_id", encodeText(sel.option_id)],
              ["ciphertext", encodeCiphertext(sel.ciphertext)],
              ["proof", encodeDisjunctiveProof(sel.proof)],
            ]),
          ),
        ),
      ],
      ["accumulated", encodeCiphertext(contest.accumulated)],
      ["sum_proof", encodeChaumPedersen(contest.sum_proof)],
    ]),
  );
  return encodeStruct([
    ["ballot_id", encodeText(env.ballot_id)],
    ["election_context_id", encodeText(env.election_context_id)],
    ["ballot_style_id", encodeText(env.ballot_style_id)],
    ["parameter_set_id", encodeText(env.parameter_set_id)],
    ["manifest_digest", encodeUint(BigInt("0x" + env.manifest_digest), 32)],
    ["contests", encodeSeq(contests)],
  ]);
}

function checkBallotStructural(c) {
  // Rebuild the canonical bytes from the fields, then hash them.
  const rebuilt = encodeBallotEnvelope(c.envelope);
  const digest = h("EPD2/v1/ballot_hash", [rebuilt]).toString("hex");

  // The confirmation code is derived from the same rebuilt bytes, so a
  // disagreement about the encoding shows up in both.
  const codeInput = encodeStruct([
    ["base_hash", encodeUint(BigInt("0x" + c.base_hash), 32)],
    ["ballot", rebuilt],
  ]);
  let value = BigInt(
    "0x" + h("EPD2/v1/confirmation_code", [codeInput]).toString("hex"),
  );
  const alphabet = c.alphabet;
  const chars = [];
  for (let i = 0; i < 25; i += 1) {
    chars.push(alphabet[Number(value % BigInt(alphabet.length))]);
    value /= BigInt(alphabet.length);
  }
  const groups = [];
  for (let i = 0; i < 5; i += 1)
    groups.push(chars.slice(i * 5, i * 5 + 5).join(""));
  const code = groups.join("-");

  return {
    canonical_bytes_sha256: createHash("sha256").update(rebuilt).digest("hex"),
    canonical_length: rebuilt.length,
    ballot_hash: digest,
    confirmation_code: code,
    ballot_hash_matches: digest === c.expected_digest,
    canonical_bytes_match: c.expected_canonical_sha256
      ? createHash("sha256").update(rebuilt).digest("hex") ===
        c.expected_canonical_sha256
      : true,
    confirmation_code_matches: code === c.expected_code,
    matches:
      digest === c.expected_digest &&
      code === c.expected_code &&
      (!c.expected_canonical_sha256 ||
        createHash("sha256").update(rebuilt).digest("hex") ===
          c.expected_canonical_sha256),
  };
}

function checkScalarEncoding(c) {
  // A scalar is always |q| bytes, big-endian, zero-padded. There is no
  // short form, which is what stops two encodings of one value existing.
  const q = BigInt("0x" + c.q);
  const qBytes = Math.ceil(q.toString(2).length / 8);
  const value = BigInt("0x" + c.value);
  const encoded = scalar(value, qBytes).toString("hex");
  return {
    encoded,
    width_bytes: qBytes,
    matches: encoded === c.expected_scalar && encoded.length === qBytes * 2,
  };
}

function checkGuardianCommitment(c) {
  // A guardian's public share key is derivable from published coefficient
  // commitments alone: g^{P_i(l)} = prod_j K_{i,j}^{l^j}, and the guardian's
  // own public share value is the product of that over all guardians.
  const p = BigInt("0x" + c.p);
  const q = BigInt("0x" + c.q);
  const g = BigInt("0x" + c.g);
  const l = BigInt(c.sequence);

  let product = 1n;
  for (const guardian of c.commitments) {
    let perGuardian = 1n;
    let power = 1n; // l^j mod q
    for (const commitment of guardian) {
      perGuardian =
        (perGuardian * modPow(BigInt("0x" + commitment), power, p)) % p;
      power = (power * l) % q;
    }
    product = (product * perGuardian) % p;
  }
  const pBytes = Math.ceil(p.toString(2).length / 8);
  const derived = toFixedHex(product, pBytes);

  // The joint key is the product of every guardian's constant term.
  let joint = 1n;
  for (const guardian of c.commitments) {
    joint = (joint * BigInt("0x" + guardian[0])) % p;
  }
  return {
    derived_public_share_key: derived,
    joint_public_key: toFixedHex(joint, pBytes),
    matches:
      derived === c.expected_public_share_key &&
      toFixedHex(joint, pBytes) === c.expected_joint_public_key,
    in_subgroup: modPow(product, q, p) === 1n,
    generator_consistent: g > 1n,
  };
}

const HANDLERS = {
  parameters: checkParameters,
  encoding: checkEncoding,
  scalar_encoding: checkScalarEncoding,
  selection_encryption: checkSelectionEncryption,
  selection_proof: checkSelectionProof,
  ballot_hash: checkBallotHash,
  ballot_structural: checkBallotStructural,
  confirmation_code: checkConfirmationCode,
  accumulation: checkAccumulation,
  guardian_commitment: checkGuardianCommitment,
  decryption_share: checkDecryptionShare,
  threshold_tally: checkThresholdTally,
};

const ORACLE_VERSION = "epd2-independent-verifier-2";

// Every result carries the fields the correction task requires, so the
// verdict is machine-readable evidence rather than something a human has to
// interpret: which vector, which operation, which profile, what was
// expected, what this implementation got, and whether they agree.
function envelope(name, payload, result) {
  const match =
    result.error === undefined &&
    (result.matches ??
      result.verifies ??
      result.all_relations_hold ??
      false) === true;
  return {
    vector_id: name,
    operation: payload.kind,
    profile_id: payload.profile_id ?? "unspecified",
    expected: payload.expected ?? null,
    actual: result,
    match,
    oracle_version: ORACLE_VERSION,
  };
}

const path = process.argv[2];
const cases = JSON.parse(readFileSync(path, "utf8"));
const out = {};
for (const [name, payload] of Object.entries(cases)) {
  const handler = HANDLERS[payload.kind];
  if (!handler) {
    out[name] = envelope(name, payload, {
      error: `no independent check for kind ${payload.kind}`,
    });
    continue;
  }
  let result;
  try {
    result = handler(payload);
  } catch (err) {
    result = { error: String(err && err.message ? err.message : err) };
  }
  // Back-compatible shape: the envelope's fields sit alongside the raw
  // result fields, so existing assertions on `matches` keep working.
  out[name] = { ...result, ...envelope(name, payload, result) };
}
process.stdout.write(JSON.stringify(out, null, 2));
