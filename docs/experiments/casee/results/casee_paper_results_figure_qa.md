# Case E Paper Results Figure QA

Generated: 2026-08-09T14:10:32.160455+00:00

## Figure Contract

- Core conclusion: The official Case E z=2 m result remains negative validation; diagnostic improvements and probe-risk gradients support limitations only.
- Chart archetype: error diagnosis / claim-primary result with limitations supports
- Primary source: `docs/experiments/casee/results/casee_manuscript_results_table.csv`
- SVG: `docs/experiments/casee/results/casee_paper_results_figure.svg`
- Source CSV: `docs/experiments/casee/results/casee_paper_results_figure_source.csv`

## Verdict

- Figure gate passed: True
- Claim readiness: `paper_ready_figure_for_negative_validation_and_limitations`
- Formal accuracy claim supported: False

## QA Checks

| check | passed |
|---|---:|
| `source_table_exists` | True |
| `source_csv_written` | True |
| `editable_svg_written` | True |
| `png_export_written` | True |
| `formal_row_negative_validation` | True |
| `diagnostic_rows_not_formal` | True |
| `n_values_visible_in_source` | True |
| `no_rainbow_palette` | True |
| `uses_hatch_and_labels` | True |
| `formal_accuracy_claim_supported` | False |

## Boundary

This figure is paper-ready for negative validation and limitations discussion only. It must not be used to claim formal Case E predictive accuracy.
