# review_pr.py - Standalone PR Review Tool

`review_pr.py` is a standalone tool for reviewing individual pull requests in openEuler repositories. It extracts the single PR review functionality from `oe_review.py` into an independent module.

## Features

- Standalone PR review without SIG-based workflow
- Support for both Gitcode and Gitee APIs
- AI-powered code review using various models
- Manual review editing with your favorite editor
- Review history lookup from similar PRs
- ChromaDB integration for context-aware reviews (optional)
- Configurable filters to skip certain PRs

## Installation

Ensure you have the required dependencies:
```bash
pip install -r requirements.txt
```

Optional: ChromaDB for enhanced review context:
```bash
pip install chromadb
```

## Usage

### Basic Usage

Review a PR by repository and number:
```bash
python3 review_pr.py openeuler/iSulad 123
```

Review a Gitee PR:
```bash
python3 review_pr.py src-openeuler/yum 456 --api gitee
```

Review using full URL:
```bash
python3 review_pr.py --url https://gitcode.com/openeuler/iSulad/merge_requests/123
```

### Advanced Options

Specify AI model:
```bash
python3 review_pr.py openeuler/iSulad 123 --model gpt-4
```

Use local AI model:
```bash
python3 review_pr.py openeuler/iSulad 123 --intelligent local
```

Disable AI review:
```bash
python3 review_pr.py openeuler/iSulad 123 --intelligent no
```

Verbose output:
```bash
python3 review_pr.py openeuler/iSulad 123 --verbose
```

Custom editor:
```bash
python3 review_pr.py openeuler/iSulad 123 --editor vim --editor-option "-c 'set noswapfile'"
```

## Configuration

Create a configuration file at `~/.openeulerrc`:

```ini
[deepseek]
model = deepseek-chat
api_key = your_api_key_here
base_url = https://api.deepseek.com/v1

[editor]
command = nvim
option = -c 'set noswapfile'

[filter]
labels = ci_failed openeuler-cla/no
submitters = bot1 bot2
repos = repo1/repo2 repo3/repo4
```

## Integration with Other Tools

### Interactive PR Selector

The `interactive_pr_review.py` and `select_pr_review.py` scripts now use `review_pr.py` for single PR reviews:

```bash
# Interactive selection with continuous review
python3 interactive_pr_review.py --sig infra

# Will call:
# python3 review_pr.py <owner>/<repo> <pr_number>
```

### oe_review.py Integration

The main `oe_review.py` now delegates single PR reviews to this module, maintaining backward compatibility:

```bash
# Both commands now internally use review_pr.py
oe_review -n openeuler/iSulad -p 123
review_pr.py openeuler/iSulad 123
```

## API Support

### Gitcode
- Default API platform
- URLs: `https://gitcode.com/<owner>/<repo>/merge_requests/<pr>`

### Gitee
- Use `--api gitee` flag
- URLs: `https://gitee.com/<owner>/<repo>/pulls/<pr>`

## Review Process

1. **Fetch PR Details**: Retrieves PR information, diff, and metadata
2. **Apply Filters**: Skips PRs based on configured filters (labels, submitters, repos)
3. **Smart Classification**: Suggests actions (close/review) based on PR state
4. **AI Review**: Generates AI-powered review comments
5. **Manual Editing**: Opens editor for final review editing
6. **Submit Review**: Posts the review to the PR
7. **Store Context**: Saves review in ChromaDB for future reference (if available)

## Output

- Verbose logs show the review progress
- Final confirmation when review is submitted
- Error messages for failures with details

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'chromadb'"**
   - Install ChromaDB: `pip install chromadb`
   - Or continue without it (features will be limited)

2. **"Invalid repository format"**
   - Use format: `owner/repo` (e.g., `openeuler/iSulad`)
   - Or use full URL with `--url` option

3. **"Error fetching PR"**
   - Check repository exists and PR number is correct
   - Verify API access permissions
   - Try with `--verbose` for detailed error

4. **"Config file not found"**
   - Create `~/.openeulerrc` with required sections
   - Or pass options via command line

## Examples in CI/CD

```bash
#!/bin/bash
# Review script for CI/CD pipeline

# Review PR from environment variables
REPO=${GITHUB_REPOSITORY}
PR_NUMBER=${PR_NUMBER}
MODEL=${AI_MODEL:-gpt-3.5-turbo}

python3 review_pr.py $REPO $PR_NUMBER --model $MODEL --verbose
```

## Differences from oe_review.py

- **Scope**: Only single PR review, no SIG-based bulk review
- **Simplicity**: Standalone with minimal dependencies
- **Flexibility**: Can be used in scripts and automation
- **Portability**: Easy to integrate with other tools