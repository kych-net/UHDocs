#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》怪动植物 声纳模型(重建)
新大气为 He 主导, 声吸收远低于地球空气, 探测距离应显著变长。本脚本重建声纳模型:
  1) 吸收 α(f,h) = k(h)·f², 经典吸收主导(He 单原子, 无振动弛豫),
     k(h) = k0·(ρ₀/ρ(h))·(c₀/c(h))³
  2) 双程传播损失 TL2(r,f) = 40·log10 r + 2·α·r   (r 单位 m)
  3) 指向性 DI(f) = 20·log10(π·D·f/c)
  4) 探测预算: TL2 − DI ≤ B  (B = SL+TS−NL−DT)
  5) 取满足预算的最高频 f_opt(r) → 定位误差 δ(r) = r·c/(f_opt·D) (波束横向分辨率)
校准: 选 B 使巡航(20 km)实用距离 = 230 m。
只读, 不改 内容/。运行: python3 脚本/复核_声纳模型.py
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
物种 = [("He",0.004003,5,0.759),("O2",0.032000,7,0.200),("N2",0.028013,7,0.019),
        ("CO2",0.044010,7,0.010),("H2O",0.018015,8,0.010),("NH3",0.017031,8,0.001)]
比 = [x[3]/sum(x[3] for x in 物种) for x in 物种]
Mbar = sum(比[i]*物种[i][1] for i in range(len(物种)))
m = [比[i]*物种[i][1] for i in range(len(物种))]
cp = sum(m[i]/sum(m)*(物种[i][2]/2)*R/物种[i][1] for i in range(len(物种)))
Γ = g/cp
γ = cp/(cp - R/Mbar)

def 温度(T0, h):
    ht = (T0-对流层顶温)/Γ
    if h <= ht: return T0 - Γ*h
    if h <= 平流层顶高: return 对流层顶温 + (平流层顶温-对流层顶温)*(h-ht)/(平流层顶高-ht)
    if h < 中间层顶高: return 平流层顶温 + (中间层顶温-平流层顶温)*(h-平流层顶高)/(中间层顶高-平流层顶高)
    return 中间层顶温
def 压强(T0, h):
    dz = 50.0; n = max(1, math.ceil(h/dz)); dh = h/n; P = P0
    for k in range(n):
        Tm = 0.5*(温度(T0,k*dh)+温度(T0,(k+1)*dh))
        P *= math.exp(-g*Mbar/(R*Tm)*dh)
    return P
def 密度(T0, h): return 压强(T0,h)*Mbar/(R*温度(T0,h))
def 声速(T0, h): return math.sqrt(γ*R*温度(T0,h)/Mbar)

T0 = 300.0
c0 = 声速(T0, 0.0); rho0 = 密度(T0, 0.0)
k0 = 1.02e-10          # dB/m/Hz², 海平面经典吸收(Stokes-Kirchhoff 估算)
D_ap = 1.0             # m, 换能器孔径(头部碰撞空间含颈部)

def k_h(h): return k0 * (rho0/密度(T0,h)) * (c0/声速(T0,h))**3

def f_opt(r, h):
    # 使 TL2-DI 最小的频率
    return math.sqrt(5.0/(k_h(h)*r*math.log(10)))

def TL2_DI(r, h):
    f = f_opt(r, h); c = 声速(T0, h); a = k_h(h)*f*f
    return 40*math.log10(r) + 2*a*r - 20*math.log10(math.pi*D_ap*f/c)

def delta(r, h):
    f = f_opt(r, h); c = 声速(T0, h)
    return r*c/(f*D_ap)

print("="*74)
print("零、声纳模型参数")
print("="*74)
print(f"  海平面: c={c0:.1f} m/s  ρ={rho0:.4f} kg/m³  k={k0:.3e} dB/m/Hz²")
print(f"  20 km : c={声速(T0,20e3):.1f} m/s  ρ={密度(T0,20e3):.4f} kg/m³  k={k_h(20e3):.3e} dB/m/Hz² (×{k_h(20e3)/k0:.1f})")
print(f"  换能器孔径 D = {D_ap} m")

# 校准预算 B: 使巡航 230 m 处 TL2-DI 恰达预算
B = TL2_DI(230.0, 20e3)
print()
print(f"  校准: 巡航 230 m 处 TL2−DI = {B:.2f} dB  → 预算 B = {B:.2f} dB")

def r_max(h):
    lo, hi = 1.0, 2000.0
    for _ in range(200):
        mid = 0.5*(lo+hi)
        if TL2_DI(mid, h) < B: lo = mid
        else: hi = mid
    return lo

for 名, h in (("海平面", 0.0), ("巡航 20 km", 20e3)):
    rm = r_max(h)
    print(f"  {名}: 实用距离 = {rm:.0f} m  (该处 δ={delta(rm,h):.1f} m)")

print()
print("="*74)
print("一、定位误差 δ(r) 剖面")
print("="*74)
for 名, h in (("海平面", 0.0), ("巡航 20 km", 20e3)):
    print(f"\n  {名}:")
    print(f"    {'r m':>6} {'f_opt Hz':>10} {'α dB/m':>10} {'δ m':>9}")
    rm = r_max(h)
    rs = [2,4,6,8,10,15,20,30,40,60,80,100,120,150,180,200,230,260,300,340]
    rs = [r for r in rs if r <= rm]
    if not rs or rs[-1] < rm: rs.append(round(rm))
    for r in rs:
        print(f"    {r:6d} {f_opt(r,h):10.0f} {k_h(h)*f_opt(r,h)**2:10.2e} {delta(r,h):9.4f}")

print()
print("="*74)
print("二、对照旧数据(附件/模块.typ 硬编码) 巡航曲线")
print("="*74)
旧 = [(2,0.0314),(4,0.0958),(6,0.1874),(8,0.3040),(10,0.4446),(20,1.5030),(40,5.6355),(60,13.8806),(80,32.4492)]
print(f"    {'r m':>5} {'旧 δ':>9} {'新 δ':>9} {'比':>6}")
for r, o in 旧:
    nw = delta(r, 20e3)
    print(f"    {r:5d} {o:9.4f} {nw:9.4f} {nw/o:6.2f}")

print()
print("  注: 旧数据为上一版模型(未随新大气重算), 仅供形态参照。")

print()
print("="*74)
print("三、Typst 数组(可直接粘贴到 附件/模块.typ)")
print("="*74)

def typst(名, h, rs):
    rs = [r for r in rs if r <= r_max(h)]
    rm = r_max(h)
    if not rs or rs[-1] < rm:
        rs.append(round(rm))
    print(f"\n#let {名} = (")
    for i in range(0, len(rs), 5):
        chunk = rs[i:i+5]
        print("  " + " ".join(f"({r}, {delta(r,h):.4f})," for r in chunk))
    print(")")

typst("海平面声纳", 0.0, [2,4,6,8,10,12,15,20,25,30,40,50,60,80,100,120,150,180,200,230,260,300,345])
typst("巡航声纳", 20e3, [2,4,6,8,10,12,15,20,25,30,40,50,60,80,100,120,150,180,200,230])