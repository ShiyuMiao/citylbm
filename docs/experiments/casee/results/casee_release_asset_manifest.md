# Case E Release Asset Manifest

Generated: 2026-08-11T03:13:41.688358+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc66`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3090850

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
| `CHANGELOG.md` | markdown_report_or_protocol | 60312 | `0781c7f28b52d96e39b7c206275d81d40dea3b2d584dbe173fe68158be4e7e9f` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `411aa903a227e92628cb21e261d32a5960bf155dde013b4ecbc21ff6c4fa0818` |
| `README.md` | markdown_report_or_protocol | 38503 | `e162d8b84de54fa141db1d9849aa10365401f962248b95890e914ba2c3b5546f` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `eaa21840313c1b86f6c6e87cc23d13c8f84329aeae9aefb3315a13aafdef5d2e` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 7174 | `b0bdefd79b809521dacf090b193e723add15b1bf7aef9f6ba31571ef849112b8` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 6695 | `e16f4016bf18ab8c1a705cf6b03eac624b34ac57a82215b44eb4fda481fdfc7f` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 31574 | `31ab3b3a360743d3dc1a9a2f6c43d1bce6a97f40639dd1d34bfe79cf39781b57` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `2bcadab3fc7453b0a1971aae441306044598159e6c17332ac897cc965ebe5be8` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `27fabea4069932cf07249ced4ab5a0a00e3f8ed6d22b5acb9e8bf6be1f643e21` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 138127 | `bf34ccd24d7fe05f5a628c34ca65dc6944aec22c3c53c339f08f1d6f31892d5e` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 240999 | `65096b41c27f2816b19822e9bad5f430898b6a3c41329c8ecc1d258ba5346dc1` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `1f9e5a960e62ba3948d56b9985a93488ad8dbc90acae008bdcf34f3b7da5e452` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `bf8fdea46e80b071d1084b5bddb11bae90e854d41d8c7e8c1d557ffdf13204c0` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `e56db0e2f95460e2511479c416b93bc0c3a74d1097fe5abc200f070cab4045f5` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `25492f43185f815519375d3cb2284027275b1b885a9b941b172e2c65908329be` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `c50650e4b296e5cb1fd557f5a5b8960e73c9a243c3b59458026f042a9ee30fb1` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `2e577d5fd5880be15d3cfd8b18c0cf122e95126ec5714aa09fce1d1d399afd16` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `2f139f5e19aee6d85054fa14f0e40d0175967d46c4c2b6626ef7d29f11c8384b` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `bcf64308c0221ed02dca4ca9aa57b8f56c6f4d65934fbf8fe1b9d419af9dffd0` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `2e18af4f49d89d38d2a5bec2acf302c2a0475abc24f141e4c5127ba78df31ba1` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `ce6f9ffc0580f6cefd7c2b9822275fa22941cd07ac03dc2d0e99a865baaf06db` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `8f8b224dc182aef0da048b83a2b4da501366c42bd3cb2aa2b991704034fa82d5` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `86268a2b396141c4f1aa53e06fd87c7e6aa8fb2e739e55f1460e9664ecc913e3` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `216e001104e6a7d5a143aae5bb52eefde6678899a3998877abc9e4e810dca322` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `9200de30d5875a49bbf638fde626ee3601feb35ff7a5dac83066084068397ff6` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `d8bf774026a12d953b8545c380e9d9613492667b01ce171cce1f199a8af9c928` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `a2f7351d5cebf8c56d2f84c152c9da4d4912332b8479252dbf2fbf530daa247f` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `48e94e0dfdfd87bc167ab10908ecde9ab9627575da58acf45022917e4a140164` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `c103b2b356d9a7d1b4e7c59c9a86f35d00c63a7e5b75eb539ba82e658d517c51` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 2314 | `72142c0f28d5c778e4d2a8df7e529e90fe257b107766e794ab1649c1352c6fd3` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3198 | `1de3990d11482a2981777f8738b62f7fbeb66c4c897fed45bcb73c32b60400e4` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `de3f3b1fd36165aa6a9784d14cf675748c81d41c28b668428329def31a17ff84` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `35a255485737eb2350e2d993de44f2b65f6c6497f6b75598a5274da18ddd9625` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `58e388392a44cd59f9a4cfd8b895eca269d0e0823162b5a921446ebafa589ea6` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `1f826c6b8ec8e9c74caaa589eb69af70c0d2222e0a0df18a557c33833ad4663f` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `195f89f0ccd33af112f81ff661d0804b57d569acf1ef98a952e8928f680ef092` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `8608c5fe3db02c74a8387c5a463730bd53c5f5c7474913c243f5de546b3142da` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `e0ad978e079275a9e432404a8da6b8beb6bcc3e38e3832d1f21a9f4b355752c6` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `8b84fe0fb6edb0a60f1db1a5c881e804c9041cbaf5de0d5fe981bb5d6a76745a` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `162bccc8bda9b6821e856a9a335766736dda94a2c147894fffe55553c7a96c1d` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `d3a697022eddd2399c4e0420ee2cc25aef19904daebf744d2025f83f2155e350` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `31edad7669ec34a01b186e930c50ccb840294d8fda213400bae0f51c52665e3b` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 60509 | `a0a5e604b14ed8fa14ee2cd901357230c02a8a0548a7a746a9e54b28bb3159fa` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 25090 | `bc5a1d8794a13279574cae7cf9bf3d8477cd669ec9c7f78729f09d5d01d26b04` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `615c4cc20be43f835edd1044cf605d8be837933ad4c94c08ab3310b2f0706ef4` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `678b517a73ec687bf5d1a76dba9e79281b8da313a6fb8e0974615df3b0ce0fbc` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `4cc686ead078d37d35579cb599f2f1cc6505cc35dac1792231c8ba5949ed1779` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `95b3abbdbe6f5d448e2461b452156ce9975f5b9919ac79458e5a2424b84b57a4` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `4182eae5ed9cc7d91529f171fc7fe9c964614afa09ed4b791d66380777e5f5b4` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `1ff96b68a029f1a5cc7320168703515ccb1f5b5c4b2dc6be162d9c2bfacbf6ff` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `84c8f9a17c205bef8635e5c702e1ac25bc8870d02a7a6b67d70f1580a42a3624` |
| `docs/releases/v0.4.0-rc66.md` | release_notes | 1375 | `6afb3330453e7e815ace3bb335e4fda39541034ebdc777941cdf5e344986d075` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
