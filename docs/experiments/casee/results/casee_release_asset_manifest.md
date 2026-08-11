# Case E Release Asset Manifest

Generated: 2026-08-11T02:14:36.711724+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc61`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 66
- Excluded/hash-only assets: 20
- Upload total size bytes: 3670331

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
| `CHANGELOG.md` | markdown_report_or_protocol | 56087 | `692cc95a1cfa039dce4cc1588c6f81ab177c371e2c040408f3824ba1e72a1a55` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1823232 | `2119738904182aed05f5d6e6ae66c683dc45de8b03c51f75bbd045041a3f6f3f` |
| `README.md` | markdown_report_or_protocol | 35679 | `d4e419f4248bd8809a81d1e834ae6921fdb6ca3e22583fb60657fc08ceb4903c` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `68d2eb983a82d4dcb69c4c3532fbd5c5050dd827df5870603ff5dbf783ae0947` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 13969 | `166e35241fad39683406c1809d2ca8da233437e88007853782bea078e9f87061` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 13498 | `28fa54d9406e4f635be315f95048c724cb6085cb08639e6838fdde3ef8343fc8` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 28952 | `d3757b402888ec0e98e52770ece49b6e7e9a3a1f1c9d55b2328dc915c6f012cb` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21136 | `4153884e4826c0d4d435381947fb12ee035a97a1b05187b60a59aaf5e90be84d` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `8187c3bcc4bff908ac2597558455d0bf9eb05dd137cb5f2028680aebc9fdc990` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 129119 | `f24d6f5fce0baef1f92681786589d189b624f79d90628d4ca17d38ab8145766e` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 224323 | `b6d65ed2545b4835a32265719ba929e2e57584be0a6c290211a8ca620417d584` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 27009 | `12b68d21a25a524812d8d8b9cc8a3eb528db4f5c6170b067eabfa8e2ec456fc8` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `a11c7a5a24ca50fd95a7baea8eaf336a40737dfd0870e53b6f4d8737dfa52f55` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `596151ceabcdcf9ef46ea887b34949263cd8dc63164b1d62f8760c69f01f19b3` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `db39c4d625f08a05dc097d81ee7fb09158122da22a512c007c174d6ca155c98f` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `7f3dce74dee8e673106a77a5175064b1c2f7c9673028a97b7390deb61422bc48` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `93723681a8b3138b376ee02b99b8bc3eb90f08142725e07638a694347f0f0aa3` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `1b3e195c889c20188e71d8780344821298091b0141646a06b2aa3ee2a4df5d5b` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `f97c8794384b30d9189eb4936743c7a6dbfdf06d580dd731d8a160e63f2b75b8` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `9cbb9197034ff707f1f83b480dda43a182e923ea20ea5f8aeaa2510eae64d485` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `23e282eb4683cca05c596595e18eb33c17be114883c4b7c21733fa36032fb5f4` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `5cf4fbce1e5f40859e31d5d7c8c7774ce66549787fe7f24af35ee28618cbab3a` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `8b837fdbbf7fa9ea225f386e2402cf04e2fcb24c708d6fed611beb652ffc4aba` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12528 | `c2a4c1a47d410b77739d62bf591aa432f22cc0542c19bff26e1793484f723881` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7392 | `b2ad968c538ec1b0fb4c752374c84f64d43cd312f035d4a9039b80d8aaa8db4c` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `7dd515cc8ed753021b98967c2918ab28c1ee44ef9fc227d43ea7a462575ed0d3` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `a8439fca5e0b74c485e2138db2270914423bf3d5b54c32e0382bf52f6faaaec6` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10930 | `d589cd8810f3fd50d52d03b366d1d2d30b7693d1a8a4fe65c938f4f0d050a066` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4365 | `e918b64e7c711f8625e0b00228917a0112efdbe501f170e2a06eaab69c4e619a` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 615389 | `30d5313bf05281d83b279e132e4371080a379be81f9a05a3293c35be38ecac3d` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 2941 | `799573a150b2c20c74dc19d5f5dfd387811c489b732a3879361eefb2d27a0c1d` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `46459a56eea5935a13a80666965c4e6d1453d14ddea99bf6e24ac1104f4f9cb1` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `c236e91f9a727756f5fb53868f8ed591d33591561501ea29fe2e924d1e5daa4a` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `f4cc5b919278fb09eee7eb2a68dbc3ba09fd9a5b16fa27bfba0ee319e2f29add` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `0204dc097a905059b3e456cc83f89519d8c6e8b8004c502f1656c0c9dfa22883` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `d93d77a9c5c4fad5381ba26ad252a57f23ed53d4f50b83840d212b1e351d2dd1` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4395 | `92be89ed8f4438cb181bbc2c47038de410dc7dd712e6ff30039d47bde4d62f22` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `ab20cd67ada71929e1c2e1c5238b332ce1e1e4511a4261a311f0e5f512f681e4` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `adf0a99f29807b377fc13071f0dbb76f1528d4d68ab58fac9c61226f1acc03c6` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `62fc3051ad2f4f48047b563d48389a1057c163b6b738d8a0bc8abe67a4af668e` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `a18e4e1cf0e589996d2d43660ea0f83900429e04cb2d8dcb22e2bd4871a9b96b` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `5ef729fa2b334a7ddbfb70ee15cea03b77c93f6c87e5d266f793dd6e32a3b5a4` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 52475 | `142603c5c3ff7c5625f05e2f92586c2e8d9610d440b2f1326957feb75b82f5c2` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 21791 | `650a53cc1a115fbf8fec02125390a7c58f2924a78ce24cd2370da0ebbf5b4a9f` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `beabdc4f07c6a9fc03c9c03b75fb167aaa172d6abdc0713d4fb5752c46237258` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `4e64adba8b3fb5dcfedfb02687b1c28e7be9bb022d7e1e39d2d5576c99051331` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `73d7f983717f416718e12744718b8f07dd97a8d07f1343608d88756eabf6f61d` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `0ef4ef44c42f8450fbfa798deed716bb80ec89289099de71d492378690101e60` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `0cff08ab478bba2ecc45ca3b86b5ee1577c74ef7310ab86184cdc8b24991ee4c` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `cd49d0b01398a54590e0eecd27e937ca6927f8273625620496bcd4a2bf429107` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `e57f781eef95d050e24a9fbfc7650fba0b392f5c3f2b0bf6f269a9123865dba0` |
| `docs/releases/v0.4.0-rc61.md` | release_notes | 1291 | `e9a2aaf63c4451fe38e5fdfeb1922d382ed1fac10d828d300ab1056852fb86d9` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
