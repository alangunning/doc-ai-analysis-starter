---
title: Pull Request Reviews
sidebar_position: 3
---

# Pull Request Reviews

Doc AI can provide AI-generated feedback on pull requests using GitHub Models. The workflow reads a prompt definition and comments on the PR with the model's response.

## Enable the Workflow

1. Ensure `ENABLE_PR_REVIEW_WORKFLOW=true` in your `.env` file (or set in the repository secrets).
2. Keep or customize `.github/prompts/pr-review.prompt.yaml` to define the review instructions.

The workflow runs automatically on every pull request. You can also trigger it again by leaving a `/review` comment on the PR.

## Customize the Model

Set `PR_REVIEW_MODEL` to change the model used.

## Manual Runs

To experiment locally, run the helper script:

```bash
python scripts/review_pr.py .github/prompts/pr-review.prompt.yaml "PR body text"
```

The script prints the model's feedback to the terminal. Use it to iterate on prompt wording before committing changes.
