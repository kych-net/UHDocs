#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反光光阵列聚光模式 —— 数值复核
只读,不改 内容/。运行: python3 脚本/设计/设计_反光阵列聚光.py

背景(内容/地理/天堂.typ 控光节):
  · 阵列在主行星-恒星 L1, 距主行星 d = 3.33e6 km
  · 帆面密度 1 g/m², 5% 散光需不透明面积 1.46e14 m², 总质量 1.5e11 kg
  · 阵列影盘半径 3.0e4 km(罩行星+半影)

聚光模式物理:
  · 镜面在 L1 附近, 入射光沿日-行轴线传播, 行星在下游
  · 平面镜反射反转法向分量 → 轴线上的镜无法把光"前向"反射给行星
    → 聚光单元必须横向偏置, 反射角 α ≈ atan(offset/d), 镜面倾角 α/2
  · 平面镜不聚太阳像: 反射光斑角径 = 恒星角径 0.533°
    → 行星处光斑半径 = d·tanα_sun + R_mirror (需分段, 单镜远小于半影斑)
  · 耦合效率 η = (R_p/R_spot)²(同轴, 行星盘内接于光斑)
"""

import math

G = 6.67430e-11
L_SUN = 3.828e26

R_P = 1.5e4 * 1e3
g_P = 20.0
M_P = g_P * R_P**2 / G
A_P_ORB = math.sqrt(L_SUN / (4 * math.pi * 1360.0))
R_SUN = 6.957e8
S = 1360.0

D_L1 = 3.33e6 * 1e3            # m
ALPHA_SUN = math.atan(R_SUN / A_P_ORB)   # 恒星角半径 0.266°
R_SPOT0 = D_L1 * math.tan(ALPHA_SUN)     # 半影斑半径(点镜)
RHO = 0.9                       # 薄膜反射率
SIGMA = 1.0e-3                  # kg/m²
A_PLANET = math.pi * R_P**2

print("=" * 78)
print("零、几何")
print("=" * 78)
print(f"L1 距离 d = {D_L1/1e3:.3e} km, 恒星角半径 = {math.degrees(ALPHA_SUN):.3f}°")
print(f"点镜光斑半径(半影) = {R_SPOT0/1e3:.0f} km = {R_SPOT0/R_P:.2f} R_p")
print(f"阵列影盘半径 3.0e4 km → 最大偏置偏角 = {math.degrees(math.atan(3.0e7/D_L1)):.3f}°")
print(f"聚光单元镜面倾角量级 = {math.degrees(math.atan(3.0e7/D_L1))/2:.3f}° (近正面朝日)")
print("注: 轴线上单元无法前向反射(平面镜反转法向分量), 聚光单元需横向偏置。")
print()

# ============ 分段与耦合效率 ============
print("=" * 78)
print("一、分段与耦合效率 η = (R_p/R_spot)², R_spot = R_spot0 + R_mirror")
print("=" * 78)
print(f"{'单镜半径 km':>12} {'R_spot km':>10} {'η':>7} {'η·ρ':>7}")
for rm_km in (10, 100, 1000, 3000, 15500, 30000):
    r_spot = R_SPOT0 + rm_km * 1e3
    eta = (R_P / r_spot)**2
    print(f"{rm_km:>12} {r_spot/1e3:>10.0f} {eta:>7.3f} {eta*RHO:>7.3f}")
print("单镜半径 ≲ 1000 km 时 η·ρ ≳ 0.7; 取单镜 ~1000 km, η = "
      f"{(R_P/(R_SPOT0+1e6))**2*RHO:.3f}")
ETA = (R_P / (R_SPOT0 + 1e6))**2 * RHO
print()

# ============ 聚光分档(所有镜整体转角, 同步偏转调光) ============
print("=" * 78)
print("二、聚光分档: 所有镜一起转, 全部参与; 同步偏转角 δ 调增益")
print("   阵列规模按控光节现有值: A_arr = 1.46e14 m² (1.5e11 kg)")
print("   全对准: 光斑同心罩行星, 增益 = A_arr·ρ·η_geo/A_planet")
print("   偏转 δ → 光斑中心偏移 s = 2δ·d, 行星截获按两圆重叠比下降")
print("=" * 78)
A_ARR = 1.46e14
R_SPOT = R_SPOT0 + 1e6              # 单镜 1000 km 分段
ETA_GEO = (R_P / R_SPOT)**2
GAIN_FULL = A_ARR * RHO * ETA_GEO / A_PLANET
print(f"全对准增益 = +{GAIN_FULL*100:.1f}% (辐照 {S:.0f} → {S*(1+GAIN_FULL):.0f} W/m²)")

def overlap(r1, r2, s_):
    """两圆重叠面积"""
    if s_ >= r1 + r2:
        return 0.0
    if s_ <= abs(r2 - r1):
        return math.pi * min(r1, r2)**2
    a1 = math.acos((s_**2 + r1**2 - r2**2) / (2 * s_ * r1)) * r1**2
    a2 = math.acos((s_**2 + r2**2 - r1**2) / (2 * s_ * r2)) * r2**2
    a3 = 0.5 * math.sqrt(max((-s_ + r1 + r2) * (s_ + r1 - r2)
                             * (s_ - r1 + r2) * (s_ + r1 + r2), 0.0))
    return a1 + a2 - a3

def solve_offset(frac):
    """给定截获比例(相对全对准), 二分解偏移 s"""
    target = frac * math.pi * R_P**2
    lo, hi = 0.0, R_P + R_SPOT
    for _ in range(200):
        mid = (lo + hi) / 2
        if overlap(R_P, R_SPOT, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

D_L1_KM = D_L1 / 1e3
print(f"{'增辐照':>8} {'偏转角':>10} {'光斑偏移 km':>12} {'表均温变化':>10}")
T0 = 255.0
for pct in (1, 5, 10, 15):
    frac = (pct / 100) / GAIN_FULL          # 相对全对准的截获比
    if frac >= 1.0:
        s_off, delta = 0.0, 0.0
    else:
        s_off = solve_offset(frac)
        delta = math.degrees(s_off / (2 * D_L1))   # 偏转角
    t = T0 * (1 + pct / 100)**0.25
    print(f"{pct:>7}% {delta:>9.3f}° {s_off/1e3:>12.0f} {t-T0:>+9.1f} K")
print()

# ============ 上限 ============
print("=" * 78)
print("三、上限")
print("=" * 78)
A_FOOT = math.pi * (3.0e7)**2
print(f"阵列影盘面积 = {A_FOOT:.3e} m² = {A_FOOT/A_PLANET:.1f}× 行星截面")
GAIN_MAX = A_FOOT * RHO * ETA_GEO / A_PLANET
print(f"影盘铺满(单元 {A_FOOT*SIGMA:.2e} kg) → 最大增辐照 = +{GAIN_MAX*100:.0f}% "
      f"(辐照 {S:.0f} → {S*(1+GAIN_MAX):.0f} W/m²)")
print(f"现有阵列({A_ARR:.2e} m²)全转聚光 = +{GAIN_FULL*100:.1f}%")
print(f"光斑半径 ≈ 行星半径(单镜 1000 km) → 行星面照度均匀, 无热斑。")

# ============ 散光偏转角(所有镜一起动) ============
print()
print("=" * 78)
print("五、散光偏转角: 所有镜正面朝日为全挡位, 同步偏转 β → 投影 cosβ 下降")
print("   散光比例 = (A_arr·cosβ)/A_foot")
print("=" * 78)
A_FOOT2 = math.pi * (3.0e7)**2
RATIO = A_ARR / A_FOOT2
print(f"现有阵列占影盘 = {RATIO*100:.2f}% (全挡位遮挡上限)")
print(f"{'散光':>8} {'偏转角':>10} {'辐照':>8} {'表均温变化':>10}")
for pct in (1, 3, 5):
    beta = math.degrees(math.acos(pct / 100 / RATIO))
    s_ = S * (1 - pct / 100)
    t_ = T0 * (1 - pct / 100)**0.25
    print(f"{pct:>7}% {beta:>9.1f}° {s_:>8.0f} {t_-T0:>+9.1f} K")
print(f"散光上限 = {RATIO*100:.1f}% (β=0); 扩至影盘铺满可挡 100%")
