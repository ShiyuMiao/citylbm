// ====================================================
// CityLBM 自动生成的 FluidX3D setup.cpp
// 场景: 验证实验AIJcaseA2121
// 生成时间: 2026-05-28 15:55:44
// 风廓线: PowerLaw
// 风速: 5.00 m/s @ z_ref=10.0m
// 粗糙度: z0=0.30m, alpha=0.22
// 风向: 1,0,0
// ====================================================

#include "lbm.hpp"

// ---- 物理参数 ----
// 网格间距    dx = 3.500 m
// 域尺寸      801.5 m x 402.5 m x 241.5 m
// 参考风速    5.00 m/s @ z_ref=10.0m
// 风廓线      PowerLaw
// 粗糙度长度  z0 = 0.300 m
// 幂律指数    alpha = 0.22
// 公式        U(z) = 5.00 * (z/10.0)^0.22
// 运动粘度    1.500E-005 m2/s
// Re ~         267166667

void main_setup() {
    // LBM 物理参数 (u_max = 0.1, tau = 0.5500, nu = 1.6667E-002)
    // 幂律风廓线: U(z) = U_ref * (z / z_ref) ^ alpha
    const float U_ref = 0.100000f;
    const float z_ref = 2.857143f;
    const float alpha = 0.220000f;
    const float dir_x = 1.000000f;
    const float dir_y = 0.000000f;
    const float dir_z = 0.000000f;

    // 风廓线速度计算函数 (C++ lambda)
    auto windProfile = [&](uint z_cell) -> float3 {
        float z = (float)(z_cell + 0.5f);
        float u_mag = U_ref * powf(z / z_ref, alpha);
        return float3(dir_x * u_mag, dir_y * u_mag, dir_z * u_mag);
    };

    // 初始化 LBM（参数：Nx, Ny, Nz, nu_lbm）
    // nu_lbm = (TAU-0.5)/3 = (0.5500-0.5)/3 = 0.016667
    LBM lbm(SX, SY, SZ, 0.01666667f);

    // 初始化边界条件和速度场（parallel_for 并行）
    const uint Nx = lbm.get_Nx(), Ny = lbm.get_Ny(), Nz = lbm.get_Nz();
    parallel_for(lbm.get_N(), [&](ulong n) {
        uint x=0u, y=0u, z=0u;
        lbm.coordinates(n, x, y, z);

        // 地面（z=0）：无滑移壁面
        if(z == 0u) {
            lbm.flags[n] = TYPE_S;
            return;  // parallel_for lambda 用 return 代替 continue
        }

        // 入口/出口边界（X 方向主导风，PowerLaw 风廓线）
        if(x == 0u)  {  // 入口：按风廓线设置速度
            lbm.flags[n] = TYPE_E;
            float3 u_in = windProfile(z);
            lbm.u.x[n] = u_in.x; lbm.u.y[n] = u_in.y; lbm.u.z[n] = u_in.z;
            return;
        }
        if(x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流
        // Y 方向侧面：自由滑移
        if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }
        // 顶面：自由出流
        if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }

        // 初始化速度场（按风廓线）
        float3 u_profile = windProfile(z);
        lbm.u.x[n] = u_profile.x;
        lbm.u.y[n] = u_profile.y;
        lbm.u.z[n] = u_profile.z;
    });

    // [FIX] 必须在 voxelize_stl 之前 write_to_device！
    // 原因：FluidX3D 的 voxelize_mesh_on_device() 内部在 !initialized 时
    // 会调用 u.read_from_device()，把 GPU 端的 u（此时还是 reset(0) 的零值）
    // 覆盖到 CPU 端，导致之前 parallel_for 设置的速度全部丢失！
    lbm.flags.write_to_device();
    lbm.u.write_to_device();

    // 导入建筑物 STL（体素化为固体壁面 TYPE_S）
    // 坐标变换：Rhino 世界坐标(m) → LBM 内部坐标(格子)
    // DomainOrigin: (-200.00, -200.00, 0.00) m
    // Dx: 3.5000 m/格子
    float3 stl_offset = float3(57.1429f, 57.1429f, 0.0000f);  // -DomainOrigin/Dx
    lbm.voxelize_stl("buildings.stl", stl_offset, float3x3(1.0f));

    // VTK 输出目录: output/

    // ── 主模拟循环 ──
#if defined(GRAPHICS) && defined(INTERACTIVE_GRAPHICS)
    // 交互式图形模式：lbm.run() 内部自动渲染每一帧
    // 按键：P=暂停/继续, Esc=退出
    lbm.graphics.visualization_modes = VIS_FLAG_SURFACE|VIS_Q_CRITERION;
    lbm.run(2000u);  // 持续模拟直到 TimeSteps
#else // 非 GRAPHICS 模式：手动循环 + VTK 输出
    lbm.run(0u);  // 初始化（0步）

    while(lbm.get_t() < 2000u) {
        uint remaining = 2000u - (uint)lbm.get_t();
        uint steps_to_run = remaining < 1000u ? remaining : 1000u;
        lbm.run(steps_to_run);

        // 输出 VTK（速度场）到指定目录
        // path 只传目录前缀，default_filename() 会自动拼接 name-timestep.vtk
        lbm.u.write_device_to_vtk("output/", true);  // true=自动转换为 SI 物理单位(m/s)

        print_info("Step: " + to_string(lbm.get_t()) +
                   " / 2000");
    }
#endif // GRAPHICS
}
