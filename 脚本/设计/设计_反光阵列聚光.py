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

# ============ 聚光分档 ============
print("=" * 78)
print("二、聚光分档: 增辐照 f% 需镜面积 A = f·A_planet/η, 质量 = A·σ")
print("=" * 78)
print(f"{'增辐照':>8} {'镜面积 m²':>12} {'质量 kg':>10} {'=散光5%质量':>12}")
M_5 = 1.5e11
for pct in (1, 5, 10, 20, 50, 100):
    a = pct / 100 * A_PLANET / ETA
    m = a * SIGMA
    print(f"{pct:>7}% {a:>12.3e} {m:>10.3e} {m/M_5:>11.2f}×")
print()

# ============ 上限 ============
print("=" * 78)
print("三、上限")
print("=" * 78)
# 阵列影盘面积
A_FOOT = math.pi * (3.0e7)**2
print(f"阵列影盘面积 = {A_FOOT:.3e} m² = {A_FOOT/A_PLANET:.1f}× 行星截面")
# 填满影盘的镜面积 → 最大增辐照
GAIN_MAX = A_FOOT * ETA / A_PLANET
print(f"影盘全部铺满聚光单元 → 最大增辐照 = {GAIN_MAX*100:.0f}% "
      f"(辐照 {S:.0f} → {S*(1+GAIN_MAX):.0f} W/m²)")
# 兼容散光: 散光占影盘 f_b%, 聚光面积 = 剩余
print(f"同一阵列分时/分区复用: 散光 5% 占影盘 5%, 其余可铺聚光 → "
      f"散光与聚光可并存, 总质量上限 {A_FOOT*SIGMA:.2e} kg (尘埃环占比 "
      f"{A_FOOT*SIGMA/2e21*100:.1e}%)")
# 光斑均匀性
print(f"光斑半径 ≈ 行星半径(单镜 1000 km) → 行星面照度均匀, 无热斑; ")
print("聚光上限受影盘面积约束, 不受聚光比约束(平面镜不聚焦太阳像)。")
