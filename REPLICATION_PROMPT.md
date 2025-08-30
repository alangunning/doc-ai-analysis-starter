# AI Agent Prompt: Replicate `doc-ai-analysis-starter`

You are an AI coding agent with access to a Bash shell and the GitHub CLI.
Recreate the `doc-ai-analysis-starter` template in a brand‑new repository.
Follow the steps exactly and stop on any error.

## 1. Prepare a fresh repository
1. Create an empty repository on GitHub (replace `NEW_REPO` with its name).
2. In the workspace, run:

```bash
mkdir NEW_REPO
cd NEW_REPO
git init -b main
```

## 2. Download the template snapshot
Fetch the contents of this template at commit `812aee771a64bfa3d00b3b1ebd16d054a1be8443`:

```bash
curl -L https://github.com/airnub/doc-ai-analysis-starter/archive/812aee771a64bfa3d00b3b1ebd16d054a1be8443.tar.gz \
  | tar xz --strip-components=1
```

## 3. Commit the files
```bash
git add .
git commit -m "Initial commit"
```

## 4. Push to the new repo
```bash
gh repo create NEW_REPO --source=. --public --push --remote=origin
```

The new repository now contains an identical copy of `doc-ai-analysis-starter`.
