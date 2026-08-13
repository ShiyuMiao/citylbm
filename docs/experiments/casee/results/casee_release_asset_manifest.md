# Case E Release Asset Manifest

Generated: 2026-08-13T08:30:22.129441+00:00

## Verdict

- Release asset manifest passed: True
- Recommended tag: `v0.4.0-rc80`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Upload assets: 97
- Excluded/hash-only assets: 20
- Upload total size bytes: 4290240

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
| `CHANGELOG.md` | markdown_report_or_protocol | 70996 | `a40c37d04fa7c9a22c7355d96972478a2274dfd8b739bbba3ab53ff236b68dfe` |
| `CityLBM/bin/CityLBM.gha` | compiled_plugin | 1838080 | `f95ff419ee7e0aa2de3d2a4774e95937b4afb57aaa1c9eaaaa368af2df7d2086` |
| `README.md` | markdown_report_or_protocol | 41847 | `d7d54ce2a5041f5b4e496743784f3499cd2dea4ba3027fc316b686ebb6083455` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | markdown_report_or_protocol | 4944 | `d48fc9c4086f1c915d5557e088830cf50535e01c9303f183bf2ae6cf81f0129d` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | markdown_report_or_protocol | 18720 | `94f8e2c30dfda4e5d89617be42bcd4ceb10ca980838ad023271cfc4020b83d99` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | markdown_report_or_protocol | 18249 | `f410eb21977eea29bad83575ecc7b23c451239c5df62c501a211feadbbffbda9` |
| `docs/experiments/casea/results/casea_smoke_regression.json` | json_manifest_or_gate | 536 | `b63ae6c7a4dfe91549b53494bcf4edd31e993c0099047bab45e1edf4ce6e76bf` |
| `docs/experiments/casea/results/casea_vtk_manifest.csv` | csv_table | 481 | `f17c8707a9db96cd89cc8c86e2eb57a7ae65e82a66713770ec655626491a897c` |
| `docs/experiments/casee/casee_preset.json` | json_manifest_or_gate | 1424 | `f198694894fc5acb80b97b36c690f238ed43f83b29b2447dfb5f5338ff6cabd4` |
| `docs/experiments/casee/casee_protocol.md` | markdown_report_or_protocol | 2343 | `f5868f1fb8651acdd60e43b96c6cc7bb7313203cef85fc472ce57f083e0396f2` |
| `docs/experiments/casee/data_manifest.csv` | csv_table | 2053 | `c868bd407b214ad6d4518f8e0c26b9205282c59e065021511c19a4b244d144a0` |
| `docs/experiments/casee/evidence_inventory.csv` | csv_table | 38325 | `39771380aaea59b9382722c4ca36fbc0a369caeaa5894adf7bbe96345e31907b` |
| `docs/experiments/casee/native_fluidx3d_run_matrix.csv` | csv_table | 2928 | `0ebcb973d6f7064f4e2aee06fcfc43d84d9ba3c8cbd4e4456becd5f7a4c497e5` |
| `docs/experiments/casee/results/build_chain_manifest.csv` | csv_table | 1385 | `4c6ac845f86052bf32cd3ffb96ad7c48790f9c5f990a664b67197f30ac87ea6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | json_manifest_or_gate | 21132 | `e710d8f69c8e7159c15b044a113010523f79927648a36ad50076066f5ba8003f` |
| `docs/experiments/casee/results/build_chain_manifest.md` | markdown_report_or_protocol | 2075 | `22298a0ab73b4040ea5b465c7d2c9f7a1c27fcd3296b9647f5a3a3af06cc7484` |
| `docs/experiments/casee/results/casee_artifact_index.csv` | csv_table | 158287 | `be2e620063f8425e1c93d6fe6f77030482f7c0351315b574acc4d3f10a3792d6` |
| `docs/experiments/casee/results/casee_artifact_index.json` | json_manifest_or_gate | 278483 | `d5baf0cf6034cf78421ecfd411f813c779a9454aa355ecfa00f68a877ec7f927` |
| `docs/experiments/casee/results/casee_artifact_index.md` | markdown_report_or_protocol | 28639 | `d61454154c37005f1f73ea50441be074b6bcbc070853c8e7a6be4a206cae6cfa` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv` | csv_table | 2346 | `2d3979c42be1d5f5683c09d57c8f2d26fa78d4fb436597a67ed22469ff6ad47c` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | json_manifest_or_gate | 27454 | `e8e2382efc234928f9b380b188d25e4d80eb48f805995128ff13c0dea270ad44` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md` | markdown_report_or_protocol | 1378 | `a3a918fdfe78de45de4e52d7df5512be582fbfb2fb9bdc45cde0bd49f6d9aa69` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.csv` | csv_table | 3516 | `cc2c9a9d21a3f932a03f72f4c4fce0a62a8656f8b72517b8ee07dd32bc761ec9` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.json` | json_manifest_or_gate | 22748 | `2489d23ba890146f146afbd13df46c4fa61a36e8746f19ac3a36ba53e8ad6371` |
| `docs/experiments/casee/results/casee_c014_residual_structure_audit.md` | markdown_report_or_protocol | 4087 | `9d5d63f01fbe57b9fd3a455586df41adb66c671190f1a17196b606d27ecde253` |
| `docs/experiments/casee/results/casee_claim_support_gate.json` | json_manifest_or_gate | 9320 | `7d9c0985e2fe0c70e84db724dfdb3f7acbe276e1cfab5d24ad02f4ce49a59412` |
| `docs/experiments/casee/results/casee_claim_support_gate.md` | markdown_report_or_protocol | 3027 | `3badca0eab1fd1b526242b521c525ca9a6dec6a7d8bb17351afda1ac9dee36e7` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | json_manifest_or_gate | 14808 | `f0b99acceefce69cd61e8f48ae50bfb8ab2691f100ec18ca38f62478e6ee9f58` |
| `docs/experiments/casee/results/casee_default_policy_gate.md` | markdown_report_or_protocol | 6850 | `b910db7964a9a77f8b4cc9e97c42026a2022c4e414bd1a1a0caea0249c53ef38` |
| `docs/experiments/casee/results/casee_manuscript_results_table.csv` | csv_table | 3565 | `cffa8a89cc0cfca5000b8383633755f860a975c348c20cfcbdde724e761af701` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | json_manifest_or_gate | 6806 | `31c108d1a1f969e61d651acf357ec350f423395dc56a19b4cf4d756965c300f7` |
| `docs/experiments/casee/results/casee_manuscript_results_table.md` | markdown_report_or_protocol | 3276 | `dc48b676019b8defbb13aa93466978e8133bfdb6688199ac0f6b23ad8113b6db` |
| `docs/experiments/casee/results/casee_metrics.csv` | csv_table | 163 | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | json_manifest_or_gate | 12891 | `37ed0d2b17daf73baeb8f45fb31b749b1e8a8a7b059f5dcf8d475dd2528955e0` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.md` | markdown_report_or_protocol | 7623 | `7aca4ef383d7c504b7c68d1f86a75aa8fdcb1aa79af9e2325b8a9f71f8c735b2` |
| `docs/experiments/casee/results/casee_paper_results_figure.png` | figure | 202797 | `fe7e4b5852bd16759b62b00175b9c1e79181ce443782d01b88f1f6543d5cc931` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | figure | 97640 | `7f94cda2b994e9cbebc92cf50691e1534f1ebedf8540dc2f3ecccfd59671ad6d` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | json_manifest_or_gate | 2230 | `019695da1059af59aecf638a1468c878af0a90783f7fbb6682b0ee6803eb8c3f` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | csv_table | 1350 | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.csv` | csv_table | 531 | `bdf027a29169410c4e057710c1a0be55485382ab36ec31bd29d0bd1f04a2ed02` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.json` | json_manifest_or_gate | 2131 | `1994f698dac001f5a9fd7f7034adfa0096f1ba0d7dabc19e810cc06686af4869` |
| `docs/experiments/casee/results/casee_postrun_official_audit_handoff.md` | markdown_report_or_protocol | 1128 | `855c3a650f3ce1e4f0585ada01342f60537bb17b893fce97fe24e4de17ef8986` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.json` | json_manifest_or_gate | 10932 | `feb3764a88fc1e644ac3773422b100e176ae030027aefd1cd3583b07628d4005` |
| `docs/experiments/casee/results/casee_publication_readiness_gate.md` | markdown_report_or_protocol | 4366 | `0e180efc0460bd5420eaed34b479ded5d68231eb50dcf10275774cd35175546a` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | json_manifest_or_gate | 939399 | `f8d1138b5a6c5524c2c832456a9052904466fc9080e3750aac72943fa9121e60` |
| `docs/experiments/casee/results/casee_reproducibility_suite.md` | markdown_report_or_protocol | 4084 | `487ad280ecc0e300cdf43fae96e94d4a9e4bf6f9e5710828da9c387b05fdbfb6` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv` | csv_table | 17562 | `b9736a6b84d48d4a0e4af1eb491f5c84ee8590427bfcc7c37cb20a72eeec405c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.json` | json_manifest_or_gate | 28455 | `b0d09af6d30dc64b017bf343c7c60de69aafa1c5e1e038b0e474b1bf9d66247c` |
| `docs/experiments/casee/results/casee_solver_run_provenance_ledger.md` | markdown_report_or_protocol | 7206 | `9c855d25d027f25ce96a61b885bce845bdf30f3bd3ef2b7bae56b1e9e49a4067` |
| `docs/experiments/casee/results/casee_validation_report.md` | markdown_report_or_protocol | 6003 | `bb6472ac89a3c8178de22715d8fdac0eabf90c6a5fb81180358431615fd0af9b` |
| `docs/experiments/casee/results/casee_validation_summary.xlsx` | workbook_summary | 16384 | `d6a06e836e5758a4d4e674449466049cfb2d6ab35b35e9b0bcce960af2e5eabf` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.csv` | csv_table | 620 | `bb2f26d96c97b947b0f9a562158e88e34b5635f4b88a39e532f65f81a27ab0c2` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.json` | json_manifest_or_gate | 1483 | `4f4220a88b229d1be7b049dec0ff630bcd724d437d3806285ec3a88117f9acee` |
| `docs/experiments/casee/results/casee_wall_followup_codegen_gate.md` | markdown_report_or_protocol | 1228 | `baa4cd597ccc4b554ff57d83bd589ad653bbaac4ad9b4a289a00f94640f98237` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.csv` | csv_table | 24297 | `b1dab70347bd1b4b2304f9a3a2de4a4acd279d25e185a25fab2433afda77b145` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.json` | json_manifest_or_gate | 49008 | `a564cd811cd4b04a703770e290cbd43c2925db36acf04a4ff815e69167ba8752` |
| `docs/experiments/casee/results/casee_workspace_hygiene_gate.md` | markdown_report_or_protocol | 701 | `4d5cfc93dab8fb6ea0f851e8f136b2a82a2a304f9bfd7a4e6307b7249ce9beb6` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.csv` | csv_table | 462 | `de24b4da8b741ac6aee8f91c57a66e19ab1c342960d4dd0cee03fe05ab2617e9` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.json` | json_manifest_or_gate | 5448 | `6055f1f79bfb2cfa1fec32489403b8f696068a3db156af956d256587be14a084` |
| `docs/experiments/casee/results/citylbm_build_hash_stability_gate.md` | markdown_report_or_protocol | 804 | `ab514d01e3add73452c95db046302f36ae9d31f4b9c2518a327088b9e55f4ded` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.csv` | csv_table | 673 | `6af6143dcb5e7c5f5eaf585fa5bd36c7256a1ef19bc388610f92ac0581e4c2e5` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.json` | json_manifest_or_gate | 1514 | `090079d6e42542a58e4e6d9987f656cfa0c0c65d48448e459f2076a36222a1fd` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.md` | markdown_report_or_protocol | 1280 | `11ad26e4255e5085c1cba7ad03aa5e23bb9a0880705ef99874ccb63a09e11242` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.csv` | csv_table | 553 | `fd99c9f2b639290d71f558f42439dae97d0433822e61a9a723aa379ee5ac9fc4` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.json` | json_manifest_or_gate | 1310 | `dbfb8e8b9fbf916b792ce87fa57a10de460ddd8ce0b13bdcccf2150207fe3c22` |
| `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.md` | markdown_report_or_protocol | 1232 | `7d631990fee61bc0196f3d1572029e8db0c3c1b8e2d0854e35bac20045187567` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.csv` | csv_table | 781 | `69ac1b0054e71b602ceb99850d2ff548e2f9e810ae9ef2e068d8eb9d185e6a6f` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.json` | json_manifest_or_gate | 4388 | `b0bc96875c19031aa31d2419cb3f62f2da2bf163d571cb8193f0f685723a0193` |
| `docs/experiments/casee/results/citylbm_gha_install_audit.md` | markdown_report_or_protocol | 2246 | `55ca428ec2ceca0d53a90de43cc005c6edcadd46fdd2dcdc5beedd5b94c9381a` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | json_manifest_or_gate | 10043 | `cd664058e75fdf0e83e4b2816a0cb3e6ac52f279ad2aabdaf4bc7465d6924739` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.md` | markdown_report_or_protocol | 5177 | `eeb3fb6b59d4911e488883d90ea89b52887aeefaa2c89f2b61978450c1ee7b83` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.json` | json_manifest_or_gate | 6453 | `d2b7d2d48a1ed7595006b80047a76dfd5bc0785f20de1d2efb9933b42af5ca9c` |
| `docs/experiments/casee/results/citylbm_manifest_schema_gate.md` | markdown_report_or_protocol | 2106 | `acd8bf8fc947c896d276a5ff1a9282cdee41d79967123fdd82157138294183df` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.json` | json_manifest_or_gate | 82402 | `57f2cd82864a00c3c4b8d6823b99f22ea5a98e95db549d6bfd3c485226a99ebb` |
| `docs/experiments/casee/results/citylbm_software_feedback_matrix.md` | markdown_report_or_protocol | 33934 | `bcb77fc19361cb793652bdae61aed6b9691ce3a0f649027d8f3bc6abdd628cca` |
| `docs/experiments/casee/results/environment_manifest.json` | json_manifest_or_gate | 3193 | `8a7ee7549e64e09040a3392f864435d55544c52694ea3f9a32f812ec7f119eff` |
| `docs/experiments/casee/results/github_release_publication_gate.csv` | csv_table | 341 | `ed5c9ebc9dca66f0710a071a03ae1107e764713cef8bc151b242a1202200b0fe` |
| `docs/experiments/casee/results/github_release_publication_gate.json` | json_manifest_or_gate | 2140 | `87d6ff5fe5da36104fd132afecaac37dc22cc0ca850b261c0689bdae60a992a9` |
| `docs/experiments/casee/results/github_release_publication_gate.md` | markdown_report_or_protocol | 686 | `45dcbbd9a7686e2337a711a3caeeb8de1278aadf49209ed884dc3fcc1b622dba` |
| `docs/experiments/casee/results/release_gate.json` | json_manifest_or_gate | 4232 | `a2820adb5d0358118190a4442e14ccf3476a2599f62889d6a524143a0d1ea21b` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | json_manifest_or_gate | 2108 | `d951e5ba4fa6e8fffc84487b75d770927c6275bf28eeb3c671677a5444cf741a` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | markdown_report_or_protocol | 1903 | `e9f2670cabcdd4b39668ef9e6f7d5c35014572b74107d82923d945dfb5e5e9ef` |
| `docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json` | json_manifest_or_gate | 3929 | `ee0757dbb21bf558f9357e8784e241c5838c33db3eecb461bb8cf5ac49c09dbf` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.csv` | csv_table | 2083 | `5244e544c1989123754b8bcaff9b7af64af101c01487385cd315ed9689ed35dc` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.json` | json_manifest_or_gate | 10329 | `7add5a207ed3345288ac48706f9e5a6480902c60ef624bb14b9c7c63c5a37c69` |
| `docs/experiments/casee/results/vs_cpp_recovery_gate.md` | markdown_report_or_protocol | 2108 | `82cf4dec3bc9870778035200fc31de7da374a1daea79dd7f05086d02d6a24875` |
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

## Boundary

This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; it does not create a GitHub Release, add CFD output, or support formal accuracy claims.
