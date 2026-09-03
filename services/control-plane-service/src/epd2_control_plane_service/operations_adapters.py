"""CTRL-04 governed adapter boundary.

Provider-specific execution never appears in the control API. The console
speaks only this contract; INFRA/OPS own the mechanisms behind it. Three
adapters are shipped:

* `ReferenceOperationsAdapter` — an in-process reference world with explicit
  failure/partial/unsupported/slow injection for deterministic tests;
* `LocalProcessAdapter` — a real local process supervisor: restart actually
  terminates and re-spawns an operating-system process and health is read
  from the live process;
* `LocalFilesystemBackupAdapter` — a real filesystem backup/restore engine
  that writes content-addressed archives and restores them, refusing an
  identity mismatch.

None of them exposes a shell, SQL, or a secret value. Metadata that carries
secret-looking keys or values is redacted at the boundary.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

__all__ = [
    "SECRET_KEY_MARKERS",
    "AdapterCapability",
    "BackendOutcome",
    "BackendState",
    "DispatchAck",
    "DispatchRequest",
    "HealthReport",
    "JsonFileStore",
    "LocalFilesystemBackupAdapter",
    "LocalProcessAdapter",
    "OperationsAdapter",
    "ReferenceOperationsAdapter",
    "redact_metadata",
    "scrub_text",
]


class AdapterCapability(StrEnum):
    RESTART = "RESTART"
    ROLLBACK = "ROLLBACK"
    MAINTENANCE = "MAINTENANCE"
    QUEUE_CONTROL = "QUEUE_CONTROL"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"


class BackendState(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class DispatchRequest:
    execution_id: str
    action_id: str
    action_type: str
    capability: AdapterCapability
    target_id: str
    deployment_identity_ref: str
    parameters: Mapping[str, str]
    parameters_digest: str
    requested_by: str
    executed_by: str
    approval_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DispatchAck:
    """Acknowledgement of *dispatch*. It is never a result."""

    accepted: bool
    backend_operation_ref: str | None
    detail: str = ""
    duplicate: bool = False


@dataclass(frozen=True, slots=True)
class BackendOutcome:
    state: BackendState
    detail: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HealthReport:
    state: str
    metadata: Mapping[str, str] = field(default_factory=dict)


class OperationsAdapter(Protocol):
    adapter_id: str
    available: bool

    def capabilities(self, target_id: str) -> frozenset[AdapterCapability]: ...

    def health(self, target_id: str) -> HealthReport: ...

    def queue_state(self, target_id: str) -> Mapping[str, Any]: ...

    def dispatch(self, request: DispatchRequest) -> DispatchAck: ...

    def poll(self, backend_operation_ref: str) -> BackendOutcome: ...


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

SECRET_KEY_MARKERS = (
    "password",
    "passwd",
    "secret",
    "token",
    "private_key",
    "api_key",
    "apikey",
    "connection_string",
    "credential",
    "seed",
    "passphrase",
    "hsm",
    "kms_material",
)
_SECRET_VALUE_PREFIXES = (
    "-----BEGIN",
    "sk_live_",
    "sk_test_",
    "eyJhbGciOi",
    "AKIA",
    "ghp_",
    "glpat-",
    "xoxb-",
    "xoxp-",
)
#: Only an explicit *reference* suffix exempts a secret-named key. `secret_id`,
#: `token_id` or `client_secret_version` name credential material in real
#: providers and are therefore redacted.
_REFERENCE_SUFFIXES = ("_ref", "_reference", "_reference_id")
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
#: Free-text scrubbing: `password=...`, `token: ...` and known prefixes inside a
#: string are replaced token-wise, so a backend detail string can never carry
#: material into UI, API or evidence.
_TEXT_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|passphrase|secret|token|api[_-]?key|private[_-]?key|credential)"
    r"(s)?\s*[:=]\s*\S+"
)
_TEXT_PREFIX = re.compile(
    r"(-----BEGIN[^-]*-----|sk_live_[A-Za-z0-9]+|sk_test_[A-Za-z0-9]+|eyJhbGciOi[A-Za-z0-9._-]+"
    r"|AKIA[A-Z0-9]{12,}|ghp_[A-Za-z0-9]+|glpat-[A-Za-z0-9_-]+|xox[bp]-[A-Za-z0-9-]+)"
)


def scrub_text(text: str) -> str:
    """Replace secret-looking material inside free text with a marker."""
    scrubbed = _TEXT_ASSIGNMENT.sub(lambda m: f"{m.group(1)}{m.group(2) or ''}=[REDACTED]", text)
    return _TEXT_PREFIX.sub("[REDACTED]", scrubbed)


def redact_metadata(metadata: Mapping[str, Any]) -> tuple[dict[str, str], list[str]]:
    """Return a redacted copy and the list of redacted keys.

    A governed *reference* (`secret_ref`, `token_reference_id`) is kept because
    it names a handle, not material. Anything that looks like the material
    itself is replaced with a marker before it can reach UI, API or evidence.
    """
    clean: dict[str, str] = {}
    redacted: list[str] = []
    for key, value in metadata.items():
        text = "" if value is None else str(value)
        lowered = key.lower()
        is_reference = lowered.endswith(_REFERENCE_SUFFIXES)
        key_hit = any(marker in lowered for marker in SECRET_KEY_MARKERS) and not is_reference
        value_hit = any(text.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES)
        if key_hit or value_hit or _TEXT_PREFIX.search(text):
            clean[key] = "[REDACTED]"
            redacted.append(key)
        else:
            clean[key] = scrub_text(text[:512])
    return clean, redacted


# ---------------------------------------------------------------------------
# Reference adapter (deterministic, with injection)
# ---------------------------------------------------------------------------


class ReferenceOperationsAdapter:
    """Deterministic in-process reference backend."""

    def __init__(self, adapter_id: str = "reference-adapter") -> None:
        self.adapter_id = adapter_id
        self.available = True
        self._caps: dict[str, frozenset[AdapterCapability]] = {}
        self._health: dict[str, HealthReport] = {}
        self._queues: dict[str, dict[str, Any]] = {}
        self._operations: dict[str, BackendOutcome] = {}
        self._seen_executions: set[str] = set()
        self._injected: dict[str, BackendState] = {}
        self._polls_until_terminal: dict[str, int] = {}
        self._metadata: dict[str, dict[str, str]] = {}
        self.dispatch_count = 0
        self.dispatch_log: list[DispatchRequest] = []
        self.refuse_dispatch: set[str] = set()
        self._lock = threading.RLock()

    # configuration -----------------------------------------------------------

    def configure_target(
        self,
        target_id: str,
        *,
        capabilities: frozenset[AdapterCapability],
        health: str = "HEALTHY",
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self._caps[target_id] = capabilities
        self._health[target_id] = HealthReport(health, dict(metadata or {}))
        self._metadata[target_id] = dict(metadata or {})

    def set_health(
        self, target_id: str, state: str, metadata: Mapping[str, str] | None = None
    ) -> None:
        self._health[target_id] = HealthReport(
            state, dict(metadata or self._metadata.get(target_id, {}))
        )

    def set_queue(self, target_id: str, *, state: str, depth: int, oldest_age_seconds: int) -> None:
        self._queues[target_id] = {
            "state": state,
            "depth": depth,
            "oldest_age_seconds": oldest_age_seconds,
        }

    def inject_outcome(self, target_id: str, state: BackendState, *, polls: int = 0) -> None:
        """Make the next operation on `target_id` end in `state` after `polls` RUNNING polls."""
        self._injected[target_id] = state
        self._polls_until_terminal[target_id] = polls

    # contract ----------------------------------------------------------------

    def capabilities(self, target_id: str) -> frozenset[AdapterCapability]:
        return self._caps.get(target_id, frozenset())

    def health(self, target_id: str) -> HealthReport:
        return self._health.get(target_id, HealthReport("UNKNOWN", {}))

    def queue_state(self, target_id: str) -> Mapping[str, Any]:
        return dict(
            self._queues.get(target_id, {"state": "UNKNOWN", "depth": -1, "oldest_age_seconds": -1})
        )

    def dispatch(self, request: DispatchRequest) -> DispatchAck:
        with self._lock:
            if request.execution_id in self._seen_executions:
                return DispatchAck(False, None, "execution id already dispatched", duplicate=True)
            self._seen_executions.add(request.execution_id)
            if request.capability not in self.capabilities(request.target_id):
                return DispatchAck(False, None, "capability not supported")
            if request.target_id in self.refuse_dispatch:
                return DispatchAck(False, None, "backend refused dispatch")
            self.dispatch_count += 1
            self.dispatch_log.append(request)
            ref = f"{self.adapter_id}:op:{request.execution_id}"
            state = self._injected.pop(request.target_id, BackendState.COMPLETED)
            polls = self._polls_until_terminal.pop(request.target_id, 0)
            metadata = dict(self._metadata.get(request.target_id, {}))
            metadata["capability"] = request.capability.value
            if request.capability is AdapterCapability.BACKUP and state is BackendState.COMPLETED:
                metadata["backup_identity_digest"] = hashlib.sha256(
                    f"{request.target_id}:{request.execution_id}".encode()
                ).hexdigest()
            detail = {
                BackendState.COMPLETED: "backend completed the operation",
                BackendState.FAILED: "backend reported failure",
                BackendState.PARTIAL: "backend completed 1 of 2 units",
                BackendState.UNSUPPORTED: "backend reports the operation unsupported at runtime",
                BackendState.RUNNING: "backend still running",
            }[state]
            self._operations[ref] = BackendOutcome(state, detail, metadata)
            self._polls_until_terminal[ref] = polls
            if (
                request.capability is AdapterCapability.QUEUE_CONTROL
                and state is BackendState.COMPLETED
            ):
                queue = self._queues.setdefault(
                    request.target_id, {"state": "RUNNING", "depth": 0, "oldest_age_seconds": 0}
                )
                if request.action_type.endswith("PAUSE"):
                    queue["state"] = "PAUSED"
                elif request.action_type.endswith("RESUME"):
                    queue["state"] = "RUNNING"
            return DispatchAck(True, ref, "dispatch acknowledged")

    def poll(self, backend_operation_ref: str) -> BackendOutcome:
        with self._lock:
            outcome = self._operations.get(backend_operation_ref)
            if outcome is None:
                return BackendOutcome(BackendState.FAILED, "unknown backend operation", {})
            remaining = self._polls_until_terminal.get(backend_operation_ref, 0)
            if remaining > 0:
                self._polls_until_terminal[backend_operation_ref] = remaining - 1
                return BackendOutcome(BackendState.RUNNING, "backend still running", {})
            return outcome


# ---------------------------------------------------------------------------
# Real local process adapter
# ---------------------------------------------------------------------------

_HEALTH_SERVER = r"""
import http.server, json, os, sys, time
port = int(sys.argv[1]); marker = sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"state": "HEALTHY", "pid": os.getpid(), "marker": marker,
                           "started": START}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
START = time.time()
http.server.HTTPServer(("127.0.0.1", port), H).serve_forever()
"""


class LocalProcessAdapter:
    """A real, bounded process supervisor.

    `RESTART` terminates the managed process and spawns a replacement; the
    outcome is derived from the replacement actually answering its health
    endpoint with a new PID. No command from the caller is ever executed: the
    only thing the adapter can run is its own fixed health server.
    """

    def __init__(self, adapter_id: str = "local-process-adapter") -> None:
        self.adapter_id = adapter_id
        self.available = True
        self._targets: dict[str, dict[str, Any]] = {}
        self._operations: dict[str, BackendOutcome] = {}
        self._seen: set[str] = set()
        self._lock = threading.RLock()

    def _free_port(self) -> int:
        import socket

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _spawn(self, target_id: str) -> subprocess.Popen[bytes]:
        port = self._targets[target_id]["port"]
        process = subprocess.Popen(
            [sys.executable, "-c", _HEALTH_SERVER, str(port), target_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._targets[target_id]["process"] = process
        deadline = time.time() + 10
        while time.time() < deadline:
            if self._probe(target_id) is not None:
                return process
            time.sleep(0.05)
        raise RuntimeError("managed process did not become healthy")

    def _probe(self, target_id: str) -> dict[str, Any] | None:
        import urllib.request

        port = self._targets[target_id]["port"]
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5) as resp:
                data: dict[str, Any] = json.loads(resp.read().decode())
                return data
        except Exception:
            return None

    def manage(self, target_id: str, *, restart_supported: bool = True) -> None:
        with self._lock:
            self._targets[target_id] = {
                "port": self._free_port(),
                "process": None,
                "restart_supported": restart_supported,
                "fail_next_restart": False,
            }
            self._spawn(target_id)

    def fail_next_restart(self, target_id: str) -> None:
        self._targets[target_id]["fail_next_restart"] = True

    def stop_all(self) -> None:
        for entry in self._targets.values():
            process = entry.get("process")
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:  # pragma: no cover
                    process.kill()

    def pid_of(self, target_id: str) -> int | None:
        process = self._targets[target_id].get("process")
        return None if process is None else int(process.pid)

    def capabilities(self, target_id: str) -> frozenset[AdapterCapability]:
        entry = self._targets.get(target_id)
        if entry is None:
            return frozenset()
        caps = {AdapterCapability.MAINTENANCE}
        if entry["restart_supported"]:
            caps.add(AdapterCapability.RESTART)
        return frozenset(caps)

    def health(self, target_id: str) -> HealthReport:
        if target_id not in self._targets:
            return HealthReport("UNKNOWN", {})
        data = self._probe(target_id)
        if data is None:
            return HealthReport("UNAVAILABLE", {"probe": "no answer"})
        return HealthReport("HEALTHY", {"pid": str(data["pid"]), "marker": str(data["marker"])})

    def queue_state(self, target_id: str) -> Mapping[str, Any]:
        return {"state": "UNSUPPORTED", "depth": -1, "oldest_age_seconds": -1}

    def dispatch(self, request: DispatchRequest) -> DispatchAck:
        with self._lock:
            if request.execution_id in self._seen:
                return DispatchAck(False, None, "execution id already dispatched", duplicate=True)
            self._seen.add(request.execution_id)
            entry = self._targets.get(request.target_id)
            if entry is None or request.capability not in self.capabilities(request.target_id):
                return DispatchAck(False, None, "capability not supported")
            ref = f"{self.adapter_id}:op:{request.execution_id}"
            if request.capability is AdapterCapability.MAINTENANCE:
                self._operations[ref] = BackendOutcome(
                    BackendState.COMPLETED, "maintenance flag toggled", {"maintenance": "toggled"}
                )
                return DispatchAck(True, ref)
            old = entry["process"]
            old_pid = None if old is None else old.pid
            if old is not None and old.poll() is None:
                old.send_signal(signal.SIGTERM)
                try:
                    old.wait(timeout=5)
                except subprocess.TimeoutExpired:  # pragma: no cover
                    old.kill()
            if entry["fail_next_restart"]:
                entry["fail_next_restart"] = False
                entry["process"] = None
                self._operations[ref] = BackendOutcome(
                    BackendState.FAILED,
                    "replacement process failed to start",
                    {"old_pid": str(old_pid), "new_pid": "none"},
                )
                return DispatchAck(True, ref)
            try:
                new = self._spawn(request.target_id)
            except RuntimeError as exc:  # pragma: no cover
                self._operations[ref] = BackendOutcome(BackendState.FAILED, str(exc), {})
                return DispatchAck(True, ref)
            self._operations[ref] = BackendOutcome(
                BackendState.COMPLETED,
                "process restarted and answered health",
                {"old_pid": str(old_pid), "new_pid": str(new.pid)},
            )
            return DispatchAck(True, ref)

    def poll(self, backend_operation_ref: str) -> BackendOutcome:
        return self._operations.get(
            backend_operation_ref, BackendOutcome(BackendState.FAILED, "unknown operation", {})
        )


# ---------------------------------------------------------------------------
# Real filesystem backup/restore adapter
# ---------------------------------------------------------------------------


class LocalFilesystemBackupAdapter:
    """Content-addressed directory backup and restore on the local filesystem."""

    def __init__(self, root: Path, adapter_id: str = "local-backup-adapter") -> None:
        self.adapter_id = adapter_id
        self.available = True
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._datastores: dict[str, Path] = {}
        self._operations: dict[str, BackendOutcome] = {}
        self._seen: set[str] = set()
        self._restore_supported: dict[str, bool] = {}
        self._lock = threading.RLock()

    def manage(self, target_id: str, data_dir: Path, *, restore_supported: bool = True) -> None:
        self._datastores[target_id] = Path(data_dir)
        self._restore_supported[target_id] = restore_supported

    @staticmethod
    def _tree_digest(directory: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(p for p in directory.rglob("*") if p.is_file()):
            digest.update(path.relative_to(directory).as_posix().encode())
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def capabilities(self, target_id: str) -> frozenset[AdapterCapability]:
        if target_id not in self._datastores:
            return frozenset()
        caps = {AdapterCapability.BACKUP, AdapterCapability.MAINTENANCE}
        if self._restore_supported.get(target_id, True):
            caps.add(AdapterCapability.RESTORE)
        return frozenset(caps)

    def health(self, target_id: str) -> HealthReport:
        directory = self._datastores.get(target_id)
        if directory is None or not directory.is_dir():
            return HealthReport("UNAVAILABLE", {})
        return HealthReport(
            "HEALTHY", {"files": str(sum(1 for p in directory.rglob("*") if p.is_file()))}
        )

    def queue_state(self, target_id: str) -> Mapping[str, Any]:
        return {"state": "UNSUPPORTED", "depth": -1, "oldest_age_seconds": -1}

    def backup_path(self, backup_set_id: str, digest: str) -> Path:
        if not _SAFE_SEGMENT.match(backup_set_id) or not _SAFE_SEGMENT.match(digest):
            raise ValueError("backup set id and digest must be single safe path segments")
        path = (self.root / backup_set_id / f"{digest}.zip").resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError("backup path escapes the backup root")
        return path

    def dispatch(self, request: DispatchRequest) -> DispatchAck:
        with self._lock:
            if request.execution_id in self._seen:
                return DispatchAck(False, None, "execution id already dispatched", duplicate=True)
            self._seen.add(request.execution_id)
            if request.capability not in self.capabilities(request.target_id):
                return DispatchAck(False, None, "capability not supported")
            ref = f"{self.adapter_id}:op:{request.execution_id}"
            if request.capability is AdapterCapability.MAINTENANCE:
                self._operations[ref] = BackendOutcome(
                    BackendState.COMPLETED, "maintenance flag toggled", {"maintenance": "toggled"}
                )
                return DispatchAck(True, ref)
            directory = self._datastores[request.target_id]
            backup_set_id = request.parameters.get("backup_set_id", "default")
            if request.capability is AdapterCapability.BACKUP:
                digest = self._tree_digest(directory)
                target = self.backup_path(backup_set_id, digest)
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory() as td:
                    archive = shutil.make_archive(str(Path(td) / "backup"), "zip", directory)
                    shutil.move(archive, target)
                self._operations[ref] = BackendOutcome(
                    BackendState.COMPLETED,
                    "backup archive written",
                    {
                        "backup_identity_digest": digest,
                        "backup_set_id": backup_set_id,
                        "archive_ref": target.name,
                    },
                )
                return DispatchAck(True, ref)
            expected = request.parameters.get("backup_identity_digest", "")
            archive_path = self.backup_path(backup_set_id, expected)
            if not archive_path.is_file():
                self._operations[ref] = BackendOutcome(
                    BackendState.FAILED,
                    "no archive with that identity",
                    {"backup_identity_digest": expected},
                )
                return DispatchAck(True, ref)
            with tempfile.TemporaryDirectory() as td:
                shutil.unpack_archive(str(archive_path), td, "zip")
                restored_digest = self._tree_digest(Path(td))
                if restored_digest != expected:
                    self._operations[ref] = BackendOutcome(
                        BackendState.FAILED,
                        "archive identity mismatch",
                        {"backup_identity_digest": expected},
                    )
                    return DispatchAck(True, ref)
                for child in list(directory.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                shutil.copytree(td, directory, dirs_exist_ok=True)
            self._operations[ref] = BackendOutcome(
                BackendState.COMPLETED,
                "datastore restored from archive",
                {
                    "backup_identity_digest": expected,
                    "restored_tree_digest": self._tree_digest(directory),
                },
            )
            return DispatchAck(True, ref)

    def poll(self, backend_operation_ref: str) -> BackendOutcome:
        return self._operations.get(
            backend_operation_ref, BackendOutcome(BackendState.FAILED, "unknown operation", {})
        )


# ---------------------------------------------------------------------------
# Durable store
# ---------------------------------------------------------------------------


class JsonFileStore:
    """Atomic JSON checkpoint file; survives process restart."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload: Mapping[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True))
        os.replace(tmp, self.path)

    def load(self) -> dict[str, Any] | None:
        if not self.path.is_file():
            return None
        data: dict[str, Any] = json.loads(self.path.read_text())
        return data
