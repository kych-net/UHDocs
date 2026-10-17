#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天堂调控主行星气候的候选手段 —— 数值复核
只读,不改 内容/。运行: python3 脚本/设计/设计_天堂气候调控.py

已有手段(已写入设定):
  · 变轨: 改天堂轨道面 → 主行星自转轴倾角 → 季节
  · 挡光: L1 遮光帆群 → 长期平均光照(1%/5%/10% → -0.6/-3.3/-6.6 K)

本脚本评估新候选:
  A 温室气体投送(NH3/CO2)   B 平流层气溶胶幕   C 海洋云增亮
  D 潮汐改自转(预期不可行)   E 主行星日心改轨   F 帆群增光(反向模式)
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
A_P = math.sqrt(L_SUN / (4 * math.pi * 1360.0))
V_P = math.sqrt(G * M_SUN / A_P)

# 大气(主行星.typ: He 76% O2 20% N2 1.9% CO2 1% H2O 1% NH3 0.1%, μ=0.0106, P=1.013e5)
P_S = 1.013e5
MU = 0.0106
M_ATM = 4 * math.pi * R_P**2 * P_S / g_P
M_CO2 = 0.01 * M_ATM * (44 / 10.6) * 0  # 质量分数换算: CO2 摩尔分数1% → 质量分数 44*0.01/10.6
M_CO2 = 0.01 * M_ATM * 44.01 / 10.6
M_NH3 = 0.001 * M_ATM * 17.03 / 10.6

print("=" * 78)
print("零、基础量")
print("=" * 78)
print(f"M_p = {M_P:.3e} kg   a_p = {A_P/AU:.4f} AU   V_p = {V_P/1e3:.2f} km/s")
print(f"大气总质量 = {M_ATM:.3e} kg (地球 5.15e18 的 {M_ATM/5.15e18:.0f} 倍)")
print(f"CO2 现量(摩尔1%) ≈ {M_CO2:.2e} kg   NH3 现量(摩尔0.1%) ≈ {M_NH3:.2e} kg")
print()

# ================= A 温室气体投送 =================
print("=" * 78)
print("A. 温室气体投送")
print("=" * 78)
LAMBDA = 0.8  # K/(W/m²), 气候敏感度类比
print("辐射强迫 ΔF = 5.35·ln(C/C0) W/m², ΔT = 0.8·ΔF (地球类比, He 大气待修正)")
for ratio in (0.5, 1.0, 2.0):
    dF = 5.35 * math.log(1 + ratio)
    dT = LAMBDA * dF
    m_add = ratio * M_CO2
    print(f"  CO2 增加 {ratio*100:.0f}%: ΔF={dF:.2f} W/m², ΔT≈{dT:+.1f} K, 需投送 {m_add:.2e} kg")
# NH3: 摩尔分数 0.1%→0.2%
print("  NH3 强温室但高空光解, 寿命短, 需持续补给维持; 增至 0.2% 需 "
      f"{M_NH3:.2e} kg (一次性)")
# 投送 Δv: 天堂轨道 → 主行星
MU_P = G * M_P
A_S = 2.29e5 * 1e3
V_A = math.sqrt(MU_P / A_S)
DV_DROP = abs(V_A * (math.sqrt(2 * R_P / (A_S + R_P)) - 1))
print(f"  投送轨道: 天堂轨道→主行星 Hohmann Δv ≈ {DV_DROP:.0f} m/s (+ 逃逸天堂 1.21 km/s)")
print(f"  评: 投送 CO2 1e18 kg 量级即得数 K 级调温; 天堂生物合成即产, 成本低。")
print()

# ================= B 平流层气溶胶幕 =================
print("=" * 78)
print("B. 平流层气溶胶幕(反照率调节)")
print("=" * 78)
# 皮纳图博: ~17 Tg SO2 → τ≈0.03, 全球 -0.5 K 级(2年)
# 换算: 气溶胶负荷按大气质量/表面积定标 → ×(R_p/R_地)² = 4
R_E = 6.371e6
SCALE = (R_P / R_E)**2
PINATUBO_SO2 = 17e9 * SCALE
print(f"面积定标因子 = {SCALE:.1f} (R_p/R_地)²")
print(f"类比皮纳图博: {PINATUBO_SO2:.2e} kg SO2 → ΔT ≈ -0.5 K (持续 1-2 年)")
print(f"维持 -1 K 需年注入 ~{PINATUBO_SO2:.1e} kg/yr 量级")
print("评: 与 L1 挡光阵列功能重叠, 但 L1 帆群失效时的行星内备份; 尘埃环可直接供料。")
print()

# ================= C 海洋云增亮 =================
print("=" * 78)
print("C. 海洋云增亮(播撒 CCN)")
print("=" * 78)
print("机理: 向海洋低云播撒海盐气溶胶, 提高云滴数密度与云反照率。")
print("量级: 云反照率 +0.02 → 行星反照率 +~0.005 → ΔT ≈ -1 K")
print(f"CCN 播撒率(地球经验 1e9-1e10 kg/yr) × 面积因子 {SCALE:.0f} → "
      f"~{3e9*SCALE:.1e} kg/yr")
print("评: 精细、可逆、区域可选; 需大气-云微物理配合, 天堂以生物气溶胶实现。")
print()

# ================= D 潮汐改自转 =================
print("=" * 78)
print("D. 潮汐改自转(验证不可行)")
print("=" * 78)
# 潮汐扭矩时标类比地球-月球: 地月自转演化时标 ~1e10 yr(耗散Q~12)
M_MOON = 7.342e22
A_MOON = 3.844e8
RATIO_TIDAL = (M_P / 5.9722e24) * 0  # 占位
# 潮汐力 ∝ M_s/a³; 扭矩 ∝ M_s²/a⁶
F_RATIO = (1.09e22 / M_MOON) / (A_S / A_MOON)**3
TORQUE_RATIO = F_RATIO**2 * (5.9722e24 / M_P)**2 * 0  # 不精确, 用简化
# 简化: 自转角动量比 + 潮汐扭矩比 → 时标
S_OMEGA = 0.33 * M_P * R_P**2 * (2 * math.pi / 86400)
T_SIDE = 1e10 * (TORQUE_RATIO if TORQUE_RATIO > 0 else 1) * 0
print(f"天堂潮汐力/月球对地球 = {F_RATIO:.2f} 倍 (不算小)")
# 时标: τ ~ ω/|dω/dt| ; dω/dt ∝ τ/I ; 类比地月(1e10 yr)按 (M_p/M_地)²/潮汐力比² 与 I 比
I_RATIO = (M_P / 5.9722e24) * (R_P / 6.371e6)**2
TS_TIDE = 1e10 * I_RATIO / (F_RATIO**2 * (M_P / 5.9722e24)**2 / (1.09e22 / M_MOON)**2) * 0
# 直接: 扭矩比 = (M_s²/a⁶)_对 比 (M_moon²/a_moon⁶)_地月, 除以自转角动量比
TQ_RATIO = (1.09e22 / M_MOON)**2 / (A_S / A_MOON)**6
TS_TIDE = 1e10 * I_RATIO / TQ_RATIO
print(f"潮汐扭矩/地月 = {TQ_RATIO:.3e}")
print(f"自转角动量/地球 = {I_RATIO:.2f}")
print(f"自转演化时标 ≈ 1e10 yr × {I_RATIO:.2f} / {TQ_RATIO:.2e} = {TS_TIDE:.2e} yr")
print("评: 时标远超恒星寿命, 潮汐改自转不可行。潮汐只影响海洋混合, 非调控手段。")
print()

# ================= E 主行星日心改轨 =================
print("=" * 78)
print("E. 主行星日心改轨(变轨脚本已算, 汇总)")
print("=" * 78)
print(f"{'辐照变化':>9} {'Δa/a':>9} {'Δv(m/s)':>9} {'工质@30km/s':>14} {'/尘埃环2e21':>12}")
for pct in (0.05, 0.1, 0.5, 1.0, 5.0):
    da_a = pct / 100 / 2
    dv = V_P * da_a
    mg = (M_P + 1.09e22) * dv / 3e4
    print(f"{pct:>8.2f}% {da_a:>9.2e} {dv:>9.1f} {mg:>14.2e} {mg/2e21:>11.1f}×")
print("评: 0.05% 辐照即需尘埃环质量 8 倍以上, 全档不可行(除非工质循环再生)。")
print()

# ================= F 帆群增光 =================
print("=" * 78)
print("F. 挡光阵列反向: 帆面改反射镜增光")
print("=" * 78)
R_SAIL = 3.0e7
A_SAIL_TOT = math.pi * R_SAIL**2
A_PLANET = math.pi * R_P**2
# 有效聚光: 帆反射到行星盘的比例(几何), 粗略上限 = 阵列可覆盖不透明面积/行星截面
A_BLOCK_5 = 0.05 * A_SAIL_TOT
print(f"阵列总帆面积 = {A_SAIL_TOT:.2e} m² = {A_SAIL_TOT/A_PLANET:.1f}× 行星截面")
print(f"5% 挡光所用不透明面积 = {A_BLOCK_5:.2e} m²")
print(f"若改反射模式: 帆把额外星光折向行星, 增辐照上限 ~1-2% (±0.7-1.4 K)")
print("评: 同一阵列双向调光, 遮挡与增光共用硬件。")
