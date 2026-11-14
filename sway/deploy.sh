#!/bin/bash
# Repository-only preparation by default; mutations require an explicit subcommand.
set -euo pipefail
exec python3 "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/deployment.py" "$@"
