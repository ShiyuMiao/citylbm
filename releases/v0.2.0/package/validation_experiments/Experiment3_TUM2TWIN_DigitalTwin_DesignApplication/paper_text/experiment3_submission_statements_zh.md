# 实验3投稿声明文本

evidence_type: newly_run + preexisting_artifact + blocked

## 数据可用性

实验3的轻量化归档包包含已处理报告、清单、部分 CFD-ready 几何、后处理统计表、论文图件、ParaView 状态文件和论文文本。完整 TUM2TWIN 原始下载、完整贴图目录、本地 ParaView 安装文件、本地 FluidX3D 源码/构建目录和完整 VTK 输出矩阵未嵌入 GitHub 包，原因是文件体量和机器环境依赖；其来源和边界记录在 `EXTERNAL_ARTIFACTS.md` 与 `manifests/data_manifest.csv`。正式投稿前，许可表述应再次对照 TUM2TWIN 与 Zenodo 原始记录核验。

## 代码可用性

归档包包含用于生成论文结果的后处理、形态分析、图件生成、声明审计和 manifest 刷新脚本。实验3 release package 根目录下的规范重建命令为 `& .\scripts\rebuild_experiment3_paper_assets.ps1`。包内同时保留 FluidX3D case 模板和 CityLBM-compatible 几何模板，但 CityLBM-Grasshopper 文件夹属于互操作模板，不应写成已经完成端到端插件运行的证据。

## 可复现性

当前归档足以审计数据层分离、CFD-ready 几何准备、已处理 FluidX3D 筛查指标、ParaView/人工审图资产、形态响应分析、图表叙事链和声明边界。完整重跑 CFD 需要恢复或重新下载外部 TUM2TWIN 资产、构建或恢复 FluidX3D，并重新生成完整 VTK 输出。本文不宣称现场验证、正式年度舒适/安全合规、污染物扩散、GCBTE 闭环或成功设计优化。

## 计算资源与数值协议

数值协议记录在 `manifests/fluidx3d_numerical_protocol_audit.csv` 与 `reports/fluidx3d_numerical_protocol_and_stability_audit.md`，包括 dx、网格/计算域、参考风速、空气黏性、LBM 转换、tau/Re 描述、风向和采样步。GPU 型号、墙钟运行时间、残差收敛和完整网格无关性证据不得臆造，只有在后续实际测量后才能写入论文。

## 伦理、资金和利益冲突

当前归档不包含新采集的人类受试者数据，也不包含现场风速实测活动。AUTHOR_INPUT_NEEDED：资金来源、利益冲突、致谢和 CRediT 作者贡献声明需要由作者补充。
