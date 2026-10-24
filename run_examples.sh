#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-${PROJECT_ROOT}/docs/examples/output}"

if [[ -n "${PYTHON:-}" ]]; then
    PYTHON_BIN="${PYTHON}"
elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
elif [[ -x "${PROJECT_ROOT}/.venv/Scripts/python.exe" ]]; then
    PYTHON_BIN="${PROJECT_ROOT}/.venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    PYTHON_BIN="$(command -v python)"
fi

case "${PYTHON_BIN}" in
    *.exe|*.EXE)
        if command -v wslpath >/dev/null 2>&1; then
            OUTPUT_DIR="$(wslpath -w "${OUTPUT_DIR}")"
        elif command -v cygpath >/dev/null 2>&1; then
            OUTPUT_DIR="$(cygpath -w "${OUTPUT_DIR}")"
        fi
        ;;
esac

cd "${PROJECT_ROOT}"
"${PYTHON_BIN}" -m braincode.example_runner --output "${OUTPUT_DIR}"
