#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天堂变轨方案1 正式复核: 尘埃/碎屑环 + 天堂喷流改倾角
只读,不改 内容/。运行: python3 脚本/复核/复核_天堂变轨方案1.py

方案(用户已选):
  · 主目标 = 改主行星自转轴倾角(→季节气候)
  · 配合天体 = 尘埃/碎屑环, 位于主行星赤道面洛希极限内, 供天堂取质
  · 变轨 = 长时间微调: 天堂吸取环质, 定向喷流, 缓慢改自身轨道面
  · 天堂 A 档: r=1000 km, ρ=2600, a=2.29e5 km, T=3.76 d, v_o=4431 m/s, m_s=1.089e22 kg

复核项:
  1 环几何 / 洛希与开普勒校核
  2 环自引力稳定性(Toomre Q)  ← 关键: 大质量环会在洛希内聚集成卫星
  3 供质预算: 改倾角所需环质
  4 倾角→气候 联动
"""

import math

G = 6.67430e-11
SIGMA_SB = 5.670374419e-8

# 主行星
R_P = 1.5e4 * 1e3
g_P = 20.0
M_P = g_P * R_P**2 / G
RHO_P = M_P / (4/3 * math.pi * R_P**3)

# 天堂 A 档
R_S, RHO_S, THETA = 1000e3, 2600.0, math.radians(0.5)
M_S = 4/3 * math.pi * R_S**3 * RHO_S
A_S = 2 * R_S / THETA
T_S = 2 * math.pi * math.sqrt(A_S**3 / (G * (M_P + M_S)))
V_O = math.sqrt(G * (M_P + M_S) / A_S)

# 环
R_IN, R_OUT = 1.6e4 * 1e3, 2.2e4 * 1e3
RHO_RING = 2600.0

def kepler_T(a, Mc):
    return 2 * math.pi * math.sqrt(a**3 / (G * Mc))

def roche(rho_sat):
    return R_P * (2 * RHO_P / rho_sat)**(1/3)

print("=" * 78)
print("一、环几何 / 洛希 / 开普勒")
print("=" * 78)
d_roche = roche(RHO_RING)
print(f"  主行星 ρ_p={RHO_P:.0f} kg/m³; 洛希极限(ρ_ring={RHO_RING:.0f}) = {d_roche/1e3:.0f} km")
print(f"  环内缘 {R_IN/1e3:.0f} km, 外缘 {R_OUT/1e3:.0f} km")
print(f"  外缘/洛希 = {R_OUT/d_roche:.2f}  (<1 才在洛希内, 环才不聚集成卫星)")
print(f"  轨道周期: 内缘 {kepler_T(R_IN,M_P)/3600:.2f} h, 外缘 {kepler_T(R_OUT,M_P)/3600:.2f} h")
print(f"  天堂轨道 {A_S/1e3:.2e} km (远在环之外, 相差 {A_S/R_OUT:.0f}×)")
print()

print("=" * 78)
print("二、环自引力稳定性(Toomre Q = c_s·κ /(π·G·Σ))")
print("=" * 78)
area = math.pi * (R_OUT**2 - R_IN**2)
for M_RING in (1e22, 2e21, 2e20, 1e20):
    Sigma = M_RING / area
    a_mid = 0.5 * (R_IN + R_OUT)
    kappa = 2 * math.pi / kepler_T(a_mid, M_P)     # 近似 κ≈n
    cs_need = math.pi * G * Sigma / kappa          # Q=1 所需速度弥散
    print(f"  M_ring={M_RING:.0e} kg: Σ={Sigma:.3e} kg/m², Q=1 需碎屑弥散 c_s>{cs_need:.2f} m/s")
print("  → 环总质量越大, 越易自引力成团; 真实行星环(土星)仅 ~1.5e19 kg")
print()

print("=" * 78)
print("三、供质预算: 改天堂轨道面(=主行星倾角)所需环质")
print("=" * 78)
print(f"  Δv=2·v_o·sin(Δi/2), 工质 m_gas=m_s·Δv/u,  m_s={M_S:.3e} kg")
print(f"{'Δi(°)':>6} {'Δv(m/s)':>9} {'m_gas@3km/s':>13} {'@30km/s':>12} {'@100km/s':>12}")
for di in (5, 10, 20, 30):
    dv = 2 * V_O * math.sin(math.radians(di) / 2)
    print(f"{di:6.0f} {dv:9.0f} {M_S*dv/3000:13.3e} {M_S*dv/30000:12.3e} {M_S*dv/100000:12.3e}")
print()
print("  环质量 vs 可改倾角次数(@30km/s):")
for M_RING in (1e22, 2e21, 2e20):
    row = []
    for di in (5, 10, 20, 30):
        dv = 2 * V_O * math.sin(math.radians(di) / 2)
        need = M_S * dv / 30000
        row.append(f"{di}°:{M_RING/need:.1f}次")
    print(f"    M_ring={M_RING:.0e}: " + "  ".join(row))
print()

print("=" * 78)
print("四、倾角 → 气候 联动(极圈纬度 = 90°-ε; 直射范围 ±ε)")
print("=" * 78)
print(f"{'ε(°)':>6} {'极圈纬度':>10} {'太阳直射范围':>14} {'季节特征':>22}")
notes = {0: "无季节", 10: "弱季节", 23.44: "地球式(现状)", 35: "季节剧烈", 45: "极圈压到中纬", 60: "极端"}
for eps in (0, 10, 23.44, 35, 45, 60):
    print(f"{eps:6.2f} {90-eps:10.2f} {'±'+str(round(eps,1)):>14} {notes[eps]:>22}")
print("  天堂只需把自身轨道面相对主行星赤道转 Δi, 主行星 ε 即随之改变 → 季节气候变。")
print()

print("=" * 78)
print("五、结论与张力")
print("=" * 78)
print("  ✓ 力学可行: 天堂独自主导倾角(进动 6.85 yr vs 太阳 6.5e4 yr)")
print("  ✓ 环在洛希内(外缘/洛希<1), 但仅在总质量不太大时稳定")
print("  ✗ 张力: 改倾角十度量级所需环质 ~1e20–1e21 kg, 仍在洛希内边缘")
print("     → 建议: 高喷速(≥30 km/s) + 环质取 2e20–2e21 kg + 碎屑弥散≥数 m/s")
print("     → 或让环只供部分工质, 其余靠天堂吸收恒星风/大气逃逸自补")