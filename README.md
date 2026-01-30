# Work Log

A simple, flexible CLI tool for logging work activities, project updates, and meeting notes.

## Overview

Work Log is a command-line tool that helps you keep organized records of your daily work. It uses plain Markdown files with YAML frontmatter, making your logs both human-readable and easy to search.

## Features

- **Multiple log types**: Quick logs, project logs, and meeting notes
- **Smart organization**: Logs automatically organized by year and month (`~/work-logs/YYYY/MM/`)
- **YAML frontmatter**: Structured metadata for easy filtering and searching
- **Auto-completion**: Projects and contacts are saved and available for quick selection
- **Flexible filtering**: Filter logs by project (`-p`) or contact (`-c`)
- **Interactive or direct**: Use the interactive menu or run commands directly
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

### Interactive Menu

Run without arguments to open the interactive menu:

```bash
./log.py
```

This presents options to:
1. Create a quick log
2. Create a project log
3. Create meeting notes
4. List recent logs
5. Search logs
6. View summary

### Direct Commands

Run specific commands directly:

```bash
./log.py log          # Quick log (no project/meeting)
./log.py project      # Log with project tag
./log.py meeting      # Meeting notes
./log.py list         # List recent logs
./log.py search       # Search logs
./log.py summary      # Weekly/monthly summary
./log.py projects     # List all projects
./log.py contacts     # List all contacts
```

### Command Examples

**Create a project log:**
```bash
./log.py project
# or specify project directly
./log.py project "API Refactoring"
```

**List logs filtered by project:**
```bash
./log.py list -p "API Refactoring"
```

**List logs filtered by contact:**
```bash
./log.py list -c "John D"
```

**Search logs:**
```bash
./log.py search "bug fix"
# or search interactively
./log.py search
```

**Limit results:**
```bash
./log.py list -n 10
```

**View weekly summary (default):**
```bash
./log.py summary
./log.py summary --week
```

**View monthly summary:**
```bash
./log.py summary --month           # Current month
./log.py summary --month 12        # Specific month (current year)
./log.py summary --month 2025-12   # Specific month and year
```

## File Structure

Logs are stored in `~/work-logs/` with the following structure:

```
~/work-logs/
├── .projects        # Auto-saved list of projects
├── .contacts        # Auto-saved list of contacts
├── 2026/
│   ├── 01/
│   │   ├── log-2026-01-12.md
│   │   ├── project-2026-01-12-api-refactoring.md
│   │   └── meeting-2026-01-12-john-d.md
│   └── 02/
│       └── ...
└── 2025/
    └── ...
```

## Log Format

Each log file uses YAML frontmatter for metadata:

**Quick log:**
```markdown
---
date: 2026-01-12
type: log
---

Your notes here...
```

**Project log:**
```markdown
---
date: 2026-01-12
type: project
project: API Refactoring
---

Project notes here...
```

**Meeting notes:**
```markdown
---
date: 2026-01-12
type: meeting
project: API Refactoring
contacts: [John D, Sarah M]
---

## Meeting Notes

- Discussion points...
- Action items...
```

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

## Auto-saved Data

The tool maintains two hidden files for auto-completion:

- **`.projects`**: List of all projects you've logged (one per line)
- **`.contacts`**: List of all contacts from meetings (one per line)

These files are automatically updated when you create logs and are used to provide quick selection options.

## Date Input

When creating meeting notes, you can use flexible date formats:

- `today` or press Enter (default)
- `tomorrow` or `yesterday`
- Day names: `monday`, `tuesday`, etc. (next occurrence)
- ISO format: `2026-01-15`
- Month-day: `01-15` (current year assumed)
- Day only: `15` (current month and year assumed)

## Tips

1. **Quick daily logs**: Create an alias for fast logging:
   ```bash
   alias qlog="/path/to/log.py log"
   ```

2. **Review recent work**: Use `list` to see your recent activity:
   ```bash
   ./log.py list -n 5
   ```

3. **Project retrospectives**: Filter by project to review all related logs:
   ```bash
   ./log.py list -p "Your Project Name"
   ```

4. **Find old notes**: Search by keywords, contact names, or project names:
   ```bash
   ./log.py search "API endpoint discussion"
   ```

## License

This tool is provided as-is for personal use.
