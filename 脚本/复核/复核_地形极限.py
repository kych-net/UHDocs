#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主行星 地形极限复核
—— 由行星基本参数(g, R, 自转)独立推导固体地形的起伏上限:
   山脉最大高度、海洋(海沟)最大深度、水的相变硬上限、赤道隆起。
只读设定,不改 内容/。运行: python3 脚本/复核_地形极限.py
"""

import math

# ---------------- 行星参数(设定) ----------------
g     = 20.0          # m/s^2  设定
R     = 1.5e7         # m      设定 1.5e4 km
T_rot = 24.0 * 3600.0 # s      设定 24 h
G     = 6.67430e-11   # 万有引力常数

# ---------------- 地球参考 ----------------
g_e       = 9.81
R_e       = 6.371e6
h_everest = 8849.0    # m  实测最高峰
d_trench  = 10900.0   # m  挑战者深渊(最深海沟)

# ---------------- 岩石力学典型值(地球) ----------------
rho_granite = 2700.0   # kg/m^3 大陆地壳(花岗质)
sig_granite = 200e6    # Pa     抗压强度
rho_basalt  = 3000.0   # kg/m^3 洋壳(玄武质)
sig_basalt  = 300e6    # Pa
rho_mantle  = 3300.0   # kg/m^3 地幔
rho_water   = 1030.0   # kg/m^3 海水

def line(c="="):
    print(c * 72)

# ================= 0. 行星基本量 =================
line()
print("0. 行星基本量")
line()
M     = g * R * R / G
V     = 4.0 / 3.0 * math.pi * R**3
rho_a = M / V
print(f"质量 M = gR²/G = {M:.3e} kg   (地球 5.97e24, 约 {M/5.972e24:.1f}×)")
print(f"平均密度 ρ̄ = M/V = {rho_a:.0f} kg/m³   (地球 5515)")
print(f"重力 g = {g} m/s²  = {g/g_e:.2f}× 地球")

# ================= 1. 山脉极限高度 =================
line()
print("1. 山脉极限高度")
line()
print("判据:山体底部压应力 ρ·g·h 达到岩石抗压强度 σ_c 时,底部岩石压碎/流变。")
print("      h_max = σ_c / (ρ_rock · g)\n")

# 先用地球实测反推"有效强度",检验模型自洽
sig_eff_mtn = rho_granite * g_e * h_everest
print(f"[自洽检验] 由珠峰 8849 m 反推有效强度:")
print(f"  σ_eff = ρ·g·h = {rho_granite:.0f}×{g_e}×{h_everest:.0f} = {sig_eff_mtn/1e6:.0f} MPa")
print(f"  与花岗岩抗压强度 200 MPa 同量级 → 模型自洽\n")

h_granite = sig_granite / (rho_granite * g)
h_basalt  = sig_basalt  / (rho_basalt  * g)
h_eff     = sig_eff_mtn / (rho_granite * g)
print(f"花岗岩 (ρ={rho_granite:.0f}, σ_c={sig_granite/1e6:.0f} MPa): h_max = {h_granite:8.0f} m = {h_granite/1000:.1f} km")
print(f"玄武岩 (ρ={rho_basalt:.0f}, σ_c={sig_basalt/1e6:.0f} MPa): h_max = {h_basalt:8.0f} m = {h_basalt/1000:.1f} km")
print(f"同岩石按地球实测标度 (g 翻 {g/g_e:.2f} 倍):      h_max = {h_eff:8.0f} m = {h_eff/1000:.1f} km")
print(f"  → 山脉极限约 4.3–5.0 km,取 {h_basalt/1000:.1f} km 量级")

# 山根(均衡):山高对应地壳山根深度
t_root_e = h_everest * rho_granite / (rho_mantle - rho_granite)
t_root_p = h_eff     * rho_granite / (rho_mantle - rho_granite)
print(f"\n[均衡山根] 山根深 t = h·ρ_c/(ρ_m−ρ_c),  Δρ=600 kg/m³")
print(f"  地球珠峰: 山根 ≈ {t_root_e/1000:.0f} km  (实际喜马拉雅山根 ~70 km)")
print(f"  本行星:   山根 ≈ {t_root_p/1000:.0f} km  (随山高按比例减小)")

# ================= 2. 海洋(海沟)极限深度 =================
line()
print("2. 海洋(海沟)极限深度")
line()
print("判据:海沟深度由俯冲岩石圈的弯曲强度与地幔浮力(g)的平衡决定。")
print("      d_max ∝ 岩石圈强度 /(ρ_m·g)。同岩石下,g 越大→深度越小。\n")

sig_eff_ocean = rho_mantle * g_e * d_trench
print(f"[自洽检验] 由挑战者深渊 10900 m 反推有效强度:")
print(f"  σ_eff = ρ_m·g·d = {rho_mantle:.0f}×{g_e}×{d_trench:.0f} = {sig_eff_ocean/1e6:.0f} MPa\n")

d_planet = sig_eff_ocean / (rho_mantle * g)
print(f"按地球标度 (g 翻 {g/g_e:.2f} 倍): d_max = {d_planet:8.0f} m = {d_planet/1000:.1f} km")
print(f"  → 海沟极限约 {d_planet/1000:.1f} km")

# 洋壳抗压强度直接判据(参考)
d_basalt = sig_basalt / (rho_water * g)
print(f"[参考] 若纯用洋壳抗压强度支撑水柱: d = σ_c/(ρ_w·g) = {d_basalt/1000:.1f} km (偏大,仅供参考)")

# ================= 3. 水的相变硬上限 =================
line()
print("3. 水的相变硬上限(物理硬顶)")
line()
print("判据:高压下液态水相变为冰 VI / 冰 VII,液态海洋不可能更深。")
print("      d = Δp / (ρ_w · g)\n")

for name, p_pa in (("冰 VI", 0.95e9), ("冰 VII", 2.1e9)):
    d_pt = p_pa / (rho_water * g)
    d_pt_e = p_pa / (rho_water * g_e)
    print(f"{name} @ ~300 K, 相变压力 {p_pa/1e9:.2f} GPa:")
    print(f"  本行星 d = {d_pt/1000:8.1f} km   (地球 {d_pt_e/1000:.1f} km)")
print(f"  → 液态水硬上限约 46 km(冰 VI),远深于任何构造海沟,不是实际约束")

# ================= 4. 赤道隆起与扁率 =================
line()
print("4. 自转引起的赤道隆起(行星尺度起伏)")
line()
omega = 2.0 * math.pi / T_rot
q     = omega**2 * R / g            # 离心/重力比
f_uni = 1.25 * q                    # 均匀密度流体静力学扁率(上限)
# 地球实测扁率约为均匀密度值的 0.78 倍(分层影响)
f_str = f_uni * 0.78                # 地球型分层估计(下限)
print(f"自转周期 {T_rot/3600:.0f} h, 角速度 ω = {omega:.4e} rad/s")
print(f"离心/重力比 q = ω²R/g = {q:.5f}")
print(f"均匀密度扁率 f = (5/4)q = {f_uni:.5f}  → 赤道隆起 {f_uni*R/1000:.0f} km")
print(f"分层(地球型)扁率 f ≈ {f_str:.5f}  → 赤道隆起 {f_str*R/1000:.0f} km")
print(f"  → 赤道隆起约 {f_str*R/1000:.0f}–{f_uni*R/1000:.0f} km,赤道半径比极半径大约 {f_str*100:.2f}–{f_uni*100:.2f}%")
print(f"  地球实测:赤道隆起 21.4 km、扁率 1/298(自转同速,但半径更大 → 隆起更大)")

# ================= 5. 地形相对起伏 =================
line()
print("5. 地形相对起伏(与地球对比)")
line()
print(f"本行星最大山脉 {h_eff/1000:.1f} km / 半径 {R/1000:.0f} km = {h_eff/R:.2e}")
print(f"地球   最高山脉 {h_everest/1000:.1f} km / 半径 {R_e/1000:.0f} km = {h_everest/R_e:.2e}")
print(f"  相对起伏之比 ≈ {(h_eff/R)/(h_everest/R_e):.2f}  → 本行星地形相对更平缓")

line()
print("结论: 山脉极限 ≈ 4–5 km,海沟极限 ≈ 5 km,水相变硬上限 ≈ 46 km,")
print("      赤道隆起 ≈ 58–74 km(行星形状,非构造起伏)。")
line()