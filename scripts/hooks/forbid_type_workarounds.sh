#!/usr/bin/env bash
set -euo pipefail

# Verify grep is available
command -v grep >/dev/null 2>&1 || { echo "Error: grep not found" >&2; exit 1; }

# No files means nothing to check
if [ "$#" -eq 0 ]; then
  exit 0
fi

has_type_ignore=0
has_type_checking=0

for file in "$@"; do
  # Only check existing Python files
  if [ "${file##*.}" != "py" ] || [ ! -f "$file" ]; then
    continue
  fi

  # Capture any lines containing type: ignore
  # grep returns 0 if found, 1 if not found, >1 on error
  matches=""
  grep_exit=0
  matches=$(grep -n "type: ignore" -- "$file") || grep_exit=$?
  if [ "$grep_exit" -gt 1 ]; then
    echo "Error: grep failed on $file" >&2
    exit 1
  elif [ "$grep_exit" -eq 0 ]; then
    printf "%s:%s\n" "$file" "$matches"
    has_type_ignore=1
  fi

  # Capture any lines containing if TYPE_CHECKING:
  matches=""
  grep_exit=0
  matches=$(grep -n "if TYPE_CHECKING:" -- "$file") || grep_exit=$?
  if [ "$grep_exit" -gt 1 ]; then
    echo "Error: grep failed on $file" >&2
    exit 1
  elif [ "$grep_exit" -eq 0 ]; then
    printf "%s:%s\n" "$file" "$matches"
    has_type_checking=1
  fi
done

exit_code=0

if [ "$has_type_ignore" -ne 0 ]; then
  echo "Error: Properly fix type errors instead of cheating with 'type: ignore'." >&2
  exit_code=1
fi

if [ "$has_type_checking" -ne 0 ]; then
  echo "Error: Remove 'if TYPE_CHECKING:' blocks." >&2
  exit_code=1
fi

exit $exit_code
