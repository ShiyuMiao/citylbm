# Case E Release Asset Manifest

Generated: 2026-08-13T04:09:53.903931+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc71`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 67
- Excluded/hash-only assets: 20
- Upload total size bytes: 3888051

## Checks

| check | passed |
|---|---:|
| `has_compiled_gha` | True |
| `has_release_note` | True |
| `has_validation_report` | True |
| `has_metrics_csv` | True |
| `has_summary_xlsx` | True |
| `has_figures` | True |
| `has_data_manifest` | True |
| `has_environment_manifest` | True |
| `has_claim_and_publication_gates` | True |
| `has_reproducibility_suite` | True |
| `excludes_raw_geometry_and_vtk` | True |
| `upload_size_within_limit` | True |
| `formal_accuracy_claim_supported` | False |

## Curated Upload Assets

| path | kind | size | sha256 |
|---|---|---:|---|
| `CHANGELOG.md` | markdown_report_or_protocol | 64718 | `c0f451f90bae53852e087bcd31fa6620fb9dae08f84089caaa22cf435ee983fd` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823744 | `79ee34f1ef7632404944943c897e7dbedaa2b1262686651027ff0482dfd85118` |
| `README.md` | markdown_report_or_protocol | 40654 | `f56f8a8b13daf432fd8139fcc68c7dfdd446363839de14d199bc7c883835c779` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `9d36a6e8157d4d60f99b58da82ff8deb29fae839667837bddfdf5ee3038a6811` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 15909 | `505c93c78f7b3721949f76abdd4a1f5090ccd6ecf8379c00b9bd6edb2cb2b2ba` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 15438 | `9a18a24b71b04f1ba18f75fbf9549b1530e35ad86d6584f7cb6c57a1096f689b` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 34271 | `dc5185b39edd07cd44933df6c651c50ceaefde5b849c9a5290c0c3c8cfd31a2d` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21088 | `c171b26c6885b2b81955eac1787ed7a53a769c2b18711b49d4fa63a8dc4fac91` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `4e3c48d878e6879a0b965620a0612c7b16c9b0ed8861644f57882c9ca3fb98cb` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 144373 | `456b9076dd23ed0030c463258b3841f6e27ecf3a32b9a5b11a34a98704f01bc1` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 252641 | `bf3a2b9dacc3cd941e874d5e55e99f841d820b6561e0678c1990dacc1e3cb0cf` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27498 | `fdf20d399a1a569cf0d3024a33c3ee3d912235e1343b0db4f37908067bc284d0` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `83746263ba05bbfe5be09d039767e6ab0540c1b4c2876716f9fbd41266969025` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `ee184079c72ee44914217351f7fc1990c2cbb1fc4b453964d27e2e54e503c455` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `135285b247e71450f0411984b395943c8a74f8373579da53e115315a2fb57285` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `d6fcf9ae35ef6bbf561fa23de86f2366adb0d2c53036d85426169ae545429ca1` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `b8d764611f9a6d5bda02d86067633434a310a73e839aa9f976cb9141e0abda6e` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `3dcce5bc78f7d1d6cbbebecb713eda1bd0fb69896f3b9f81f22a2c1ecd8d47a3` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `6da00895d47c994194377f9d444c050923b45d088b62ae53f33fb1cf84a45cfd` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `ab33ac369b902dcc552122efb4fb66355b2af25e776c3a85bf9c81630a16e6d4` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `b642adbcc79ed0a2d59b3cb69be86540e039f0f3bc90166bafaa69dd54223487` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `4896ced23085815cf081ad0270a95f093e80bd7a890afac3021bec4800fc120d` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `ef49f003c1b3ad92dc3de9aeaa360de6cabbc64edcc9e6457b415effadcc43ed` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12529 | `bb149b9a7e37dccbc5819f7042377d0b9cadb4c4d7bde5e304954d92aba5c5a2` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7393 | `473fff54972aa484b0cf81624edd6dfb3c11cf10c93566290245f5b14c89d578` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `a744d0c0fb4fccbb885ea28f772645b6ed4bad8fe2d569955895b151516389f2` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `6cafda54536f77c6d963aa47f0276845684a0c253177bf93a9a2ef47ce7faa6c` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `6a5a88eaff2385ade9ba3f9cba1e9c5d2971fe1ac7e38153ba5612543592c277` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `5289c84c4e9abc04c5028295ae47de3d9608448475282c1850dfbee84b3afcc9` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 740419 | `5c57ba99838489721c75f4917576551a847dc151d32be45efd71806414fdc7bf` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3393 | `5ea2844c04828e91fc90de582af46916837af4cdbb4ebeb0140e160d894f43f6` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `2f0892d1ebab8870f609d3b197f3ed4887b9580fe93bc33d105da32a4670389f` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `43173adbcecd7861fc291b8f9c7d244ce2b77e02f4058928cbdfd080b98817b9` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 5926 | `bf55bfe72a548c2606a014cbebf0424f22e9575171f6eebc25c75d303e37131a` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16384 | `3b4f785fe3654de0bbe6df611b036cf98e2cfbd6437a35028f1ae8976ad29964` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 782 | `5d5818c5778f175a94d096dd3921d1221be24102e78ef094d64fb8fac7b5cf1c` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4391 | `29de142ef4718ac63fd439ae9b442c7b51d1c08ccc7ed5d655fc2b9c77d780db` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2249 | `2f319428258f9cdc06a2377847cad9b6b2f813af3338fdc25eab0f4e2dd2e7c3` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `a2d584377313408038f6c6d1bd1b5cb3e2cfd6c602be1b544b541af42fae306a` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `062230efcc026673bd09e05b35a4dd3eba9e387745dd7c5abe5597e984ef7310` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `9690ccd6f600dbd60f9f961b7b21ca2de422a882824d2cb9d6cbb0ca8d9559d1` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `64f66b657f5b83aadc2bc00df19856c111b2689c38a0ca71875b51340bce0f13` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 68904 | `24bd48ebb3e0011b290168cd079f1c53460dd02033ba5b7f0c7541593a7b85c1` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 28505 | `fd44e351cea43c91e35e74bc1d090f94a2e2e8dd20e704902c0cb0c77ffad128` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3064 | `2f15c319093f0fa644b316015c53f0c208fc985ba393550169f42a98ea32413c` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4103 | `97b332db087a515b2a5abac9c7055f3fe581344efa62bd482aa6681a086575aa` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `3aca1bd4bdee8b51dff98530624fad3ec3c61c75d5b4dc8e23eaaad72687775c` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `cb1add3a556d2a905deac0ec390731d96c6904c12fcd2ef4757c8e24cc997b27` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `ccb950ba76ff8f78f003b18d293990fc0e4f6697b4d548bb27de7c2316c3bdf0` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `a5c6082f3b0ce220483f094b259b06461d0eada3d52dfdbe6159227060474485` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `785e889e3c5ffce5860c8f59e39cd028ecb0e01acfc6953bb6636be4dfd0949a` |
| `docs/releases/v0.4.0-rc70.md` | release_notes | 1716 | `72cf2575abc924ab40589868ea21cbdc117b4d9d7e67159e63b4653021db4c5d` |
| `docs/releases/v0.4.0-rc71.md` | release_notes | 1672 | `8077e5be2e7107ff5be297cb147f0fc94b86d9b856ce86c3865900de9b583c55` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
