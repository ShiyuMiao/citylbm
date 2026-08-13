# Case E Release Asset Manifest

Generated: 2026-08-13T04:20:46.068390+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc72`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 68
- Excluded/hash-only assets: 20
- Upload total size bytes: 3156404

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
| `CHANGELOG.md` | markdown_report_or_protocol | 65412 | `d604f8149f5c0b87869123c6590ad28e87a94b01eb78f69cbc17fdf1060553a4` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823744 | `0781aafe2041fdd68d73c80fd4872aa59f3dfafb94777e8630b6dfa1ba32c3c4` |
| `README.md` | markdown_report_or_protocol | 40687 | `a86bbac40e528556cf759ab90e1fe702d2a68711c418edf06b6a2d8e7bb03efa` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `0eea280eb77f676c5e4a41e50c64715d5ed3bab2d12b6c8a87a8da68dc1f7281` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 15775 | `0a0ba3c8e803bb904d8da3ec7b34a60f58555c3285886701295a704a96723568` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 15304 | `813b40289ca6bc7e409eec83f1b6fcff40cc8df71e8da3ec9add19d730256be4` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 34685 | `7529903b99019817f816c6232431bbb7283431d1a7cc9aa89fbd502a60a551ec` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21087 | `c5fde546aa963c9153c5f407147ccfd0f3e9ed86cf5f765ed2c0a9e340ad9b0d` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2074 | `993f268d8671922f324b2729fa78a37c2cff1a3f62ecbf4b83e7eb550372c913` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 144656 | `c88a0368b1a2fcb285e1758bfc5db8923f48f0fb9689352639d6a4c5b7d26083` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 253208 | `6a0550ef717b693e337e86310ea9722ee18ba830fe7af365a10d346b6a72a69a` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27661 | `4d1f45d4ca83f3cf3767e1350e62fc2750e18a88854cef1ff30418a7c21edd5c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `2239c9a3aa6a8ae893a0da166331c18f5f1fb1844724bd447278eb15d05507ee` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `bce07ef6c422994af6f3a50b87736e90613fd327eef81d2db02f0253057d954d` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `4d0995d65be454f58e8af74626d16acd1d923cc1071b9bee5ffad76fa5ef5e37` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `7529f4a314cca6226da5586a8d5204d29de6ee5af698955d9bb47b3a07d3ce3c` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `4d16b351f6abd87a3a25824447b441ea991c3a8f5279ad19ae717041b09eaaa1` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `98961858e591b6dc0f2446a53712cfb1356dddd373c726ed399c41963e902cb7` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `8d03511d55e35dd4a246b8a63d312c1cd4570d446c6de27759832d01922b5c6f` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `7933de418c4d240c6e68db9696de52cd2692c84286e2f050830a47a72c51b7bb` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `dcad3724ec3ffde1ffde81e2ac97b4ea22d7163fa048291f557057d73196b4b4` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `e9dc55ba6afcaefa95423921c3addcb40833d7807b44bcbb96ed1191c161164b` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `eba46b49e312de68186c9f84b1089036a571cf15da5f7f6537201f4b01db4bcd` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `e17249980f987569513609a2bf79a3097c3ec5dbcd4021d503ad801ac818d15d` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `5ffbc6dc5594b58270a06fd64ccaa8f8dff6facacd1d3d4b58e39c266ea69337` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `45a93316bd474cb3eb78fb1934bd46c9ae5629f5a0d3bbd3d2adb4422255e22a` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `796c5baeaf3042b8b1275bc030654053c00733d19d5375063c45062fd2fbcf82` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `af22a9fda7708ac28333aa795dd88778e628a29f819e08b25844315f41b708a9` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `b84069d0dacb7561b49bba92e16151ee5cb066b19180f9d62f4d88437af3efd5` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 2381 | `fb9887f51157f9ad9f87a108276cea3da98d8e8f03ec6d0724e52c03d1d0d6d7` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3323 | `1f7972768c0d8cba951abe9fce46f5bc9bbc21959e217ccee7eefd4aa27fc6bb` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `55c8b72cbfc9aafd377d9a0a840444792b5db977475d1a0c441592663641187c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `453b843ddc002c2fbe83c44ac8afd4e15748e8bb5358ffa1cd13daa8e5a4bd1d` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `f380d774cbbca63005d774d8fece64c09fb69e80064fbe88afb74d94460eabe9` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16384 | `2c3aee205301319a0831f7569e7da801ff420961a253af547ed358a7bf6c9a5b` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `4fe5ce4e8bb8ac4907475f3298b3f8f9dc831f6495de8900b2be72a12246416d` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4388 | `18ca812a41042777922407224b5b952d4f48131c6b2901694dccd11bf2363a6c` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `f37092bfd5ddc24c384dc1d1836d442e869309620b0b3c1650d30c81029f512c` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `afe00c9ff4efb04d5d16572f4bf3fca33822b8845e861b22086779dd008da906` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `311cb60cd911f35fef2deda1cb8c81f65e3eca13a07264ad3336261e4fd3189c` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `6314a347113f578a57c52d562d03dd06bb6fa70f77dcb2cb88506db8d7e17246` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `5accc2785f1d395ea2f9ded48f2546557ffaa6b935d0ae61c7302dcb554ca7de` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 70527 | `6f1722a806f378094dfef00e56aa88cddb75b6ad709e51417c5b12b1182729b8` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 29197 | `0f33a446f126aee3222556a46fa72ca43775ba3f52f8f0974229a1adcce813cc` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3194 | `b1083f1a016d84fe0717b12c260c437bd9dc2ec0cf7e64bcf991b0447631af73` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4233 | `8fbee1c09cba5d09d25da434204f73ccc211e9786101f516f7a044f7c3757fd7` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `88c74a920d1a5d563fd7881137adb729937f8c551b496639e0f4636f206161ce` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `5b150b02ade58666487fedf8af01df63f23be4ea604bfcbd07d936f853d9e37b` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `f9d29536607a9822bfca57ba925dad64ffb60d9f06f59f365f994c005d328e32` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `e2b7b65340ecc1df50781362ed5df142f2e8487aceaf1c99bea3b9c847ffb3e9` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `5c4a86c426611ee8c9e6394971a2e3da21be7287c144e94e7688e802a8654dda` |
| `docs/releases/v0.4.0-rc70.md` | release_notes | 1716 | `72cf2575abc924ab40589868ea21cbdc117b4d9d7e67159e63b4653021db4c5d` |
| `docs/releases/v0.4.0-rc71.md` | release_notes | 1672 | `8077e5be2e7107ff5be297cb147f0fc94b86d9b856ce86c3865900de9b583c55` |
| `docs/releases/v0.4.0-rc72.md` | release_notes | 1934 | `6334ff601da8529e83cd53c2789efb03d774a5bda27ac161a4e6b9c201b8c427` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
