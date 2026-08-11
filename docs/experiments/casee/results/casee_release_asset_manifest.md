# Case E Release Asset Manifest

Generated: 2026-08-11T03:02:12.318480+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc65`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3756497

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
| `CHANGELOG.md` | markdown_report_or_protocol | 59455 | `bb99efa951e012c91bc00f8501d8c8aaf4f3d7931210ef7229ddf9d1ca2c9f2a` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `944f471b171e7e00e8ee09867b60324669f6f08014039461ba467dca95d9895b` |
| `README.md` | markdown_report_or_protocol | 37959 | `04bfec711471b91428f452126b2529cf503d1d812329c08e753f5e64af1b14ed` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `6a2e6e79e2faf6bbeee4ea902492bc4e1556299376a602335788e0fd97991be7` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 15059 | `b8e7a87ea6026ae2d364274c08e9fd1bd018d6e975f00fb63a30bc3d39a1e675` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 14588 | `01c19d42a9a378046df3de4dc2b70a0e272cb59435941ae6df5ac5d5052a677c` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 31018 | `45b16eae777681b5e723934266953096015b6f0fde8c7c90e8f2f41916e332b3` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `b0bdbc0699cd1e9775b3f9c8d4241eee0db78107e73967367d0cfb77528af243` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `c6cfb0e570306c907e9a6b48b1c974b866c228ddf30e1ee47eeacf6987c9fb51` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 136464 | `1d1c7fefdf7d4b74cccfcf335633ab88448115936f9675528edd668a1d3b5d77` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 237916 | `380227151a6d680bdef773953dd0cc8e8673888cb4f511657cace6dc171768fa` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `87eea7a43d653e84fe54b414f18d6d2f501f017a84375ce7fb9ad76831637629` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `8385a1ec958a1ccb5e379a3b8331c497a458b8fc13b961ee9bf324580c4b454d` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `461ef78275947944029cdd2a8725e4aefa2df91f6d5321bdce52e9967bffc0a9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `dc4c97e01f7fb66fb2263ccd664ba06c47b7888f71b64b6b830ea845671f5835` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `7a79447f443a57cb1aaec679c2151dd96f0e824af3b9473b70459638e87ea9ac` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `9d535085f3a4a8c3ffc317f8ccc80fabec1190e928f37602a4251f66c9785875` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `b29d646342e85f67f1f4fcbd8db81ba76da988cbcb2fb654d72b83c15786f903` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `874daad19f46d76600e7b13f48eaad648eacbb2f26893ad0ed60bf1514bd5eed` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `cdd3a09d7fab7c29c6a9284a36c29472a6045c0d143ddbcb27a3d1fa6a7b1aef` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `f6cbe7ca0f020e63a47b4f0d506d5be4ddbd7c30e3fa174acffc416cd4f5e3e9` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `1b0ba10349caa477da5db4ba114a036aeec8c723def45d265b4eea4a33c1e417` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `9f589f2fed09fc3d6b1844835e9ab810289d9a96a269ed05384cccc1d9fba87c` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `d11936b2c826f16bda3afa5b081e93074623dfe14add2ed258baef5a71a43286` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `2369b848e976c45af204cbdf04c53fefba0a89511d5b9847f4436a66f24a195c` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `67787f60ce98fa0d3c1d8821c448d800ee6f1f65516cd8cefb2285b5eba4c4a2` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `abd1ccf306e84e668f9d6bacef0b030ddcdc03a7f87fda9b9383bceba929abc2` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10932 | `51c7f3f67a0f51a4005ff0f3244690a79625a3956c18285fb528d33e33099a4f` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4366 | `8eec1734e463af5e58e28a453b11665a4f01038c986900a78d2e919f3b737954` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 661186 | `ee586a18104c1453860f9dcf16fb629f3317f2305d063e14d250a8ecb2009f6e` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3201 | `8e65970712042858acb38297c988ee8d5fdeca18ffc6eac7554206c142e70e46` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `1af938c2cc3b919ee9fdfac382013e8b9c252721c5a2aa4ddb9e4699ab220095` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `55c7e9e46b2d7a5263de0cb5330ae60e47cc7175a9dc6c73f8939f15c7fa0e61` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `4758c851eeeda53c7c4f8f0e8974df16a2de01d0940941ba98f8bc66f518b81f` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `fcbe46adab46181977c706a9d1163e8e6255dea7f83a16527c5844a7d268c928` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `433c0ac18e57231c8003bf9a2ad92b3a4e343e4ba9049881b64624f243c32aff` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `a9664c247a017d7c3c2cf39dbe4c0431d67d15b4bce005fe621f2aea8ff8d580` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `66f03d8a7e1622c987a9cb4782c85a961a314eb04d60c749b1c674155c367c86` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `8e59b2aec3057abec247c7e0c0e78d9b9e84be1398076366a2d5da52775d7ba5` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `216acb1e545691683bfef285bfeee922c66fa5a09fc81e3a4ddfcb51503d5778` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `a1c75ffc0605f2a1ce789db4d4c52e65b7a3b26879bf9efada75dfbdd041250d` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `3c952f3ccdb3566193e35cc2cb0d208c57f0bf150ddafd438d32c631995dd8ec` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 58866 | `80882f87ebaf6c25f1a22ff325e606fd8d4c5b1cd193725a017d6a144726bfaa` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 24398 | `314529cb5ab5c743ae1a20a30eb6282cac6564e25948d28e209932b636a401a0` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `591d8c7f7a933e83ddbd00602aca33b08d33a630d75d8e8a4979c3c05e3a5540` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `8d840c1b75088a8ea4c0f6a1d2673fef50c39096fd5c1f3649f16022c20bebe2` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `2ffb2757d0de607b5a60de315f9d7440e30f38fbb8e4d45cf2876901a461a35d` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `0e33886eaa8b5665fdee1e123df59fd5b252c1cdb4927b7a14415390e42a40a9` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `44ec3bac4c9394917aa27b67a002af68066dd53909986e8d17186bb59cc2ae0a` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `d8efeb87656d1a22ffcab9c07b51074a03eea8aa1e5a0a6b9bc51d661cfaffb5` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `28c2269849b965be74b6c4a6cf07f8e1d1a71930add6e05f03ea0a52d2659e6b` |
| `docs/releases/v0.4.0-rc65.md` | release_notes | 1404 | `e100c6987288851bc1f4060aed91f2dfe94e425ea1f87a6b0f0abb157da66e31` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
