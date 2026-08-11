# Case E Release Asset Manifest

Generated: 2026-08-11T03:24:26.750418+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc67`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3833604

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
| `CHANGELOG.md` | markdown_report_or_protocol | 61227 | `f0622b663bd4af77a28a6aa8604426c5e897faec5f926c6f6ec201a31b476f0a` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `74a3ce2f58c8a97bec5b0410fee429fa39cacc1639215b8d6721629cf0dae574` |
| `README.md` | markdown_report_or_protocol | 39240 | `d329023d0a1f99a5b1c057011d9775c109b0f2459de0fe838dcb04fc049df2aa` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `f6eafb3e7e76d9d32b268072bed26ee9a79e0f502ca1c0044b6edd1221bd2894` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 15479 | `1a4fda904f5277c24eba5d8a58eae8ee7a9fe9835d1d881d22fc0c37a5be16df` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 15008 | `21c537c49d081e73755d3330462dedba755b8fd864b1419c3d338d35dfa24967` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 32173 | `264d03777dbaa4faed239a88ede82766abd4bb3f46da9f8e15bce2028b742373` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21135 | `c219474f8211b5d8f8661f8816b070d9fadc18fdfe2ab0559de94290c8b59bad` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2074 | `a20815b28eb51bff4bc33a675803ba9d6c7d04995fd0279d4cbe786f64f44b98` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 140478 | `e9bca580711c0fa0011651485a639a10bc03b7e4ffbfe7cbbce02c4a7370d3c5` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 245338 | `89bbef0d3dc48023e66b1da54104e50fcd18e3333183817489e68177953f69d2` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `783c21f07d43370c139dd4f7f7aba4ca553a041db6aec2b4fc22bcd7bab29ac1` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `4b86fc855ed7934b97c31a9a56c45a99ff7dae42d898f21d5e40ee73c915ac14` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `9d1a244a8866687f91595064ad1b699e3250f90a802208e0d27aa8ffe0e132e7` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `a845085b7b78b80ec69c088f70d6c43f44d69f40afc189590414d497db41eb86` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `28aa1a90499a5babad9c245810e59d252fae1e0a2d35377295d80e93dd0e9b53` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `c90c2590ab543f94a31fb83aac1d3d2d3274b6b934b0c4f905f1ac206006d303` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `e24846372851f2fe2151a063872efe7766ae9d7f9c127361dc692a74768a2027` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `3ee006a3ecf78d9a235ed42557c1c276b0e0eee19e65b211a2ee9e96a74b9bfa` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `25e021201bddd445306fdd55accc8ff1128216603e84f00c8b0c24a50e1e9012` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `5b4073b27894d73fe8084a3450e9c1eb4460d29b3cde1906e1d893b5150be895` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `e5ff0a79b76568a9836f8aa49411f9698b6374d60c8fd9e746651891ab373472` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `7ff118732d85b6073c9fbc2923917f17ffc7b8cb1c2d7c41b9a4ccb6de75529c` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12580 | `baef260d87d71d330b0114941176d79a7323aadb88d9732e953476aba0198f52` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `707a0cb2bf10ca52662b2a722eabfd7331aad8210cafaad4b50651efac75888e` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `2ca95c0e392eb8213d3fb18633a784f889ba927313507608bc187f163d08c74a` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `d15792e4a8681fc04b123ec2a3ebb68a639c31e59b44e1cf8a57c023ab2ce0ad` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10934 | `3c00ca68fa65ef25a06334727903602695141c97bfb3aa55a305dc734b66d106` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4366 | `93a1d79055d67d7f0ac171b10b48af7561164098ca5eeb14c8fc256c0b5d26c2` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 716856 | `8de101d947720c35f2cf22c1e1cc1eb6a0db1b8cc4460ba8ee3e7cd024d80828` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3299 | `c4f61970a5abdc182e2e19a28fc9adac1933eb3c33c0813f3069269338439a64` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `1befffbf79f0c6d1336e62f56754e6ac0d2c7ddfe748cf586a49c5eb54005f65` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `b12a51e6899098c894b74bf52f159075858a51b4667aec966984f45e787c35b7` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `b4f9f2eac9a7e5a3057f5d09c69485487fbdfa17e99f6c60872985b8287e4e65` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16384 | `d94454067e9daac82d269ccb6fb407da5bec82921a7c60750f1e209e259619b0` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `926df3a5f05ad738e19973ff62ea50dfdca1047106f7809f635957f99358db4c` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `c9c0783a4380403bdbf39a88758d90aaa1273cb428ef763f50238a0b669e98de` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `4978a6e5c24186fa6f6e9464d58c66a1dea0a2055fe6a6c3c5961f447fbad180` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `5ac9bca9752ff6ba707b223657f17c732899b1a43fc318f34d09f51822e5ab05` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `9a14a45ddc634066f0cc9477bb4a05bfcf7e27c2789c5692a3c79fd5096251d3` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `47ab1875dc3bf9079a834e03e5faff90cef00853db11743bac7f3d5a82818e0c` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `623f9b53d906eabbf49ac563d7b811985c383d3a62c8e0994a231754cc7c10ce` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 62292 | `3bbca89d15f8a9fe1660c8a1cbf34abb16a3b851babda702ca53d43885685d79` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 25759 | `6cb0996c52037faa532dbefcca29ff21c79b26debb83be3860f754c6f01c7238` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `811e174ae71b8522115316fead6e3365f00608ed9fe7d89ec2df3b367ab45071` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `5bd2328db0db1e42a181d9ee3f6d4ba6a8ec5aea66c98eec6dc25ed1b3d9db71` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `86ff9ed226b960e0b4b721873e9496825239d2da316b669b66d3d289dedd931d` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `62f25533a419d04b1246363b0463d84dffe21450e5159305d7c9418cac406149` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `87fc8c6a5ab4ea669ef1a827b84531c8bba5e64c7e8fa4b9e53e4260d08fb351` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `d0da5e3030fb0b958a70f8bce760e5ed56360c6a3b0e04612a68448a336971c4` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `d0a7cb878610481e5b6ea682430e3faa96c153ace3f7c36fbd832e0e5b6a2a1e` |
| `docs/releases/v0.4.0-rc67.md` | release_notes | 1419 | `ee9179e9bb031abe9d2dfe849c15bb9780ef844783e5d65d03b5bbe450034d58` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
