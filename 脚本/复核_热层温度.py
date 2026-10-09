#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》主行星 —— 热层段温度
热层由热传导平衡控制: 常数向下热流 q0 满足 κ dT/dz = -q0, κ(T)=κ0·T^0.7
  → T_exo - T_meso = q0 · H_meso / (κ0 · T_meso^0.7)      (H 必须用 m)
  Bates 剖面: T(z) = T_exo - (T_exo - T_meso)·exp(-s), s=∫dz/H
大气成分(He 主导新方案): He 76% / O2 20% / N2 1.9% / CO2 1% / H2O 1%
  → M̄ ≈ 0.0106 kg/mol; 热层按此成分均匀处理(不再假设 He>99% 分离)。
只读, 不改 内容/。运行: python3 脚本/复核_热层温度.py
"""

import math

R = 8.314462618
kB = 1.380649e-23

# —— 行星参数 ——
g = 20.0
P0 = 101300.0
T0 = 300.0
Z_MESO = 85.0e3        # 中间层顶(热层底) m
T_MESO = 183.0         # 中间层顶温度 K

# —— 新大气成分: (名, 摩尔质量 kg/mol, 体积比, κ@300K W/(m·K)) ——
物种 = [
    ("He",  0.004003, 0.76,  0.152),
    ("O2",  0.032000, 0.20,  0.0266),
    ("N2",  0.028013, 0.019, 0.0258),
    ("CO2", 0.044010, 0.010, 0.0166),
    ("H2O", 0.018015, 0.010, 0.0187),
]
Mbar = sum(x*M for _, M, x, _ in 物种)

def kappa_mix(T=300.0):
    """Wassiljewa 混合导热率"""
    def phi(i, j):
        if i == j:
            return 1.0
        ki, Mi = 物种[i][3], 物种[i][1]
        kj, Mj = 物种[j][3], 物种[j][1]
        return (1 + math.sqrt(ki/kj)*(Mi/Mj)**0.25)**2 / math.sqrt(8*(1+Mi/Mj))
    return sum(物种[i][2]*物种[i][3] / sum(物种[j][2]*phi(i, j) for j in range(len(物种)))
               for i in range(len(物种)))

K_MIX_300 = kappa_mix()
k0_mix = K_MIX_300 / 300**0.7

# 纯 He 参考
K_HE_300 = 0.152
k0_He = K_HE_300 / 300**0.7
K_AIR_300 = 0.0262
k0_air = K_AIR_300 / 300**0.7

def H(T, M, gg=g):
    return R * T / (M * gg)     # 标高, m

print("=" * 74)
print("一、大气成分与导热率")
print("=" * 74)
print(f"  成分: " + ", ".join(f"{n} {x*100:.1f}%" for n, _, x, _ in 物种))
print(f"  平均摩尔质量 M̄ = {Mbar:.5f} kg/mol = {Mbar*1000:.2f} g/mol")
print(f"  κ_mix(300K) = {K_MIX_300:.4f} W/(m·K)   (纯 He {K_HE_300}, 空气 {K_AIR_300})")
print(f"  κ0_mix = {k0_mix:.4e}   κ0_He = {k0_He:.4e}   κ0_air = {k0_air:.4e}")
print(f"  κ_mix/κ_air = {K_MIX_300/K_AIR_300:.2f}")

print()
print("=" * 74)
print("二、标高(热层底)")
print("=" * 74)
print(f"  行星, 新成分(M={Mbar*1000:.2f}, 183K, g=20)  H = {H(T_MESO,Mbar)/1e3:6.2f} km")
print(f"  行星, 纯 He 参考(M=4.00, 183K)             H = {H(T_MESO,0.004003)/1e3:6.2f} km")
print(f"  地球, 空气(M=28.97, 190K, g=9.81)          H = {H(190,0.02897,9.81)/1e3:6.2f} km")

print()
print("=" * 74)
print("三、外逸温度 T_exo 与热流 q0")
print("=" * 74)
print("  T_exo - T_meso = q0 · H_meso / (κ0 · T_meso^0.7)")

Te_e, Tm_e, M_air = 1000.0, 190.0, 0.02897
H_e = H(Tm_e, M_air, 9.81)
q0_earth = k0_air * Tm_e**0.7 * (Te_e - Tm_e) / H_e
print(f"\n  地球标定: T_exo=1000K → q0 = {q0_earth*1e3:.2f} mW/m²")

def T_exo(q0, M=Mbar, k0=k0_mix):
    return T_MESO + q0 * H(T_MESO, M) / (k0 * T_MESO**0.7)

print(f"\n  [新成分 M={Mbar*1000:.2f} g/mol, κ_mix]")
print(f"    {'q0 mW/m²':>10} {'T_exo K':>10}")
for q0 in (0.5e-3, 1.0e-3, 1.5e-3, 2.0e-3, q0_earth, 3.0e-3, 4.0e-3):
    print(f"    {q0*1e3:10.2f} {T_exo(q0):10.1f}")

print(f"\n  [纯 He 参考 M=4.00 g/mol, κ_He]")
print(f"    {'q0 mW/m²':>10} {'T_exo K':>10}")
for q0 in (1.0e-3, q0_earth, 3.0e-3):
    print(f"    {q0*1e3:10.2f} {T_exo(q0,0.004003,k0_He):10.1f}")

print()
print("  注意: 本行星恒星辐照度与地球相近(1360 W/m²), 取与地球同量级 q0≈2.8 mW/m²;")
print("        但 He 只吸收 λ<50 nm 的 EUV, 实际 q0 会更低, T_exo 应偏下限。")

print()
print("=" * 74)
print("四、热层温度剖面 T(z)  (Bates)")
print("=" * 74)

def bates(q0, M=Mbar, k0=k0_mix, z_top=1500e3, dz=1e3):
    Te = T_exo(q0, M, k0)
    z, T = Z_MESO, T_MESO
    prof = [(z, T)]
    while z < z_top:
        T += (Te - T) / H(T, M) * dz
        z += dz
        prof.append((z, T))
    return Te, prof

for q0 in (1.0e-3, q0_earth):
    Te, prof = bates(q0)
    print(f"\n  新成分, q0={q0*1e3:.2f} mW/m² → T_exo ≈ {Te:.0f} K")
    for zt in (85e3, 100e3, 150e3, 200e3, 300e3, 500e3, 800e3, 1200e3):
        T = min(prof, key=lambda p: abs(p[0]-zt))[1]
        print(f"    {zt/1e3:6.0f} km   T = {T:6.1f} K")

print()
print("=" * 74)
print("五、外逸层底 (平均自由程 = 标高)")
print("=" * 74)

# 热层底压强: 按文档赤道温度剖面(对流层顶1.5km@216.65, 等温到17.2km,
# 平流层到24km@232.65, 中间层 -2.5K/km)积分, 成分取均匀 M̄
def T_doc(h):
    if h <= 1.5e3:
        return 300.0 - (300.0 - 216.65) * h / 1.5e3
    if h <= 17.2e3:
        return 216.65
    if h <= 24.0e3:
        return 216.65 + 2.3529e-3 * (h - 17.2e3)
    return 232.65 - 2.5e-3 * (h - 24.0e3)

def P_at(z):
    P = P0
    h = 0.0
    dz = 100.0
    while h < z:
        Tm = 0.5 * (T_doc(h) + T_doc(h+dz))
        P *= math.exp(-g * Mbar / (R * Tm) * dz)
        h += dz
    return P

P85 = P_at(Z_MESO)
print(f"  按文档剖面积分: P(85 km) ≈ {P85:.2f} Pa")

d_He = 2.2e-10   # 碰撞直径 m (按 He 计)
def exobase(q0, M=Mbar, k0=k0_mix):
    Te, prof = bates(q0, M, k0, z_top=2000e3)
    P = P85
    prev = Z_MESO
    for (z, T) in prof[1:]:
        P *= math.exp(-(z - prev) / H(T, M))
        prev = z
        n = P / (kB * T)
        mfp = 1.0 / (math.sqrt(2) * math.pi * d_He**2 * n)
        if mfp >= H(T, M):
            return z / 1e3
    return None

for q0 in (1.0e-3, q0_earth, 3.0e-3):
    print(f"  q0={q0*1e3:5.2f} mW/m² → 外逸层底 ≈ {exobase(q0):.0f} km")

print()
print("=" * 74)
print("六、小结")
print("=" * 74)
print(f"  新成分(M̄={Mbar*1000:.2f} g/mol, κ_mix={K_MIX_300:.3f})")
print(f"  T_exo ≈ {T_exo(1.0e-3):.0f}–{T_exo(3.0e-3):.0f} K; 地球同热流({q0_earth*1e3:.1f} mW/m²)约 {T_exo(q0_earth):.0f} K")
print(f"  对照地球 ~1000 K: 本行星热层更冷")
print(f"  主因: ①He 主导, 导热率约为空气 {K_MIX_300/K_AIR_300:.1f} 倍, 梯度被压平;")
print( "        ②He 只吸收 λ<50 nm 的 EUV, 实际 q0 低于地球")
print()
print(f"  提醒: 文档温度模型中间层为无界线性降温(232.65K 起, −2.5K/km),")
print(f"        到 85 km 仅 {232.65-2.5e-3*(85e3-24e3):.1f} K, 物理上不成立;")
print( "        此处另设中间层顶 183 K @ 85 km 作锚点。")