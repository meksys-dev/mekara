#!/usr/bin/env bash
# Clean up sync marker after successful commit
set -euo pipefail

if [ -f .mekara/.sync-in-progress ]; then
    rm .mekara/.sync-in-progress
fi
