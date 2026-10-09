#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》主行星 —— 罗斯贝半径 与 热成风切变 独立复核
对照 内容/地理/主行星.typ 气候段的标称值:
  罗斯贝半径 3.4e3 至 1.3e4 km, 与行星半径之比 0.2 至 0.9, 地球 0.4
  热成风切变约 12 至 24 m/s, 地球同纬度约 30 m/s
只读, 不改 内容/。运行: python3 脚本/复核_罗斯贝与热成风.py
"""

import math

# —— 行星与大气参数(取自 附件/模块.typ) ——
a_planet = 1.5e7          # m 行星半径 1.5e4 km
g = 20.0                  # m/s^2
Rs = 8.314462618 / 0.010618   # 比气体常数 J/(kg·K)  ≈ 783
T0 = 300.0                # K 赤道海平面
T_pole = 240.0            # K 极点海平面
period = 24 * 3600.0      # s 自转周期
Om = 2 * math.pi / period # rad/s

# 地球对照
g_E = 9.81
Rs_E = 287.0
T_E = 288.0
a_E = 6.371e6

H_pl = Rs * T0 / g / 1000.0          # 标高(用赤道海平面温)
H_pl_mean = Rs * 270.0 / g / 1000.0  # 标高(用对流层平均温)
H_E = Rs_E * T_E / g_E / 1000.0

print("=" * 76)
print("零、基本量")
print("=" * 76)
print(f"  自转周期 {period/3600:.0f} h → Ω = {Om:.4e} rad/s  (与地球同)")
print(f"  行星标高 H = Rs·T/g: 赤道海平面 {H_pl:.2f} km, 对流层均温 {H_pl_mean:.2f} km")
print(f"  地球标高 H_E = {H_E:.2f} km")
print(f"  sqrt(g·H): 行星 {math.sqrt(g*H_pl*1000):.1f} m/s, 地球 {math.sqrt(g_E*H_E*1000):.1f} m/s")

print()
print("=" * 76)
print("一、罗斯贝半径 L_R = sqrt(g·H)/f  (外部/正压变形半径)")
print("=" * 76)
print(f"  {'φ°':>4} {'f (1/s)':>11} {'L_R km':>9} {'L_R/a':>7}")
for φ in (0, 5, 10, 15, 20, 30, 45, 60, 75, 90):
    f = 2 * Om * math.sin(math.radians(φ))
    if f == 0:
        print(f"  {φ:4d} {0.0:11.3e} {'∞':>9} {'—':>7}")
        continue
    LR = math.sqrt(g * H_pl * 1000) / f / 1000.0
    print(f"  {φ:4d} {f:11.3e} {LR:9.0f} {LR*1000/a_planet:7.2f}")

# 极点到 15° 的区间
LR_pole = math.sqrt(g * H_pl * 1000) / (2 * Om * math.sin(math.radians(90))) / 1000.0
LR_15 = math.sqrt(g * H_pl * 1000) / (2 * Om * math.sin(math.radians(15))) / 1000.0
print(f"\n  区间(15°→90°): {LR_15:.0f} 至 {LR_pole:.0f} km  → 比 a: {LR_pole*1000/a_planet:.2f} 至 {LR_15*1000/a_planet:.2f}")

print()
print("  地球对照:")
for φ in (45, 90):
    f = 2 * Om * math.sin(math.radians(φ))
    LR = math.sqrt(g_E * H_E * 1000) / f / 1000.0
    print(f"    φ={φ:2d}°  L_R = {LR:.0f} km  L_R/a = {LR*1000/a_E:.2f}")

print()
print("  内部(斜压)半径 L_R = N·H/f 参照 —— 对流层近干绝热, N≈0 → 不适用:")
for N in (0.005, 0.010, 0.015):
    f = 2 * Om * math.sin(math.radians(45))
    LR = N * H_pl * 1000 / f / 1000.0
    print(f"    N={N:.3f} 1/s → L_R(45°) = {LR:.0f} km")

print()
print("=" * 76)
print("二、热成风切变 Δu = (g/(f·T̄))·|∂T/∂y|·Δz")
print("=" * 76)
print("  纬向温度 T(φ) = 300 − 60·sin²φ (内容/地理/主行星.typ)")
print("  ∂T/∂y = (dT/dφ)/a,  dT/dφ = −60·sin2φ  K/rad")

def Tlat(φ):
    return 300.0 - 60.0 * math.sin(math.radians(φ))**2

def dTdy(φ):
    # dT/dφ = -60·sin(2φ) K/rad ; ∂T/∂y = (dT/dφ)/a
    return (-60.0 * math.sin(math.radians(2*φ))) / a_planet

print(f"\n  {'带(φ1–φ2)':>12} {'ΔT K':>7} {'f@mid':>10} {'∂T/∂y K/m':>12} {'Δu m/s':>8}")
for φ1, φ2 in ((0, 20), (10, 30), (20, 40), (30, 50), (30, 60), (40, 60), (45, 65), (60, 80)):
    φm = 0.5 * (φ1 + φ2)
    f = 2 * Om * math.sin(math.radians(φm))
    dT = Tlat(φ2) - Tlat(φ1)
    dTdy_m = dTdy(φm)
    Tm = 0.5 * (Tlat(φ1) + Tlat(φ2))
    dz = 9000.0     # 对流层约 9 km
    du = abs(g / (f * Tm) * dTdy_m * dz)
    print(f"  {φ1:3d}–{φ2:<3d}{'':>4} {dT:7.1f} {f:10.3e} {abs(dTdy_m):12.2e} {du:8.1f}")

print("\n  地球对照(ΔT 同式, g=9.81, T̄=260, a=6371km, Δz=11km):")
a_E_ = 6.371e6
def dTdy_E(φ):
    return (-60.0 * math.sin(math.radians(2*φ))) / a_E_
for φ1, φ2 in ((30, 60),):
    φm = 0.5 * (φ1 + φ2)
    f = 2 * Om * math.sin(math.radians(φm))
    dT = Tlat(φ2) - Tlat(φ1)
    du = abs(9.81 / (f * 260.0) * dTdy_E(φm) * 11000.0)
    print(f"    {φ1}–{φ2}°: Δu = {du:.1f} m/s  [设定卡地球 30]")

print()
print("=" * 76)
print("三、与正文标称值对照")
print("=" * 76)
print(f"  正文: 罗斯贝半径 3.4e3–1.3e4 km, 比 0.2–0.9, 地球 0.4")
print(f"  复核: L_R(90°)={LR_pole:.0f} km (比 {LR_pole*1000/a_planet:.2f}), "
      f"L_R(15°)={LR_15:.0f} km (比 {LR_15*1000/a_planet:.2f})")
print(f"  正文: 热成风切变 12–24 m/s")
print(f"  复核: 见上表 Δu 列")