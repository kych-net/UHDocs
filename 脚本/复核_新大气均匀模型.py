#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复现改版后 附件/模块.typ 的解析大气模型(低空均匀成分 + 三层温度 + 有界中间层)。
成分含 NH₃ 0.1%。用于生成 内容/地理/主行星.typ 的表格与图表数值。
只读, 不改 内容/。运行: python3 脚本/复核_新大气均匀模型.py
"""

import math

g = 20.0
R = 8.314462618
P0 = 1.013e5
对流层顶温 = 216.65
平流层顶温 = 270.0
平流层顶高 = 47.0e3
中间层顶温 = 183.0
中间层顶高 = 85.0e3

# (名, 质量 kg/mol, 自由度 f, 海平面体积比)
物种 = [
    ("He",  0.004003, 5, 0.759),
    ("O2",  0.032000, 7, 0.200),
    ("N2",  0.028013, 7, 0.019),
    ("CO2", 0.044010, 7, 0.010),
    ("H2O", 0.018015, 8, 0.010),
    ("NH3", 0.017031, 8, 0.001),
]
N = len(物种)
和 = sum(x[3] for x in 物种)
比 = [x[3]/和 for x in 物种]

Mbar = sum(比[i]*物种[i][1] for i in range(N))
m = [比[i]*物种[i][1] for i in range(N)]
mtot = sum(m)
cp = sum(m[i]/mtot * (物种[i][2]/2) * R / 物种[i][1] for i in range(N))
Γ = g/cp
γ = cp/(cp - R/Mbar)

赤道参数 = dict(海平面温=300.0)
极点参数 = dict(海平面温=240.0)

def 顶高(区):
    return (区["海平面温"] - 对流层顶温)/Γ

def 温度(区, h):
    ht = 顶高(区)
    if h <= ht:
        return 区["海平面温"] - Γ*h
    if h <= 平流层顶高:
        return 对流层顶温 + (平流层顶温-对流层顶温)*(h-ht)/(平流层顶高-ht)
    if h < 中间层顶高:
        return 平流层顶温 + (中间层顶温-平流层顶温)*(h-平流层顶高)/(中间层顶高-平流层顶高)
    return 中间层顶温

def 压强(区, h):
    dz = 50.0
    n = max(1, math.ceil(h/dz))
    dh = h/n
    P = P0
    for k in range(n):
        z = k*dh
        Tm = 0.5*(温度(区, z)+温度(区, z+dh))
        P *= math.exp(-g*Mbar/(R*Tm)*dh)
    return P

def 密度(区, h):
    return 压强(区, h)*Mbar/(R*温度(区, h))

def 声速(区, h):
    return math.sqrt(γ*R*温度(区, h)/Mbar)

print("="*78)
print("一、常量(含 NH₃ 0.1%)")
print("="*78)
print("  归一化后: " + ", ".join(f"{物种[i][0]}={比[i]*100:.3f}%" for i in range(N)))
print(f"  M̄ = {Mbar:.6f} kg/mol = {Mbar*1000:.3f} g/mol")
print(f"  c_p = {cp:.1f} J/(kg·K)")
print(f"  Γ = g/c_p = {Γ*1000:.3f} K/km")
print(f"  γ = {γ:.4f}")
print(f"  比气体常数 R_spec = {R/Mbar:.1f} J/(kg·K), 标高 H(300K) = {R*300/(Mbar*g)/1000:.2f} km")
for 名, 区 in (("赤道", 赤道参数), ("极点", 极点参数)):
    ht = 顶高(区)
    print(f"  {名}: 海平面 {区['海平面温']:.0f} K, 对流层顶 {ht/1000:.2f} km")
print(f"  平流层: 对流层顶 → 47 km, 216.65 → 270 K")
print(f"    赤道升率 = {(平流层顶温-对流层顶温)/(平流层顶高-顶高(赤道参数))*1000:.3f} K/km")
print(f"    极点升率 = {(平流层顶温-对流层顶温)/(平流层顶高-顶高(极点参数))*1000:.3f} K/km")
print(f"  中间层: 47 → 85 km, 270 → 183 K, 降率 = {(平流层顶温-中间层顶温)/(中间层顶高-平流层顶高)*1000:.3f} K/km")

表高 = (0, 1, 2, 3, 5, 8.5, 10, 12, 15, 17, 20, 24, 30, 35, 40, 45, 50, 55, 60)
for 名, 区 in (("赤道", 赤道参数), ("极点", 极点参数)):
    print()
    print("="*78)
    print(f"二、{名}剖面 (对流层顶 {顶高(区)/1000:.2f} km)")
    print("="*78)
    print(f"  {'h km':>6} {'T K':>7} {'ρ kg/m³':>10} {'a m/s':>7} {'He%':>6} {'O₂%':>6} {'N₂%':>6}")
    hs = sorted(set(list(表高) + [顶高(区)/1000, 47.0]))
    for hkm in hs:
        h = hkm*1000
        print(f"  {hkm:6.2f} {温度(区,h):7.1f} {密度(区,h):10.3e} {声速(区,h):7.1f} "
              f"{比[0]*100:6.1f} {比[1]*100:6.1f} {比[2]*100:6.1f}")

print()
print("="*78)
print("三、图表量程(剖面图 0–30 km)")
print("="*78)
for 名, 区 in (("赤道", 赤道参数), ("极点", 极点参数)):
    Ts = [温度(区, h*1000) for h in range(0, 31)]
    ρs = [密度(区, h*1000) for h in range(0, 31)]
    as_ = [声速(区, h*1000) for h in range(0, 31)]
    print(f"  {名}: T {min(Ts):.1f}–{max(Ts):.1f} K, ρ {min(ρs):.3e}–{max(ρs):.3e}, a {min(as_):.1f}–{max(as_):.1f} m/s")

print()
print("="*78)
print("四、关键点")
print("="*78)
ρ0e = 密度(赤道参数, 0); ρ0p = 密度(极点参数, 0)
print(f"  海平面密度: 赤道 {ρ0e:.4f}, 极点 {ρ0p:.4f} kg/m³")
print(f"  海平面声速: 赤道 {声速(赤道参数,0):.1f}, 极点 {声速(极点参数,0):.1f} m/s")
for hkm in (20, 30, 47, 60, 85):
    print(f"  {hkm} km 赤道: T={温度(赤道参数,hkm*1000):.1f} K, ρ={密度(赤道参数,hkm*1000):.3e}, a={声速(赤道参数,hkm*1000):.1f}")
print(f"  20 km 密度比(赤道) = 海平面的 1/{ρ0e/密度(赤道参数,20e3):.1f}")