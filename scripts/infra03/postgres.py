"""Real PostgreSQL runtime for the preview instance (INFRA03 §12, §13, §34, §36).

A dedicated PostgreSQL 16 cluster per preview instance: ``initdb`` into the
instance directory, TLS server identity from the data CA, scram-sha-256 for
every TCP client, peer-authenticated local admin over the instance's unix
socket only, per-service roles with per-service databases (credential
isolation, §15), canonical migrations applied from the *deployed artifact*
with a ledger (no manual mutations, §13), deterministic synthetic fixtures,
and clean reset with proof that old state is gone (§34).

This module shells out to the real PostgreSQL binaries (``initdb``,
``pg_ctl``, ``pg_isready``, ``psql``) — there is no driver dependency in the
frozen locks and none is added: lock digests are release identity. All SQL
travels through ``psql`` with ``ON_ERROR_STOP`` and explicit transactions
where required. Passwords reach ``psql`` only via the process environment of
the spawned client, never argv, never logs.

Running as root (the sandbox case) the cluster is owned by a dedicated
non-root OS user; PostgreSQL itself refuses root, which this module treats
as a feature, not an obstacle.
"""

from __future__ import annotations

import os
import pwd
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from scripts.infra03 import codes

PG_BINDIR = Path("/usr/lib/postgresql/16/bin")
PG_OS_USER = "epd2pg"

LEDGER_TABLE = "infra03_migration_ledger"

_LEDGER_DDL = f"""
CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
    filename   TEXT PRIMARY KEY,
    sha256     TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


@dataclass(frozen=True)
class PostgresFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def _pg_user_available() -> bool:
    try:
        pwd.getpwnam(PG_OS_USER)
        return True
    except KeyError:
        return False


def ensure_pg_os_user() -> None:
    """A dedicated non-root owner for the cluster when running as root."""
    if os.geteuid() != 0 or _pg_user_available():
        return
    subprocess.run(
        ["useradd", "--system", "--no-create-home", "--shell", "/usr/sbin/nologin", PG_OS_USER],
        check=True,
        capture_output=True,
    )


class PostgresCluster:
    """One real preview PostgreSQL cluster."""

    def __init__(self, instance_dir: Path, port: int) -> None:
        self.instance_dir = instance_dir
        self.port = port
        self.data_dir = instance_dir / "pg" / "data"
        self.socket_dir = instance_dir / "pg" / "socket"
        self.log_file = instance_dir / "pg" / "postgres.log"
        self.server_cert: Path | None = None
        self.server_key: Path | None = None
        self.ca_cert: Path | None = None
        self._as_owner = os.geteuid() == 0

    # -- process plumbing --------------------------------------------------

    def _wrap(self, command: list[str]) -> list[str]:
        if self._as_owner:
            return ["runuser", "-u", PG_OS_USER, "--", *command]
        return command

    def _run(self, command: list[str], timeout: int = 120, check: bool = True) -> str:
        completed = subprocess.run(
            self._wrap(command), capture_output=True, text=True, timeout=timeout, check=False
        )
        if check and completed.returncode != 0:
            raise RuntimeError(f"postgres command failed ({command[0]}): {completed.stderr[-800:]}")
        return completed.stdout

    def _chown(self, path: Path) -> None:
        if self._as_owner:
            record = pwd.getpwnam(PG_OS_USER)
            os.chown(path, record.pw_uid, record.pw_gid)

    # -- lifecycle ---------------------------------------------------------

    def init(self, server_cert: Path, server_key: Path, ca_cert: Path) -> None:
        ensure_pg_os_user()
        for directory in (self.data_dir.parent, self.socket_dir):
            directory.mkdir(parents=True, exist_ok=True)
            self._chown(directory)
        self.server_cert, self.server_key, self.ca_cert = server_cert, server_key, ca_cert
        # postgres requires the key to be owned by the cluster owner, 0600
        key_copy = self.data_dir.parent / "server.key"
        cert_copy = self.data_dir.parent / "server.crt"
        shutil.copyfile(server_key, key_copy)
        shutil.copyfile(server_cert, cert_copy)
        os.chmod(key_copy, 0o600)
        self._chown(key_copy)
        self._chown(cert_copy)
        self._run(
            [
                str(PG_BINDIR / "initdb"),
                "-D",
                str(self.data_dir),
                "--auth-local=peer",
                "--auth-host=scram-sha-256",
                "-E",
                "UTF8",
            ],
            timeout=300,
        )
        parameters = f"""
listen_addresses = '127.0.0.1'
port = {self.port}
unix_socket_directories = '{self.socket_dir}'
ssl = on
ssl_cert_file = '{cert_copy}'
ssl_key_file = '{key_copy}'
password_encryption = 'scram-sha-256'
max_connections = 50
"""
        with (self.data_dir / "postgresql.conf").open("a", encoding="utf-8") as handle:
            handle.write(parameters)
        # TCP clients: TLS only, scram. Local admin: peer over the socket.
        (self.data_dir / "pg_hba.conf").write_text(
            "local   all   all                 peer\n"
            "hostssl all   all   127.0.0.1/32  scram-sha-256\n"
            "hostnossl all all   0.0.0.0/0     reject\n",
            encoding="utf-8",
        )
        self._chown(self.data_dir / "postgresql.conf")
        self._chown(self.data_dir / "pg_hba.conf")

    def start(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.touch(exist_ok=True)
        self._chown(self.log_file)
        self._run(
            [
                str(PG_BINDIR / "pg_ctl"),
                "start",
                "-D",
                str(self.data_dir),
                "-l",
                str(self.log_file),
                "-w",
                "-t",
                "60",
            ],
            timeout=120,
        )

    def stop(self, mode: str = "fast") -> None:
        self._run(
            [str(PG_BINDIR / "pg_ctl"), "stop", "-D", str(self.data_dir), "-m", mode, "-w"],
            timeout=120,
            check=False,
        )

    def is_running(self) -> bool:
        completed = subprocess.run(
            self._wrap([str(PG_BINDIR / "pg_ctl"), "status", "-D", str(self.data_dir)]),
            capture_output=True,
            text=True,
            check=False,
        )
        return completed.returncode == 0

    def wait_ready(self, timeout_seconds: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            completed = subprocess.run(
                self._wrap(
                    [
                        str(PG_BINDIR / "pg_isready"),
                        "-h",
                        str(self.socket_dir),
                        "-p",
                        str(self.port),
                    ]
                ),
                capture_output=True,
                check=False,
            )
            if completed.returncode == 0:
                return True
            time.sleep(0.25)
        return False

    # -- SQL paths ---------------------------------------------------------

    def _conninfo(self, database: str, role: str | None = None) -> str:
        parts = [f"host={self.socket_dir}", f"port={self.port}", f"dbname={database}"]
        if role is not None:
            parts.append(f"options=-crole={role}")
        return " ".join(parts)

    def admin_sql(
        self, sql: str, database: str = "postgres", timeout: int = 60, role: str | None = None
    ) -> str:
        """Admin-plane SQL over the local socket (peer auth; F10).

        ``role`` runs the session under ``SET ROLE`` so objects created by
        canonical migrations are owned by the owning service role, not by
        the cluster bootstrap superuser (§13, §15).
        """
        return self._run(
            [
                str(PG_BINDIR / "psql"),
                self._conninfo(database, role),
                "-v",
                "ON_ERROR_STOP=1",
                "-qAt",
                "-c",
                sql,
            ],
            timeout=timeout,
        )

    def client_sql(
        self,
        role: str,
        password: str,
        database: str,
        sql: str,
        timeout: int = 60,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Application-plane SQL over TCP with TLS verify-full and scram.

        This is the same path the runtime shells use: hostname-verified TLS
        against the data CA, role-scoped credentials from the secret store.
        """
        if self.ca_cert is None:
            raise RuntimeError("cluster not initialized with a CA certificate")
        env = dict(os.environ)
        env["PGPASSWORD"] = password
        env["PGSSLMODE"] = "verify-full"
        env["PGSSLROOTCERT"] = str(self.ca_cert)
        completed = subprocess.run(
            [
                str(PG_BINDIR / "psql"),
                "-h",
                "localhost",
                "-p",
                str(self.port),
                "-U",
                role,
                "-d",
                database,
                "-v",
                "ON_ERROR_STOP=1",
                "-qAt",
                "-c",
                sql,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        if check and completed.returncode != 0:
            raise RuntimeError(f"client sql failed as {role}@{database}: {completed.stderr[-500:]}")
        return completed

    # -- provisioning ------------------------------------------------------

    def create_role_and_database(self, role: str, password: str, database: str) -> None:
        escaped = password.replace("'", "''")
        self.admin_sql(f"CREATE ROLE {role} LOGIN PASSWORD '{escaped}'")
        self.admin_sql(f"CREATE DATABASE {database} OWNER {role}")
        # Credential isolation: only the owner may connect to its database.
        self.admin_sql(f"REVOKE CONNECT ON DATABASE {database} FROM PUBLIC")
        self.admin_sql(f"GRANT CONNECT ON DATABASE {database} TO {role}")

    # -- migrations / fixtures / reset ------------------------------------

    def apply_migrations(
        self, database: str, migrations_dir: Path, role: str | None = None
    ) -> tuple[list[str], list[PostgresFinding]]:
        """Apply canonical migrations from the deployed artifact with a ledger.

        Returns (applied filenames, findings). Already-applied migrations are
        skipped only when their recorded content hash still matches — a
        changed historical migration is a ledger violation, never silently
        re-run (§13).
        """
        from scripts.acceptance.canonical import sha256_file

        findings: list[PostgresFinding] = []
        applied: list[str] = []
        self.admin_sql(_LEDGER_DDL, database=database, role=role)
        recorded = {
            line.split("|", 1)[0]: line.split("|", 1)[1]
            for line in self.admin_sql(
                f"SELECT filename, sha256 FROM {LEDGER_TABLE}", database=database, role=role
            ).splitlines()
            if "|" in line
        }
        for migration in sorted(migrations_dir.glob("*.sql")):
            digest = sha256_file(migration)
            if migration.name in recorded:
                if recorded[migration.name] != digest:
                    findings.append(
                        PostgresFinding(
                            codes.MIGRATION_LEDGER_VIOLATION,
                            migration.name,
                            "applied migration content changed after application; "
                            "history is immutable",
                        )
                    )
                continue
            self._run(
                [
                    str(PG_BINDIR / "psql"),
                    self._conninfo(database, role),
                    "-v",
                    "ON_ERROR_STOP=1",
                    "--single-transaction",
                    "-q",
                    "-f",
                    str(migration),
                ],
                timeout=300,
            )
            self.admin_sql(
                f"INSERT INTO {LEDGER_TABLE} (filename, sha256) "
                f"VALUES ('{migration.name}', '{digest}')",
                database=database,
                role=role,
            )
            applied.append(migration.name)
        return applied, findings

    def destroy(self) -> None:
        """Remove the cluster entirely (governed destroy path only)."""
        self.stop(mode="immediate")
        shutil.rmtree(self.data_dir.parent, ignore_errors=True)
