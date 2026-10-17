#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天堂挡光方案设计(L1 遮光帆群 vs L1 尘雾) —— 数值复核
只读,不改 内容/。运行: python3 脚本/设计/设计_天堂挡光.py

用户决策:
  · 目标调光幅度 5%(辐照度 1360 W/m², 每 1% 对应有效温度约 -0.7 K)
  · 两个方案都算, 对比后再定
  · 帆面密度 1 g/m²(薄膜)

物理要点:
  · 天堂本体视直径 0.5°, 直接遮挡 ~2e-5, 可忽略 → 需专门结构
  · 方案A: L1 遮光帆群(遮星板), 单元帆倾斜调向, 影子罩住行星
  · 方案B: L1 尘雾, 光压与引力平衡的颗粒云, 连续补给
  · 原料: 尘埃环 2e21 kg, 天堂负责加工与部署
"""

import math

G = 6.67430e-11
AU = 1.495978707e11
L_SUN = 3.828e26
M_SUN = 1.9885e30
R_SUN = 6.957e8
C = 2.99792458e8

# ---------- 主行星 ----------
R_P = 1.5e4 * 1e3
g_P = 20.0
M_P = g_P * R_P**2 / G
A_P = math.sqrt(L_SUN / (4 * math.pi * 1360.0))
OMEGA_P = 2 * math.pi / 86400.0
N_P = 2 * math.pi / (365.25 * 86400.0)      # 公转角速度

S = L_SUN / (4 * math.pi * A_P**2)          # 辐照度
P_LIGHT = S / C                              # 全吸收光压

# L1 距离(数值求解, 二分法)
def l1_distance(M_p, a):
    """解 GMs/(a-d)² - Ω²(a-d) - GMp/d² = 0, d 为 L1 距行星距离"""
    OM2 = G * (M_SUN + M_p) / a**3
    def g(d):
        return G * M_SUN / (a - d)**2 - OM2 * (a - d) - G * M_p / d**2
    lo, hi = 1e3, a * (1 - 1e-6)
    for _ in range(300):
        mid = (lo + hi) / 2
        if g(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2

D_L1 = l1_distance(M_P, A_P)
R_HILL = A_P * (M_P / (3 * M_SUN))**(1/3)

# L1 处不稳定恢复梯度(沿日-行方向), 用残差函数数值差分
def f_res(d):
    OM2 = G * (M_SUN + M_P) / A_P**3
    return G * M_SUN / (A_P - d)**2 - OM2 * (A_P - d) - G * M_P / d**2
K_GRAD = abs((f_res(D_L1 + 1e7) - f_res(D_L1 - 1e7)) / 2e7)  # s^-2

# ---------- 遮挡几何 ----------
F = 0.05                                     # 遮挡比例
ALPHA_SUN = math.atan(R_SUN / A_P)           # 恒星角半径 ≈ 0.267°
PEN_R = D_L1 * math.tan(ALPHA_SUN)           # 半影外扩半径
A_PLANET = math.pi * R_P**2                  # 行星截面积

print("=" * 78)
print("零、几何与光压基础")
print("=" * 78)
print(f"M_p = {M_P:.4e} kg  R_p = {R_P/1e3:.0f} km")
print(f"a_p = {A_P/AU:.4f} AU  辐照度 S = {S:.1f} W/m²  全吸收光压 = {P_LIGHT:.3e} Pa")
print(f"希尔半径 = {R_HILL/1e3:.3e} km, L1 距行星 = {D_L1/1e3:.3e} km ({D_L1/R_HILL:.3f} R_Hill)")
print(f"恒星角半径 = {math.degrees(ALPHA_SUN):.3f}° → L1 处半影外扩半径 = {PEN_R/1e3:.0f} km")
print(f"行星截面积 π R_p² = {A_PLANET:.4e} m² = {A_PLANET/1e6:.3e} km²")
print()

# ================= 方案A L1 遮光帆群 =================
print("=" * 78)
print("方案A: L1 遮光帆群(遮星板)")
print("=" * 78)
# 帆需罩住: 行星盘 + 半影外扩
R_SAIL = R_P + PEN_R
A_SAIL = math.pi * R_SAIL**2
A_BLOCK = F * A_SAIL                         # 需要的不透明面积
SIGMA = 1.0e-3                               # kg/m²
M_SAIL = A_BLOCK * SIGMA
# 光压总力与配平
F_LIGHT = P_LIGHT * A_BLOCK
# 帆面光压加速度; 有效恢复加速度(偏离 1000 km); 配平倾角
A_SAIL_LIGHT = P_LIGHT / SIGMA
a_eff_L1 = K_GRAD * 1e6                      # 1000 km 偏差
TILT_BAL = math.degrees(math.atan(a_eff_L1 / A_SAIL_LIGHT))
# 遮挡效率损失(倾斜 cos 因子)
COS_LOSS = math.cos(math.radians(TILT_BAL))

print(f"帆半径(含半影余量) = {R_SAIL/1e3:.0f} km ({R_SAIL/R_P:.2f} R_p)")
print(f"总帆面积 = {A_SAIL:.3e} m², 需不透明面积(5%) = {A_BLOCK:.3e} m²")
print(f"帆面密度 1 g/m² → 总质量 = {M_SAIL:.3e} kg = {M_SAIL/2e21*100:.2e}% 尘埃环")
print(f"帆总光压推力 = {F_LIGHT:.3e} N, 帆面光压加速度 P/σ = {A_SAIL_LIGHT:.2e} m/s²")
print(f"L1 恢复梯度 K = {K_GRAD:.3e} s^-2 (偏离 1000 km → 加速度 {a_eff_L1:.2e} m/s²)")
print(f"配平倾角(1000 km 偏差) ≈ {TILT_BAL:.3f}°, 遮挡损失 cos ≈ {COS_LOSS:.6f}")
print()

# 站控维持: L1 本身不稳定, 悬振周期
T_HALO = 2 * math.pi / math.sqrt(K_GRAD)
print(f"L1 悬振(晕轨道)周期 ≈ {T_HALO/86400/365.25:.2f} yr (不稳定, 需主动站控)")
# 站控 Δv 估计: 不稳定时间尺度 τ=1/sqrt(K), 年漂移校正
print("站控: 帆面光压加速度远大于引力恢复项 → 调倾角即可无工质站控(太阳帆站控)")
print()

# 部署: 从天堂轨道(2.29e5 km)到 L1 的 Hohmann 转移
A_S_T = 2.29e5 * 1e3
mu_p = G * M_P
dv1 = math.sqrt(mu_p / A_S_T) * (math.sqrt(2 * D_L1 / (A_S_T + D_L1)) - 1)
dv2 = math.sqrt(mu_p / D_L1) * (1 - math.sqrt(2 * A_S_T / (A_S_T + D_L1)))
print(f"部署转移: 天堂轨道 {A_S_T/1e3:.3e} km → L1, Hohmann Δv = {abs(dv1)+abs(dv2):.0f} m/s")
print()

# ================= 方案B L1 尘雾 =================
print("=" * 78)
print("方案B: L1 尘雾(光压支撑颗粒云)")
print("=" * 78)
# 颗粒: 半径 s=1μm, 密度 ρ_d, β = 光压/引力 ≈ 0.57 Q_pr/(ρ[g/cm³]·s[μm])
RHO_D = 3000.0
BETA_1UM = 0.57 * 1.0 / (RHO_D / 1e3 * 1.0)   # ρ=3 g/cm³, s=1μm
KAPPA = 3 / (4 * RHO_D * 1e-6)                # 不透明度 m²/kg (s=1μm)
M_CLOUD = F * A_SAIL / KAPPA                  # 光深 0.05 所需尘质量(投影面同帆)
# 驻留: 辐射加速度把颗粒推离 L1, 逃逸尺度取 R_Hill - D_L1
GRAV_SUN = G * M_SUN / A_P**2
A_PUSH = BETA_1UM * GRAV_SUN                  # 辐射加速度
D_ESCAPE = R_HILL - D_L1
T_RES = math.sqrt(2 * D_ESCAPE / max(A_PUSH - K_GRAD * 1e7, 1e-12))
M_FLOW = M_CLOUD / T_RES

print(f"颗粒: s = 1 μm, ρ_d = {RHO_D} kg/m³ → β ≈ {BETA_1UM:.2f}")
print(f"不透明度 κ = {KAPPA:.0f} m²/kg")
print(f"光深 0.05 所需云质量 = {M_CLOUD:.3e} kg (与帆方案同量级)")
print(f"辐射加速度 = {A_PUSH:.2e} m/s², 逃逸尺度 {D_ESCAPE/1e3:.2e} km")
print(f"驻留时间 ≈ {T_RES/86400:.1f} d → 补给流量 ≈ {M_FLOW:.3e} kg/s = {M_FLOW*3.156e7:.3e} kg/yr")
print(f"年耗量占尘埃环 = {M_FLOW*3.156e7/2e21*100:.2e}% /yr")
print(f"粒径加倍(s=2μm) → β 减半, κ 减半: 云质量×2, 驻留×~2, 流量近似不变量级")
print()

# ================= 对比 =================
print("=" * 78)
print("对比(遮挡 5%)")
print("=" * 78)
print(f"{'维度':<18}{'A 帆群':<30}{'B 尘雾':<30}")
rows = [
    ("在轨质量",    f"{M_SAIL:.2e} kg",           f"{M_CLOUD:.2e} kg"),
    ("补给需求",    "无(帆持久)",                  f"{M_FLOW*3.156e7:.1e} kg/yr"),
    ("站控",        "太阳帆倾角, 无工质",           "持续补给即站控"),
    ("可控性",      "单元帆调向, 精细分档",         "粗调(密度)"),
    ("散逸污染",    "无",                          "尘入行星系/大气"),
    ("技术门槛",    "大型薄膜结构自持",             "颗粒尺寸控制"),
    ("失效模式",    "帆漂移→遮挡渐失(慢)",          "停供→数天~月衰减(快)"),
]
for r in rows:
    print(f"{r[0]:<18}{r[1]:<30}{r[2]:<30}")
print()
print("两方案在轨质量同为 1e11 kg 量级, 尘埃环(2e21 kg)供给均无压力。")
print(f"遮挡 5% → 辐照 1360→1292 W/m², 有效温度 255→251.8 K (表均温 ΔT ≈ -3.3 K)")
print("待用户择一或组合; 选定后写入 内容/地理/天堂.typ 的 挡光 节。")
