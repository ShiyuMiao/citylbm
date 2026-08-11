# Case E Release Asset Manifest

Generated: 2026-08-11T02:39:56.199158+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc63`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3719695

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
| `CHANGELOG.md` | markdown_report_or_protocol | 57853 | `bb189dd15d1577f51354580270e2542ef3ef621fb5c1c204439ab006382aaa09` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `2d4c76336387fd90ea0fa2270a273a81c0e9e0bc03b427ba616133e6415ae478` |
| `README.md` | markdown_report_or_protocol | 36943 | `8bd40c2a08831778ceb1c7347e53262cc6704d31f04cef8aace3b509b5f3e46d` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `a830a81ae4637ab618c49eff5a25afb02e6a839658a0ae5d991d316b96c630e9` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 14625 | `a03d881289634b5b141579c655b2614cd5561c4d3c1326bbf5b6f253668e51c9` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 14154 | `a542e50acd5eae127d0fa85b34f83923e777bd40e38dfe196da592bc2fddd216` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 29962 | `8d1ab8dbfa0e4789eb9edb395198a53c870cefcd41baaa6c30733a24f475e228` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `49bd813d78f05331ee1cf9f83ab5ce6dd839b3ad07ab5239ddc4b7dabb8f1170` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `10e9a05891a5e1faceb116d4b83e42e2913ea802f093756d27e506dd8705aa1b` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 133138 | `6066d334663f3b83b5a18ab6ebd4354c29b69a9cc3a848ad93ed906d9776a8f2` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 231750 | `64afb0fb6facd015a9f15fe39cf1085b2ae1172b05ebe95bd92f8bef91ea2c10` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `5b00b20f896a71165d8d59dec5cbde33857bab2da6f941568ad0f19e341be343` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `b40606ddd8faa24c0674917f1da0bb8904d5f2668d3f9730a080bcda3b715cbb` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `618480b402fd14141243ca1ce05adaf93ae178901ade72497249bbc1a7410516` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `4b31519590bbde3036b7cba4b6432c0c49660b2878b80da6108c929423bd47f8` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `95111bb286e8c5ef6d4f2da42668a714b6745b601456c3a2ce6dc7125fa7222a` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `4b619fc039deb067be89fa26d7454b76386fc085ced16a9e3f3a1923778f50b8` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `57601849331c1cb24cb1dfc41987ca9e97bcc7e147416c288a5a1c0b68f40db6` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `9144fe792c62e4644e993154babc9b26c55407f20c7c961f03792422c13eb82e` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `3564e959b12e67caed0ca18df7d1015d0fbb9e77e2dec104c42bc123e6dd97ac` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `831b1accbb58a9b60e03c767f796a9ca302e55b345cad7034dfe30742aa5e1ff` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `12f1af71b0b0ca49650af55fd9924eaf63ff5f8b81d8f25b113f5e433b84afce` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `f1069f2e04b58c5f56341a5ebf62a6125cea7425b8b11c61ff87df377e5839e7` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `572973a8007f7287d5122ffaee37cb105ad725d5f296a7c1ae903001a895b7c2` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `3555914ab58f7db9acb22b1e76f590063985126e57535b7c4b8cac54f608b003` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `10994cbae4d4e7204e5ade7484eb34bfd79be21f5b00d83e4bfdf478de6ae676` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `e17e3a05a95c4c982ecca58c161d4949d129cb22de0272c0c85f6864007b45c6` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10932 | `1e494ee1d4606ab27d4a33340132b015b891ad1805967c283303baf214059f74` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4366 | `877ddcb27b03c503fc6ecd1be417703281f0cb382e39d40ebc8a47223ee68af2` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 643116 | `7a2b052e17ebf52c66669b739923149be287f937d6ce2c3f3c67ed352d175705` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3099 | `9f73133479ac16df1e797dd0e08836d9e658fb6a4bf005d02b942b490e9dc86d` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `33d6c0d871c453fa3a806daec6f38fb2b2129f3c51577124d76472b315b463d0` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `ab1bd75a5d9216efc161e1f71f31e4913800387bd27523da3a7721d706edadd8` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `637f4151ab093d5bd6713fdf3d118a8dac4622a66d2f6eafe3cff80bb6927923` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `6f45e50b3ff65727f3c81a1891d78ba626f0b563142575d14ad6fac82173be53` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `49b8d91187ae304f5b07da52eb8413a7324f310215eafc9e0e05f1b1223464be` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `b4fe16a888d18be861e439502aef8e97c9befef2ccac87e64a649715055b91e7` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `5ffb1e983d5a6f8a3e601224b4552851cd81594dd3a638063df5a5be75ee1a8e` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `62fa27287ae46e500f82228924498ace752a2e737cd8467ff8eb17c1fb8c5865` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `756139abe3e5222492c66e3d3942a25df14265ad188998fc7694bcf82972c173` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `0a65e99367289a85f6c2a7f68559199abd53b0cc8f1a2d5a5c25812f031707e9` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `23e9ef9b173bf87209d909719bee5a45b34323ab683a4b4d569a28f0e600cf3b` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 55631 | `206ebe5ac9c36a791dea0e15f9fe55ce4e6e9a2d967b2ceefbfb6c15562dee45` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 23095 | `02b2f03bf5cb122cce91dc0ec68ddbbb0510f15c66954259b503ffc25b179047` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `e07235fe3210f129928b44c00274c72d9987caa20a0cb895280399c85cd109e6` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `8097058aa6b3c68e5b57f470918e10e6c59013ded0a0f35f030176dcdc1eeaa1` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `a30d42176625edba6a7fbb21f93d39fcf16170ef3aa152c2d17f1540a2162e30` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `e7dddc2309c843536f10527b97e4d60535f685bee527561f94b33f67205583ac` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `ae8f601b6d039e3208f0d7e552dca0ca118e25621a6708307b5373528c3c0f13` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `c05801f059600d3680a9ccbfbeec511ec4e5273d31145edd8d1c88d931eebb97` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `faa899bc5f83080cb4d832a6468f661d45cc93eadade97ca518ed950d55fca43` |
| `docs/releases/v0.4.0-rc63.md` | release_notes | 1346 | `9429ffa28d47362d387a6f87e0355cbef921015b5ed4d59d45ede3dd58e50977` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
