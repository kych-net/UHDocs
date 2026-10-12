#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天堂变轨方案设计(方案1/3/4 对比) —— 数值复核
只读,不改 内容/。运行: python3 脚本/设计_天堂变轨.py

用户决策:
  · 主目标 = 改主行星自转轴倾角(→季节气候), 不是改日心轨道
  · 配合天体候选: 1 尘埃/碎屑环, 3 大质量工质库天体, 4 行星级伴星, 三者都设计比较
  · 天堂 A 档: r=1000 km, ρ=2600, 视直径 0.5° → a=2.29e5 km, T=3.76 d
  · 变轨方式: 长时间微调 + 其它天体配合

关键物理:
  · 自转轴进动率 α=(3/2)(n²/ω)·H, H=(C-A)/C, n=扰源平均角速度
  · 倾角只需'改动天堂自身轨道面', 所需 Δv=2·v_o·sin(Δi/2), 工质 m_gas=m_s·Δv/u
  · 轴对称赤道环不产生自转轴力矩, 只能当工质库
  · Kozai-Lidov: 外层天体可零工质驱动内层轨道倾角振荡(需相互倾角>39.2°)
"""

import math

G = 6.67430e-11
AU = 1.495978707e11
L_SUN = 3.828e26
M_SUN = 1.9885e30

# ---------- 主行星 ----------
R_P = 1.5e4 * 1e3
g_P = 20.0
M_P = g_P * R_P**2 / G
RHO_P = M_P / (4/3 * math.pi * R_P**3)
OMEGA_P = 2 * math.pi / 86400.0            # 自转角速度(24h)
q_flat = OMEGA_P**2 * R_P**3 / (G * M_P)   # 扁率参数 ω²R³/GM
H_INERT = 0.95 * q_flat                     # (C-A)/C, 地球类比 0.95q
A_P = math.sqrt(L_SUN / (4 * math.pi * 1360.0))
V_P = math.sqrt(G * M_SUN / A_P)
R_HILL = A_P * (M_P / (3 * M_SUN))**(1/3)

# ---------- 天堂 A 档 ----------
R_S, RHO_S, THETA = 1000e3, 2600.0, math.radians(0.5)
M_S = 4/3 * math.pi * R_S**3 * RHO_S
A_S = 2 * R_S / THETA
T_S = 2 * math.pi * math.sqrt(A_S**3 / (G * (M_P + M_S)))
V_O = math.sqrt(G * (M_P + M_S) / A_S)

def alpha_prec(a, M_central):
    """自转轴进动角速度 rad/s: α=(3/2)(n²/ω)H"""
    n2 = G * M_central / a**3
    return 1.5 * n2 / OMEGA_P * H_INERT

def P_prec(a, M_central):
    return 2 * math.pi / alpha_prec(a, M_central)

print("=" * 80)
print("零、参考量")
print("=" * 80)
print(f"M_p={M_P:.4e} kg   R_p={R_P/1e3:.0f} km   ω_p={OMEGA_P:.4e} rad/s")
print(f"扁率 q={q_flat:.4e}  (C-A)/C=H={H_INERT:.4e} (取 0.95q, 地球类比)")
print(f"天堂: m_s={M_S:.4e} kg  a_s={A_S/1e3:.4e} km  T_s={T_S/86400:.2f} d  v_o={V_O:.0f} m/s")
print()

# ---------- 一、倾角主导权 ----------
print("=" * 80)
print("一、谁能主导主行星自转轴进动(改倾角的前提)")
print("=" * 80)
sources = [
    ("太阳",        A_P,        M_SUN),
    ("天堂(A档)",   A_S,        M_P),
    ("方案3 工质库天体 a=1e9 m", 1.0e9, M_P),
    ("方案4 伴星 a=1e9 m",      1.0e9, M_P),
]
a_sun = alpha_prec(A_P, M_SUN)
for name, a, mc in sources:
    al = alpha_prec(a, mc)
    print(f"  {name:24s}: 进动周期 P={P_prec(a,mc)/(86400*365.25):9.3g} yr   α/α_太阳={al/a_sun:9.3g}")
print("  注: 天堂轨道很近, α∝n² 极大 → 天堂独自主导倾角; 环在赤道面无力矩, 只供质。")
print()

# ---------- 二、改倾角所需工质 ----------
print("=" * 80)
print("二、改动天堂轨道面(即改主行星倾角)所需 Δv 与工质")
print("=" * 80)
print(f"{'Δi(°)':>7} {'Δv(m/s)':>9} {'m_gas/m_s @3km/s':>18} {'@30km/s':>10}")
for di in (10, 30, 60, 90):
    dv = 2 * V_O * math.sin(math.radians(di) / 2)
    print(f"{di:7.0f} {dv:9.0f} {dv/3000.0:18.3f} {dv/30000.0:10.3f}")
print("  (m_s=1.089e22 kg; >1 表示需超过天堂自身质量 → 必须有外部工质库)")
print()

# ---------- 方案1 尘埃/碎屑环 ----------
print("=" * 80)
print("方案1: 尘埃/碎屑环")
print("=" * 80)
R_ROCHE = R_P * (2 * RHO_P / RHO_S)**(1/3)
print(f"  洛希极限(ρ=2600)={R_ROCHE/1e3:.0f} km → 环限于 ~1.2–1.6e4 km 之外")
print(f"  设计: 赤道环, 内缘 1.6e4 km, 外缘 2.2e4 km, 总质量 M_ring=1e22 kg (≈1×m_s)")
print(f"  角色: 工质库(无力矩, 不改倾角)")
for di in (30, 60):
    dv = 2 * V_O * math.sin(math.radians(di) / 2)
    for u in (3000, 30000):
        mg = M_S * dv / u
        print(f"    改天堂倾角 {di}° @u={u/1000:.0f} km/s: 取环质 {mg:.3e} kg = {mg/M_S:.2f}×m_s "
              f"({mg/1e22*100:.1f}% 环质量)")
print("  评价: 供质充足; 但环自身不驱动倾角, 改倾角全靠天堂喷流。")
print()

# ---------- 方案3 大质量工质库天体(+KL) ----------
print("=" * 80)
print("方案3: 大质量工质库天体(兼 KL 驱动)")
print("=" * 80)
r3, rho3, a3 = 2000e3, 3000.0, 1.0e9
m3 = 4/3 * math.pi * r3**3 * rho3
P3 = 2 * math.pi * math.sqrt(a3**3 / (G * (M_P + m3)))
P_in = T_S
T_KL3 = (8/(15*math.pi)) * (P3**2 / P_in) * ((M_P + M_S + m3) / m3)  # e_out=0
print(f"  天体: r=2000 km, ρ=3000 → m={m3:.3e} kg ({m3/M_P:.1e} M_p), a={a3/1e6:.1f}e3 km")
print(f"  P_out={P3/86400:.2f} d, P_out/P_in={P3/P_in:.1f} (KL 需 ≥5 ✓)")
print(f"  KL 倾角振荡时标 T_KL≈{T_KL3/86400/365.25:.1f} yr, 相互倾角>{39.2}° 可触发大振荡")
print(f"  角色: 工质库 + 零工质驱动天堂轨道面振荡 → 主行星倾角随之周期变化")
print()

# ---------- 方案4 行星级伴星 ----------
print("=" * 80)
print("方案4: 行星级伴星(双行星)")
print("=" * 80)
m4, a4 = 0.1 * M_P, 1.0e9
P4 = 2 * math.pi * math.sqrt(a4**3 / (G * (M_P + m4)))
T_KL4 = (8/(15*math.pi)) * (P4**2 / P_in) * ((M_P + M_S + m4) / m4)
print(f"  伴星: m=0.1M_p={m4:.3e} kg, a={a4/1e6:.1f}e3 km, P={P4/86400:.2f} d (P/P_in={P4/P_in:.1f})")
print(f"  主行星绕双星质心半径 r_p=a·m_b/(M_p+m_b)={a4*m4/(M_P+m4)/1e3:.3e} km")
print(f"  对天堂 KL 时标 T_KL≈{T_KL4/86400/365.25:.1f} yr (很强, 驱动天堂倾角剧烈振荡)")
print(f"  角色: 巨量工质库 + 引力弹弓平台 + 直接改写主行星进动几何(双行星季节)")
print()

# ---------- 对比 ----------
print("=" * 80)
print("三、三方案对比")
print("=" * 80)
print(f"{'维度':<16}{'1 环':<22}{'3 工质库天体':<22}{'4 伴星':<22}")
rows = [
    ("工质供给",  "中(1×m_s)", "大(10×m_s)", "极大(600×m_s)"),
    ("是否零工质驱动倾角", "否", "是(KL)", "是(KL,强)"),
    ("对主行星几何影响", "小", "小", "大(双行星)"),
    ("引入代价/风险", "低", "中", "高(改写整个系统)"),
    ("时间尺度", "10²–10³ yr", "10² yr", "10¹–10² yr"),
]
for r in rows:
    print(f"{r[0]:<16}{r[1]:<22}{r[2]:<22}{r[3]:<22}")
print()
print("待用户择一或组合; 选定后我把该方案写进脚本并出正式复核。")