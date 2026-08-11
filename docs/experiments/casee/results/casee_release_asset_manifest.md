# Case E Release Asset Manifest

Generated: 2026-08-11T02:23:00.511005+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc62`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3684400

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
| `CHANGELOG.md` | markdown_report_or_protocol | 56954 | `67631f0b92e0cf45ac4151e2f53083cd3277fe2c9a79673b2c93ba0a208b3aea` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `5874c50f46704a296f34811492b1acae8fc55a94e700f99afb57f0c52c1f6e07` |
| `README.md` | markdown_report_or_protocol | 36191 | `20fa373cfe2c969ec9bba8cedd767fb5cbb88dfc440bb82024cfac71a479499e` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `72883c29aaeb71baf4da5928a77bfd27708aa12523b2f8fb1c4192fff3fc5799` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 14194 | `e53ea206faed9d0f36d6730b79ec00c18fc702c1f4a6535e741093e169a178b5` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 13723 | `19ef358dad1c8f745033a88d4f94471a7075e38a9884ab0b9324ebea5808f2f7` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 29447 | `002d4d3876a51fbccfb9b7fbf9bb2a65146cbaabdf427d71bca96fce8474ca5c` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `40c596b02b29ddaf0419c8c76995da46c19f6fced450a0644ef15c9dcca7c57c` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `d8c2deef0d98ec18748a6ae600ddb27d7c827ebe0eb7e5d57beaae48fe06c06c` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 130790 | `3844d0b6b67b573062fd44ffd27f17b2a8ed0031fe56c8258bbe9fb9f78cb6ed` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 227414 | `8e8ffabb1526f63107a92adc47c7ec274d5177a606a1b5eb77769445b69ff174` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `52bf1d840062e3fd9f64f21d47116b1cf876531a2057863d1476fd97576d81fa` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `adb62206e1ea22e90ba4006cce36e601c0cda48476f29572ea8eb5899423a098` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `28bb7004922af4a08607b9a6e3ccdeb39eebf7406d130e469728befa57813a34` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `c40fb868cc55ac2e0f131872a2b981a8280ff482ffaf3ee5270653d0ab0d222a` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `fdd93d9fb75bce1391f9ef2a81c22a4d416be118a664ef0b69ebccfbbd1a312a` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `77dec43d44a84ce03e6a05f39b633b620bb8386d6f3ce9163243909c34560f31` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `433d867298a7a496b4a887fbde5bb01b4012c31561f800afecacc809f072adca` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `fe081b4db23e15d0640268739b34fbe84aa83a471a7e3d5be51318ad6fc7b9dc` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `3b889adb1d12db68e73160c391271713e71af3dc7e9cc8f95d44b7a143429df0` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `ba10ce2d6c71187358d4bb9ffade2b65c7fdff7c2abc0eb181c7ceb6bb14843d` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `f9f4ec1b8e594e07da2b709eae957b89289a05123e603ae7f3fe72400a2a769b` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `0fbd12afac8e8344bfd225081fc696e2a37c72f122f33a77d42d655af8c97fee` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `58891c8b3d9f680a78092f7e1271766b53818c13741a7495d3851d04e3aa753d` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `a052c43d1970d8298d8885d5fc92b03f0d78cf296c6a9ddf5bed3b12d07d70d2` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `01b70176ae2411ab321f97ec4adfa8db02e265e7d30b68dc8b22600263201db0` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `a9fe28eaa9da240fa34b5e0c784e6abff91c897a48be1c4ddf00f3c9389d1dc9` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `50b9cff1aab0ff6eb55094d3e90fefd3aaa5ecd8f73c33469339a7bfbbd9c01b` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `367d154a5b8d69cb8b945c3fe3941e6be33da0a36f52183d3f16009bad41f67b` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 620156 | `97a630dc9e65ebc4fb20cd7b462a45480b985d780bbb09d4415f2d6722b87a1a` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 2996 | `88f0ef32a155d2649d222dcf49e554b4c0d3ac79b9e12f22100c1d86d7741819` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `96e32e92c34297d96e319f2eaa149c4f087208511aefa6e5c5c8e54824c1684c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `ee908a0f814ab5f57d2d6827bba9b3b24c268451e55fe133f5c6d1645809a05f` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `ee166d4f785b358c8c7b3afa6f1432454e19ceac4e49e8a202da40906930e72f` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `b58920103ef0e85ed6e8cd8d66829de9612c545cf72edb1578ebb63cf2c26c21` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `8e7013c61030068e4e23b8ccd029ac5878d8d995f7aeb6bdd5ca2f72c2a59e31` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `f53c914d07ab1fe58309dd1deade40b20034070afd6522b8444bb0061adf325b` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `0f68ee9946eea1bf16f33916d8b362fbe4b92cc99391c4196d3867b6f409a39c` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `adac869ebb16013df0c8f091d8149d0228834595c85ecb33013f5ffb9e4bdcf0` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `b362e7aaaa6ae7e279487660e6a33073809ac66ca2069875a9c47e0db5879673` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `1e3fbfdcd86968ab2469d7b588ea4c6426ff2f973a03d6c18dc51046781d22e5` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `a584b04f414015abe868c7c8f209dbd787a05f069114fe2a99a4713bac8d29d9` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 53936 | `0bd03510b28170e868441a2e9705aa72ccaf74cd64df43e58f50d3182ef40d95` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 22435 | `bbc9b451cc1a1ae3af5cd368bfa4720f1aa90bd139bf69d2f17b56fedf391d5f` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3194 | `07c478f042d5401d50caaae6e649d862eb5d687b7d6bb1e6367df8ce46a91998` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4233 | `5a6b77f17b54269b848e6ef769807f05b924f0dc81274dc977179110a2c9eeb5` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `667a65c8b9545d885b4b27f1c8afed5ba265fe12d9c5337089db4812aeca1d47` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `c6ae18b9b64b6c9c1a87b22b0ff244b8491704db1ec229377b54be9e82e0b43a` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `36feb6da395c923447ad484343d8f53582b0ab458b751506486bacc2ce92a8da` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `fc6a90d45d8fd4b5cb2518a9659fb8f9bc0ec0e13198ab93456ab9cf18ad11eb` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `7cb9d06b59ae68b0c7ec7d3d28b42928255d84367062705c403b7a246a458f17` |
| `docs/releases/v0.4.0-rc62.md` | release_notes | 1182 | `1aec8cd612580ae6c3c20c94060cc6f7edbadc13e31f97fe14d281ac66dd1df4` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
