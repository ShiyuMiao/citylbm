# Case E Release Asset Manifest

Generated: 2026-08-11T01:58:33.854256+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc59`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3633663

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
| `CHANGELOG.md` | markdown_report_or_protocol | 54475 | `50a3bcae4ce389077209af467997bfecfe0a7ecbe64f96a32c27972eaa71cee8` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1818112 | `2f96a89a6293c5e4111bf27448cfc2579751b6b11294d37a2df4167b72c5216b` |
| `README.md` | markdown_report_or_protocol | 34546 | `270f5475365c7a14bd7a0f5eb392b9ae10c7a664c9fa2ec48226b0748bcc515e` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `0858e810c6043c01507bde744072b8e1c6038fc1d3206cb59671a950254af6f3` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 13762 | `2b8b36276cd155b7e337eb641d4c78f0164d4da99e06a9b7c24602ebee52e790` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 13291 | `5ad093a5b0cd99e3e8e4ea3bdfd81ed37f3a8d856740d76acf930286f21740d1` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 27863 | `ff309e5fb6cc50dfed44fa804f3b619229c8b3cf77aeacbe9464016ef6225f75` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21135 | `bc88f5f9f53a0560814db3b2ba68b5e43f125a1435e743d5aea53dfde87fd6ff` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2074 | `b5d02ab2b7f62d83ead652f90cd65e904fb0121c6bc426f9851e04d466fe854c` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 125442 | `a54a5ea62af2e4d9a300e9ce1c9b8dfa7651df0a602a490867053d19d1396fca` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 217522 | `ee1cad90270e289e6c2969033c123fe6fa3c8edea29d22d4a8786328ae40abd8` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 26683 | `1954c6830a9635f02141263b5481f08d9e8a2edba23c66793d9c1dcdd2b7c7c4` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `b5fc5b08ccc67d67d842a8e702d8c896f93e01b6c90db61d1d4309a40b4e91fc` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `1c0ec35f3ed0e451da7123ef0e260c8bdec8574264657b6535d46422e3a4d7df` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `28ced654a2398ae0a8c6b498621aec23338b9dcce98e37119ac0e9e3b997dacc` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `f6d4c46ab1846c98b7f6bcd9ddeaf2420a690f80f42822ba1b157018b3e1fd7e` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `fee232a2a8abf4fd03dd12ecb0e97f111c32ce2618703bfa0e2f00e52d8a737b` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `a5db5ac27254cd40718484850a43a154e05d4536b89e9dab96f0c326c7a8b3e2` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `f46a9790d4350ecc3939d63b1c635b130ee5a957685dc196e50e68b79c3cf204` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `80130e93f97cd28a12f8fe63f8b3b89d8b2719545721830cc10fcebe11393087` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `f5cf9b41184d447b4146d49ef2b34a4351b7f5fca5027ee764dc4b833858a623` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `ead59d28e34c7f74fe19da93df5e423b10af1138056fdab107013313cd334d3e` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `fb0307efeb93fadce87fb905bd00dffc212c28ef9cf46925ac2441bf3c07ea76` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12529 | `6800cfdba464cb4c7d577f55248b4e2fada185d5b7401369fdd2df52cbe3a565` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7393 | `d7d820b9e8112e96b53fcc2883af7f75b64291116cbd06275ab3542116ac6778` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `916fdfd8ac8be4086c8cc61220d8b9d43e6b5dca1f0d41f104bf07eb06097cf6` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `900793a31be0ead77449b431fd1a439daf5fd5e58a503fdad34ac0f6a2e30b21` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `5c5993c0675a5b516b962c2c94b6b568c34c873eefc7a610f1b1ed271148da88` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `92546fc9b614d7746e84206cd447727a0912b4f186fd36c50a1640d6467693f7` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 603037 | `f4e7eeb52decf7e5034ab2a01b42d0794d81391f4099319574cafe9950513e27` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 2814 | `0b5aec034440225d865906a35eec9655c312d14b885870e545b6ba3eb0d76d17` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `2f0d310f106e6114529ea8f4e652e7c899609b90a6f3f2d1156245897754ced8` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `1161f34c2ced162033204fcff71ecd851ca429ad37bcfab24c5e11e2816bd368` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `75c7ac31d2636ec7333210aabc6ca762e0441566f31ec94a0ecd56901c1ed8fe` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16384 | `4e81ac5bc87565e23693ad35da0f75809a60eacba17f80c4b2e7dac84e0258cd` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `2f6bf5dd73da25816f417846d1f3aa2e624f79ef3044805b65cf89291278fc86` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `c24719b4f959d85d4019d26114bd24ba75b188247c87c54c970e9dad14f848e2` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `91fea88bb12a4223aa7372dd6745ad7d1d041f7842e53bb6ffdf1597fd6c32e5` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `858070118fbc0624d0fa56b4b7c1e61f710b2b6e6abb8be3b3e9196bd73a9803` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `8697e7bc8808290d1f910b620810c5bce7b065bb5e7cf1cc2969274fadbb8f83` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `2843cf6f2b9ef27f1561ebfcafdfe8a7a2498dab5e0b5d9d2fc20e02527038e0` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `0880464be755d2ac0068b8297324cf1e89aefd17c5c8e00ee498b8a632f9f14e` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 49533 | `d7586d22c7527d2105cf3db8651341eaf4911e939c32de92631df3324a39c444` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 20562 | `6267893495dc7f3f3172da7425270a6f3cf86094682eda7c16c01d361a5653b5` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `7845469d5306ee2ef00643a830b9966e83dceb20d072e631dd1232c31bdbe537` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `c17f91811a69dbf8a6f21d2cb42ae0a50b163c49c8b19954d7e94b12ccd3c973` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `b508f7033628bc4b229be7ac42c4e88347ef5b9b9a4a2b99e5e3bdf8f2d36c58` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `68f73990948d740613e1bb7ef95701585d6c9203e71439b67e6796aa68d35dd3` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `bd19d6719f52e096d4cf079972b7f4448ef768f925f7dd03a3fb6a0c501394d4` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `cfa18c4896d4418f992a4cfbbec275869bcb1363165470eeb862872f2aa3011d` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `61ead2bce734c66a089bc944201ab4e1cc3cc81bac890b381f054eb0efe4d51a` |
| `docs/releases/v0.4.0-rc59.md` | release_notes | 1444 | `5f31dfe46c24aca85d9f06d52763c2eeabd40fcea60f5457f254adca9e43001e` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
