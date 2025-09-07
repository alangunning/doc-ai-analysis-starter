# Contributing to Documentation

Please ensure all images include meaningful alt text. This project runs `npm run lint:alt-text` during the build to catch missing `alt` attributes. Docs changes that introduce images without alt text will fail these checks.

Run the following commands locally before submitting documentation PRs:

```bash
npm run lint:alt-text
npm run build
```
