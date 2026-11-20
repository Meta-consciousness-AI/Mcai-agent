#!/bin/sh
# MCAI remote knowledge skill: POSIX wrapper.
# Usage: sh bin/query.sh answer "什么是元识？"
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BASE="${MCAI_BASE_URL:-https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com/api/v1}"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$DIR/mcai_client.py" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$DIR/mcai_client.py" "$@"
fi

# Fallback: curl + jq, answer only.
if [ "$#" -ge 2 ] && [ "$1" = "answer" ] && command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  jq -n --arg q "$2" '{question:$q}' \
    | curl -sS -m 90 -X POST "$BASE/answer" \
        -H 'Content-Type: application/json; charset=utf-8' \
        -H 'User-Agent: mcai-remote-skill/1.0' \
        --data-binary @-
  exit 0
fi

printf '%s\n' '{"ok":false,"error":"no_python_or_jq","detail":"需要 python3，或 curl + jq"}' >&2
exit 1
