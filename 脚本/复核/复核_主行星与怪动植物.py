#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》终版设定卡 数值复核
—— 独立重算大气热力学、声速剖面、飞行性能，与设定卡逐项对比。
只读,不改 内容/。运行: python3 脚本/复核_主行星与怪动植物.py
"""

import math

R = 8.314462618          # J/(mol·K)
g = 20.0                 # m/s^2   设定
P0 = 101300.0            # Pa      设定
T0 = 300.0               # K       设定(海平面)

def mark(ok):
    return "✓" if ok else "✗"

def rel(a, b):
    return abs(a - b) / abs(b) * 100.0

print("=" * 72)
print("一、大气成分与热力学")
print("=" * 72)

# 组分: (摩尔分数, 摩尔质量 kg/mol, 质量定压比热 J/kg/K, γ)
comp = {
    "He":  (0.759, 0.004, 5193.0, 1.667),
    "O2":  (0.200, 0.032,  918.0, 1.395),
    "N2":  (0.019, 0.028, 1040.0, 1.400),
    "CO2": (0.010, 0.044,  844.0, 1.289),
    "H2O": (0.010, 0.018, 1900.0, 1.330),
    "NH3": (0.001, 0.017, 2190.0, 1.310),
}
xs = sum(v[0] for v in comp.values())
print(f"摩尔分数合计 = {xs:.4f}  (设定隐含 1.000)")

Mbar = sum(x * M for x, M, _, _ in comp.values())      # kg/mol
print(f"平均摩尔质量 M̄ = {Mbar*1000:.3f} g/mol   [设定 10.61]  {mark(abs(Mbar*1000-10.61)<0.05)}")

w = {k: x * M / Mbar for k, (x, M, _, _) in comp.items()}
print("质量分数:", {k: round(v, 4) for k, v in w.items()})

cp = sum(w[k] * comp[k][2] for k in comp)
Rspec = R / Mbar
cv = cp - Rspec
gamma = cp / cv
Gamma = g / cp * 1000.0        # K/km
print(f"混合定压比热 cp = {cp:.1f} J/(kg·K)")
print(f"比气体常数 Rspec = {Rspec:.1f} J/(kg·K)")
print(f"比热比 γ = {gamma:.4f}   [设定 1.570]  {mark(abs(gamma-1.570)<0.005)}")
print(f"干绝热递减率 Γ = g/cp = {Gamma:.3f} K/km   [设定 9.27]  {mark(abs(Gamma-9.27)<0.1)}")

H0 = Rspec * T0 / g / 1000.0   # km
print(f"标高 H₀ = Rspec·T₀/g = {H0:.3f} km   [设定 11.7]  {mark(abs(H0-11.7)<0.1)}")

rho0 = P0 * Mbar / (R * T0)
print(f"海平面密度 ρ₀ = P₀·M̄/(R·T₀) = {rho0:.4f} kg/m³   [设定 0.431]  {mark(abs(rho0-0.431)<0.005)}")

a0 = math.sqrt(gamma * Rspec * T0)
print(f"海平面声速 a₀ = √(γ·Rspec·T₀) = {a0:.1f} m/s   [设定 607]  {mark(abs(a0-607)<4)}")

# 柱质量与柱热惯量
col_mass = P0 / g
col_heat = col_mass * cp
earth_col_mass = 101300 / 9.81
earth_col_heat = earth_col_mass * 1004.0
print(f"柱质量 = P₀/g = {col_mass:.0f} kg/m²   (地球 {earth_col_mass:.0f})")
print(f"柱热惯量比 = {col_heat/earth_col_heat:.3f}   [设定 ≈地球]  {mark(abs(col_heat/earth_col_heat-1)<0.15)}")

# 地转风: 同气压梯度下 u ∝ 1/ρ
print(f"地转风比 = ρ_earth/ρ₀ = {1.225/rho0:.2f}   [设定 ×2.8]  {mark(abs(1.225/rho0-2.8)<0.15)}")

print()
print("=" * 72)
print("二、温度/压强/声速剖面与层界")
print("=" * 72)

def T(h):  # 设定卡分段
    if h <= 9.3:
        return T0 - 9.27 * h
    if h <= 47.0:
        return 216.65 + (h - 9.3) / (47.0 - 9.3) * (270.0 - 216.65)
    if h <= 85.0:
        return 270.0 + (h - 47.0) / (85.0 - 47.0) * (183.0 - 270.0)
    return 183.0

def P(h):
    return P0 * math.exp(-h / H0)

def rho(h):
    return rho0 * math.exp(-h / H0)

def a(h):
    return math.sqrt(gamma * Rspec * T(h))

h_trop = (T0 - 216.65) / 9.27
print(f"若 Γ=9.27 恒定, T=216.65 K 对应高度 = {h_trop:.3f} km   [设定 9.3]  {mark(abs(h_trop-9.3)<0.15)}")
print(f"  → 反过来, 9.3 km 处 T = {T(9.3):.2f} K   (设定层界标称 216.65 K)")

for h in (9.3, 20.0, 40.0, 47.0, 48.0, 85.0):
    print(f"h={h:5.1f} km: T={T(h):6.1f} K  P={P(h):8.1f} Pa  ρ={rho(h):.5f} kg/m³  a={a(h):6.1f} m/s")

# O2 分压 (全程混合 → O2 摩尔分数恒 20%)
xO2 = 0.20
for h in (20.0,):
    pO2 = P(h) * xO2
    print(f"h={h:.0f} km O₂分压(全程混合, x=20%) = {pO2/1000:.2f} kPa   [设定 2.3]  {mark(abs(pO2/1000-2.3)<0.15)}")
    need_x = 2300.0 / P(h)
    print(f"  要得 2.3 kPa, 需 O₂ 摩尔分数 = {need_x*100:.1f}% (与'全程混合'矛盾)")
    h_eq = H0 * math.log(P0 / (2300.0 / xO2))
    print(f"  或 O₂=20% 的 2.3 kPa 对应高度 = {h_eq:.1f} km")

# 可降水量 (H2O 自身标高, 忽略冷阱)
M_H2O = 0.018
H_H2O = R * T0 / (M_H2O * g) / 1000.0
rho_v0 = 0.01 * P0 * M_H2O / (R * T0)
PW = rho_v0 * H_H2O * 1000.0
print(f"H₂O 自身标高 = {H_H2O:.2f} km, 表面 ρv = {rho_v0*1000:.3f} g/m³")
print(f"可降水量(无冷阱) = {PW:.1f} mm   [设定 51]  {mark(abs(PW-51)<6)}  (冷阱会显著降低, 见报告)")

# 声速极小(声道)
hs = [i * 0.5 for i in range(0, 181)]
amin = []
for i in range(1, len(hs) - 1):
    if a(hs[i]) < a(hs[i - 1]) and a(hs[i]) < a(hs[i + 1]):
        amin.append(round(hs[i], 1))
print(f"声速局部极小(声道)高度 ≈ {amin} km   [设定 9 / 85]")

# 变后掠马赫数对照
print()
print("马赫数对照 (按上面声速):")
print(f"  20 km: a={a(20):.0f} m/s → 465 m/s = M{465/a(20):.2f}   [设定 'M0.9 封顶']")
print(f"  40 km: a={a(40):.0f} m/s → 570 m/s = M{570/a(40):.2f}   [设定 'M1.05–1.1']")
print(f"         M1.05 = {a(40)*1.05:.0f} m/s,  M1.10 = {a(40)*1.10:.0f} m/s")

# 碳酸盐雪 deck 分压
h_deck = 7.2
print()
print(f"碳酸盐雪 deck @ {h_deck} km: T={T(h_deck):.1f} K, P={P(h_deck):.0f} Pa")
print(f"  p(NH₃)={P(h_deck)*0.001:.2f} Pa,  p(CO₂)={P(h_deck)*0.01:.1f} Pa")

print()
print("=" * 72)
print("三、怪动植物 飞行性能")
print("=" * 72)

m_body = 20.0
b = 10.0          # 翼展 m
AR = 40.0
S = b * b / AR
print(f"翼面积 S = b²/AR = {S:.2f} m² (翼展 {b} m, AR {AR})")
LD = 68.0

def cruise(h, m_total, V, eta, label):
    L = m_total * g
    CL = L / (0.5 * rho(h) * V * V * S)
    D = L / LD
    Pmech = D * V
    Pelec = Pmech / eta
    CDi = CL * CL / (math.pi * AR * 0.9)
    CD = CL / LD
    CD0 = CD - CDi
    print(f"{label}: m={m_total:.0f} kg → L={L:.0f} N")
    print(f"  C_L = {CL:.3f}  (诱导 C_Di={CDi:.4f}, 寄生 C_D0={CD0:.4f})")
    print(f"  阻力 D = L/(L/D) = {D:.2f} N")
    print(f"  功率 P = D·V/η = {Pmech:.0f} W / {eta} = {Pelec/1000:.3f} kW")
    return Pelec / 1000.0

P20 = cruise(20.0, 45.0, 83.0, 0.95, "20 km 满载 45 kg")
print(f"  [设定 0.92 kW]  {mark(abs(P20-0.92)<0.05)}   (差 {rel(P20,0.92):.0f}%)")
print(f"  若 P=0.92 kW 反推所需 L/D = {45*g*83/(0.92*1000*0.95):.1f}")
print()
P40 = cruise(40.0, 20.0, 182.0, 1.0, "40 km 空载 20 kg")
print(f"  [设定 1.07 kW]  {mark(abs(P40-1.07)<0.05)}   (差 {rel(P40,1.07):.0f}%)")

print()
print("航程核对 (航程 = V × 续航):")
r20 = 83.0 * 23.0 * 3.6      # m/s × h × 3.6 = km
r40 = 182.0 * 21.0 * 3.6
print(f"  20 km: 83 m/s × 23 h = {r20:.0f} km   [设定 6900]  {mark(abs(r20-6900)<150)}")
print(f"  40 km: 182 m/s × 21 h = {r40:.0f} km   [设定 13600]  {mark(abs(r40-13600)<300)}")

print()
print("隐含储能 (P×续航) — 两点应一致:")
e20 = 0.92 * 23.0
e40 = 1.07 * 21.0
print(f"  20 km: 0.92 kW × 23 h = {e20:.1f} kWh = {e20*3.6:.0f} MJ")
print(f"  40 km: 1.07 kW × 21 h = {e40:.1f} kWh = {e40*3.6:.0f} MJ")
print(f"  差异 {rel(e20,e40):.1f}%")
e20b = P20 * 23.0
print(f"  若 20 km 用力学功率 {P20:.2f} kW: 储能 = {e20b*3.6:.0f} MJ (与 40 km 的 {e40*3.6:.0f} MJ 不一致)")

print()
print("每米能耗 (越低越省):")
print(f"  20 km: {0.92*1000/83:.2f} J/m   vs   40 km: {1.07*1000/182:.2f} J/m  → 40 km 更省 ✓")

print()
print("=" * 72)
print("四、其它量级")
print("=" * 72)
print(f"火焰: 体积热容 ρ₀·cp = {rho0*cp:.0f} J/(m³·K)   vs 地球空气 {1.225*1005:.0f}  → 低 {100*(1-1.225*1005/(rho0*cp)):.0f}%")
print(f"起飞滑翔: 45 m 落差 × L/D 68 = {45*68:.0f} m 水平距离 (逆风 10 m/s 另计)")