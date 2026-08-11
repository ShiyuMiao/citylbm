# Case E Release Asset Manifest

Generated: 2026-08-11T01:39:43.053104+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc58`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3615329

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
| `CHANGELOG.md` | markdown_report_or_protocol | 53782 | `3a127dd613948ae489af42a5e7026b1717b7d1755a80c093f27780d52d6b6f39` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1818112 | `a3a3034308a0d67b8dffb54815d052b19d60c39503df13ddc63532ea6b5823ca` |
| `README.md` | markdown_report_or_protocol | 34470 | `946ebde2249a051cb3ff8d5c7f6106dc5c668841d5f32554ad90b83b8d6c785a` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `282ecca521cb6e1fe1ef3cb579fb7827fed884a5f33e59ddd6c7dd8256957a80` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 13563 | `ebdbb700a9780c86e4f5dcbab9949ecddb50683c69604dd87c294055beb17806` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 13092 | `1ab2f859a0c572b35c0126035c24ea7a4dd24e165d112dd658a903639e691ca8` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 27364 | `52e75e4bd46c4fd2a3b828e68fb25f0ed0e2101237447fd852b2ad129fd0903f` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `c081555f66bbee331a1f14f59c055407b08458df521c73bd5a3f076f63cac950` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `8e8d044037322d9d8427dcbeff473f01a518fce10196ac5842aa8531cf288a8c` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 125151 | `db0cd89024e3e68a766527e6ce076e9a6f85acc69abd0d7059abf0c84c8401ea` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 216947 | `0ae9d5f8bff8c47af5e8823ef123f2348f167a32749dff293a7f6cc07d56e068` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 26520 | `0cbfa1821612a0eebe1490f35093f1e1492a819bc82fa3e07426c4a4eb1254f8` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `3d9eda381224e97a7a2a0318c4df0d19b3ccf1e084d55382c2065e54f1a6c605` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `6a3acd720a928c3ab7555e8bb358e08f98e25d6722baebf21c4c6438d04145f3` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `1a313d44e7a58b8780328cc2bfc1a4295085fe799530781ddd9665cb075e1396` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `b94e33aae5f704ceeef4daed9ce2ecd0b75dfc6d442d44293f559387b0a5b096` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `bc005a0eed731a3b7f08df5357dc29c21a19bb3dc7726eb376bc577225aa8f88` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `1ff849b65449d3950e85b6b50d847be69d660a4e03f53cc020932ff6b16b45b1` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `0886f663cfea2ade0879e2267f73a86ae3cfd9c4fa62fa56538e43aff3ec75a4` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `3e5f570e5a11bffcbd14dd863937e543093f8d8685279e99b2440740079cf432` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `0760c1b3ae2161ebc3a6cbd590a94a7fb4f5c8e256e5f6eb1ace9e5b432f34ab` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `52d8793de0e13c56ff3ad231cc4d45d4d536a5fe2a66f13deb62a88fcdc95357` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `1041764075db0a559d3fba7dd341edbe12f6edc1230b6112b529fc3e8b390189` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12139 | `6a671fb6578ebb615aef1908e1268d77efa105d03426ff28234dbe9f21a29378` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7061 | `d813093c111a4c1899d5364b42e68245983e9ba772dc223e9cf669b2d1ed9ee3` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `8089dad61153e98dbed1e7026fac75319d2ad61bf12670891c16330df8963fa5` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `c5f2dfd35e64cb55efc98d7a703d6a998e280117da4a853ab5d66126d1d655d4` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10640 | `96c840d70b63efb918f37bfdda82d1be572d67be32a189f6cde9661bb7350e55` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4310 | `e1bc4b451cb3cde6f4e3bb07507ab4306d5184cdde27343d108c0f98d2e80e70` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 589080 | `fb514985499a2ad3626d9197b5ac9db75cc6c29d199dd8efdb56274162f11110` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 2772 | `f1585598698fcfac30563e804f6a876190617a1a47968529320fcce0e5d714dd` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `aaa0ffc57db5c574e78d9b5ac18de6cb183f21b10aedc6315d22236b7b83e5b2` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `df69c1753385ab82e3622bd443f8c1cda9b074a65ac4a0ec77dfc415a321dc8b` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `11c20c3e0693e54df0347b536354635a944db6af450ea4194a4b442b62e7dc02` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `02f9cb2dca369811ba5f52bb72363897730991e013aec99aa54dabc61b755396` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 613 | `4899520a9d833e8c3f2824586335cddaaeaf03938b131799772fb8d7e2f0707f` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4226 | `8d99cb0496203d5993034263ba11240ce523d06d6c368962a9d351b8cce70285` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2118 | `69b1d2651282b493bf525b3ec06305b326ca9cd1c73b45ee7a2d31ba3c7ee8f0` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `0bee6b4685c0d0b5871019af1f7510a6800398adf009f5ab1973fb31272f3824` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `f3b12cabd4bc2ffb825df795663a5aa5072a945aa32b8e158e05f15dfd993565` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `eca7d8a802b1a6e07f68b92ab02457913020bdc68fb0671a45efc1d405100d24` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `f0aca015a0b1e8625dfa4f2f09b34fb7d500c2452fd379502ea36dec131dad91` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 49534 | `6fdba2b48172c5cb9a61de4a292f81d94f9c50a924a802789d4a295b1977a3b5` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 20562 | `e1716dee407a223ab64918c935470e32f6f95ce26ef3adcd7bcec7967466776a` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3194 | `651d5235341b71007761d1d64c20e8c3c37bbce8dd5305ddc70455e68e4052a6` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4233 | `f757a6cbd43d9676427d2706e1a2d9e558f135376dfc69b8ad921d8e93c5af0f` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `37d337f7baec6169cb5ae546615c45b5c2d29d2dd503bfccf075e200411df8af` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `c2206435437da13c2deafbc209728a9b5d818b2fcf50ff21497fa584baf66ad3` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `070d0c2203756a7dc4a517e152ef0080a4c7a704406d9a92eda2727e492e73f7` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `7e5a3e14f737b7897d64e9b947526184e04059b96931fddc1312db7385749e83` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `69df1a734b7a0f563c880f5997d3c1e43f93c69b11031c80038b51515d624bd8` |
| `docs/releases/v0.4.0-rc58.md` | release_notes | 1332 | `71443c8e08f6fe4533e035ca991f29ec0c605e2eb46333405b79da889a6001b9` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
