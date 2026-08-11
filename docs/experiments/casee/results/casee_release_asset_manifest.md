# Case E Release Asset Manifest

Generated: 2026-08-11T02:50:45.184208+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc64`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3727311

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
| `CHANGELOG.md` | markdown_report_or_protocol | 58629 | `7849fc366673946c647f7f2359fda9888ef9c72edf8a0ae30b6fd7283a3d6b79` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `b41bf2601bc9889c90f57a64e244f0f7c805bda64f36a847c8e304d30667a4a5` |
| `README.md` | markdown_report_or_protocol | 37445 | `2556e232e239a8d9fb6250d3bb26a823bd5fba59306792b051106294383bf338` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `6c25bea094e71158180396af95315668b9e41a66b0148bed0c082dab35a10fc3` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 14624 | `510f575020c9f02dccfac5a629d88fcd66e3f98c47f95a15aed5b6a6e5f80627` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 14153 | `8b2bbc4b69e310425d0d351f911576cf6fcd7f50ee6a04ca572736500bccd4b3` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 30421 | `24bdff3896e5e6b98784a89c645ec5b3bbad3a6aee80f6854bbbc53fa0272fac` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `cbd6c1ae6bf4cadc9b31586e32cf9e2ae75099f25bb87a1f99da4e3e17da9431` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `19b6cd78beffb34d97c2bcea19e69b78b87dd3c340dc4d9911f1e0a776dce992` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 134797 | `c5dab6697f4cf17d5b236ffc8a26f3b9a199543a74a4bbc6fdda8fe26e14e720` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 234829 | `840f8862c721996505b8bafcfb2212f1dd125e11d4a193336d93da6d26f235d5` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27172 | `8d63828af74884b2a0a59fa0ef6bd3563f3489eeb1700c8b29f1964aff3c2dfa` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `13e2c7f07da8ad7d454966f5f905e7d16c1d9d428f77efba2702fc9f3933415c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `0d505e4e57f22322714eda876765d21ae5bbd44444443721139c0a45aa22260f` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `314c168682f274e2eb24d2c68f83d1d145de10bc7403d5a4048af82d5356d8a5` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `7a92f4e6fa49e2e2dccc7a60fd1072613fee99ebabdeeaeacac18140effb4cdf` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `2c95556aebc533428013fac3c14ef3549875aefd7c850ece18eee9a12338f44f` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `a51bbeccb6a9674229d88fc388eb714c272c457db6da8a1a8e6b428a728e87e9` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `c6488d05ed17bf5c35db5fb8abdebfba4d0f57a7a436a931cec5ad4f18b237e9` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `344cb5b2ba2d1cb31a2f8bbb70a209c308bdee9c91ceefd8ee7636970fe2a923` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `65ad93e339487e99b7600f0ea20e9d741dda4d531a45d3bd8c03ed3bd965469e` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `ec6326bf0d33916dec049e1080e6320331639629ac81350b432760508de0cc01` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `4cd8de5f38ca27a55d5a68fcd15de242c4545ccccfbb99f0d015df5821c469c6` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `c98eda21b4df6a9e2ed8e32d270fde69299279fa6b833b62044147f9eda2a8ce` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `db83c13d087a01d83f6e212f9ca7261029867ba988ebb33a3c20d221bdaed2db` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `09a8222dd30d86188515a4636e5a8f652a8e07ed6673b3560beb18b1d3a2d486` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `be46908614ae158aededb46161904e9809c9c45bbb498e20ba3ff26969768953` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `3419a3258c232b64902aad5e08b2075ddd648277d99e5115ce34c9cc7251712d` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `03cf333e70adc070ca6d867eb889e17065cd5c7c85205edb6ed33e533cbb8d09` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 642245 | `5148303332e82848dc3ae69f32a208fe71a38525c29c9f217344d2964a2836c8` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 3096 | `8ae93c36e4f3155c2d55480d9b1a1bec5474dea63091365b9187c27dc772cb6b` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `d3ad3ba0b264d012e11e438e76241d6c4dd48c810182f0b5a5a9c3208cdb892d` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `83aef59b17050ef478a2a50e823a59e3f961482d5728747dabc4e6abf596c22b` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `02bcdf147c6880ca86ecc87ab245d87ab6473e34ea31fcb0418e7746697afc3d` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `a85bda83f00462f97c8fdfd61347c9ff03be1c17e257149583b4c6781598e5fe` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `f07badd7490b0cf3d0b96b1c46a6d604b275002ac4b6a7cbcb3bf93bd0822a6c` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `f671d79afc9bf14e9851f55e5f776e1deae1ea547564bbc3078aac26b2dd2440` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `2fba0e4eea95a34429244beb2cbd64801bf6672604b664fd5507b40394a10490` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `a074856d1d241037c335b554035b5fea728e46e0a98742bde42bab2efc05a742` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `b437eb5dcf144b84f8676ef21165860b42f658583aef6446862680da8d15e67b` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `dbbc1d8573f3eb41e279c312360225dcf72a9c49b0fe7efcf80f692acded8615` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `ccba4f207919d6e15eb9ea14ea312b30892b1b39420ca9839592979020cc6cf3` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 57206 | `6b21726020707c87f10fb301509be45f79ac26906d9af7a39602aa12445f105f` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 23728 | `93286960939afd9832ec5fdda1596a41b44b4b4aaa480a2acc4c7a87fad0557f` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `1a0e68954cbd6d549591951fc69ee3bdbd3933c3a9396851ad323ce565d24bca` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `19d94daafcbdced9e4e212e4f2778d9f34166ab055582aa2cb741c6c44713f01` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `93fbd66519e11d8d3eb62ccb29970185a83a33a634cf4edf90ac473c5aa8aa9c` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `9e51374537744119f0dd1aa024f7a1ed4bbf0d314f6465a57b849741b9fd3338` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `0b2c0a3ba75d832c4f3dac025d2b5dec4e45ce0294211ee4edd1d0cc4b13fa92` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `37dd0a8e6c7d2cb081a4f52d2ada85c69ebf41f8a199f6a12136493fcc526fda` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `4635e546f40b6bf6326940ab50031de9651cd10fe61f567be66b22ee50c4c5da` |
| `docs/releases/v0.4.0-rc64.md` | release_notes | 1158 | `bba85041b9ee7eebc74296321fa3ffa1a49229f8bc7a57c3e3e04a33d5c51317` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
