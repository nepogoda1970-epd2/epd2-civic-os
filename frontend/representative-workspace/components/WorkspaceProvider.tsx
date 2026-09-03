"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { restrictedFor, type RestrictionKnowledge } from "../domain/conflict";
import { bindScope, type ScopeBound } from "../domain/scope";
import {
  ANONYMOUS_SESSION,
  applySessionEvent,
  interruptionFor,
  mustClearLoadedContent,
  type SessionEvent,
} from "../domain/session";
import type {
  MandateScope,
  MandateSession,
  Result,
  SafeRefusal,
} from "../domain/types";
import { sessionPermitsWork } from "../domain/types";
import { resolveRepresentativeRuntime } from "../runtime/compose";
import type { RepresentativeRuntime } from "../runtime/ports";

/**
 * The workspace state, held in memory for the life of the mounted tree.
 *
 * Nothing here writes to localStorage, sessionStorage, IndexedDB, a cookie, the
 * URL, the page title or a telemetry payload. There is no such call in this
 * file and the static validator asserts its absence — which is what the
 * `CASE_CONFIDENTIAL` storage prohibition amounts to in practice, since a case
 * body that never reaches a store cannot be recovered from one.
 *
 * Drafts are deliberately volatile. There is no accepted route that persists
 * one, so a draft that survived a reload could only have survived in the
 * browser, which is precisely what is forbidden. The interface therefore says
 * the draft is unsaved rather than quietly keeping it somewhere.
 */

export type WorkspaceValue = {
  readonly session: MandateSession;
  readonly scope: MandateScope | null;
  readonly refusal: SafeRefusal | null;
  readonly restrictions: RestrictionKnowledge;
  readonly ready: boolean;
  readonly busy: boolean;
  readonly profile: "production" | "governed_test" | "unresolved";
  readonly runtime: () => Promise<RepresentativeRuntime>;
  readonly bind: <T>(
    value: T,
    mandateId?: string | null,
  ) => Result<ScopeBound<T>>;
  readonly restrictedIn: (scopeLabel: string) => boolean;
  readonly apply: (event: SessionEvent) => void;
  readonly guarded: (run: () => Promise<void>) => Promise<void>;
};

const WorkspaceContext = createContext<WorkspaceValue | null>(null);

export function useWorkspace(): WorkspaceValue {
  const value = useContext(WorkspaceContext);
  if (!value) {
    throw new Error("useWorkspace used outside the WS-04 workspace boundary");
  }
  return value;
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<MandateSession>(ANONYMOUS_SESSION);
  const [scope, setScope] = useState<MandateScope | null>(null);
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [restrictions, setRestrictions] = useState<RestrictionKnowledge>({
    known: false,
    reason: "WS04_CONFLICT_REGISTER_NOT_ACCEPTED",
  });
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [profile, setProfile] = useState<
    "production" | "governed_test" | "unresolved"
  >("unresolved");

  /** One in-flight consequential action at a time; a second click is ignored. */
  const inFlight = useRef(false);
  const runtimeRef = useRef<RepresentativeRuntime | null>(null);

  const runtime = useCallback(async () => {
    if (!runtimeRef.current) {
      runtimeRef.current = await resolveRepresentativeRuntime();
      setProfile(runtimeRef.current.profile);
    }
    return runtimeRef.current;
  }, []);

  const guarded = useCallback(async (run: () => Promise<void>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try {
      await run();
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }, []);

  /**
   * Bootstrap. Each step is allowed to fail independently, and a failure sets a
   * refusal rather than throwing: an unavailable dependency is the expected
   * state at this baseline, not an exception.
   */
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const api = await runtime();
      const current = await api.session.current();
      if (cancelled) return;
      if (current.ok) {
        setSession(current.value);
        if (current.value.scope !== null) setScope(current.value.scope);
      } else {
        setRefusal(current.error);
      }

      const resolved = await api.scope.resolve();
      if (cancelled) return;
      if (resolved.ok) {
        setScope((previous) => {
          if (mustClearLoadedContent(previous, resolved.value)) {
            // A different mandate: nothing previously loaded may remain.
            setRefusal(null);
          }
          return resolved.value;
        });
      }

      const bound = bindScope(
        current.ok ? current.value : ANONYMOUS_SESSION,
        null,
        {},
      );
      if (bound.ok) {
        const list = await api.conflict.restrictions(bound.value);
        if (cancelled) return;
        setRestrictions(
          list.ok
            ? { known: true, restrictions: list.value }
            : { known: false, reason: list.error.reasonCode },
        );
      }
      if (!cancelled) setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime]);

  const apply = useCallback((event: SessionEvent) => {
    setSession((current) => {
      const next = applySessionEvent(current, event);
      const interruption = interruptionFor(next.state);
      if (interruption) setRefusal(interruption.refusal);
      if (mustClearLoadedContent(current.scope, next.scope)) setScope(null);
      return next;
    });
  }, []);

  const bind = useCallback(
    <T,>(value: T, mandateId: string | null = null): Result<ScopeBound<T>> =>
      bindScope(session, mandateId, value),
    [session],
  );

  const restrictedIn = useCallback(
    (scopeLabel: string) => restrictedFor(restrictions, scopeLabel),
    [restrictions],
  );

  const value = useMemo<WorkspaceValue>(
    () => ({
      session,
      scope,
      refusal,
      restrictions,
      ready,
      busy,
      profile,
      runtime,
      bind,
      restrictedIn,
      apply,
      guarded,
    }),
    [
      session,
      scope,
      refusal,
      restrictions,
      ready,
      busy,
      profile,
      runtime,
      bind,
      restrictedIn,
      apply,
      guarded,
    ],
  );

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

/** Convenience for surfaces that must not render while work is not permitted. */
export function useWorkPermitted(): boolean {
  const { session } = useWorkspace();
  return sessionPermitsWork(session.state);
}
