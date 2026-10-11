#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》主行星 —— 大气是否分层 + 温度剖面复核
1) 组分分层: 均质层(湍流混合) vs 非均质层(分子扩散), 求均质层顶(homopause)
2) 温度剖面: 按设定卡九层剖面重算, 校验递减率与层界
只读, 不改 内容/。运行: python3 脚本/复核_大气分层与温度.py
"""

import math

R = 8.314462618
kB = 1.380649e-23
NA = 6.02214076e23
g = 20.0
P0 = 101300.0
T0 = 300.0

print("=" * 74)
print("一、温度剖面")
print("=" * 74)

T_EXO = 1000.0     # 热层外逸温度假设(未给, 取地球量级)
H_TH = 50.0        # 热层升温标高假设 km

def T_atm(h):
    if h <= 9.3:
        return T0 - 9.27 * h
    if h <= 47.0:
        return 216.65 + (h - 9.3) / (47.0 - 9.3) * (270.0 - 216.65)
    if h <= 85.0:
        return 270.0 + (h - 47.0) / (85.0 - 47.0) * (183.0 - 270.0)
    return 183.0 + (T_EXO - 183.0) * (1.0 - math.exp(-(h - 85.0) / H_TH))

def lapse(h, dh=0.5):
    return (T_atm(h + dh) - T_atm(h - dh)) / (2 * dh)  # K/km

print("层界温度:")
for name, h in [("对流层顶", 9.0), ("对流层顶(设定9.3)", 9.3),
                ("平流层顶", 47.0), ("中间层顶", 85.0)]:
    print(f"  {name:16s} h={h:5.1f} km  T={T_atm(h):6.1f} K")

print()
print("递减率对照 (Γ_干绝热 = g/cp = 9.27 K/km):")
print(f"  对流层  dT/dz = {lapse(4.0):+6.2f} K/km  (干绝热, 但含1%水汽应为湿绝热, 更小)")
print(f"  平流层  dT/dz = {lapse(30.0):+6.2f} K/km  (O₂/O₃ 光化学加热, 升温)")
print(f"  中间层  dT/dz = {lapse(65.0):+6.2f} K/km  (CO₂ 15μm 辐射冷却, 降温)")
print(f"  地球对照: 对流-6.5 / 平流+2.7 / 中间-2.6 K/km")

# 对流层顶: Γ=9.27 恒定下 T=216.65K 的高度
h_trop = (T0 - 216.65) / 9.27
print(f"  注: Γ=9.27 恒定下 T=216.65K 在 {h_trop:.2f} km, 非设定的 9.3 km")
print(f"      9.3 km 处实为 {T_atm(9.3):.1f} K (与平流层起点 216.65K 有 {216.65-T_atm(9.3):.1f}K 跳变)")

def P_atm(h):
    return P0 * math.exp(-h / 11.76)

print()
print("压强/密度/声速:")
gamma = 1.570
Rspec = 784.0
for h in (0, 9.3, 20, 40, 47, 85, 90, 100, 120, 140, 160):
    a = math.sqrt(gamma * Rspec * T_atm(h))
    print(f"  h={h:5.1f} km  T={T_atm(h):6.1f} K  P={P_atm(h):10.3g} Pa  "
          f"ρ={P_atm(h)*0.010605/(R*T_atm(h)):.3e} kg/m³  a={a:6.1f} m/s")

print()
print("=" * 74)
print("二、组分分层 —— 均质层顶(homopause)")
print("=" * 74)

# 各组分自身标高 H_i = R·T/(M_i·g)
comp = {"He": 0.004, "O2": 0.032, "N2": 0.028, "CO2": 0.044, "H2O": 0.018, "NH3": 0.017}
Mbar = 0.010605
print("海平面(300K)各组分标高  [混合标高 H_mix=11.76 km]:")
for k, M in comp.items():
    Hi = R * T0 / (M * g) / 1000.0
    print(f"  {k:4s} M={M*1000:5.1f} g/mol  H={Hi:6.2f} km   (H_i/H_mix={Hi/11.76:.2f})")
print("  → He 标高 31 km、O₂ 仅 3.9 km, 相差 8 倍: 分子扩散会把 He 顶到高空、重气体压到底")

# 海平面二元扩散系数 (Chapman-Enskog)
def D_sealevel(sigma1, sigma2, M1, M2, T=300.0, P=101300.0):
    mu = (M1 * M2) / (M1 + M2)                    # kg
    s12 = (sigma1 + sigma2) / 2.0
    num = (3.0 / 16.0) * math.sqrt(2 * math.pi * kB**3 * T**3 / mu)
    den = P * math.pi * s12**2 * 1.1              # Ω_D ≈ 1.1
    return num / den

D_He_He = D_sealevel(2.55e-10, 2.55e-10, 4*1.6605e-27, 4*1.6605e-27)
D_He_O2 = D_sealevel(2.55e-10, 3.47e-10, 4*1.6605e-27, 32*1.6605e-27)
print()
print(f"海平面扩散系数 D(He-He)={D_He_He:.2e}  D(He-O₂)={D_He_O2:.2e} m²/s")

D0 = D_He_He    # 用 He 自扩散作代表
def D_He(h):
    return D0 * (T_atm(h) / T0) ** 1.75 * (P0 / P_atm(h))

print()
print("分子扩散系数随高度 (∝ T^1.75 / P):")
for h in (50, 70, 85, 90, 100, 110, 120, 130, 140, 150, 160, 180):
    print(f"  h={h:5.1f} km  T={T_atm(h):6.1f} K  D_He={D_He(h):9.3e} m²/s")

print()
print("均质层顶 = 涡扩散系数 K_zz 降到与 D_He 相等的高度:")
print("(K_zz 取决于湍流/重力波, 无法第一性原理定值, 给几种情形)")
for K in (0.05, 0.5, 5.0, 60.0):
    # 求 D_He(h)=K
    lo, hi = 40.0, 400.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if D_He(mid) < K:
            lo = mid
        else:
            hi = mid
    print(f"  若 K_zz={K:6.2f} m²/s (该处) → 均质层顶 ≈ {lo:6.1f} km")
print()
print("  标定: 地球均质层顶 ~100 km, 对应 K_zz ≈ 60 m²/s")
print("  本行星若湍流强度与地球同级 → 均质层顶 ≈ 140-150 km, 远高于设定的 90 km")
print("  要均质层顶落在 90 km, 需该处 K_zz ≈ 0.05 m²/s, 比地球弱约 1000 倍")

print()
print("=" * 74)
print("三、平衡组分剖面 (混合 vs 扩散)")
print("=" * 74)

def H_i(k, h):
    return R * T_atm(h) / (comp[k] * g)

# 扩散平衡: n_i(h) ∝ n_i0·(T0/T)·exp(-∫dh/H_i)
# 混合: n_i(h) ∝ n_i0·(T0/T)·exp(-∫dh/H_mix), 摩尔分数不变
x0 = {"He": 0.759, "O2": 0.200, "N2": 0.019, "CO2": 0.010, "H2O": 0.010, "NH3": 0.001}

def profile_diffusive(h):
    n = {}
    for k in comp:
        s = 0.0
        dz = 0.1
        z = 0.0
        while z < h:
            s += dz / (H_i(k, z) / 1000.0)
            z += dz
        n[k] = x0[k] * (T0 / T_atm(h)) * math.exp(-s)
    return n

print(f"{'h km':>6} {'He%':>8} {'O₂%':>8} {'N₂%':>8} {'CO₂%':>8}  (扩散平衡, K→0)")
for h in (0, 50, 85, 90, 100, 110, 120, 130, 140, 150):
    n = profile_diffusive(h)
    tot = sum(n.values())
    print(f"{h:6.0f} {n['He']/tot*100:8.2f} {n['O2']/tot*100:8.2f} "
          f"{n['N2']/tot*100:8.2f} {n['CO2']/tot*100:8.2f}")
print("  (混合情形: 各高度恒为 He75.9 / O₂20 / ... 即设定卡的低空描述)")

# 外逸层底(逃逸基准): 平均自由程 = 标高
print()
print("外逸层底估计 (λ_mfp = H):")
def exobase():
    for h in range(100, 600):
        T = T_atm(h)
        n = P_atm(h) / (kB * T)
        lam = 1.0 / (math.sqrt(2) * math.pi * (3e-10)**2 * n)
        H = R * T / (0.004 * g)   # 高空 He 主导
        if lam >= H:
            return h
    return None
he = exobase()
print(f"  外逸层底 ≈ {he} km  (设定卡未给此高度)")

# 逃逸判据
GM = g * (1.5e7)**2
vesc = math.sqrt(2 * GM / 1.5e7)
for T in (1000,):
    lam_He = GM * 4 * 1.6605e-27 / (kB * T * 1.5e7)
    print(f"  He 逃逸参数 λ=GM·m/(kT·R) = {lam_He:.0f} @T={T}K  (≫1 → 基本不逃逸, 需源补给)")