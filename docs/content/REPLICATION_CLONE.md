---
sidebar_position: 3
---

# AI Agent Prompt: Clone `doc-ai-analysis-starter`

You are an AI coding agent with access to a Bash shell and the GitHub CLI.
Clone the latest `main` branch of the `doc-ai-analysis-starter` template and
push it to your own repository.

## Steps
1. Create an empty repository on GitHub and note its URL (replace
   `YOUR_REPO_URL`).
2. In the workspace, run:
   ```bash
   git clone --depth 1 https://github.com/airnub/doc-ai-analysis-starter.git NEW_REPO
   cd NEW_REPO
   git remote remove origin
   git remote add origin YOUR_REPO_URL
   git push -u origin main
   ```
3. The new repository now contains the latest template from `main`.
