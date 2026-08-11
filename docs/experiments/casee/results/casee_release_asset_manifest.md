# Case E Release Asset Manifest

Generated: 2026-08-11T06:28:41.774928+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc70`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3881425

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
| `CHANGELOG.md` | markdown_report_or_protocol | 63938 | `88aaa5d15c1301faa5a9fda4b2a7bfa45c97cc1f94a1dec7133faafbcdc88329` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823744 | `ea6717db0226f4cd1a95f515cb4556604db6f6b59daf452b9d9bb39abc3e9af3` |
| `README.md` | markdown_report_or_protocol | 40621 | `f599721e59bbc2fbb84c59e884e5cc39db61019c996495332fe31e2ce3197a31` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `51ac931bc4aad17f91b7e3111af6e461d5e52d01050d4bf431d3ef9748c4e1a5` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 15688 | `caccc301b27b28ad42ff76e7c0d4f44d3ec93547fa218e506d4a4d06bfa31f13` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 15217 | `7589087c3fdd1e3ffd7fca8e6a8d461915ccd40f2e706d1a6fec1e168db1d4ea` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 33816 | `300bcbcf80aaca27bf427583a337b6b70d5db35004b86e6c62d0840af614910b` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `2efc59fa353be8d33814fce1a0cf81a1ddb20c2a7b3eba8fc212309f3436779f` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `453a274c44aa7374d7e678b960fc1b1638b44a5590d509c576d065f34ccab7bf` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 144085 | `02bb990dd44040e243ac425b920e369663a3f46e0e4d8b842c41966908a7aee0` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 252069 | `b8c63fff425e7dd5c3eb36f0bb5d216838d19086e128824e8a27a0ca3fa981ef` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27335 | `e0f542569c6b07732e67c2b8a9f422d1720913994c875006cbe2865ea3b6afdb` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `83746263ba05bbfe5be09d039767e6ab0540c1b4c2876716f9fbd41266969025` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `ee184079c72ee44914217351f7fc1990c2cbb1fc4b453964d27e2e54e503c455` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `135285b247e71450f0411984b395943c8a74f8373579da53e115315a2fb57285` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `d6fcf9ae35ef6bbf561fa23de86f2366adb0d2c53036d85426169ae545429ca1` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `33027c0bd8f4118dd421d96ea90b118890b36e8321058b69a035b58683f81604` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `a122aa401bcf84caba8dc6059e8e1750daf978ea3f70477ef1fb42efc6109d86` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `12342edaa03782c941fb70837134bf0ce928f7031eb5d78aa00303641c378bfa` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `ff91a8521373db77fe325175b6531f4e5ab9ee0a27d3dd6ca94806e382f091eb` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `48d4dfa21de4841b78e24ef249e7269a0b1f44fa60ea985298659b17a584e0d8` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `e8871d89363f3d6f48f57bd4c49fbaa44bc8070b341a35646ed22270ba2f140f` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `fa929a92d3bee3391b20140d4b1edc6684982ba504bcd91027cac8d519f92831` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `412f8eb6b3babdc228b88c09197180d8ddb0bb608b8099a9e260259bb15a16fe` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `8a86cc978f17db1fea9d803c7ffba5d1abfad7883984943e6230152b475cd7cb` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `a744d0c0fb4fccbb885ea28f772645b6ed4bad8fe2d569955895b151516389f2` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `6cafda54536f77c6d963aa47f0276845684a0c253177bf93a9a2ef47ce7faa6c` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `08f8451fa0a74f0ebcf8b570926719f9458cf1615cbdf4c6068fc3b011d5252b` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `87fb9c53b39dd3ec60b30a35a71b3df46d0553aa068dde6c62f99981f4b95a58` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 740419 | `5c57ba99838489721c75f4917576551a847dc151d32be45efd71806414fdc7bf` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3393 | `5ea2844c04828e91fc90de582af46916837af4cdbb4ebeb0140e160d894f43f6` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `2f0892d1ebab8870f609d3b197f3ed4887b9580fe93bc33d105da32a4670389f` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `43173adbcecd7861fc291b8f9c7d244ce2b77e02f4058928cbdfd080b98817b9` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 5926 | `26be5fc745203ff0c4ac26d84961ef7ae04c87a8fd7db455fd376fefbe069946` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16384 | `8bcea88de05a05b5dc34e26fc518247dd47c482092f719c780890bcddc402516` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `abb83c43673ea22280222681629c6aca10046296967f3e01afb568dfeb37a58a` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `a66b188a8f79ca2cfdd67346c64f042e619551ad7251df6188e71b942e5d8980` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `a0bbf55443de422ce83cba790d33d64f67d35b3f37226b009590bda485708887` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `a2d584377313408038f6c6d1bd1b5cb3e2cfd6c602be1b544b541af42fae306a` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `062230efcc026673bd09e05b35a4dd3eba9e387745dd7c5abe5597e984ef7310` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `5ff64fd668e88129e12a9ff02e0fa30b97d4b80dd750a2993f75cfbf61c757bc` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `7b4a4d47be364ccde51ad402f70aa9bc44d8ca437bc0032290af07003caad6f8` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 67324 | `4d2a52d5bed28a4309f699b967ca53445e8f74a3bab19e3919223f8c69e60462` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 27818 | `946f5bd5e6b4b5b89d9cc0fed85398dcd0faf2c4f8e5e73922b1e4d267244fa3` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3064 | `38548555522eff7c1e3be7ec65dcc38c35642e1b9d05ab521dcdbe563700b731` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4103 | `5806855985da8d866cfcc649d8526b5c9bc426e35c9af00b7ef0c27ebaa19378` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `a080ec87d8715bff95952527371ec479243e99a80b48f2a3ba602f78a18c0bec` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `e5fb3e17dbfdb634e4d24ce5ebcfa30eb86ace685095388cf4ba6bb19f11eb61` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `ccb950ba76ff8f78f003b18d293990fc0e4f6697b4d548bb27de7c2316c3bdf0` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `a5c6082f3b0ce220483f094b259b06461d0eada3d52dfdbe6159227060474485` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `785e889e3c5ffce5860c8f59e39cd028ecb0e01acfc6953bb6636be4dfd0949a` |
| `docs/releases/v0.4.0-rc70.md` | release_notes | 1716 | `72cf2575abc924ab40589868ea21cbdc117b4d9d7e67159e63b4653021db4c5d` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
