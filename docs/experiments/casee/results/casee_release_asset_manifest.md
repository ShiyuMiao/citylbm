# Case E Release Asset Manifest

Generated: 2026-08-11T03:43:36.909238+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc69`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3864485

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
| `CHANGELOG.md` | markdown_report_or_protocol | 63042 | `54723f4fbfe64aa758ad2e7e3c11aa53f28ea2f2206ce213dcab518804a0347c` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `4ccad3995ea5c6812d96133f50765e4a0f02254ce2c54ebf42487151dc0f2a3b` |
| `README.md` | markdown_report_or_protocol | 40588 | `06e8c8608c956860994630385aa4a4ab42008b2d8be33bd99ffe51663b08101b` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `51ac931bc4aad17f91b7e3111af6e461d5e52d01050d4bf431d3ef9748c4e1a5` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 15688 | `caccc301b27b28ad42ff76e7c0d4f44d3ec93547fa218e506d4a4d06bfa31f13` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 15217 | `7589087c3fdd1e3ffd7fca8e6a8d461915ccd40f2e706d1a6fec1e168db1d4ea` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 33339 | `834e1162055096728977884bd07161abea75dc47461c783952ea4d2838c8ff29` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `2efc59fa353be8d33814fce1a0cf81a1ddb20c2a7b3eba8fc212309f3436779f` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `453a274c44aa7374d7e678b960fc1b1638b44a5590d509c576d065f34ccab7bf` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 143805 | `2efa27f1e7dee8c32479a8b7880989a5e7bc5965f456180d25401b29992229e5` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 251505 | `6d14e0a9a1b6d358e1ab2bfdcbac7533be63d240c4dbcdfdeaffc18981b2c96a` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `ae849b56cfcd09d5c767576257d21861bc757a41b69c3243ed68e7a9018744b5` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `83746263ba05bbfe5be09d039767e6ab0540c1b4c2876716f9fbd41266969025` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `ee184079c72ee44914217351f7fc1990c2cbb1fc4b453964d27e2e54e503c455` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `135285b247e71450f0411984b395943c8a74f8373579da53e115315a2fb57285` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `d6fcf9ae35ef6bbf561fa23de86f2366adb0d2c53036d85426169ae545429ca1` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `33027c0bd8f4118dd421d96ea90b118890b36e8321058b69a035b58683f81604` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `a122aa401bcf84caba8dc6059e8e1750daf978ea3f70477ef1fb42efc6109d86` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `2e4525c524195a76a81c5e47e8a22922181d1dc830a199da4e00442a5d1543f5` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `155b5d7cfa1b1b7c4c913b3accae4cc1b3e83cd2c764307c4d6a56074888c736` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `48d4dfa21de4841b78e24ef249e7269a0b1f44fa60ea985298659b17a584e0d8` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `e8871d89363f3d6f48f57bd4c49fbaa44bc8070b341a35646ed22270ba2f140f` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `fa929a92d3bee3391b20140d4b1edc6684982ba504bcd91027cac8d519f92831` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12821 | `65c6910926113e3650acf04da1e8156005c1f3894b4be7f632a018200a34b3bb` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7691 | `d236435160c202fbf6fc38196d1fd3e5a30f75a5152888c488cad95282ea2867` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `a744d0c0fb4fccbb885ea28f772645b6ed4bad8fe2d569955895b151516389f2` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `6cafda54536f77c6d963aa47f0276845684a0c253177bf93a9a2ef47ce7faa6c` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `b756e7cf018d9561becb60a4735369598e87eac19ed31cc3c06f98610ece096a` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `732bb6d03eb4a7205da5ae0581af5ff5f575c66b985d1fbb6f9e99df242b86cd` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 728183 | `c9351073f12606effa56ac8b7c72401b71b9543ffcefa1544f7d1f0c88d0e839` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3340 | `455e23e6629d90b76c1f8e765115c2eca42e7e7d1b2841d41ac2252074ca29ba` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `2f0892d1ebab8870f609d3b197f3ed4887b9580fe93bc33d105da32a4670389f` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `43173adbcecd7861fc291b8f9c7d244ce2b77e02f4058928cbdfd080b98817b9` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `7ac8a0f606653c9f77a4638e28aa1d9627ce4b41dbea14e87004cdac8ee4f5ba` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `c0dfce69c5ce82ead1236f85f25fcb6f28170a3b81e9d0bab25cb5906c971fa5` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `abb83c43673ea22280222681629c6aca10046296967f3e01afb568dfeb37a58a` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `a66b188a8f79ca2cfdd67346c64f042e619551ad7251df6188e71b942e5d8980` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `a0bbf55443de422ce83cba790d33d64f67d35b3f37226b009590bda485708887` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `a2d584377313408038f6c6d1bd1b5cb3e2cfd6c602be1b544b541af42fae306a` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `062230efcc026673bd09e05b35a4dd3eba9e387745dd7c5abe5597e984ef7310` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `38bb5a90f46ef296cade2425d09d67db665316577a3a018576ea2e54a0cb2be0` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `c68c6e87bbbaa027617a5775e7b1df1dab9a983091ab41c8a95cd9986466108d` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 65709 | `fb4892e3f3a6d0d2e646df5d83646719592025c20f2f71986c6d4a0402b148f1` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 27159 | `18c76bbdd1160857281b2663d5871afe2bd12b32ef9d8189a8cebb8bdb8d0a8b` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3194 | `d01dd3aff2b9fee92e0385d9a41df22938cc5c8f9c45eef7e0c175e67d79a822` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4233 | `6d4db9009e4ca66b84c5b7da167397e632c711820c481d6bc17101f5e393243a` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `a080ec87d8715bff95952527371ec479243e99a80b48f2a3ba602f78a18c0bec` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `e5fb3e17dbfdb634e4d24ce5ebcfa30eb86ace685095388cf4ba6bb19f11eb61` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `ccb950ba76ff8f78f003b18d293990fc0e4f6697b4d548bb27de7c2316c3bdf0` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `a5c6082f3b0ce220483f094b259b06461d0eada3d52dfdbe6159227060474485` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `785e889e3c5ffce5860c8f59e39cd028ecb0e01acfc6953bb6636be4dfd0949a` |
| `docs/releases/v0.4.0-rc69.md` | release_notes | 1336 | `4efa3d7bc0e037e8b654a88c865700f8114664ad86553fe5885f33ff96cf206a` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
