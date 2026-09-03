#!/usr/bin/env bash
set -euo pipefail
p=verification/integration01-c3/transport-probe.b64
wc -c "$p"
sha256sum "$p"
base64 -d "$p" > "$RUNNER_TEMP/probe.bin"
wc -c "$RUNNER_TEMP/probe.bin"
sha256sum "$RUNNER_TEMP/probe.bin"
