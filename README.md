# Work Log

A simple, flexible CLI tool for logging work activities with action item tracking.

## Overview

Work Log is a command-line tool that helps you keep organized records of your daily work. It uses plain Markdown files with YAML frontmatter, making your logs both human-readable and easy to search.

## Features

- **Unified log creation**: Single workflow for all types of logs
- **Smart organization**: Logs automatically organized by year and month (`~/work-logs/YYYY/MM/`)
- **YAML frontmatter**: Structured metadata for easy filtering and searching
- **Recent items**: Projects and contacts derived from recent logs for quick selection
- **Flexible filtering**: Filter logs by project, contact, or time period
- **Action item tracking**: Extract and list action items across logs
- **Taskwarrior integration**: Raw output mode for piping to task managers
- **Editor integration**: Opens logs in your preferred editor (set via `$EDITOR`)

## Installation

1. Clone this repository
2. Make `log.py` executable (optional):
   ```bash
   chmod +x log.py
   ```
3. Add to your PATH or create an alias:
   ```bash
   alias log="/path/to/log.py"
   ```

## Usage

### Create a New Log

Run without arguments to create a new log:

```bash
log
```

This prompts for:
1. **Date** - Enter for today, or type a date/day name
2. **Project** - Select from recent projects or type a new one
3. **Contacts** - Select from recent contacts or type new ones (comma-separated)

Then opens the log in your editor.

### Browsing and Searching Logs

Logs are plain Markdown files stored in `~/work-logs/YYYY/MM/`. Use your shell's native tools to browse and search them:

```bash
# Browse logs interactively (requires fzf)
logbrowse

# Full-text search across all logs
logsearch "api endpoint"

# Filter by project
logproject "api-refactor"

# Filter by contact
logcontact "sarah"

# Review this week's logs
logweek
```

See `shell-functions.sh` in the repo root to install these helpers.

### Action Items

```bash
log actions                 # Action items from last 10 logs
log actions thisweek        # Action items from this week
log actions lastweek        # Action items from last week
log actions --raw           # Pipe-friendly output
```

Normal output:
```
=== 2026-02-02 | vims-website ===
  1. Follow up with Sarah about API docs
  2. Schedule review meeting

=== 2026-02-01 | content-cleanup ===
  3. Send reminder to publishers
  4. Update tracking spreadsheet

Enter number to open source log, or press Enter to exit:
```

Raw output (`--raw`):
```
2026-02-02 | vims-website | Follow up with Sarah about API docs
2026-02-02 | vims-website | Schedule review meeting
2026-02-01 | content-cleanup | Send reminder to publishers
2026-02-01 | content-cleanup | Update tracking spreadsheet
```

The raw format uses ` | ` as delimiter for easy parsing with `cut` or `awk`.

## File Structure

Logs are stored in `~/work-logs/` with the following structure:

```
~/work-logs/
├── 2026/
│   ├── 01/
│   │   ├── log-2026-01-12.md
│   │   └── log-2026-01-12-143052.md  # Second log same day
│   └── 02/
│       └── ...
└── 2025/
    └── ...
```

## Log Format

Each log file uses YAML frontmatter for metadata:

```markdown
---
date: 2026-01-12
project: API Refactoring
contacts: [John D, Sarah M]
---

Your notes here...

## Action Items
- Follow up with John about the spec
- Review pull request #123
```

The `## Action Items` section is parsed for the `log actions` command. Use standard markdown bullet points (`- `).

## Configuration

### Editor

Set your preferred editor using the `EDITOR` environment variable:

```bash
export EDITOR=vim        # Default
export EDITOR=nano
export EDITOR=code       # VS Code
```

### Log Directory

By default, logs are stored in `~/work-logs/`. To change this, edit `LOG_DIR` in `worklog/config.py`:

```python
LOG_DIR = Path.home() / "work-logs"
```

## Date Input

When creating logs, you can use flexible date formats:

- `today` or press Enter (default)
- `tomorrow` or `yesterday`
- Day names: `monday`, `tuesday`, etc. (next occurrence)
- ISO format: `2026-01-15`
- Month-day: `01-15` (current year assumed)
- Day only: `15` (current month and year assumed)

## Taskwarrior Integration

Use the raw output mode to pipe action items to Taskwarrior or other task managers:

```bash
# Add all action items from this week as tasks
log actions thisweek --raw | while IFS='|' read -r date project item; do
  task add "$item" project:"${project// /}" due:eow
done
```

## Tips

1. **Quick alias**: Add to your shell config:
   ```bash
   alias log="/path/to/log.py"
   ```

2. **Review recent work**:
   ```bash
   logweek
   ```

3. **Project retrospectives**:
   ```bash
   logproject "Your Project Name"
   ```

4. **Find old notes**:
   ```bash
   logsearch "API endpoint discussion"
   ```

5. **Weekly action item review**:
   ```bash
   log actions lastweek
   ```

## License

This tool is provided as-is for personal use.
