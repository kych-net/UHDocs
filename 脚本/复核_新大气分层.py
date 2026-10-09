#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新大气(He 主导)的分层判定:低空湍流混合,高空分子扩散。
均质层顶(homopause) = 涡扩散系数 K_zz 与 He 分子扩散系数 D_He 相等的高度。
只读, 不改 内容/。运行: python3 脚本/复核_新大气分层.py
"""

import math

R = 8.314462618
kB = 1.380649e-23
g = 20.0
P0 = 1.013e5
Mbar = 0.010605          # 新大气平均摩尔质量 kg/mol
M_He = 0.004003
T0 = 300.0

# —— 温度剖面(均匀成分, Γ=g/c_p) ——
cp = 2151.4
Γ = g/cp
h_trop = (T0 - 216.65) / Γ
等温顶, 平流层顶, 升率, 降率 = 17.2e3, 24.0e3, 2.3529e-3, 2.5e-3
中间层顶温 = 183.0       # 加中间层顶(否则线性降温到 117 km 归零)

def T_at(h):
    if h <= h_trop:
        return T0 - Γ*h
    if h <= 等温顶:
        return 216.65
    if h <= 平流层顶:
        return 216.65 + 升率*(h-等温顶)
    return max(232.65 - 降率*(h-平流层顶), 中间层顶温)

h_meso = 平流层顶 + (232.65-中间层顶温)/降率
print(f"  中间层顶(183K)位于 h={h_meso/1000:.1f} km")

print("="*74)
print("一、温度剖面(新大气, 均匀成分)")
print("="*74)
print(f"  c_p={cp:.0f} J/(kg·K), Γ=g/c_p={Γ*1000:.2f} K/km")
print(f"  赤道对流层顶 h={h_trop/1000:.2f} km (300K → 216.65K)")
print(f"  极点(240K)对流层顶 h={(240-216.65)/Γ/1000:.2f} km")

# —— 压强剖面(均匀成分) ——
def P_at(h):
    P = P0; z = 0.0; dz = 50.0
    while z < h:
        Tm = 0.5*(T_at(z)+T_at(z+dz))
        P *= math.exp(-g*Mbar/(R*Tm)*dz)
        z += dz
    return P

print()
print("="*74)
print("二、压强与分子扩散系数 D_He")
print("="*74)

# 海平面 He-He 扩散系数 (Chapman-Enskog)
mu = M_He/2/6.02214076e23 * 1e3   # 约化质量 kg
σ = 2.55e-10
def D_ce(T, P):
    num = (3/16)*math.sqrt(2*math.pi*kB**3*T**3/mu)
    den = P*math.pi*σ**2*1.1
    return num/den
D0 = D_ce(300.0, P0)
print(f"  海平面 D_He(He-He) = {D0:.3e} m²/s")
print(f"  {'h km':>6} {'T K':>7} {'P Pa':>11} {'D_He m²/s':>11}")
for hkm in (30, 50, 70, 85, 90, 100, 110, 120, 130, 140, 150, 160, 180, 200):
    h = hkm*1000
    P = P_at(h)
    D = D0*(T_at(h)/300)**1.75*(P0/P)
    print(f"  {hkm:6.0f} {T_at(h):7.1f} {P:11.3e} {D:11.3e}")

print()
print("="*74)
print("三、均质层顶(homopause): D_He = K_zz")
print("="*74)
def homopause(K):
    lo, hi = 20e3, 400e3
    for _ in range(200):
        mid = (lo+hi)/2
        D = D0*(T_at(mid)/300)**1.75*(P0/P_at(mid))
        if D > K: hi = mid
        else: lo = mid
    return lo

for K in (0.05, 0.5, 5.0, 60.0):
    print(f"  K_zz={K:6.2f} m²/s → 均质层顶 ≈ {homopause(K)/1000:6.1f} km")
print("  地球标定: 均质层顶 ~100 km 对应 K_zz≈60 m²/s")
print(f"  新大气若湍流与地球同级(K=60): 均质层顶 ≈ {homopause(60)/1000:.0f} km")

print()
print("="*74)
print("四、成分剖面(均质层顶以下均匀, 以上扩散分离)")
print("="*74)
物种 = [("He",0.004003,0.76),("O2",0.032,0.20),("N2",0.028013,0.019),("CO2",0.04401,0.010),("H2O",0.018015,0.010)]

def 扩散分离(h_homo, h):
    # 从均质层顶起, 各成分按自身标高衰减
    Ψ = 0.0; z = h_homo; dz = 100.0
    while z < h:
        Tm = 0.5*(T_at(z)+T_at(z+dz))
        Ψ += g/(R*Tm)*dz
        z += dz
    w = [x*math.exp(-M*Ψ) for _,M,x in 物种]
    s = sum(w)
    return [v/s for v in w]

for K in (0.5, 60.0):
    hh = homopause(K)
    print(f"\n  [K_zz={K} → 均质层顶 {hh/1000:.0f} km]")
    print(f"  {'h km':>6} {'He%':>7} {'O₂%':>7} {'N₂%':>7} {'CO₂%':>7}")
    for hkm in (0, 30, 60, 85, 90, 100, 120, 150, 200):
        h = hkm*1000
        if h <= hh:
            b = [x for _,_,x in 物种]
        else:
            b = 扩散分离(hh, h)
        print(f"  {hkm:6.0f} {b[0]*100:7.2f} {b[1]*100:7.2f} {b[2]*100:7.2f} {b[3]*100:7.2f}")

print()
print("="*74)
print("五、结论")
print("="*74)
print(f"  新大气 He 占 76%, 海平面标高 {R*300/(Mbar*g)/1000:.2f} km。")
print( "  低空湍流混合主导: 若湍流与地球同级, 均质层顶 ≈ 130 km 以上,")
print( "  文档覆盖的 0–60 km 内成分基本不变(He 76%), 不存在 15 km He>99%。")
print( "  只有均质层顶以上(>130 km)才发生 He 富集。")