# Experiment 3 Chinese Text Quality Audit

evidence_type: newly_run

## Scope

This audit checks paper-facing Chinese Markdown files for common mojibake patterns and replacement characters after the clean Chinese manuscript layer and caption files are regenerated. It is a text-integrity gate, not a scientific-content review.

## Summary

- Chinese/draft Markdown files scanned: `49`
- Passed files: `49`
- Files requiring review: `0`
- Canonical direct-use files scanned: `8`
- Canonical direct-use files requiring review: `0`

## Canonical Use Policy

Use the clean Chinese manuscript package and the regenerated SCI caption files as the direct writing surface. Older Chinese Markdown files may remain as supporting provenance, but any file flagged by this audit must be corrected before being copied into a manuscript.

## Top Audit Rows

| relative_path | file_role | mojibake_hits | replacement_question_marks | quality_status |
|---|---|---:|---:|---|
| paper_text/basic_morphology_multivariate_robustness_conclusion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/basic_morphology_wind_response_conclusion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/building_form_wind_environment_discussion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/building_form_wind_mechanism_conclusion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/conclusion_climate_campus_digital_twin_wind_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/deepened_results_and_discussion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/design_intervention_s1_discussion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/design_intervention_s2_discussion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/design_sensitivity_directional_tradeoff_discussion_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/detailed_paper_conclusions_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/discussion_limitations_zh.md | supporting_or_legacy_text | 0 | 0 | pass |
| paper_text/experiment3_clean_chinese_core_paragraphs_zh.md | canonical_direct_use | 0 | 0 | pass |

## Output Artifacts

- `manifests/experiment3_chinese_text_quality_audit.csv`
- `reports/experiment3_chinese_text_quality_audit.md`
