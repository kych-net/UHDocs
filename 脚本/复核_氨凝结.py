#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复核:大气里的 NH3 会在什么高度凝结(液化)?(只读,不改文档)
运行: python3 脚本/复核_氨凝结.py

两条判据:
  A 痕量气体正确判据: NH3 分压 p_NH3 = x·P(h) 达到其饱和蒸气压 p_sat(T(h))。
  B 纯物质判据(常见误用): 环境温度 T(h) 降到 NH3 在*当地总压* P(h) 下的沸点以下。
"""
import numpy as np

# ---------- 大气(同 附件/模块.typ) ----------
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
x_NH3 = 比[5]                                    # NH3 体积比


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


# ---------- NH3 饱和蒸气压(Clausius-Clapeyron, 参考常压沸点) ----------
Tb = 239.82          # K, 1 atm 沸点
dHvap = 23350.0      # J/mol, 汽化热
def p_sat(T): return 101325.0 * np.exp(-dHvap / R * (1.0 / T - 1.0 / Tb))
def T_沸点(P): return 1.0 / (1.0 / Tb - R / dHvap * np.log(P / 101325.0))


print(f"M̄={Mbar*1000:.3f} g/mol  Γ={Γ*1000:.3f} K/km  x_NH3={x_NH3*100:.2f}%")
print(f"NH3: 常压沸点 {Tb:.2f} K, 汽化热 {dHvap/1000:.2f} kJ/mol")
print(f"赤道对流层顶 = {(300-对流层顶温)/Γ/1000:.2f} km   极点对流层顶 = {(240-对流层顶温)/Γ/1000:.2f} km")

for T0, 名 in ((300.0, "赤道 300 K"), (240.0, "极点 240 K")):
    print()
    print("=" * 96)
    print(f"【{名}】")
    print("=" * 96)
    print(f"  {'h km':>5} {'T K':>7} {'P kPa':>8} {'p_NH3 Pa':>9} {'p_sat kPa':>10} "
          f"{'p/p_sat':>9} {'沸点K':>7} {'T-沸点':>8}")
    最接近 = (0.0, 0.0)
    B_交 = None
    prev = None
    for hkm in np.arange(0, 60.001, 0.5):
        h = hkm * 1000
        T = 温度(T0, h)
        P = 压强(T0, h)
        pN = x_NH3 * P
        ps = p_sat(T)
        ratio = pN / ps
        Tb_local = T_沸点(P)
        d = T - Tb_local
        if ratio > 最接近[1]:
            最接近 = (hkm, ratio)
        if prev is not None and prev[1] > 0 >= d:
            B_交 = hkm
        prev = (hkm, d)
        if hkm % 4 == 0 or abs(hkm - 8.96) < 0.3:
            print(f"  {hkm:5.1f} {T:7.1f} {P/1000:8.2f} {pN:9.2f} {ps/1000:10.2f} "
                  f"{ratio:9.2e} {Tb_local:7.1f} {d:8.1f}")
    print(f"  → 判据A(分压=饱和): 最大 p/p_sat = {最接近[1]:.2e} 于 {最接近[0]:.1f} km  "
          f"{'（会凝结）' if 最接近[1] >= 1 else '（始终未饱和,不凝结）'}")
    print(f"  → 判据B(纯NH3沸点): 液化高度 ≈ "
          f"{'%.1f km' % B_交 if B_交 else '不出现(全程 T 高于沸点)'}")

print()
print("=" * 96)
print("【凝结所需的 NH3 浓度】在赤道对流层顶 8.96 km, T=216.65 K, p_sat=%.1f kPa" % (p_sat(216.65)/1000))
print("=" * 96)
P_trop = 压强(300.0, 8.96e3)
print(f"  该处总压 P={P_trop/1000:.2f} kPa → 要饱和, x_NH3 需 = {p_sat(216.65)/P_trop*100:.1f}%")
print(f"  实际 x_NH3 = {x_NH3*100:.2f}%,分压仅 {x_NH3*P_trop:.1f} Pa,差 "
      f"{p_sat(216.65)/(x_NH3*P_trop):.0f} 倍")