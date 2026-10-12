#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天堂(生物卫星)天体参数设计 —— 数值复核
只读,不改 内容/。运行: python3 脚本/设计_天堂天体.py

已知(内容/地理/主行星.typ):
  · 主行星半径 R_p ≈ 1.5e4 km, 表面重力 g_p ≈ 20 m/s²
  · 恒星辐照度 ≈ 1360 W/m²(与地球太阳常数同) → 按太阳(G2V)取 a_p ≈ 1 AU
  · 主行星自转 24 h, 轴倾角 23.44°

设定(内容/index.typ): 天堂是主行星的"生物卫星", 可改变自身轨道进而改变主行星轨道。

本脚本把天堂的"自由度"参数化, 其余量由天体力学导出:
  自由: 半径 r_s, 密度 ρ_s, 天上视直径 θ
  导出: 质量 m_s, 轨道半长轴 a_s, 周期 T, 表面重力 g_s, 逃逸速度 v_esc,
        轨道速度 v_o, 洛希极限, 希尔球占比, 质心偏移(改变主行星轨道的杠杆)
"""

import math

# ========== 常数 ==========
G = 6.67430e-11          # m³/(kg·s²)
AU = 1.495978707e11      # m
L_SUN = 3.828e26         # W
M_SUN = 1.9885e30        # kg

# ========== 主行星 ==========
R_P = 1.5e4 * 1e3        # m  半径(设定)
g_P = 20.0               # m/s² 表面重力(设定)
M_P = g_P * R_P**2 / G   # 由 g=gM/R² 反推质量
RHO_P = M_P / (4/3 * math.pi * R_P**3)
MU_P = G * M_P
V_ESC_P = math.sqrt(2 * g_P * R_P)

# 恒星(按 1360 W/m² 取太阳量级)
A_P = math.sqrt(L_SUN / (4 * math.pi * 1360.0))     # 行星-恒星距离
T_P = 2 * math.pi * math.sqrt(A_P**3 / (G * M_SUN)) # 行星公转周期
R_HILL = A_P * (M_P / (3 * M_SUN))**(1/3)           # 主行星希尔球半径

print("=" * 78)
print("零、主行星(由设定反推)与恒星参考系")
print("=" * 78)
print(f"主行星半径 R_p      = {R_P/1e3:.0f} km        (设定 1.5e4)")
print(f"表面重力 g_p        = {g_P:.1f} m/s²       (设定 20)")
print(f"→ 质量 M_p          = {M_P:.4e} kg   = {M_P/5.9722e24:.2f} M_地")
print(f"→ 平均密度 ρ_p      = {RHO_P:.0f} kg/m³    (地球 5514)")
print(f"→ 引力常数 μ_p=GM_p = {MU_P:.4e} m³/s²")
print(f"→ 逃逸速度 v_esc    = {V_ESC_P/1e3:.1f} km/s")
print(f"恒星(太阳量级)距离 a_p = {A_P/AU:.4f} AU  (辐照度 1360 W/m²)")
print(f"公转周期 T_p        = {T_P/86400:.1f} d")
print(f"主行星希尔球 r_Hill = {R_HILL/1e3:.3e} km = {R_HILL/R_P:.0f} R_p")
print()

# ========== 天堂: 参数化 ==========
def rho_from(r_km, m_earth_ratio=None, rho=None):
    pass

def scenario(name, r_km, rho_s, theta_deg):
    """给定半径、密度、天上视直径, 导出全部轨道/表面量"""
    r_s = r_km * 1e3
    m_s = 4/3 * math.pi * r_s**3 * rho_s
    mu_tot = G * (M_P + m_s)
    # 视直径 θ = 2 r_s / a_s
    theta = math.radians(theta_deg)
    a_s = 2 * r_s / theta
    T_s = 2 * math.pi * math.sqrt(a_s**3 / mu_tot)
    v_o = math.sqrt(mu_tot / a_s)
    g_s = G * m_s / r_s**2
    v_esc_s = math.sqrt(2 * g_s * r_s)
    # 洛希极限(刚体) d = R_p (2 ρ_p/ρ_s)^(1/3); 流体 ×2.44
    d_roche = R_P * (2 * RHO_P / rho_s)**(1/3)
    # 质心偏移(改变主行星轨道的位置杠杆): 卫星动 Δa 时行星反向动 q·Δa
    q = m_s / (M_P + m_s)
    return dict(
        name=name, r_km=r_km, rho_s=rho_s, theta_deg=theta_deg,
        r_s=r_s, m_s=m_s, q=q, a_s=a_s, T_s=T_s, v_o=v_o,
        g_s=g_s, v_esc_s=v_esc_s, d_roche=d_roche,
        a_over_Rp=a_s / R_P, hill_frac=a_s / R_HILL,
        roche_margin=a_s / d_roche,
    )

def show(s):
    print("-" * 78)
    print(f"【{s['name']}】 r_s={s['r_km']:.0f} km, ρ_s={s['rho_s']:.0f} kg/m³, 视直径={s['theta_deg']:.2f}°")
    print(f"  质量 m_s        = {s['m_s']:.4e} kg  = {s['m_s']/5.9722e24:.4f} M_地,  m_s/M_p = {s['q']:.4f}")
    print(f"  轨道半长轴 a_s  = {s['a_s']/1e3:.4e} km = {s['a_over_Rp']:.1f} R_p")
    print(f"  轨道周期 T_s    = {s['T_s']/86400:.2f} d")
    print(f"  轨道速度 v_o    = {s['v_o']:.0f} m/s")
    print(f"  表面重力 g_s    = {s['g_s']:.3f} m/s²  ({s['g_s']/9.81:.2f} g_地)")
    print(f"  逃逸速度 v_esc  = {s['v_esc_s']:.0f} m/s")
    print(f"  希尔球占比      = {s['hill_frac']*100:.1f}% r_Hill  (须远小于 0.5)")
    print(f"  洛希极限(刚体)  = {s['d_roche']/1e3:.0f} km,  a_s/洛希 = {s['roche_margin']:.1f}× (须 >1)")
    print(f"  质心偏移杠杆 q  = {s['q']:.4f}  → 天堂外移 Δa 时主行星反向移 {s['q']:.4f}·Δa")

print("=" * 78)
print("一、候选方案(视直径统一取 0.50°, 与地球看月亮相当)")
print("=" * 78)
schemes = [
    scenario("A 小卫星(冥卫/月球量级)", 1000, 2600, 0.50),
    scenario("B 中卫星(火星量级)", 2500, 3000, 0.50),
    scenario("C 大卫星(近双行星)", 4000, 3200, 0.50),
]
for s in schemes:
    show(s)
print()

print("=" * 78)
print("二、放大到显著影响主行星轨道的杠杆(方案B 为基准)")
print("=" * 78)
base = schemes[1]
for mult in (1, 10, 100):
    dm = mult * 1e3 * 1e3  # 天堂沿轨道外移 Δa = mult × 1e3 km
    ds = base['q'] * dm
    print(f"  天堂外移 Δa={dm/1e3:>6.0f} km → 主行星反向位移 {ds/1e3:8.1f} km "
          f"= {ds/base['r_s']:.2f} 天堂半径, {ds/R_P:.3f} R_p")
print("  说明: 行星相对日地距离的绝对位移不改平均辐照, 只改变'摆动',")
print("        要真正改轨道需非保守的角动量/质量流(生物推进喷流), 属机制设定。")
print()

print("=" * 78)
print("三、同步自转(潮汐锁定)一致性")
print("=" * 78)
for s in schemes:
    print(f"  {s['name']}: 若潮汐锁定, 天堂自转周期 = 轨道周期 = {s['T_s']/86400:.2f} d, "
          f"同一面恒朝主行星。")
print()

print("=" * 78)
print("四、结论(待用户拍板的自由度)")
print("=" * 78)
print("  · 半径 r_s        : 决定质量与表面重力;  A/B/C 三档相差一个量级")
print("  · 密度 ρ_s        : 生物卫星多为岩石/有机, 取 2600–3200 kg/m³")
print("  · 天上视直径 θ    : 定轨道半径与周期; 0.5°≈月亮, 更大则更近更慢")
print("  · 是否潮汐锁定    : 影响自转与'同一面朝主行星'")
print("  · 改轨机制        : 物理摆动量很小, 显著改轨需设定层面的质量流/推进")