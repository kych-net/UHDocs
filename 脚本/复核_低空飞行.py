#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复核:按现参数,怪动植物低空能不能飞?
只读模型(大气同 附件/模块.typ,推力上下限同 脚本/绘制_飞行包线.py),不改设定。
运行: python3 脚本/复核_低空飞行.py

现模型里没有任何随高度衰减推力的项:
  最低速度 V_lo(h) = 30 + 0.5556·h^1.52   (过 20 km/83、40 km/182)
  最高速度 V_hi(h) = min(300 + 19.55·h^0.71, 气动加热(h))
两者在 h=0 都有定义,故可飞速度带一直延伸到地面。本脚本把它换算成推力、
功率、航程,看低空到底要多少推力、飞得动飞不动。
"""

import numpy as np

g = 20.0
R_gas = 8.314462618
P0 = 1.013e5
对流层顶温 = 216.65
平流层顶温 = 270.0
平流层顶高 = 47.0e3
中间层顶温 = 183.0
中间层顶高 = 85.0e3
物种 = [("He", 0.004003, 5, 0.759), ("O2", 0.032000, 7, 0.200), ("N2", 0.028013, 7, 0.019),
        ("CO2", 0.044010, 7, 0.010), ("H2O", 0.018015, 8, 0.010), ("NH3", 0.017031, 8, 0.001)]
比 = [x[3] / sum(x[3] for x in 物种) for x in 物种]
Mbar = sum(比[i] * 物种[i][1] for i in range(len(物种)))
_m = [比[i] * 物种[i][1] for i in range(len(物种))]
cp = sum(_m[i] / sum(_m) * (物种[i][2] / 2) * R_gas / 物种[i][1] for i in range(len(物种)))
Γ = g / cp
γ = cp / (cp - R_gas / Mbar)


def 温度(T0, h):
    ht = (T0 - 对流层顶温) / Γ
    if h <= ht:
        return T0 - Γ * h
    if h <= 平流层顶高:
        return 对流层顶温 + (平流层顶温 - 对流层顶温) * (h - ht) / (平流层顶高 - ht)
    if h < 中间层顶高:
        return 平流层顶温 + (中间层顶温 - 平流层顶温) * (h - 平流层顶高) / (中间层顶高 - 平流层顶高)
    return 中间层顶温


def 压强(T0, h):
    h = float(h)
    dz = 50.0
    n = max(1, int(np.ceil(h / dz)))
    dh = h / n
    P = P0
    for k in range(n):
        Tm = 0.5 * (温度(T0, k * dh) + 温度(T0, (k + 1) * dh))
        P *= np.exp(-g * Mbar / (R_gas * Tm) * dh)
    return P


_ρ = {}
def 密度(T0, h):
    if (T0, h) not in _ρ:
        _ρ[(T0, h)] = 压强(T0, h) * Mbar / (R_gas * 温度(T0, h))
    return _ρ[(T0, h)]


b = 10.0; AR = 40.0; S = b * b / AR
C_Lmax = 1.6; C_D0 = 0.006; LD_max = 68.0
e_os = C_D0 / (np.pi * AR) * (2 * LD_max) ** 2
E_st = 100e6; m_空 = 20.0; η_0, η_k = 0.9, 0.0025


def η(h_km): return min(1.0, η_0 + η_k * h_km)
def 升阻比(T0, V, h, m):
    CL = 2 * m * g / (密度(T0, h) * V * V * S)
    return CL / (C_D0 + CL * CL / (np.pi * AR * e_os))
def 阻力(T0, V, h, m): return m * g / 升阻比(T0, V, h, m)
def 功率(T0, V, h, m): return 阻力(T0, V, h, m) * V / η(h / 1000.0)
def 航程(T0, V, h, m): return (E_st / m) * η(h / 1000.0) * 升阻比(T0, V, h, m) / g
def 最低速度(h_km): return 30.0 + 0.5556 * h_km ** 1.520
def 最高速度(h_km): return 300.0 + 19.55 * h_km ** 0.710
q_热 = 密度(300.0, 20e3) * 500.0 ** 3
def 气动加热(T0, h): return (q_热 / 密度(T0, h)) ** (1.0 / 3.0)
def 失速(T0, h, m): return np.sqrt(2 * m * g / (密度(T0, h) * S * C_Lmax))


for T0, 名 in ((300.0, "赤道 300 K"), (240.0, "极点 240 K")):
    print("=" * 78)
    print(f"{名}   ρ₀={密度(T0,0):.3f} kg/m³  失速@0={失速(T0,0,m_空):.1f} m/s")
    print("=" * 78)
    print(f"{'h km':>5} {'V_lo':>6} {'V_hi':>6} {'失速':>6} | "
          f"{'T_lo N':>7} {'T_hi N':>7} | {'P_lo kW':>8} {'P_hi kW':>8} | {'R_lo km':>8}")
    for hkm in (0, 2, 5, 10, 20, 30, 40, 48):
        h = hkm * 1000
        vlo = 最低速度(hkm)
        vhi = min(最高速度(hkm), 气动加热(T0, h))
        print(f"{hkm:5.0f} {vlo:6.0f} {vhi:6.0f} {失速(T0,h,m_空):6.1f} | "
              f"{阻力(T0,vlo,h,m_空):7.1f} {阻力(T0,vhi,h,m_空):7.1f} | "
              f"{功率(T0,vlo,h,m_空)/1000:8.3f} {功率(T0,vhi,h,m_空)/1000:8.1f} | "
              f"{航程(T0,vlo,h,m_空)/1000:8.0f}")
    print()

print("=" * 78)
print("低空端点(赤道,空载 20 kg)")
print("=" * 78)
for V in (30, 60, 100, 150, 200, 266):
    print(f"  V={V:3.0f} m/s: L/D={升阻比(300.,V,0,20):5.1f}  D={阻力(300.,V,0,20):6.1f} N  "
          f"P={功率(300.,V,0,20)/1000:6.2f} kW  续航={E_st/功率(300.,V,0,20)/3600:5.2f} h  "
          f"航程={航程(300.,V,0,20)/1000:6.0f} km")

print()
print("对照:设定卡给的 20 km 满载 45 kg 需推力 = "
      f"{阻力(300.,83,20e3,45.0):.1f} N;40 km 空载 182 m/s 需推力 = "
      f"{阻力(300.,182,40e3,20.0):.1f} N")
print("结论:现模型低空速度带 [30, 266] m/s 有定义,推力需求 6~229 N,低空可飞,")
print("      且慢速低空航程(≈1.5×10⁴ km)不比高空差——正文「不能低空飞行」无模型支撑。")