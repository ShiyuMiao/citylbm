# Rhino/GHA Load Manifest Schema Gate

Generated: 2026-08-13T14:14:00.329347+00:00

## Verdict

- Schema gate passed: True
- Manual manifest present: False
- Manual manifest claim-ready: False
- Rhino loaded new GHA: False
- Claim readiness: `author_input_needed_manual_rhino_load_manifest`

## Checks

| check | passed |
|---|---:|
| `plugin_identity_gate_passed` | True |
| `evidence_kit_ready` | False |
| `template_exists` | True |
| `template_required_fields_present` | True |
| `template_allows_placeholders_only` | True |
| `template_lists_evidence_artifacts` | True |
| `manual_manifest_absent_or_schema_checked` | True |
| `manual_manifest_claim_ready` | False |
| `rhino_load_gate_fail_closed_until_manual_ready` | True |
| `formal_accuracy_claim_not_supported` | True |

## Required Template Fields

| field | present | placeholder allowed | passes |
|---|---:|---:|---:|
| `checked_at` | True | True | True |
| `operator` | True | True | True |
| `rhino_version` | True | True | True |
| `grasshopper_version` | True | True | True |
| `observed_plugin_version` | True | True | True |
| `observed_assembly_version` | True | True | True |
| `observed_gha_sha256` | True | True | True |
| `evidence_artifacts` | True | True | True |
| `notes` | True | True | True |

## Boundary

This gate validates the Rhino/GHA manual load manifest schema and evidence-file contract only. It does not create manual evidence, prove Rhino loaded the plugin, run CFD, improve official z=2 m metrics, or permit formal v0.4.0.
