#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》怪动植物 新设定卡 数值复核
按 附件/模块.typ 的精确模型(低空均匀成分 + 三层温度 + 积分压强)复算飞行相关量,
对照新设定卡:
  20 km 满载 45 kg: V=83, η=0.95, P=0.92 kW, 23 h, 6900 km
  40 km 空载:       V=182, η=1.0, P=1.07 kW, 21 h, 13600 km
  L/D=68, 翼展 10 m, AR 40, 升限 ~48 km, 20 km O₂ 分压 2.3 kPa
只读, 不改 内容/。运行: python3 脚本/复核_怪动植物新设定.py
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

def 顶高(T0): return (T0-对流层顶温)/Γ
def 温度(T0, h):
    ht = 顶高(T0)
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
print("="*74)
print("零、大气基本量(赤道 300 K)")
print("="*74)
print(f"  M̄={Mbar*1000:.3f} g/mol  c_p={cp:.1f}  Γ={Γ*1000:.3f} K/km  γ={γ:.4f}")
print(f"  ρ₀={密度(T0,0):.4f} kg/m³  a₀={声速(T0,0):.1f} m/s")

print()
print("="*74)
print("一、高度剖面")
print("="*74)
print(f"  {'h km':>5} {'T K':>7} {'P kPa':>8} {'ρ kg/m³':>10} {'a m/s':>7} {'ρ₀/ρ':>7}")
for hkm in (0, 20, 40, 48, 60):
    h = hkm*1000
    print(f"  {hkm:5d} {温度(T0,h):7.1f} {压强(T0,h)/1000:8.2f} {密度(T0,h):10.4e} {声速(T0,h):7.1f} {密度(T0,0)/密度(T0,h):7.1f}")

print()
print("="*74)
print("二、巡航点功耗 (D=L/(L/D), P=D·V/η)")
print("="*74)
b = 10.0; AR = 40.0; S = b*b/AR; LD = 68.0
print(f"  翼面积 S = b²/AR = {S:.2f} m² (翼展 {b} m, AR {AR}), L/D = {LD}")
print()
for label, hkm, mtot, V, eta, card in (
    ("20 km 满载 45 kg", 20, 45.0, 83.0, 0.95, 0.92),
    ("40 km 空载 20 kg", 40, 20.0, 182.0, 1.0, 1.07),
):
    h = hkm*1000
    L = mtot*g
    CL = L/(0.5*密度(T0,h)*V*V*S)
    D = L/LD
    Pmech = D*V
    Pelec = Pmech/eta/1000
    print(f"  {label}: L={L:.0f} N  C_L={CL:.3f}")
    print(f"    D={D:.2f} N  P_mech={Pmech:.0f} W  P_elec={Pelec:.3f} kW   [卡 {card}]  "
          f"{'✓' if abs(Pelec-card)<0.05 else '✗ 差 %.0f%%'%(abs(Pelec-card)/card*100)}")
    print(f"    若按卡 P={card} kW 反推所需 L/D = {L*V/(card*1000*eta):.1f}")

print()
print("="*74)
print("三、储能与续航一致性 (同一储能, 两点应相等)")
print("="*74)
for label, P, t in (("20 km", 0.92, 23.0), ("40 km", 1.07, 21.0)):
    print(f"  {label}: P×t = {P*t:.2f} kWh = {P*t*3.6:.1f} MJ")
print(f"  差 {(abs(0.92*23-1.07*21)/(1.07*21)*100):.1f}%")
print("  能量脂 2 kg × 50 MJ/kg = 100 MJ (满储上限)")

print()
print("="*74)
print("四、航程核对 (航程 = V × 续航 × 3.6)")
print("="*74)
print(f"  20 km: {83*23*3.6:.0f} km  [卡 6900]")
print(f"  40 km: {182*21*3.6:.0f} km  [卡 13600]")

print()
print("="*74)
print("五、马赫与升限")
print("="*74)
for hkm, V in ((20, 465.0), (40, 570.0)):
    a = 声速(T0, hkm*1000)
    print(f"  {hkm} km: a={a:.0f} m/s, V={V:.0f} m/s → M{V/a:.3f}")
print(f"  升限 ~48 km: T={温度(T0,48e3):.1f} K, ρ={密度(T0,48e3):.4e} kg/m³ "
      f"(海平面 1/{密度(T0,0)/密度(T0,48e3):.0f})")

print()
print("="*74)
print("六、20 km O₂ 分压 (全程混合 x=20%)")
print("="*74)
pO2 = 压强(T0, 20e3)*比[1]
print(f"  P(20km)={压强(T0,20e3)/1000:.2f} kPa  → p(O₂)={pO2/1000:.2f} kPa  [卡 2.3]  "
      f"{'✓' if abs(pO2/1000-2.3)<0.2 else '✗'}")