#!/usr/bin/env bash
# Shell helper functions for browsing and searching work logs.
# Source this file from your ~/.bashrc or ~/.zshrc:
#   source /path/to/shell-functions.sh

WORKLOG_DIR="${WORKLOG_DIR:-$HOME/work-logs}"

# Browse all logs interactively using fzf.
# Requires: fzf
logbrowse() {
    local selected
    selected=$(find "$WORKLOG_DIR" -name "*.md" | sort -r | fzf --preview 'cat {}')
    if [[ -n "$selected" ]]; then
        "${EDITOR:-vim}" "$selected"
    fi
}

# Full-text search across all logs using grep, preview with fzf.
# Usage: logsearch <query>
# Requires: fzf
logsearch() {
    local query="$*"
    if [[ -z "$query" ]]; then
        echo "Usage: logsearch <query>" >&2
        return 1
    fi
    local selected
    selected=$(grep -rl --include="*.md" -i "$query" "$WORKLOG_DIR" | sort -r \
        | fzf --preview "grep -i --color=always -C3 '$query' {}")
    if [[ -n "$selected" ]]; then
        "${EDITOR:-vim}" "$selected"
    fi
}

# Filter logs by project name (case-insensitive partial match).
# Usage: logproject <project-name>
# Requires: fzf
logproject() {
    local project="$*"
    if [[ -z "$project" ]]; then
        echo "Usage: logproject <project-name>" >&2
        return 1
    fi
    local selected
    selected=$(grep -rl --include="*.md" -i "^project:.*${project}" "$WORKLOG_DIR" | sort -r \
        | fzf --preview 'cat {}')
    if [[ -n "$selected" ]]; then
        "${EDITOR:-vim}" "$selected"
    fi
}

# Filter logs by contact name (case-insensitive partial match).
# Usage: logcontact <contact-name>
# Requires: fzf
logcontact() {
    local contact="$*"
    if [[ -z "$contact" ]]; then
        echo "Usage: logcontact <contact-name>" >&2
        return 1
    fi
    local selected
    selected=$(grep -rl --include="*.md" -i "contacts:.*${contact}" "$WORKLOG_DIR" | sort -r \
        | fzf --preview 'cat {}')
    if [[ -n "$selected" ]]; then
        "${EDITOR:-vim}" "$selected"
    fi
}

# Browse logs from the current week (Monday through today).
# Requires: fzf
logweek() {
    local monday
    monday=$(date -d "last monday" +%Y-%m-%d 2>/dev/null \
        || date -v-monday +%Y-%m-%d 2>/dev/null \
        || python3 -c "from datetime import date, timedelta; t=date.today(); print((t - timedelta(days=t.weekday())).isoformat())")
    local selected
    selected=$(find "$WORKLOG_DIR" -name "*.md" | sort -r \
        | while IFS= read -r f; do
            stem=$(basename "$f" .md)
            filedate="${stem:0:10}"
            if [[ "$filedate" > "$monday" || "$filedate" == "$monday" ]]; then
                echo "$f"
            fi
        done \
        | fzf --preview 'cat {}')
    if [[ -n "$selected" ]]; then
        "${EDITOR:-vim}" "$selected"
    fi
}
