# Case E Release Asset Manifest

Generated: 2026-08-13T11:21:58.717625+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc87`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 133
- Excluded/hash-only assets: 20
- Upload total size bytes: 4582310

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
| `CHANGELOG.md` | markdown_report_or_protocol | 75824 | `4356ad01ddf0a58dd8e1f854624f665c6efdac539ff5bc763241d6665b2dc652` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1838080 | `90e2a84115958130bd3adb63c8c13f60b3df12fcfd30d54e633b44900e47fc48` |
| `README.md` | markdown_report_or_protocol | 45120 | `39f0df221a8caeef1a383930e69172c23bec493265a0e5480e4e55e84c10555c` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `f48ce1efbb599d901fc0ae6cc4c8d116cd5f7d6e9a377989e6526817dad2485e` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 20193 | `f9033715a160ea39d5977c95115be21dc39db7e38bc7b9d31a39eb4670b6c0c3` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 19722 | `cf2d5ae669a4e0171c827d3dc39c111ae3dc1736037d653251fea15b3ae4ba21` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 41969 | `6cfaf1aee90c3f4b874b97547cd240ba3cba84f6361bb31e28dacd0dffb78d6b` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21130 | `9478302ffbce7f8867eedceb33e2487f44ebfa97e50f96f2be10d46070761996` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `e382df5f218c0387aad1472f7dff9ab3ab28c04278a6e446c8d213c3ab0144ba` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 170212 | `88270c42bcd106a15ac657eab9e530c6c5cb8f9ee2a70c664667a22fb65c9731` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 300632 | `0529b8dc3c63f09c5ea5cb78b5d1e1563143c771a1a9c373f49d33c7ebf6f757` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 28639 | `262e35a04e67ace7a3508ce8a54ecf94b164bc416ca983ae6383ff52330e27de` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `030fa61ae8af0c7392cb6b702b32680b1d2c8a23e48bf6937a89b400cf3e5ea2` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `cfbe28a6198ae792554cc8f4a51f31817b20cbf1c74cb9763d6df64196dc9ea0` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `cf63faa0c172c8aba99858ed2bd85067383a56d3fb0faeb092410c09fedea41f` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `7bbce100cdaf5baa27b1f9577c2f2c09ae6a0e24d2fb75f36ed20b1d436fb787` |
| `docs/experiments/casee/results/casee_c016_codegen_gate.csv` | csv_table | 530 | `6d1a4be6550c2b103b8ece2f5b03544dcd8440595df81cbd164b32b2bea802bd` |
| `docs/experiments/casee/results/casee_c016_codegen_gate.json` | json_manifest_or_gate | 1516 | `ccee3b74bf37ec2b8d2e8586267b79b3e76be1394935a105dcd76485dc0ed444` |
| `docs/experiments/casee/results/casee_c016_codegen_gate.md` | markdown_report_or_protocol | 1175 | `47e0799138f81cd2ed565b8a885e5a36e27acd88955636570f8a6ddf133bf711` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `b7a0c7d98dda250a4b2aac239452344ad145d1695ce48ee787d7dfe55787216c` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `97df6547c1b29efbb8a88138f8e73795a9f26e95c4b52d703e92a074ee105378` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `5eb678b6c88dc937eb5c6bdd31b0990b555bd94942e8a97f1e74eebe7e189a9e` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `93621be7bc9097d94a8452485e157b9f20f47749d8f2c328fd0a747218388747` |
| `docs/experiments/casee/results/casee_default_promotion_gate.csv` | csv_table | 3752 | `63b82f4ddb695e33ae8320122f857aee3852b0885d2ed1087e876709941fcf28` |
| `docs/experiments/casee/results/casee_default_promotion_gate.json` | json_manifest_or_gate | 7713 | `9e68fd625cc1cb110869d6a0f1870a752dbe3d79ae906619eae36956368c1057` |
| `docs/experiments/casee/results/casee_default_promotion_gate.md` | markdown_report_or_protocol | 1311 | `dbda3b02695246a2196e84a67a14392147110086e42d6abec0212112159925e1` |
| `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.csv` | csv_table | 531 | `310914cc64c4b739d4f56d5fc9457d96f9d14f8ff7f2d3596770d55cfb002943` |
| `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.json` | json_manifest_or_gate | 1409 | `f2216c7fc9841a4bdcd3b38b637b232693230f3378074b532b468a02b87a13e0` |
| `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.md` | markdown_report_or_protocol | 1154 | `8edc7fbd1c9bbfcf1ce8f630e220c4d730a5631ef1a2d4290af57859779f6d69` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `abc5e5fd6afe3bf14b12e5c13e73df6a59b2fec9b5cebebb295dc83f0aedf053` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `45597fed04ffda865d134e6888a30a1be41597f7afd0650a908c6a0b2fcd7bcc` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `f0b63a91f708126087033012f3db73577204c227094e9329924262d8c9d554f6` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_native_codegen_smoke_gate.csv` | csv_table | 724 | `018a3197da90ccb7ce497279fd509baef04116f9fcd4b9ceff905b128febf8a8` |
| `docs/experiments/casee/results/casee_native_codegen_smoke_gate.json` | json_manifest_or_gate | 7363 | `319bd4dbd33dceb4cdc077bb4adc7233d0c3f07ed7e85c3e386644d8ccf6da54` |
| `docs/experiments/casee/results/casee_native_codegen_smoke_gate.md` | markdown_report_or_protocol | 1227 | `341aa40013972097f0f6717227a2d4b2cd7a4332cb00da73f6c375f58213ae59` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12892 | `b2605df8d8178c434b4f0dd97cec03d21c38d6338b9142dacee47e50234d9293` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7624 | `072af4ba14d352009fa43c916ed2e2c76c194d5ad2260de51addebd0e2e0215f` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `13dc59e0578134d98b789bb8d7ddc91ece5f8f07717ceeb86835bf366d1b0759` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `19cbfdd5385ed2eff645b111d510d6f9370c25ac548c9594faa1224d89636512` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.csv` | csv_table | 531 | `bdf027a29169410c4e057710c1a0be55485382ab36ec31bd29d0bd1f04a2ed02` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.json` | json_manifest_or_gate | 2131 | `bf39e938aab8cdda0c7d08f647ad13c9b09a809c886ed71dff80452e4b65a4ca` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.md` | markdown_report_or_protocol | 1128 | `44f7344b34b825565595c7952b35c0ba724114348f4913a74e3b73668ddb768b` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10964 | `7a04c800a95a435ea6508fefc966956d94971589e394e0e77b484132df7f0404` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4366 | `56953c5352348fdc4a39386dbe356910739c6a0ed853a80dd3a529765f96e360` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 1066985 | `ffaeb906d2d2f05f1961b8f914b113a1b4f87aeda752d44c96e280ba4c812e8a` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 4417 | `c6464f53129d379330fef6ab5cf1f8c3196d4fe2cec2f041da373c477bc7c9fc` |
| `docs/experiments/casee/results/casee_research_accuracy_gap_gate.csv` | csv_table | 2103 | `b2fe2ec37e07d444fb58a44846a58329cf4659ea93c80bf8c18059b7fdea8ef7` |
| `docs/experiments/casee/results/casee_research_accuracy_gap_gate.json` | json_manifest_or_gate | 5131 | `4eb6be35acccc9c6877321085b682b662aea39dcbb95ddbb86674c23ec467257` |
| `docs/experiments/casee/results/casee_research_accuracy_gap_gate.md` | markdown_report_or_protocol | 1227 | `3cb7fe2375e80dfb96406a6a86622d6aac3d7bdd351c96c5fed3622f60adb12f` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_kit.csv` | csv_table | 1453 | `ca1b35b7522728592c4539cbb01c7e087942a31d958e853fa99de06856ce13a0` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_kit.json` | json_manifest_or_gate | 5204 | `c4f33fd3bb8c43a2bd8171ea3555af26b3de80a22373387b607119da9b97a0a9` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_kit.md` | markdown_report_or_protocol | 2457 | `9d0101a5308361fa2b7f1a8cbb5c13ad81a467c2410a96e10316bb3a96e57abd` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.csv` | csv_table | 2398 | `0b92ae8f846f04994916e2afce4d50fe8cd7693d46660b11ff74800ef0066772` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.json` | json_manifest_or_gate | 8724 | `237d90f6cbe3d1f86861ea21dbd81cd46b7ccda4e42cf42ddef756ffb855a9d9` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.md` | markdown_report_or_protocol | 2172 | `8653502b381b14dfead1503a858efd72e14018d2f578c9c3d3922cdcde600641` |
| `docs/experiments/casee/results/casee_runbook_codegen_preflight.csv` | csv_table | 1068 | `7d7cee7049e2c8a3a9738bd59873c98fa2c7968f14734879a9ccc58c17d2a9b6` |
| `docs/experiments/casee/results/casee_runbook_codegen_preflight.json` | json_manifest_or_gate | 12110 | `299a733cae1f5c729fae2a00fad56e48e8778004e9790f167db33fb436ff3384` |
| `docs/experiments/casee/results/casee_runbook_codegen_preflight.md` | markdown_report_or_protocol | 1449 | `b0f029f6e5371b0f6892d6b028fd9a9ba536032da184728231d851a6c19c4548` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `6fe43a2fda4b4da84a0a18ce9231b10f2d2a51d2b51890ef2aa41c2cf615145b` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `23b3ce967b59462b5804b6143caac987dab0f00a7baa113e88bf4df5d5aa50b2` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `6e772726e03075925b2cc3dfcb959f5ae4d0389d7bc58ed2f2a1db1de0db6a21` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `dc64277070dfaf39102dc77b7f3b101b8bcbf01ea2fd254f2122fdaccf5c36f5` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `af5823a21c8fc764758815be1205c2e8369cb032862b6e74636a5cea239647e1` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.csv` | csv_table | 620 | `bb2f26d96c97b947b0f9a562158e88e34b5635f4b88a39e532f65f81a27ab0c2` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.json` | json_manifest_or_gate | 1483 | `1185965d028b5901cce19e2e79df79fd9846ef0757701a87c4dd9b09bbbc28f6` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.md` | markdown_report_or_protocol | 1228 | `5adda11c8b4a9616a590719aae0ae45d915322d2c09ef35361919c61472d2e8c` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.csv` | csv_table | 25216 | `9595b90a90a2a173d1733a55ed1ede788798355f1f6f94f3888c00a13b0179f9` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.json` | json_manifest_or_gate | 50917 | `9ab44f60d8627e072d1e631937301639a8cf8299fced82ae929bbbe5b985d505` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.md` | markdown_report_or_protocol | 701 | `a09d8225d3a5d45914f39683d9e167a7b78f70f8a5073cc125929ad94355a3a4` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.csv` | csv_table | 462 | `7face81afa9f8dfa6dba162fdaf209001a86ca3c6556d7dbadf64089a5925f06` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.json` | json_manifest_or_gate | 5448 | `bd4c078d6fe42ba91d7ee6bfecaacf3144f54c8d832acb927896e9d02a1d73e9` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.md` | markdown_report_or_protocol | 804 | `b72cbbc9e3258a42481fff21721cfbe9ae9e32f339ecddd9f9fa0adc5cf04ff4` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.csv` | csv_table | 673 | `6af6143dcb5e7c5f5eaf585fa5bd36c7256a1ef19bc388610f92ac0581e4c2e5` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.json` | json_manifest_or_gate | 1514 | `b4a451138d926f558746f671ad6039ccaf74481e63c5fcfaadaadb38ffb1a278` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.md` | markdown_report_or_protocol | 1280 | `68ae11e3086d425d300a303f4f0f295e7f5a48d384a0a454a4856c4c6533ad92` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.csv` | csv_table | 553 | `fd99c9f2b639290d71f558f42439dae97d0433822e61a9a723aa379ee5ac9fc4` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.json` | json_manifest_or_gate | 1310 | `b2bff68bcf98d190924e870f0f544ee84e86d477fa4cdbb1401df48f4d5b5ab2` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.md` | markdown_report_or_protocol | 1232 | `0977a9a355d651f105fe81e50896f6201b0b564bd80e1e15951d0e5b9dd50c09` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `e7e2ea50ead66a1ff586157e650797bf008a6d5144c4e34231f76f16d7bcb856` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4388 | `88fb0ad4314656856fb2c34bfbb7cb82529ed776ecfbcfa3c85af5c93c81b107` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `33719db5c7bd6d84765e5242a668675d5c83922b1f08618bda334727ee1c59fa` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `24487ad6bc7fcb2222d6181d228dd07a2965a9d2d8e2c51a25b90a263eb8cda6` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `d4e6e93f6dc9d0cb3527ec4165f11b34bce2602ed136d42d8a2c100a687a46e6` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `c04d7cda07a580e72d6903a731ad1f4afae946aae16044e2c912a43e2a66b387` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `9f94caf563f325d1fc4a15e095f59d07830683d2e37e97e2cd5d632bb8157a82` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 95028 | `3c9ea2e3df7ae71bbf610b27530822c621ad33b3294f116d6070caf160d82421` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 39400 | `19f723702863548a65e48791ec992c093841f68b364f8550802c1f549ae5be77` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `099ab367c9c1849dcb48957f655c1c10f19260f81275fda2d10f0a033832147c` |
| `docs/experiments/casee/results/github_release_publication_gate.csv` | csv_table | 341 | `6b777979c08ed3473ebfd57e29fa587377e597ac99ebd1e61c9bb448bf000b4b` |
| `docs/experiments/casee/results/github_release_publication_gate.json` | json_manifest_or_gate | 2141 | `1165c8a5deb142d261067ec5d8d1b659d89aa52f3ce3dde46605645db346c1f3` |
| `docs/experiments/casee/results/github_release_publication_gate.md` | markdown_report_or_protocol | 686 | `572117bd14d0d2072c343e1c8493ef7b15585bf2f8171c066f3f877e2c5141bc` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `068a92dfbaaa78088a3549e8ce95e5aa3e7245975259ecd43cfdad93f1d4dadb` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `07ecce78227173ab142abb7a862505d64517bd020bd0676a129c93053851b85f` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `89158c8bd6b2441bf1099dac4a828636819d0e9315693ef7d76654eeea58ab88` |
| `docs/experiments/casee/results/rhino_gha_load_manifest.expected.json` | json_manifest_or_gate | 2013 | `7d6bd7de0b29814695e6b9fe4c79d6bfaed31934102d4084a36e09870e503959` |
| `docs/experiments/casee/results/rhino_gha_load_manifest.template.json` | json_manifest_or_gate | 803 | `42ba2b1f5a8c1f66d6e9ab3d418d9ddc0142c02fc0f875ec454e85f595163d6d` |
| `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.csv` | csv_table | 1347 | `09acc127e2d10116158d49308ae76ff8f1c089074098595538b7f4ed32ec0770` |
| `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.json` | json_manifest_or_gate | 4725 | `db3eb7351a129219d1cd60000404edce29750e031158008909f8d0929999db1b` |
| `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.md` | markdown_report_or_protocol | 1560 | `19105dc43752dc47001ec19e8ae4c73f5dd2e9693a04bd4da0f0dc6eafb58b60` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `f7990d38e9316c14bc8cf1ab290998eea384b38a4dda6b706d506fc88f8003e4` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `928d5b9a74e654f00f41d95cf86ab75a7321433d11f6eefaa67d4b4feeccc9cc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `9be4d1120c906fc50d18ee12e585d3e087dff76462779bb05b100ca69a83fb8f` |
| `docs/releases/v0.4.0-rc70.md` | release_notes | 1716 | `72cf2575abc924ab40589868ea21cbdc117b4d9d7e67159e63b4653021db4c5d` |
| `docs/releases/v0.4.0-rc71.md` | release_notes | 1672 | `8077e5be2e7107ff5be297cb147f0fc94b86d9b856ce86c3865900de9b583c55` |
| `docs/releases/v0.4.0-rc72.md` | release_notes | 1934 | `ab734e283ffc12a018aae5051ca1b64ab00c787ef8bd3ff098a7424d5e48caa4` |
| `docs/releases/v0.4.0-rc73.md` | release_notes | 1567 | `17f7d19417db876ddaf2e085107d8467da7a0c75986248fdaa0dc00513476c0a` |
| `docs/releases/v0.4.0-rc74.md` | release_notes | 1374 | `e9404c95d657fae138cbf02a4d935f49d2a7850a9b56677de8d6250713d8381a` |
| `docs/releases/v0.4.0-rc75.md` | release_notes | 1567 | `cd19c3d3a18c721ccec0d5ac9fde624cea08581fad7109bdc57b59dcd1f1de4d` |
| `docs/releases/v0.4.0-rc76.md` | release_notes | 1226 | `86ad0f81670fce1c191fc559538906ae0474a4b3142c1b8f79f44abe53f3b13c` |
| `docs/releases/v0.4.0-rc77.md` | release_notes | 1136 | `0f9e1510169de59140e94bcd7dc3a479395e23669b8a545139c7d343703be322` |
| `docs/releases/v0.4.0-rc78.md` | release_notes | 1158 | `ac5c9be3f0fd721f3d6132780f6331721b6a3c32df3cdfe3fc154325c663d482` |
| `docs/releases/v0.4.0-rc79.md` | release_notes | 1411 | `4f6b487f4f4060de1bfb2ef1fda1582b7bd2a78776b73f54bfeb20511bd6d7c5` |
| `docs/releases/v0.4.0-rc80.md` | release_notes | 1301 | `b94eba94d236d7219fa096a3d7b6528ebb5eb636f221a96154d46234e9589b31` |
| `docs/releases/v0.4.0-rc81.md` | release_notes | 1419 | `4438c18426c00dfeb884a1b859363db282f4007e7e2fbae25a0da8ffa04d89ae` |
| `docs/releases/v0.4.0-rc82.md` | release_notes | 1720 | `a2cfabf99fe2dee5f50ea7775b1958be8c34a60960e7dec4224a174ec9db0d90` |
| `docs/releases/v0.4.0-rc83.md` | release_notes | 1594 | `94a9e02ec8b0a28f836f8446e08d4d43be04486f138918151b69cbc252c7b1a0` |
| `docs/releases/v0.4.0-rc84.md` | release_notes | 1307 | `f75d1886476b0b0d19b54e1a74ba19cd18d56e6f81309737f3572a27509e878b` |
| `docs/releases/v0.4.0-rc85.md` | release_notes | 1300 | `012fe48a052a885404fa595c5b3108a5061468248e78b6a1c155457a46f228b5` |
| `docs/releases/v0.4.0-rc86.md` | release_notes | 1395 | `6777536e465e630374f868a549d70ed11278377c855e05527ec364ce05280252` |
| `docs/releases/v0.4.0-rc87.md` | release_notes | 1350 | `2d6227c67442c0f2c743fe18cb3f77f68baacd205227191358a62affcc7034f6` |

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
