---
title: Converter Module
sidebar_position: 3
---

# Converter Module

The `doc_ai.converter` package wraps the
[Docling](https://github.com/docling/docling) backend to convert source
files into several text-based representations.  The module exposes a small
API so callers can request formats without depending on Docling directly.

## Supported formats

The `OutputFormat` enumeration lists every canonical output.  Each format
has a convenience file suffix:

| Format | Description | Suffix |
| ------ | ----------- | ------ |
| `markdown` | GitHub-flavored Markdown | `.md` |
| `html` | HTML document fragment | `.html` |
| `json` | Raw JSON export of the Docling document | `.json` |
| `text` | Plain text rendering | `.txt` |
| `doctags` | Docling "doctags" markup | `.doctags` |

## API

### `convert_files(input_path, outputs)`
Convert a single input document to multiple formats in one pass.  Pass a
`pathlib.Path` to the source file and a mapping of `OutputFormat` to
destination paths.  A dictionary mapping each format to the written path is
returned.

### `convert_file(input_path, output_path, fmt)`
Convenience wrapper for converting to a single format.  Returns the path
that was written.

### `suffix_for_format(fmt)`
Return the default file suffix for an `OutputFormat` value.

## Example

```python
from pathlib import Path
from doc_ai.converter import (
    OutputFormat, convert_file, convert_files, suffix_for_format,
)

# Convert to Markdown only
convert_file(Path('report.pdf'), Path('report.pdf.converted.md'), OutputFormat.MARKDOWN)

# Convert to multiple formats at once
outputs = {
    OutputFormat.MARKDOWN: Path('report.pdf.converted.md'),
    OutputFormat.HTML: Path('report.pdf.converted.html'),
}
convert_files(Path('report.pdf'), outputs)

# Look up the default suffix for a format
suffix_for_format(OutputFormat.JSON)  # returns '.json'
```
