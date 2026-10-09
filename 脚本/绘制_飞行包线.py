#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》怪动植物 飞行包线图（重绘）
输出 图片/飞行.png。模型与 附件/模块.typ 的大气一致(低空均匀成分 + 三层温度 + 积分压强)。

包线(空载 20 kg):
  下界 = max(推力下限, 失速速度);上界 = min(推力上限, 气动加热);顶棚 48 km。
  - 推力下限:过 (20 km, 83 m/s) 与 (40 km, 182 m/s)   [卡]
  - 推力上限:过 (20 km, 465 m/s) 与 (40 km, 570 m/s)  [卡]
  - 失速速度:V = sqrt(2 m g /(ρ S C_Lmax)), C_Lmax=1.6
  - M0.9 线:V = 0.9 a(h)   (变后掠延后波阻,仅作参考线)
  - 气动加热:q ∝ ρ V³,标定 20 km 处 500 m/s

航程(Breguet,空载 20 kg):
  R = (E/m)·η(h)·(L/D)(V,h)/g
  - 储能 E = 100 MJ(2 kg 能量脂 × 50 MJ/kg)
  - 推进效率 η(h) = clamp(0.9 + 0.0025·h_km, 0.9, 1.0)  (低空 NH₃ 簇离子→高空 He⁺)
  - L/D = 68·exp(−((V−V_opt)/170)²),V_opt 为最佳升阻速度 ∝ 1/√ρ
  标定后:40 km 空载巡航(182 m/s)≈ 13600 km;20 km 满载(45 kg, 83 m/s)≈ 7200 km。
  注:卡上 20 km 满载 6900 km 与 40 km 空载 13600 km 在任何单一模型下无法同时成立
  (两点要求 20 km 接近最佳升阻、40 km 偏离 0.83,而离最佳速度的距离分别为 5 与 80 m/s),
  本图取 40 km 点对齐,20 km 点偏高约 4%。

只写 图片/飞行.png。运行: python3 脚本/绘制_飞行包线.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "LXGW WenKai"]
plt.rcParams["axes.unicode_minus"] = False

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


def 温度(h):
    ht = (300.0 - 对流层顶温) / Γ
    if h <= ht:
        return 300.0 - Γ * h
    if h <= 平流层顶高:
        return 对流层顶温 + (平流层顶温 - 对流层顶温) * (h - ht) / (平流层顶高 - ht)
    if h < 中间层顶高:
        return 平流层顶温 + (中间层顶温 - 平流层顶温) * (h - 平流层顶高) / (中间层顶高 - 平流层顶高)
    return 中间层顶温


def 压强(h):
    h = float(h)
    dz = 50.0
    n = max(1, int(np.ceil(h / dz)))
    dh = h / n
    P = P0
    for k in range(n):
        Tm = 0.5 * (温度(k * dh) + 温度((k + 1) * dh))
        P *= np.exp(-g * Mbar / (R_gas * Tm) * dh)
    return P


_ρ表 = {}
def 密度(h):
    if h not in _ρ表:
        _ρ表[h] = 压强(h) * Mbar / (R_gas * 温度(h))
    return _ρ表[h]


def 声速(h):
    return np.sqrt(γ * R_gas * 温度(h) / Mbar)


# ---------- 翼与储能 ----------
b = 10.0
AR = 40.0
S = b * b / AR
C_Lmax = 1.6
C_D0 = 0.006
e_os = 0.85
LD_max = 68.0
W_ld = 170.0
E_st = 100e6
m_空 = 20.0
η_0, η_k = 0.9, 0.0025


def η(h_km):
    return min(1.0, η_0 + η_k * h_km)


def 最佳升阻速度(h, m):
    ρ = 密度(h)
    return np.sqrt(2 * m * g / (ρ * S) * np.sqrt(1.0 / (np.pi * AR * e_os * C_D0)))


def 航程(V, h, m):
    ρ = 密度(h)
    Vopt = 最佳升阻速度(h, m)
    LD = LD_max * np.exp(-((V - Vopt) / W_ld) ** 2)
    return (E_st / m) * η(h / 1000.0) * LD / g


# ---------- 包线边界 ----------
def 推力下限(h_km):
    return 30.0 + 0.5556 * h_km ** 1.520


def 推力上限(h_km):
    return 300.0 + 19.55 * h_km ** 0.710


def 失速速度(h, m):
    return np.sqrt(2 * m * g / (密度(h) * S * C_Lmax))


q_热 = 密度(20e3) * 500.0 ** 3
def 气动加热(h):
    return (q_热 / 密度(h)) ** (1.0 / 3.0)


顶棚 = 48e3

# ---------- 网格 ----------
Vs = np.linspace(20, 660, 340)
Hs = np.linspace(0, 50e3, 280)
VV, HH = np.meshgrid(Vs, Hs)
hkm = HH / 1000.0

Rng = np.array([[航程(VV[i, j], HH[i, j], m_空) / 1000.0 for j in range(Vs.size)] for i in range(Hs.size)])

下界 = np.maximum(推力下限(hkm), np.array([[失速速度(HH[i, j], m_空) for j in range(Vs.size)] for i in range(Hs.size)]))
上界 = np.minimum(推力上限(hkm), np.array([[气动加热(HH[i, j]) for j in range(Vs.size)] for i in range(Hs.size)]))
有效 = (HH <= 顶棚) & (VV >= 下界) & (VV <= 上界)
Rng = np.where(有效, Rng, np.nan)

# ---------- 绘图 ----------
fig, ax = plt.subplots(figsize=(10, 6.4), dpi=100)
cmap = plt.get_cmap("turbo").copy()
cmap.set_bad(alpha=0.0)

levels = np.linspace(0, 17000, 60)
cf = ax.contourf(VV, HH / 1000.0, Rng, levels=levels, cmap=cmap, extend="max")
cb = fig.colorbar(cf, ax=ax, pad=0.015)
cb.set_label("航程 (km)")

hc = np.linspace(0, 顶棚, 400)
hkc = hc / 1000.0
ax.plot(推力下限(hkc), hkc, color="#C62828", lw=1.8, label="最低速度(推力下限)")
ax.plot(推力上限(hkc), hkc, color="#E8791A", lw=1.8, label="最高速度(推力上限)")
ax.plot([失速速度(h, m_空) for h in hc], hkc, color="#777777", lw=1.4, ls=(0, (6, 4)), label="失速速度")
ax.plot(0.9 * np.array([声速(h) for h in hc]), hkc, color="#111111", lw=1.3, ls=(0, (5, 3)), label="M0.9")
ax.plot([气动加热(h) for h in hc], hkc, color="#999999", lw=1.2, ls=":", label="气动加热")
ax.axhline(48, color="#00A6A6", lw=1.4, ls=(0, (4, 3)), label="升限 48 km")

ax.plot([83, 182], [20, 40], "o", mfc="none", mec="white", mew=1.8, ms=9)
ax.plot([83, 182], [20, 40], "o", mfc="none", mec="black", mew=1.0, ms=9)
ax.annotate("20 km 满载 45 kg", (83, 20), xytext=(150, 15.5), color="white", fontsize=9,
            arrowprops=dict(arrowstyle="->", color="white", lw=1.2))
ax.annotate("40 km 空载 20 kg", (182, 40), xytext=(250, 44.5), color="white", fontsize=9,
            arrowprops=dict(arrowstyle="->", color="white", lw=1.2))

ax.set_xlim(0, 660)
ax.set_ylim(0, 50)
ax.set_xlabel("速度 (m/s)")
ax.set_ylabel("高度 (km)")
ax.set_title("怪动植物飞行包线（赤道/极点平均，航程）")
ax.grid(True, alpha=0.25)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

fig.tight_layout()
fig.savefig("图片/飞行.png")
print("已写入 图片/飞行.png")

# ---------- 复核输出 ----------
for V, hkm_, m, 标 in ((83, 20, 45, "20 km 满载 45 kg"), (182, 40, 20, "40 km 空载 20 kg")):
    print(f"  {标}: R = {航程(V, hkm_*1000, m)/1000:.0f} km")
print(f"  空载航程上限 ≈ {np.nanmax(Rng):.0f} km")
print(f"  20 km 上界 = {min(推力上限(20), 气动加热(20e3)):.0f} m/s (卡 465)")
print(f"  40 km 上界 = {min(推力上限(40), 气动加热(40e3)):.0f} m/s (卡 570)")