import assert from "node:assert/strict";
import test from "node:test";
import {
  acceptedApi02C13,
  createApi02C13Runtime,
} from "../member/api02Runtime";

const account = {
  account_id: "discarded-account-reference",
  account_status: "active",
  email_status: "verified",
  mfa_status: "configured",
  locale: "de",
  membership_state: "membership_governed",
  identity_verified: false,
};
const governedMembership = {
  account_reference: "discarded-account-reference",
  organization_id: "2f5b9d24-6c1e-4a37-9f18-0b7d3c5e8a41",
  membership_state: "membership_governed",
  is_governed_membership: true,
  unreachable_states: [],
  unreachable_reason: "",
  latest_application_status: "accepted",
};

function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function installFetch(
  responses: Record<string, unknown | { status: number; body: unknown }>,
) {
  const original = globalThis.fetch;
  const calls: { path: string; init?: RequestInit }[] = [];
  globalThis.fetch = (async (
    input: string | URL | Request,
    init?: RequestInit,
  ) => {
    const path =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.pathname
          : new URL(input.url).pathname;
    calls.push({ path, init });
    const configured = responses[path];
    if (configured === undefined)
      return jsonResponse({ error: "unexpected path" }, 404);
    if (
      configured &&
      typeof configured === "object" &&
      "status" in configured &&
      "body" in configured
    ) {
      const row = configured as { status: number; body: unknown };
      return jsonResponse(row.body, row.status);
    }
    return jsonResponse(configured);
  }) as typeof fetch;
  return {
    calls,
    restore() {
      globalThis.fetch = original;
    },
  };
}

test("C1 pins the independently accepted API-02 C13 identity", () => {
  assert.equal(
    acceptedApi02C13.sha256,
    "9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9",
  );
  assert.equal(acceptedApi02C13.acceptanceRun, "33497989489");
});

test("production principal is derived from account + membership and no bearer header", async () => {
  const mock = installFetch({
    [acceptedApi02C13.routes.accountMe]: account,
    [acceptedApi02C13.routes.membershipMe]: governedMembership,
  });
  try {
    const result = await createApi02C13Runtime().principal.resolve();
    assert.equal(result.ok && result.value.actor, "member");
    assert.equal(
      result.ok && result.value.scopeRef,
      governedMembership.organization_id,
    );
    assert.deepEqual(
      mock.calls.map((call) => call.path).sort(),
      [
        acceptedApi02C13.routes.accountMe,
        acceptedApi02C13.routes.membershipMe,
      ].sort(),
    );
    for (const call of mock.calls) {
      assert.equal(call.init?.credentials, "same-origin");
      const headers = new Headers(call.init?.headers);
      assert.equal(headers.has("authorization"), false);
      assert.equal(headers.has("cookie"), false);
    }
  } finally {
    mock.restore();
  }
});

test("non-governed membership remains Applicant and cannot enter Member scope", async () => {
  const mock = installFetch({
    [acceptedApi02C13.routes.accountMe]: {
      ...account,
      membership_state: "application_pending",
    },
    [acceptedApi02C13.routes.membershipMe]: {
      ...governedMembership,
      membership_state: "application_pending",
      is_governed_membership: false,
      latest_application_status: "under_review",
    },
  });
  try {
    const runtime = createApi02C13Runtime();
    const principal = await runtime.principal.resolve();
    assert.equal(principal.ok && principal.value.actor, "applicant");
    const scopes = await runtime.organizationScope.listAuthorized();
    assert.equal(scopes.ok, false);
  } finally {
    mock.restore();
  }
});

test("C13 current scope can be revalidated but a different scope cannot be invented", async () => {
  const mock = installFetch({
    [acceptedApi02C13.routes.accountMe]: account,
    [acceptedApi02C13.routes.membershipMe]: governedMembership,
  });
  try {
    const runtime = createApi02C13Runtime();
    const listed = await runtime.organizationScope.listAuthorized();
    assert.equal(listed.ok, true);
    if (listed.ok) {
      assert.equal(listed.value.length, 1);
      assert.equal(listed.value[0]?.ref, governedMembership.organization_id);
      assert.equal(listed.value[0]?.level, undefined);
    }
    const same = await runtime.organizationScope.reauthorize(
      governedMembership.organization_id,
    );
    assert.equal(same.ok, true);
    const invented =
      await runtime.organizationScope.reauthorize("another-scope");
    assert.equal(invented.ok, false);
    if (!invented.ok) assert.equal(invented.error.kind, "forbidden");
  } finally {
    mock.restore();
  }
});

test("security projection strips session and credential references", async () => {
  const mock = installFetch({
    [acceptedApi02C13.routes.securityState]: {
      account_status: "active",
      activated: true,
      credential_count: 1,
      credential_types: ["passkey"],
      factor_classes: ["possession"],
      active_session_count: 1,
      lock_in_force: false,
      restriction_in_force: false,
      closure_requested: false,
    },
    [acceptedApi02C13.routes.sessions]: {
      sessions: [
        {
          session_reference: "must-not-leave-adapter",
          workspace: "member",
          origin: "https://app.epd.example",
          assurance: "substantial",
          issued_at: "2026-09-01T00:00:00Z",
          idle_deadline: "2026-09-01T01:00:00Z",
          absolute_deadline: "2026-09-02T00:00:00Z",
          device_label: "Notebook",
          status: "active",
          current: true,
        },
      ],
    },
    [acceptedApi02C13.routes.credentials]: {
      credentials: [
        {
          credential_reference: "must-not-leave-adapter-either",
          credential_type: "passkey",
          nickname: "Notebook",
          binding: "device_bound",
          status: "active",
        },
      ],
    },
  });
  try {
    const result = await createApi02C13Runtime().sessionAssurance.read();
    assert.equal(result.ok, true);
    const encoded = JSON.stringify(result);
    assert.doesNotMatch(encoded, /must-not-leave-adapter/);
    assert.match(encoded, /substantial/);
    assert.match(encoded, /passkey/);
    assert.doesNotMatch(encoded, /session_reference|credential_reference/);
  } finally {
    mock.restore();
  }
});

test("unexpected response shape and unauthenticated API fail closed", async () => {
  const malformed = installFetch({
    [acceptedApi02C13.routes.accountMe]: account,
    [acceptedApi02C13.routes.membershipMe]: { organization_id: 7 },
  });
  try {
    const result = await createApi02C13Runtime().principal.resolve();
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.error.kind, "unknown");
  } finally {
    malformed.restore();
  }

  const unauthenticated = installFetch({
    [acceptedApi02C13.routes.accountMe]: { status: 401, body: {} },
    [acceptedApi02C13.routes.membershipMe]: { status: 401, body: {} },
  });
  try {
    const result = await createApi02C13Runtime().principal.resolve();
    assert.equal(result.ok, false);
    if (!result.ok) assert.equal(result.error.kind, "forbidden");
  } finally {
    unauthenticated.restore();
  }
});

test("operations whose accepted contract is not safely represented stay unavailable", async () => {
  const runtime = createApi02C13Runtime();
  assert.equal((await runtime.applicantCase.readOwnCase()).ok, false);
  assert.equal((await runtime.initiatives.list("scope")).ok, false);
  assert.equal(
    (
      await runtime.initiatives.commit("scope", {
        title: "T",
        summary: "S",
        clientRequestRef: "r",
        expectedVersion: "1",
      })
    ).ok,
    false,
  );
  assert.equal((await runtime.votingHandoff.create()).ok, false);
});
