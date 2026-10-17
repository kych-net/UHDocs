#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天堂(生物卫星)天体参数设计 —— 数值复核  [已按用户决策固化]
只读,不改 内容/。运行: python3 脚本/设计_天堂天体.py

用户决策:
  1) 大小档 A(小卫星, 冥卫/月球量级)
  2) 视直径 θ = 0.50°(待确认, 下方 DEFAULT_THETA 可改)
  3) 潮汐锁定: 不一定, 取决于变轨方式
  4) 改轨机制: 允许生物推进 / 质量流(非保守)
  5) 恒星: 按类太阳 G2V(待确认)

已知(内容/地理/主行星.typ): R_p≈1.5e4 km, g_p≈20 m/s², 辐照度≈1360 W/m²
设定(内容/index.typ): 天堂可改变自身轨道 → 改变主行星轨道 → 影响气候
"""

import math

# ========== 常数 ==========
G = 6.67430e-11
AU = 1.495978707e11
L_SUN = 3.828e26
M_SUN = 1.9885e30

# ========== 主行星 ==========
R_P = 1.5e4 * 1e3
g_P = 20.0
M_P = g_P * R_P**2 / G
RHO_P = M_P / (4/3 * math.pi * R_P**3)
MU_P = G * M_P
V_ESC_P = math.sqrt(2 * g_P * R_P)

A_P = math.sqrt(L_SUN / (4 * math.pi * 1360.0))
T_P = 2 * math.pi * math.sqrt(A_P**3 / (G * M_SUN))
V_P = math.sqrt(G * M_SUN / A_P)          # 主行星公转速度
R_HILL = A_P * (M_P / (3 * M_SUN))**(1/3)

print("=" * 78)
print("零、参考系: 主行星(由设定反推) + 恒星")
print("=" * 78)
print(f"R_p={R_P/1e3:.0f} km  g_p={g_P:.1f} m/s²  →  M_p={M_P:.4e} kg ({M_P/5.9722e24:.2f} M_地)")
print(f"ρ_p={RHO_P:.0f} kg/m³  μ_p={MU_P:.4e} m³/s²  v_esc={V_ESC_P/1e3:.1f} km/s")
print(f"恒星(类太阳) a_p={A_P/AU:.4f} AU  T_p={T_P/86400:.1f} d  v_p={V_P/1e3:.2f} km/s")
print(f"希尔球 r_Hill={R_HILL/1e3:.3e} km = {R_HILL/R_P:.0f} R_p")
print()

# ========== 天堂: 定案 A 档 ==========
R_S = 1000 * 1e3            # m
RHO_S = 2600.0             # kg/m³ 生物/岩石
DEFAULT_THETA = 0.50       # °  待确认

M_S = 4/3 * math.pi * R_S**3 * RHO_S
Q = M_S / (M_P + M_S)
MU_TOT = G * (M_P + M_S)
THETA = math.radians(DEFAULT_THETA)
A_S = 2 * R_S / THETA
T_S = 2 * math.pi * math.sqrt(A_S**3 / MU_TOT)
V_O = math.sqrt(MU_TOT / A_S)
G_S = G * M_S / R_S**2
V_ESC_S = math.sqrt(2 * G_S * R_S)
D_ROCHE = R_P * (2 * RHO_P / RHO_S)**(1/3)

print("=" * 78)
print(f"一、天堂定案参数 (A 档, 视直径 {DEFAULT_THETA}°)")
print("=" * 78)
print(f"半径 r_s        = {R_S/1e3:.0f} km")
print(f"密度 ρ_s        = {RHO_S:.0f} kg/m³")
print(f"质量 m_s        = {M_S:.4e} kg = {M_S/5.9722e24:.4f} M_地    m_s/M_p = {Q:.3e}")
print(f"轨道半长轴 a_s  = {A_S/1e3:.4e} km = {A_S/R_P:.1f} R_p")
print(f"轨道周期 T_s    = {T_S/86400:.2f} d")
print(f"轨道速度 v_o    = {V_O:.0f} m/s")
print(f"表面重力 g_s    = {G_S:.3f} m/s² ({G_S/9.81:.2f} g_地)")
print(f"逃逸速度 v_esc  = {V_ESC_S:.0f} m/s")
print(f"洛希极限(刚体)  = {D_ROCHE/1e3:.0f} km,  a_s/洛希 = {A_S/D_ROCHE:.1f}× (>1 稳定)")
print(f"希尔球占比      = {A_S/R_HILL*100:.1f}% r_Hill")
print(f"视半径(主行星看)= {DEFAULT_THETA/2:.2f}°")
print()

# ========== 二、变轨机制与自转 ==========
print("=" * 78)
print("二、变轨机制(决策 4)与自转(决策 3)")
print("=" * 78)
print("机制: 天堂喷射工质, 推力 F=m_dot·u 经引力耦合改变整个系统的日心动量。")
print(f"冲量预算: 使系统质心 Δv 需 I=(M_p+m_s)·Δv = {M_P+M_S:.3e}·Δv")
print(f"喷出工质 Δm=I/u; 以天堂质量 m_s={M_S:.3e} kg 为分母。")
print()
print(f"{'Δv(m/s)':>9} {'Δa/a':>9} {'Δa/AU':>10} "
      f"{'Δm/m_s @u=3km/s':>17} {'Δm/m_s @u=30km/s':>18}")
for dv in (0.01, 0.1, 1.0, 10.0, 100.0):
    I = (M_P + M_S) * dv
    da_a = 2 * dv / V_P                       # vis-viva: Δa/a ≈ 2Δv/v
    f3 = I / (3000.0 * M_S)
    f30 = I / (30000.0 * M_S)
    print(f"{dv:9.3g} {da_a:9.2e} {da_a*A_P/AU:10.2e} {f3:17.3g} {f30:18.3g}")
print("  (>1 表示所需工质已超过天堂自身质量)")

print()
print("辐照∝a⁻², 故改辐照 x% 只需 Δa/a=x%/2:")
for pct in (0.1, 1.0, 5.0):
    da_a = pct / 100.0 / 2
    dv = V_P * da_a / 2
    I = (M_P + M_S) * dv
    print(f"  改辐照 {pct:>4}% → Δa/a={da_a:.3g}, Δv={dv:.1f} m/s, "
          f"I={I:.1e} N·s, 工质@{3000} m/s={I/3000.0/M_S:.3g}×m_s")

print()
print("自转(决策3): 若喷射推力偏心, 反作用力矩使天堂自转可主动控制,")
print("  故不服从自然潮汐锁定; 自转周期由变轨操作决定, 不被 T_s 约束。")
print()

# ========== 三、待确认项 ==========
print("=" * 78)
print("三、仍待确认")
print("=" * 78)
print(f"  · 视直径 θ(现取 {DEFAULT_THETA}°, 与地球看月同) → 决定 a_s 与 T_s")
print("  · 恒星是否类太阳 G2V(现按此取 a_p=1 AU, T_p=365 d)")
print("  · 变轨的时间尺度与代价是否要在设定中软化(纯物理下改轨极难)")