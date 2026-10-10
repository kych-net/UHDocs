#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复核:NH3 与 CO2 在高空是否反应?(只读,不改文档)
运行: python3 脚本/复核_高空氨碳.py

判断依据:
  1) 两者生成氨基甲酸铵/铵盐都是"缔合+三体碰撞"过程,速率 ∝ P²;高空压力骤降 → 速率骤降。
  2) 水相路径(NH3+CO2+H2O→铵盐)只在有液态水时走;有液态水 ⟺ p_H2O > p_sat(H2O)(T)。
  3) 平流层温度回升,水汽更不饱和;中间层降温才可能再出现水冰。
"""
import numpy as np

g = 20.0
R = 8.314462618
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
cp = sum(_m[i] / sum(_m) * (物种[i][2] / 2) * R / 物种[i][1] for i in range(len(物种)))
Γ = g / cp
x_H2O, x_NH3, x_CO2 = 比[4], 比[5], 比[3]


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
    dz = 25.0
    n = max(1, int(np.ceil(h / dz)))
    dh = h / n
    P = P0
    for k in range(n):
        Tm = 0.5 * (温度(T0, k * dh) + 温度(T0, (k + 1) * dh))
        P *= np.exp(-g * Mbar / (R * Tm) * dh)
    return P


# H2O 饱和蒸气压(Clausius-Clapeyron, 参考 273.15 K / 611.657 Pa)
def p_sat_H2O(T): return 611.657 * np.exp(-45050.0 / R * (1.0 / T - 1.0 / 273.15))


print(f"x(H2O)={x_H2O*100:.1f}%  x(NH3)={x_NH3*100:.2f}%  x(CO2)={x_CO2*100:.1f}%")
print("三体碰撞相对率 = (P/P0)²,以海平面为 1")
for T0, 名 in ((300.0, "赤道 300 K"), (240.0, "极点 240 K")):
    print()
    print("=" * 104)
    print(f"【{名}】")
    print("=" * 104)
    print(f"  {'h km':>5} {'T K':>7} {'P kPa':>9} {'(P/P0)²':>10} {'p_H2O Pa':>10} "
          f"{'p_sat(H2O) Pa':>14} {'水相':>6}")
    for hkm in (0, 5, 8.96, 12, 20, 30, 40, 47, 55, 65, 75, 85):
        h = hkm * 1000
        T = 温度(T0, h)
        P = 压强(T0, h)
        pH = x_H2O * P
        ps = p_sat_H2O(T)
        液 = "有" if pH > ps else "无"
        print(f"  {hkm:5.1f} {T:7.1f} {P/1000:9.4f} {(P/P0)**2:10.2e} {pH:10.4f} {ps:14.4f} {液:>6}")

print()
print("=" * 104)
print("三体缔合速率(相对海平面)对比")
print("=" * 104)
for hkm in (0, 20, 40, 48, 85):
    P = 压强(300.0, hkm * 1000)
    print(f"  {hkm:>3} km: (P/P0)² = {(P/P0)**2:.3e}  → 相对海平面 "
          f"{'×1' if hkm==0 else '÷%.0f' % (1/(P/P0)**2)}")