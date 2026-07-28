# FluidX3D 数值协议方法段落

evidence_type: newly_run + preexisting_artifact + blocked

实验 3 将 TUM2TWIN 核心校园街区作为 FluidX3D-native 筛查算例处理，而不是作为求解器精度验证或年度舒适度合规评价。被接受的碰撞边界为 z0 对齐的闭合核心棱柱几何，而不是带纹理摄影测量外壳。归档协议记录了 320 x 390 x 60 的计算格点、dx = 2 m、Uref = 5 m/s、空气运动黏度 1.5e-5 m2/s、dt = 0.02 s、LBM nu = 0.01000 和 tau = 0.52999996。算例包含 8 个 velocity-to 来流方向（0-315 deg，间隔 45 deg），每个方向先运行 6000 steps spin-up，并在 8000、10000 和 12000 steps 抽取 3 个后续样本。后处理在 z~2、4、10、20 和 40 m 高度层统计风速比指标。这些参数支持可复现的筛查性解释，包括行人层低风速区和上部风场恢复；但它们不构成正式残差收敛证明、实测验证、完整网格无关性或 Lawson/NEN/AIJ 年度舒适度评价。