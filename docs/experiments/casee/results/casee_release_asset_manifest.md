# Case E Release Asset Manifest

Generated: 2026-08-13T06:08:46.709313+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc78`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 86
- Excluded/hash-only assets: 20
- Upload total size bytes: 4202210

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
| `CHANGELOG.md` | markdown_report_or_protocol | 69482 | `cd8da7d56af703a451ca91d5ec31056757ba7045d8aa1137692a6136692f16d2` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823744 | `1c3d08567a8d2a6a6c928b1d3183601d6c5444de53d4707910bb47066927d098` |
| `README.md` | markdown_report_or_protocol | 41315 | `3c3ff92030ad3668a683f1a64c85d5c9a32c1cd15a36aecf9c3ae8acc2086f96` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `159097a0725aa5cf2c69563bd41456ba8a30d42285be617a008efbf7258b9a94` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 17913 | `57fb40e88b82d8488f82174e598ff1070c1cbb69d689793dd0056bd423864d2d` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 17442 | `b6fab53998e13ddf1365ed50d28ab28e504525c25d2f7c26757f21f19af33dd6` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 37366 | `f7606126f3a2cc20e9d99f8ec3a5b6a312679ddcf32346d00cb27aaf82a657a6` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21131 | `d4babed7c896d4750e87e1b2ea3c351fdffc29cc94f7d21f9ed9f8c5a9dfebf7` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2074 | `b5c32fb174e40993d766938f2a885b4bbf34836d832e92db4ea0de9bbba52869` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 153535 | `c92cf415a346c0a617a4e350bb46d6889ae025ffdbb2cb5bdb5262ab5b1debe8` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 269755 | `b2f036068c4eb330659e15a6975d78367158a2e6abc8663e36855f9007fd3a62` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 28639 | `872a315a37e7a9f12535877e336185a9633bd6ca5965d177b2b238d0d8ae530f` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `eba3ff3df3365f169187451792e0c799b709c6bfeac294b887608045e75836b9` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `ce099506118b99a726c7cd8c361fdd485836972f1be6d12693480115bf5cfee0` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `a24d1b33584f961c1e5189a208e016c7586b8c537a2e62ac36286be7cc1d8da8` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `28d0edc295b6b6ac32d85269844604a8b24b6076afd00ef9a229b1625b5648b4` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `e39d929509b724c1a14b4bdd4b2a843732f3ff361e7937ea701dce664ea6a363` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `57f1c6e37d50cad265c543b654629d75acb86bdb709c88275799c430a9c49fe3` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `d649af1e57ec72c131885b0080bfea5b4bf13357819a56c7ed8f204db8c25160` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `e16c5319435d9a73ad07374230deafec8bd1384adcb61e267cdbe63da7313d8f` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `b7ee78ffd6e8039f6de2468b9a25494828e541ad4347fd004c709844ebfd5dcd` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `4c7ae2587cf7c448f3903c222dcc60ee9ae571f35eb345ad17e7ef21d9eb68f0` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `baa0cb4201d135d45a343cd4b2529bc5677692c514555503612220dbb38760e9` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12891 | `0bdea21fedd5f56b6cd2570b9e24c4da314cf3a41900f8143afa50ca5890af0d` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7623 | `dcfe0604f87b99f4c4c9b55491d4a7202ec2df434eac5bef98aaadba92868447` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `2cbfce301d5d247f0422b20062f6e9b0ef46daa8c1f0aba8b9d36b402e7a221f` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `4bbbaecf430b71d0b4f8f3c1dc0753a19dec203253a9b88fed66d94b0f737ae6` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.csv` | csv_table | 531 | `bdf027a29169410c4e057710c1a0be55485382ab36ec31bd29d0bd1f04a2ed02` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.json` | json_manifest_or_gate | 2131 | `a4026098a7ccfaad8acf75334a0b346ca37c87d63f8d6460f232d38e1b8f2910` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.md` | markdown_report_or_protocol | 1128 | `0af44c6da6171c83dcb72882f1bbfaddb8baf0a50c1b3e1cc37f728089cf5156` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `485c98575d7925271f7259f3e5d790de8094a6bfc1bbdd23d33801ba01fe6920` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `6970225a25d3060272e0e7ddead37588a36aad9888df48e3508587c7a359c283` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 904513 | `54903a1d833d860085bb72ce68b24b78d79e065965037855f741f0c54244c8a4` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3845 | `19234b5d9b9e61f53e7a7fc840e8a343068067089025aeb370723704fb8a8102` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `977517cf2548a368cfd2f65000b78e6d142872811437dc16d188f08be87caf4a` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `5affd93c5cf137205c721dcf7b55d37d801e8fdd78f67e60c3861e6026756f84` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `56940d6e00fa097e683efc5543a9994853395366dd1e413e2608e528da8b2e7e` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `5b629c008b6aaf4a8a97392b22d4bcf3bfee527c398de0306bdb82cb9e1d9fe3` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.csv` | csv_table | 23277 | `5f1e987838cc3bd577fc35cbdd37aa2408b0a92227c1c3d880515ec603ac4240` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.json` | json_manifest_or_gate | 46778 | `f460019857b363e0e871855ddd418ff263feb69e15f295241c93bd83f9787ebe` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.md` | markdown_report_or_protocol | 1455 | `833963e628fc2cc20648b88e02f8e55424ab18c6174bed2e84a04f05958ca297` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.csv` | csv_table | 462 | `ccef0466e22068613928f4cfd4b41ec8b490d2229836d564e1a4b91a5d6a2eba` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.json` | json_manifest_or_gate | 5448 | `1c65bbec3cba84080bd663d3a15fbc75a90f9bbc1303724dc5e7e95d107d40a7` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.md` | markdown_report_or_protocol | 804 | `e7fefb03035fe56758234ff3bb153338dfec9faa6ce1a51528acc3b21e3704ac` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `0ca62a93144a4829a5f430be734006771626cd5cacc9515671123f03e0cbcdd4` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4388 | `d8f63cd08cf23a00a17ae87da05b14c099b5b2e44e4d47b7d323dfa99e4a0abe` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `8f7782e45af77561405195206f84a380f01bf6fd7f261b7904c3a4627d538a27` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `7b3a05805e3074977135a68ce12feadfcc37a8e29b58679c58c66be9326770d4` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `9e93eb8b5c3b6524b76292233934d294bf3fdaf8f973f162102b6beb6810d432` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `274d347747cc432ad3c4605ba78357eade58071c58b3503758160a2b39e4680d` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `adfad886d0d3aaf2c3246478cdc03cfa0d5ba9a0fd29132f3ead86ceecc40428` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 78394 | `42dde7caef3b8f6ab63886a4cf69d5b86cf04e52b1ce1ef92ceaf9757adf6390` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 32505 | `28489d8a06aed439b2cb0fdb2bd0d6d4dc48b56d4d86bb469c9d9901b5db9d3e` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `69d822dc28666f5941ed87da1a49feb9d34c00dff06cd85a43b687c7299870f3` |
| `docs/experiments/casee/results/github_release_publication_gate.csv` | csv_table | 341 | `3589f72063dcaa505213dfde1e17d6dba473d69d566d0bd50f7c399577996256` |
| `docs/experiments/casee/results/github_release_publication_gate.json` | json_manifest_or_gate | 2214 | `e269c660d33b1214a1ceaf836f008145fe94e1fb94d99ed324db6a61d969293a` |
| `docs/experiments/casee/results/github_release_publication_gate.md` | markdown_report_or_protocol | 686 | `47b87646dc026022cdec2d5124d8b66b6ac462c950b10027e3440101fbd83f05` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `07a7f540a9b653ff730c42b7713711d4e7d39ffb519a356da6ad24a0002232e7` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `50aa1a845a4574a443785ef8f92addf925a69762ecfc4ca086077556ad5af90b` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `11231367dfb7e3533beb6729b02e6ff6ad6d28b0b95113ef055f6dfe44842d75` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `f51e7aa0979f4d82161088b706f255b7282af0307606d970b5ff190a1bdc4cd9` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `d1bef9447521a7ee55ab16bd2237d1f1e70cac2ab72adab9dcfaf7a8a3177931` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `c93748e1f49ab7e8f3a9ce6cb9d7ea517938c4378e887e6c3eeaf0fd85e858b4` |
| `docs/releases/v0.4.0-rc70.md` | release_notes | 1716 | `72cf2575abc924ab40589868ea21cbdc117b4d9d7e67159e63b4653021db4c5d` |
| `docs/releases/v0.4.0-rc71.md` | release_notes | 1672 | `8077e5be2e7107ff5be297cb147f0fc94b86d9b856ce86c3865900de9b583c55` |
| `docs/releases/v0.4.0-rc72.md` | release_notes | 1934 | `ab734e283ffc12a018aae5051ca1b64ab00c787ef8bd3ff098a7424d5e48caa4` |
| `docs/releases/v0.4.0-rc73.md` | release_notes | 1567 | `17f7d19417db876ddaf2e085107d8467da7a0c75986248fdaa0dc00513476c0a` |
| `docs/releases/v0.4.0-rc74.md` | release_notes | 1374 | `e9404c95d657fae138cbf02a4d935f49d2a7850a9b56677de8d6250713d8381a` |
| `docs/releases/v0.4.0-rc75.md` | release_notes | 1567 | `cd19c3d3a18c721ccec0d5ac9fde624cea08581fad7109bdc57b59dcd1f1de4d` |
| `docs/releases/v0.4.0-rc76.md` | release_notes | 1226 | `86ad0f81670fce1c191fc559538906ae0474a4b3142c1b8f79f44abe53f3b13c` |
| `docs/releases/v0.4.0-rc77.md` | release_notes | 1136 | `0f9e1510169de59140e94bcd7dc3a479395e23669b8a545139c7d343703be322` |
| `docs/releases/v0.4.0-rc78.md` | release_notes | 1158 | `ac5c9be3f0fd721f3d6132780f6331721b6a3c32df3cdfe3fc154325c663d482` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
