# Experiment 3 Clean Chinese Manuscript Pack Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This audit records a clean UTF-8 Chinese manuscript layer for Experiment 3.
It fixes the paper-facing writing surface by providing non-mojibake Chinese
title, abstract, methods, results, discussion, conclusion and figure/table
caption text while preserving the existing evidence boundaries.

## Outputs

- `paper_text/experiment3_clean_chinese_sci_package_zh.md`
- `paper_text/experiment3_clean_chinese_core_paragraphs_zh.md`
- `paper_text/experiment3_clean_chinese_figure_table_captions_zh.md`
- `paper_text/experiment3_final_sci_discussion_conclusion_zh.md`
- `paper_text/experiment3_sci_manuscript_module_zh.md`
- `manifests/experiment3_clean_chinese_manuscript_evidence_map.csv`

## Boundary

The clean Chinese text does not add new CFD evidence. It converts verified
Experiment 3 evidence into readable SCI-style Chinese and keeps blocked claims
explicit: field validation, annual comfort/safety compliance, pollutant
dispersion, GCBTE closure, CityLBM-Grasshopper end-to-end execution and
successful design optimization remain unsupported.
