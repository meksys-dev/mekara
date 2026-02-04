#!/usr/bin/env bash
# Syncs scripts between .mekara/scripts/nl/ and docs/wiki/.
# Validates that bundled NL and compiled scripts are updated together.
# Alerts when .mekara or bundled scripts change without corresponding changes in the other location.
set -euo pipefail

# If we just synced on a previous hook run, skip conflict check
if [ -f .mekara/.sync-in-progress ]; then
    exit 0
fi

# Detect which sources have changed in this commit
changed_files=$(git diff --cached --name-only)

nl_changed=false
wiki_changed=false
bundled_nl_changed=false
bundled_compiled_changed=false

if echo "$changed_files" | grep -q "^\.mekara/scripts/nl/"; then
    nl_changed=true
fi

if echo "$changed_files" | grep -q "^docs/wiki/"; then
    wiki_changed=true
fi

if echo "$changed_files" | grep -q "^src/mekara/bundled/scripts/nl/"; then
    bundled_nl_changed=true
fi

if echo "$changed_files" | grep -q "^src/mekara/bundled/scripts/compiled/"; then
    bundled_compiled_changed=true
fi

# Check for conflicts: both .mekara/scripts/nl/ and docs/wiki/ changed
if [ "$nl_changed" = true ] && [ "$wiki_changed" = true ]; then
    echo "Error: Both .mekara/scripts/nl/ and docs/wiki/ were modified in this commit."
    echo "This creates a sync conflict. Please commit changes to only one source at a time."
    exit 1
fi

# Sync based on what changed
synced=false

if [ "$nl_changed" = true ]; then
    echo "Natural language scripts changed. Syncing to docs/wiki/ and bundled scripts..."
    python3 scripts/sync-nl.py --direction=to-docs
    git add docs/wiki/ src/mekara/bundled/scripts/nl/
    synced=true
fi

if [ "$wiki_changed" = true ]; then
    echo "Wiki changed. Syncing to .mekara/scripts/nl/ and bundled scripts..."
    python3 scripts/sync-nl.py --direction=to-mekara
    git add .mekara/scripts/nl/ src/mekara/bundled/scripts/nl/
    synced=true
fi

# If we synced, create marker and exit 1 to re-run hooks
if [ "$synced" = true ]; then
    touch .mekara/.sync-in-progress
    exit 1
fi

# Validate bundled scripts: if bundled NL changed, corresponding compiled must also change
if [ "$bundled_nl_changed" = true ]; then
    # Get list of changed bundled NL scripts and convert to expected compiled paths
    bundled_nl_files=$(echo "$changed_files" | grep "^src/mekara/bundled/scripts/nl/" | sed 's/nl/compiled/; s/\.md$/.py/')

    missing_compiled=()
    for compiled_path in $bundled_nl_files; do
        if ! echo "$changed_files" | grep -q "^${compiled_path}$"; then
            missing_compiled+=("$compiled_path")
        fi
    done

    if [ ${#missing_compiled[@]} -gt 0 ]; then
        echo "Error: Bundled natural language scripts changed without corresponding compiled scripts."
        echo "The following compiled scripts must also be updated:"
        for path in "${missing_compiled[@]}"; do
            echo "  - $path"
        done
        echo ""
        echo "When editing bundled scripts, update both the .md and .py versions together."
        exit 1
    fi
fi

# Alert when .mekara or bundled scripts change without corresponding changes in the other location
if [ "$nl_changed" = true ] && [ "$bundled_nl_changed" = false ]; then
    # Check if any changed .mekara scripts have corresponding bundled versions
    nl_files=$(echo "$changed_files" | grep "^\.mekara/scripts/nl/")
    has_bundled_equivalent=false

    for nl_file in $nl_files; do
        # Convert .mekara path to bundled path
        bundled_path=$(echo "$nl_file" | sed 's|^\.mekara/scripts/nl/|src/mekara/bundled/scripts/nl/|')
        if [ -f "$bundled_path" ]; then
            has_bundled_equivalent=true
            break
        fi
    done

    if [ "$has_bundled_equivalent" = true ]; then
        echo ""
        echo "Warning: .mekara/scripts/nl/ changed but bundled scripts didn't."
        echo "Check if src/mekara/bundled/scripts/nl/ needs corresponding updates."
        echo ""
    fi
fi

if [ "$bundled_nl_changed" = true ] && [ "$nl_changed" = false ]; then
    # Check if any changed bundled scripts have corresponding .mekara versions
    bundled_files=$(echo "$changed_files" | grep "^src/mekara/bundled/scripts/nl/")
    has_mekara_equivalent=false

    for bundled_file in $bundled_files; do
        # Convert bundled path to .mekara path
        mekara_path=$(echo "$bundled_file" | sed 's|^src/mekara/bundled/scripts/nl/|.mekara/scripts/nl/|')
        if [ -f "$mekara_path" ]; then
            has_mekara_equivalent=true
            break
        fi
    done

    if [ "$has_mekara_equivalent" = true ]; then
        echo ""
        echo "Warning: Bundled scripts changed but .mekara/scripts/nl/ didn't."
        echo "Check if .mekara/scripts/nl/ needs corresponding updates."
        echo ""
    fi
fi
