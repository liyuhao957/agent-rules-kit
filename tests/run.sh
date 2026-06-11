#!/usr/bin/env bash
# Run the full Relay Rules test suite. Zero dependencies beyond python3 + git.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fail=0

run() {
  echo "==> $1"
  if ! "${@:2}"; then
    fail=1
  fi
}

run "bash_guard"      python3 "$here/test_bash_guard.py"
run "stop_gate"       python3 "$here/test_stop_gate.py"
run "scanner"         python3 "$here/test_scanner.py"
run "adapt_deferral"  python3 "$here/test_adapt_deferral.py"
run "lifecycle"       bash    "$here/test_lifecycle.sh"
run "prune"           bash    "$here/test_prune.sh"

echo ""
if [[ "$fail" -eq 0 ]]; then
  echo "ALL SUITES PASSED"
else
  echo "SOME SUITES FAILED"
fi
exit "$fail"
