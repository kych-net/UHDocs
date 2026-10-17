#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容/地理/天堂.typ 全部表格数据复核
只读。运行: python3 脚本/设计/设计_天堂表格复核.py
"""

import math

G = 6.67430e-11
M_SUN = 1.9885e30
R_SUN = 6.957e8

print("=" * 70)
print("一、天体参数表")
print("=" * 70)
R = 1.0e6          # 半径 1e3 km
RHO = 2.6e3        # 密度
M = 4 / 3 * math.pi * R**3 * RHO
g = G * M / R**2
v_esc = math.sqrt(2 * G * M / R)
print(f"质量 = {M:.3e} kg   (设定 1.09e22)")
print(f"表面重力 = {g:.3f} m/s²   (设定 0.73)")
print(f"逃逸速度 = {v_esc/1e3:.3f} km/s   (设定 1.21)")

print()
print("=" * 70)
print("二、尘埃环表(μ_p = G·M_p, M_p 由 20 m/s² 与 R_p=1.5e4 km 得)")
print("=" * 70)
M_P = 20 * (1.5e7)**2 / G
MU_P = G * M_P
for a_km, tag in ((1.6e4, "内缘"), (2.2e4, "外缘")):
    T = 2 * math.pi * math.sqrt((a_km * 1e3)**3 / MU_P)
    print(f"{tag} a={a_km:.2e} km → 周期 {T/3600:.3f} h")
RHO_P = M_P / (4 / 3 * math.pi * (1.5e7)**3)
a_roche = 2.44 * (1.5e7) * (RHO / RHO_P) ** (1 / 3) / 1e3  # 流体洛希
print(f"主行星密度 = {RHO_P:.0f} kg/m³, 洛希极限(流体) ≈ {a_roche:.2e} km "
      f"(环外缘 2.2e4 km 在内: {2.2e4 < a_roche})")

print()
print("=" * 70)
print("三、控光: 散光/聚光表 (L1 = 3.33e6 km, 阵列 1.46e14 m², 影盘 3.0e4 km)")
print("=" * 70)
S0, T0 = 1360.0, 255.0
D_L1 = 3.33e9
R_P = 1.5e7
A_ARR, A_FOOT = 1.46e14, math.pi * (3.0e7)**2
R_SPOT = D_L1 * math.tan(math.atan(R_SUN / 1.496e11)) + 1e6
ETA_GEO = (R_P / R_SPOT)**2
RHO_M = 0.9
print(f"阵列占影盘 = {A_ARR/A_FOOT*100:.2f}% (散光上限)")
print("-- 散光: 遮挡 = 占影盘·cosβ --")
for f, beta in ((0.01, 78.8), (0.03, 54.5), (0.05, 14.5)):
    b = math.radians(beta)
    frac = A_ARR * math.cos(b) / A_FOOT
    s, t = S0 * (1 - frac), T0 * (1 - frac)**0.25
    print(f"β={beta:>5.1f}° → 遮挡 {frac*100:.2f}%  辐照 {s:.0f}  ΔT {t-T0:+.2f} K")
print("-- 聚光: 偏转 δ → 光斑偏移 2δ·d, 两圆重叠 --")
def overlap(r1, r2, s_):
    if s_ >= r1 + r2: return 0.0
    if s_ <= abs(r2 - r1): return math.pi * min(r1, r2)**2
    return (math.acos((s_**2 + r1**2 - r2**2) / (2*s_*r1)) * r1**2
            + math.acos((s_**2 + r2**2 - r1**2) / (2*s_*r2)) * r2**2
            - 0.5 * math.sqrt(max((-s_+r1+r2)*(s_+r1-r2)*(s_-r1+r2)*(s_+r1+r2), 0)))
for f, delta in ((0.01, 0.234), (0.05, 0.160), (0.10, 0.088), (0.15, 0.021)):
    s_off = 2 * math.radians(delta) * D_L1
    ov = overlap(R_P, R_SPOT, s_off)
    # 截获功率 = A·ρ·S·ov/(πR_spot²); 增益 = 截获/(S·πR_p²)
    gain = A_ARR * RHO_M * ov / (math.pi * R_SPOT**2 * math.pi * R_P**2)
    s_, t_ = S0 * (1 + gain), T0 * (1 + gain)**0.25
    print(f"δ={delta:>5.3f}° → 增益 +{gain*100:.2f}%  辐照 {s_:.0f}  ΔT {t_-T0:+.2f} K")
print(f"全对准增益 = +{A_ARR*RHO_M*ETA_GEO/(math.pi*R_P**2)*100:.1f}%")

print()
print("=" * 70)
print("四、倾角与季节表")
print("=" * 70)
for eps_deg in (0, 10, 23.44, 35, 45):
    e = math.radians(eps_deg)
    pol = 90 - eps_deg
    if 45 + eps_deg < 90:
        r45 = math.cos(math.radians(45 - eps_deg)) / math.cos(math.radians(45 + eps_deg))
        r45s = f"{r45:.2f}"
    else:
        r45s = "∞(45°极夜)"
    print(f"ε={eps_deg:>6}°  极圈 {pol:>5.1f}°  45°冬夏比 {r45s:>10}  极点夏至 sinε={math.sin(e):.3f}")
