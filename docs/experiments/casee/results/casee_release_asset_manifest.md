# Case E Release Asset Manifest

Generated: 2026-08-13T11:05:05.554506+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc86`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 129
- Excluded/hash-only assets: 20
- Upload total size bytes: 4546317

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
| `CHANGELOG.md` | markdown_report_or_protocol | 75175 | `300714795558c56a9e06d24f46c0a9be308323c1ee536aff3b2b100920ac798e` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1838080 | `e116a5c2d827aea5022de48ab2c2b9c48caad3326de5b2d1069ad448ca73171d` |
| `README.md` | markdown_report_or_protocol | 44047 | `062afd0de99745a2939f6992ab4fbf2da98ff0d0396be25436af5cc9cfaa5a3b` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `24cd3e8390f5010142860002c4f2fe8d379f88133cbe90d896e6fb62ed7799bb` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 19980 | `e448133ce7237b8394656622371cb3e96bb3a86a37c69874ad703b1257eabc2b` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 19509 | `2d5ccf86391cb178517457d1b5392432fbbdd633b3bcfb3a1f6e35cd94e9b748` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 41413 | `ffdd97c5a37876232f483f22ab6e805b79dd931d308b52d3ee466f054be4084e` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21130 | `306e8448c519ff32dfbbd11c6344797cff902d78746281b89d203f2bcc71f79f` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `ed9043e7140b685bd6f5d7859ff5070d72a40e2363e7f898db946fca13bf1c1c` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 168552 | `2f59b7aaa122899c21f57ea389f9e984f8b95ebae7de7eb6000d0f111b6fe6d5` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 297552 | `8334d04ad7a3cf9e886b0a6b2baafb9efab0956ec89f0e7488a986db3f074f8f` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 28639 | `5adf110bd67d57ee232cf0cfba80e970115e9a2303f658a660c7049c5b361f82` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `43f1c6e6b50d0df93ab264fd343040eee83fb1983077e99a0378f77a4e1a7f48` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `10fe40322b34d6f54b01907eb41dbc4e05258bc17e9bd132e48b01032335b54b` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `64d442147c0fc81f718127aca8624da43d3a805b5d0034d8ad5d3ccad3ede5b5` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `5aabecccf0905c72434f6188e2b2937c2c8617c4bd24602942aaf93f433608a2` |
| `docs/experiments/casee/results/casee_c016_codegen_gate.csv` | csv_table | 530 | `6d1a4be6550c2b103b8ece2f5b03544dcd8440595df81cbd164b32b2bea802bd` |
| `docs/experiments/casee/results/casee_c016_codegen_gate.json` | json_manifest_or_gate | 1516 | `eadd8466a826352abbef608e07f62261779492442c0bc49457b4b29d9ef02e4d` |
| `docs/experiments/casee/results/casee_c016_codegen_gate.md` | markdown_report_or_protocol | 1175 | `fcbecc1555a09e3e6b241069febe9446514e56d2a8d6059a747c2733ccdd8f80` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `37e8a7e43cf5dc3ab1e43b110c988a87b0980af8954f198477608845f679d371` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `6347a789678bd5b80830c8bcc0b87dcac013ee9ccbd074d97af2e8f0c9d6e70f` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `a5e6c6cc8d00830871e00958e43539930a6113c3bc9bd0fa91ba48697cbfcc8b` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `dea53715114f1260f2ceb16a7dbea6f128a08e249f08af1f7f1bb9f0d33332c0` |
| `docs/experiments/casee/results/casee_default_promotion_gate.csv` | csv_table | 3752 | `63b82f4ddb695e33ae8320122f857aee3852b0885d2ed1087e876709941fcf28` |
| `docs/experiments/casee/results/casee_default_promotion_gate.json` | json_manifest_or_gate | 7713 | `e1413b750155281a3e367905272c1db5df238eb964cc4dcb14659203d9066e14` |
| `docs/experiments/casee/results/casee_default_promotion_gate.md` | markdown_report_or_protocol | 1311 | `0853323fbc628fe92f7c52f7f91191469182fe6a5f1b1a240391437211131e1f` |
| `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.csv` | csv_table | 531 | `310914cc64c4b739d4f56d5fc9457d96f9d14f8ff7f2d3596770d55cfb002943` |
| `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.json` | json_manifest_or_gate | 1409 | `0ecead27ccd4cb603c8a188c10f776850c9aafb08e0220f553dcaaed9bb5e979` |
| `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.md` | markdown_report_or_protocol | 1154 | `39645d047652110ee224951028672dff555b32d540b03f49463c637dc9c7aea5` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `fa2a5a993d0ae62b50b7abec19776bb8944f47f573d30d35326f6351539064d0` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `22caa888f8b4eabe06fd2886f64b10d13e8e74bbb9f8882821d4f9062825cacf` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `82fcf433daed8afede5f0846d8626ef6cf0bc7e9c5e4ca599d599bb4a2b4b81f` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_native_codegen_smoke_gate.csv` | csv_table | 724 | `018a3197da90ccb7ce497279fd509baef04116f9fcd4b9ceff905b128febf8a8` |
| `docs/experiments/casee/results/casee_native_codegen_smoke_gate.json` | json_manifest_or_gate | 7363 | `00fd23ba5ad7bc94a5fcfdcee5e0d5ea34e14a84dea70c17be811fdf2d0255c2` |
| `docs/experiments/casee/results/casee_native_codegen_smoke_gate.md` | markdown_report_or_protocol | 1227 | `6dc464898f7db371a3681f3891ab4006260f087ded0a5d5230759cbd7d8919a8` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12892 | `25ba3882c9171818fbaff33c859ec888606ac8087c1b13b163ff562082e8b09a` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7624 | `f57e3ebaaf61f7256f25e081c7ad9cf0877eb1285293fa71bb65ade06742e05d` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `67bf042e75e283035d223c6beaef547afb7ba034fd3473a543ef43d851e4b54a` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `49e4038ffe308e9b1b8a77c985fcf3929ad446c26e98ce32d5e9064034c2d103` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.csv` | csv_table | 531 | `bdf027a29169410c4e057710c1a0be55485382ab36ec31bd29d0bd1f04a2ed02` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.json` | json_manifest_or_gate | 2131 | `4ecf463d835c221a82b35c5803087a1152833168f739c0edd5935306c16ccfea` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.md` | markdown_report_or_protocol | 1128 | `b85f85f80aa56c963a719bad22288c99c6f33c9bd91ce3e4cb562f27bb7159bb` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10964 | `c5fd4f2e8496c8c385c3b5690de05d61bb8c06f2ff31a785a2329ce5b6f63607` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4366 | `ced18e6a43deab0fedde8c7639ffd79e8dbbf044a20785bbeaedc6d34a4622fb` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 1051295 | `1befaddd23638eb21b53be62e1315c31033e80631693533bb49d800cda3448da` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 4368 | `d341b8ad1d8dc330af83477645ea5fde5457baf9e7fa5cedb24960e6ebad90e6` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_kit.csv` | csv_table | 1453 | `4bb4882aa78f02a5957b4f572c44d9ef18655c3a3e95291f298e8bcd9a3a1d63` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_kit.json` | json_manifest_or_gate | 5204 | `716d0e17c77c1cffdd6a926a1bdc7118348d5a6a9d16a547f613f4f2a1e7b80f` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_kit.md` | markdown_report_or_protocol | 2457 | `84e5034a4a6dd14b66a6d1e5dfd3c0815da5c86f45ded8e1cbf7377cd4f8bf58` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.csv` | csv_table | 2398 | `0b92ae8f846f04994916e2afce4d50fe8cd7693d46660b11ff74800ef0066772` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.json` | json_manifest_or_gate | 8724 | `99842939ff41fab37d649b01860b96973f9835e332f502d4c9db35a89e08607e` |
| `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.md` | markdown_report_or_protocol | 2172 | `b43fb03bbfb4dfd49162857f961dae7ab14cadeda1e67157cf4519480e5f2599` |
| `docs/experiments/casee/results/casee_runbook_codegen_preflight.csv` | csv_table | 1068 | `7d7cee7049e2c8a3a9738bd59873c98fa2c7968f14734879a9ccc58c17d2a9b6` |
| `docs/experiments/casee/results/casee_runbook_codegen_preflight.json` | json_manifest_or_gate | 12110 | `d382bbe94dbac3878db540b226ec675d17b4009839568d9546b9f543fea46a0f` |
| `docs/experiments/casee/results/casee_runbook_codegen_preflight.md` | markdown_report_or_protocol | 1449 | `018fa6e1eeeb7da9bf38b0217b9ccdfaba3ce2cb6f28dc93bd0d09a57f1539e6` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `6fe43a2fda4b4da84a0a18ce9231b10f2d2a51d2b51890ef2aa41c2cf615145b` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `e5cc907bfd0bd65c505e04696801366be8c4419b4bc558026c126078c298c693` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `54922df74c7a5ced96a5d4765c7e1b16e74e6dd141f5f1e2f1aff30cd0f1679a` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `17dab001091114c8961f826b14ae84d03732cc9849b10c7fa2ce40d87e8fb027` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16383 | `3d3f0f916f5310da0883b66c2d7778c58540a23fcf28c1237d2dfb9e0810cebd` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.csv` | csv_table | 620 | `bb2f26d96c97b947b0f9a562158e88e34b5635f4b88a39e532f65f81a27ab0c2` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.json` | json_manifest_or_gate | 1483 | `b72d44f5c8c673cb83c7b83435cf03193438aa02813e0fbba59f2fcae06bc410` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.md` | markdown_report_or_protocol | 1228 | `38a0a7f010a02ee0b4efbede5152af93e4d4555ced94516b077e6de4e4c52c19` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.csv` | csv_table | 25010 | `ea9ec196b77d917daf3171ffdc6ad2e326bab34aa9053fb15c634d52185e3c81` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.json` | json_manifest_or_gate | 50491 | `bbbff358a48e5289fe642d7b2001b28643537200aa1b5ac8187a3d33a85d3c95` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.md` | markdown_report_or_protocol | 701 | `2818998c29d907da97fd0b3ab6ba41ca42237e3b1c2b4101a4e1fd08cfec3afc` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.csv` | csv_table | 462 | `234d2eac2d7e8ba8120ba7785a8e40b482f5cfa0a19ff90270639931e59f6506` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.json` | json_manifest_or_gate | 5448 | `70ff1bd30f3296a02b431d31c7eb564e86aa22d21ccc73810198377a069d49cf` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.md` | markdown_report_or_protocol | 804 | `61ecb8b9946696450828958a28d054a44f952379e49e84f4769813db845abddf` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.csv` | csv_table | 673 | `6af6143dcb5e7c5f5eaf585fa5bd36c7256a1ef19bc388610f92ac0581e4c2e5` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.json` | json_manifest_or_gate | 1514 | `863494c252ab0789e59a183594cd83d5ef7c264a6d8cecc84db598353b689cfc` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.md` | markdown_report_or_protocol | 1280 | `4fd770976345ef624bc458c41a5ba67ab4f4e87b7800fc7de6597e307188c66f` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.csv` | csv_table | 553 | `fd99c9f2b639290d71f558f42439dae97d0433822e61a9a723aa379ee5ac9fc4` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.json` | json_manifest_or_gate | 1310 | `2184f709373d38f48cc0123980c9f3ff6597afa0e069f3fe3b8191a5f4265200` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.md` | markdown_report_or_protocol | 1232 | `28f7e63f89056d2646f2845339f9814d5c82a24072595a36e9fe7b07f3ac7b99` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `cef095844cdc0734c89cb5d83322b713be8922904ce514438f56da0315510761` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4388 | `844023dd4bad8a2074102a8d1a94f275dfef702c949f1b94200ba33eb65abe02` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `5894f895e366e842715051cb2b42637b13adc66a6d9c77c7f62b81d947855ec9` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `dfaf8471dd02c43a9f3a6e6f7112d8b0c26bbda9ad960aa9cd1e8097ff6bf543` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `cd9f18e54b20abc9e38501f7fa439945667fd09fc57f967bd05bd18863e77e19` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `556b5f555303057215b4b1a1191c6f29794c803ad341062206caff82557c9c34` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `1f062f9742f9ff4e1aa0f2c12500dfc903690eec219db4f74178a68b67887b54` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 93404 | `f194f98e263464fd67959c7ffdcf96173797e361ec3a1ca020e218f35297c2ef` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 38658 | `828a723fd895bd661fa2f64735e93457506d98b567dd353dfd4ce5df5c85f3ed` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `fb83174173fec376d93589acdaabd128337f99bbfbef5863ac557065d883d095` |
| `docs/experiments/casee/results/github_release_publication_gate.csv` | csv_table | 341 | `419c881ab3bf93d0c67738618b4d2250a493f83eaaae38a437ed152717af6630` |
| `docs/experiments/casee/results/github_release_publication_gate.json` | json_manifest_or_gate | 2140 | `eb48b475b35e45b85dbd1adb63cf36f2d1494e7177d9fc7e6c1774739a9a0514` |
| `docs/experiments/casee/results/github_release_publication_gate.md` | markdown_report_or_protocol | 686 | `c056f1f7805d6bbb41f81e03337de74626eca2b4455c5b88598bb064413c06aa` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `71375c71d637d5e61d20c34509e80fe75a23c58950b9549cd97b107ab97ebe28` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `21896bdce93fc1326424390ca2f00e33f5cc290aca99f5512c80c63299f2ddb0` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `0bfbd09dce56e32080ee5e3d1d7b52dea6cb3f5285d2815b05d6e365317d6299` |
| `docs/experiments/casee/results/rhino_gha_load_manifest.expected.json` | json_manifest_or_gate | 2013 | `812cfe5bc6ddc6b7de1a2602ef4744ab2966d842e325b5de42bda4c05ab02a82` |
| `docs/experiments/casee/results/rhino_gha_load_manifest.template.json` | json_manifest_or_gate | 803 | `cbe0f7b2b80607fd4f6e703e7911d3449aed1d1190361855c918478bdd6828fa` |
| `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.csv` | csv_table | 1347 | `a3a8e0358fc1038db41f421f5637a87cf08be42478d772c81acdfac4acf07c9a` |
| `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.json` | json_manifest_or_gate | 4725 | `c19e9896ead96e31ecfff4e80cef815d9cac317d21bcfd56b45f9f48d7f36bbb` |
| `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.md` | markdown_report_or_protocol | 1560 | `01b7f64f48c669c1c63d64f096e5709a51ed67b8e4be48b38a4d48fe3a13e988` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `c90414e5b94ab3d15d2434a3e0b7c8b6dcd118d5af9fb964fe1643a3c9782a89` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `cb377fee6689d9f7946055285cc7fdbb83a9b5663c935d83738d8a3081a4b6cd` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `4c82b4568ecddd5ec38771e8cf826978039ded25a2e8eec4730ed29044d5c003` |
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

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
