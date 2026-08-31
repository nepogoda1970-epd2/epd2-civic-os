"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import type { OrganizationScopePort, Scope } from "./types";

export function useScopeTransition(port: OrganizationScopePort) {
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [scope, setScope] = useState("");
  const [contextVersion, setContextVersion] = useState("");
  const [pending, setPending] = useState(false);
  const [loadingScopes, setLoadingScopes] = useState(true);
  const [contextReady, setContextReady] = useState(false);
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);

  const transition = useCallback(
    async (target: string) => {
      const current = ++generation.current;
      controller.current?.abort();
      controller.current = new AbortController();
      setContextReady(false);
      setContextVersion("");
      setScope("");
      setPending(true);
      const result = await port.reauthorize(target, controller.current.signal);
      if (current !== generation.current) return false;
      setPending(false);
      if (!result.ok) return false;
      setScope(result.value.scopeRef);
      setContextVersion(result.value.contextVersion);
      setContextReady(true);
      try {
        localStorage.setItem("epd2.display.last-scope", result.value.scopeRef);
      } catch {}
      return true;
    },
    [port],
  );

  useEffect(() => {
    let active = true;
    setLoadingScopes(true);
    setContextReady(false);
    setContextVersion("");
    void port.listAuthorized().then(async (result) => {
      if (!active) return;
      if (!result.ok) {
        setScopes([]);
        setLoadingScopes(false);
        return;
      }
      const authorized = result.value.filter(
        (candidate) => candidate.authorized,
      );
      setScopes(authorized);
      let preferred = "";
      try {
        preferred = localStorage.getItem("epd2.display.last-scope") ?? "";
      } catch {}
      const target = authorized.some((candidate) => candidate.ref === preferred)
        ? preferred
        : (authorized[0]?.ref ?? "");
      setLoadingScopes(false);
      if (target) await transition(target);
    });
    return () => {
      active = false;
      controller.current?.abort();
    };
  }, [port, transition]);

  const selected = scopes.find((candidate) => candidate.ref === scope);
  return {
    scopes,
    scope,
    scopeLabel: selected?.label ?? "",
    contextVersion,
    pending,
    loadingScopes,
    contextReady,
    transition,
  };
}
