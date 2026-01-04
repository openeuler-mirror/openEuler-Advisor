# Interactive PR Review Scripts

This directory contains two scripts for interactive PR selection and review using the openEuler-Advisor toolchain.

## Scripts

### 1. `interactive_pr_review.py` - Full-screen Interactive Selector

A full-screen TUI application with keyboard navigation for selecting and reviewing PRs.

**Features:**
- Arrow keys (↑↓) or `j`/`k` for navigation
- `Enter` to select and review a PR
- `i` to view detailed PR information
- `q` to quit
- **Continuous review mode**: Automatically returns to selection after each PR review
- Visual indicators (✓) for reviewed PRs
- Progress tracking showing reviewed/total PR count
- Scrollable list for large PR sets
- Real-time status bar showing current selection and review progress

**Usage:**
```bash
# Review PRs from a SIG
python3 interactive_pr_review.py --sig infra

# Review PRs from a specific repository
python3 interactive_pr_review.py --repo src-openeuler python-marshmallow

# Use a specific AI model for review
python3 interactive_pr_review.py --sig devkit --model gpt-4

# Enable verbose output
python3 interactive_pr_review.py --repo openeuler TSB-agent --verbose
```

### 2. `select_pr_review.py` - Simple Line-based Selector

A simpler terminal-based selector that works in any terminal environment.

**Features:**
- Numbered list of PRs
- Interactive selection or direct PR number selection
- Works without curses library
- Pipes and redirection friendly

**Usage:**
```bash
# Interactive selection
python3 select_pr_review.py --sig infra

# Direct selection by PR number from the list
python3 select_pr_review.py --repo src-openeuler python-marshmallow --number 1

# Pipe selection
echo "2" | python3 select_pr_review.py --sig devkit
```

## Common Options

Both scripts support these options:

- `-s, --sig SIG`: Fetch PRs by SIG name
- `-r, --repo OWNER REPO`: Fetch PRs from a specific repository
- `--model MODEL`: AI model to use for review (passed to oe_review)
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## Requirements

### interactive_pr_review.py
- Python 3
- curses library (usually included with Python)
- Terminal with TUI support

### select_pr_review.py
- Python 3
- Basic terminal (no special libraries required)

Both scripts use:
- `get_openeuler_pending_pr.py` for fetching PRs
- `advisors/oe_review.py` for reviewing selected PRs

## Example Workflow

### Interactive Continuous Review

1. Start the interactive reviewer:
   ```bash
   python3 interactive_pr_review.py --sig infra
   ```

2. The TUI shows all PRs with navigation:
   ```
   ┌────────────────────────────────────────────────────────────┐
   │                 Select PR to Review                        │
   └────────────────────────────────────────────────────────────┘
   ↑/↓: Navigate | Enter: Review | q: Quit | i: PR Info | r: Refresh

     1. src-openeuler/package1#123 ✓ - Fix bug in package1 by author1
   → 2. src-openeuler/package2#456 - Add new feature by author2
     3. openeuler/project#789 - Update documentation by author3

   PR 2/5 | Reviewed: 1/5 | Owner: src-openeuler/package2 | Author: author2
   ```

3. Navigate and select a PR to review. After the review completes:
   ```
   ============================================================
   Review completed for: src-openeuler/package2#456
   Total PRs reviewed: 2/5
   ============================================================

   Continue reviewing? (Y/n):
   ```

4. Press Enter to continue reviewing next PR or 'n' to quit

5. Reviewed PRs are marked with ✓ and dimmed in the interface

### Simple Selection Mode

1. Quick selection from command line:
   ```bash
   python3 select_pr_review.py --sig infra
   ```

2. Output shows:
   ```
   Found 5 PRs:
   ------------------------------------------------------------
     1. src-openeuler/package1#123 - Fix bug in package1 by author1
     2. src-openeuler/package2#456 - Add new feature by author2
     3. openeuler/project#789 - Update documentation by author3
   ------------------------------------------------------------
   Select PR to review (1-3, q to quit):
   ```

3. The selected PR will be passed to `oe_review.py` for AI-powered review

## Integration with oe_review

The scripts automatically invoke `oe_review.py` with appropriate arguments:
```bash
python3 advisors/oe_review.py --repo REPO_NAME --owner OWNER --pr PR_NUMBER [--model MODEL]
```

Ensure `oe_review.py` and its dependencies are properly configured:
- Required Python modules installed
- OpenAI API key configured (if using OpenAI models)
- Git/Gitee credentials set up

## Troubleshooting

### Common Issues

1. **"No PRs found"**
   - Check that the SIG name or repository exists
   - Verify internet connection
   - Try verbose output (`-v`) to see API details

2. **Module import errors**
   - Install required modules: `pip install -r requirements.txt`
   - Ensure virtual environment is activated

3. **Terminal issues with interactive_pr_review.py**
   - Use `select_pr_review.py` instead (no curses required)
   - Check terminal supports curses/TUI

4. **oe_review.py errors**
   - Verify all dependencies are installed
   - Check API keys and configuration
   - Run `oe_review.py --help` for specific requirements