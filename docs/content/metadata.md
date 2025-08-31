---
title: Metadata Module
sidebar_position: 5
---

# Metadata Module

The `ai_doc_analysis_starter.metadata` package tracks processing state in [Dublin Core](https://www.dublincore.org/specifications/dublin-core/) JSON files that live alongside each source document.

## Overview

Each document can have a companion `<name>.metadata.json` file storing a checksum and a map of completed workflow steps. The metadata is represented by a `DublinCoreDocument` record, allowing workflows to skip work they have already done.

## API

### `metadata_path(doc_path)`
Return the path to the metadata file for a source document.

### `load_metadata(doc_path)`
Load metadata for a document, returning a `DublinCoreDocument` instance.

### `save_metadata(doc_path, meta)`
Write metadata alongside the document.

### `compute_hash(doc_path)`
Compute a blake2b checksum of the file at `doc_path`.

### `is_step_done(meta, step)`
Check whether a processing step has been marked complete.

### `mark_step(meta, step, done=True)`
Record completion state for a processing step.

## Dublin Core fields

`DublinCoreDocument` supports these properties:

- `title`
- `description`
- `publisher`
- `creator`
- `subject`
- `contributor`
- `date`
- `type`
- `format`
- `identifier`
- `source`
- `language`
- `relation`
- `coverage`
- `rights`
- `audience`
- `mediator`
- `accrual_method`
- `accrual_periodicity`
- `accrual_policy`
- `alternative`
- `bibliographic_citation`
- `conforms_to`
- `date_accepted`
- `date_available`
- `date_created`
- `date_issued`
- `date_modified`
- `date_submitted`
- `extent`
- `has_format`
- `has_part`
- `has_version`
- `is_format_of`
- `is_part_of`
- `is_referenced_by`
- `is_replaced_by`
- `is_required_by`
- `issued`
- `is_version_of`
- `license`
- `provenance`
- `rights_holder`
- `spatial`
- `temporal`
- `valid`

Additional non-Dublin Core fields include `content`, `blake2b`, `id`, `size`, and an `extra` dictionary that stores workflow-specific data such as the `steps` completion map.
