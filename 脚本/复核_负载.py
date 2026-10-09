#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复核:怪动植物在不同情况下的负载能力(只读,不改文档)。
运行: python3 脚本/复核_负载.py

负载定义: 总质量 m = 自重 20 kg + 负载 m_p。
三条约束(全部取自现有模型,与 绘制_飞行包线.py / 附件/模块.typ 一致):
  1) 失速: V ≥ V_stall(m,h) = sqrt(2 m g/(ρ S C_Lmax)), C_Lmax = 1.6
  2) 速度带: V ∈ [推力下限(h), 推力上限(h)],上界再受气动加热限制
  3) 能量: 航程 R = (E/m)·η(h)·(L/D)/(g), E = 100 MJ
最优航程速度取极曲线 L/D 最大处的 V,再夹到速度带内。
"""

import numpy as np

# ---------- 大气(同 附件/模块.typ) ----------
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


_ρ表 = {}
def 密度(T0, h):
    key = (T0, h)
    if key not in _ρ表:
        _ρ表[key] = 压强(T0, h) * Mbar / (R_gas * 温度(T0, h))
    return _ρ表[key]


# ---------- 翼与储能 ----------
b = 10.0
AR = 40.0
S = b * b / AR
C_Lmax = 1.6
C_D0 = 0.006
LD_max = 68.0
e_os = C_D0 / (np.pi * AR) * (2 * LD_max) ** 2
E_st = 100e6
m_空 = 20.0
η_0, η_k = 0.9, 0.0025
CL_star = np.sqrt(np.pi * AR * e_os * C_D0)      # 极曲线 L/D 最大处的 C_L


def η(h_km): return min(1.0, η_0 + η_k * h_km)
def 推力下限(h_km): return 30.0 + 0.5556 * h_km ** 1.520
def 推力上限(h_km): return 300.0 + 19.55 * h_km ** 0.710
q_热 = 密度(300.0, 20e3) * 500.0 ** 3
def 气动加热(T0, h): return (q_热 / 密度(T0, h)) ** (1.0 / 3.0)
顶棚 = 48e3


def 升阻比(T0, V, h, m):
    CL = 2 * m * g / (密度(T0, h) * V * V * S)
    return CL / (C_D0 + CL * CL / (np.pi * AR * e_os))
def 失速速度(T0, h, m): return np.sqrt(2 * m * g / (密度(T0, h) * S * C_Lmax))
def 最优速度(T0, h, m): return np.sqrt(2 * m * g / (密度(T0, h) * S * CL_star))


def 速度带(T0, h, m):
    lo = max(推力下限(h / 1000.0), 失速速度(T0, h, m))
    hi = min(推力上限(h / 1000.0), 气动加热(T0, h))
    return lo, hi


def 性能(T0, h, m):
    """返回 (可飞, V, L/D, P_kW, R_km);不可飞则 V 等为 nan"""
    lo, hi = 速度带(T0, h, m)
    if lo > hi:
        return False, np.nan, np.nan, np.nan, np.nan
    V = min(max(最优速度(T0, h, m), lo), hi)
    LD = 升阻比(T0, V, h, m)
    P = m * g / LD * V / η(h / 1000.0)
    R = (E_st / m) * η(h / 1000.0) * LD / g
    return True, V, LD, P / 1000.0, R / 1000.0


def 最大负载(T0, h):
    """总质量上限:失速速度不超过速度带上界 hi(h);返回 (m_max, m_p_max)"""
    hi = min(推力上限(h / 1000.0), 气动加热(T0, h))
    m_max = 密度(T0, h) * S * C_Lmax * hi * hi / (2 * g)
    return m_max, m_max - m_空


高度 = [0, 5, 10, 20, 30, 40, 48]
负载 = [0, 10, 20, 25, 30, 40]
区域 = [("赤道 300K", 300.0), ("极点 240K", 240.0)]

print("=" * 92)
print(f"翼: 翼展 {b:.0f} m, AR {AR:.0f}, S {S:.2f} m², C_Lmax {C_Lmax}, (L/D)max {LD_max:.0f}  |  "
      f"储能 {E_st/1e6:.0f} MJ, 自重 {m_空:.0f} kg")
print("=" * 92)

# 表 A/B:各高度 × 各负载的最优航程
for 区名, T0 in 区域:
    print()
    print(f"【{区名}】最优航程 R (km) —— 行=高度, 列=负载(kg)")
    print("  h\\m_p " + "".join(f"{p:>10d}" for p in 负载))
    for hkm in 高度:
        h = hkm * 1000
        行 = f"  {hkm:5d} "
        for p in 负载:
            ok, V, LD, P, R = 性能(T0, h, m_空 + p)
            行 += f"{'✗':>10}" if not ok else f"{R:>10.0f}"
        print(行)
    print("  (✗ = 该负载下失速速度超过速度带上界,包线内无可用速度)")

print()
print("=" * 92)
print("【最大负载】总质量上限 / 负载上限 (受速度带上界与失速约束)")
print("=" * 92)
print(f"  {'h km':>5} | {'赤道 m_max':>10} {'负载上限':>10} | {'极点 m_max':>10} {'负载上限':>10}")
for hkm in 高度:
    h = hkm * 1000
    m1, p1 = 最大负载(300.0, h)
    m2, p2 = 最大负载(240.0, h)
    print(f"  {hkm:5d} | {m1:10.1f} {p1:10.1f} | {m2:10.1f} {p2:10.1f}")

print()
print("=" * 92)
print("【关键点对照】满载 25 kg(设定卡) 与 40 kg(正文) 在各高度的性能")
print("=" * 92)
for p in (25, 40):
    m = m_空 + p
    print(f"  负载 {p} kg (总质量 {m:.0f} kg):")
    print(f"    {'h km':>5} | {'V_opt':>7} {'L/D':>6} {'P kW':>7} {'R km':>8} | "
          f"{'V_opt':>7} {'L/D':>6} {'P kW':>7} {'R km':>8}  (左赤道/右极点)")
    for hkm in 高度:
        h = hkm * 1000
        c = 性能(300.0, h, m)
        d = 性能(240.0, h, m)
        fmt = lambda t: (f"{t[1]:7.0f} {t[2]:6.1f} {t[3]:7.2f} {t[4]:8.0f}") if t[0] else "     ✗ 包线内无可用速度"
        print(f"    {hkm:5d} | {fmt(c)} | {fmt(d)}")
    print()

print("=" * 92)
print("【设定卡复核点】20 km 满载 45 kg @83 m/s;40 km 空载 20 kg @182 m/s")
print("=" * 92)
for 区名, T0 in 区域:
    for 名, hkm, m, V in (("20 km 满载 45 kg", 20, 45.0, 83.0), ("40 km 空载 20 kg", 40, 20.0, 182.0)):
        h = hkm * 1000
        lo, hi = 速度带(T0, h, m)
        LD = 升阻比(T0, V, h, m)
        P = m * g / LD * V / η(hkm)
        R = (E_st / m) * η(hkm) * LD / g / 1000
        print(f"  [{区名}] {名} @{V:.0f}: 速度带[{lo:.0f},{hi:.0f}] L/D={LD:.1f} "
              f"P={P/1000:.3f} kW R={R:.0f} km  {'可飞' if lo <= V <= hi else '✗速度越界'}")

print()
print("结论:负载越大,最优速度越高、航程越短;低速端受失速限制,是最先顶不住的约束。")