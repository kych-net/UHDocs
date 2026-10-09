#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》怪动植物 飞行包线图（重绘）
输出 图片/飞行.png。大气模型与 附件/模块.typ 一致:
低空均匀成分 + 三层温度(对流层干绝热 / 平流层升温 / 中间层降温) + 静力平衡积分压强。
设定卡的航程数值仅作参考,本图航程一律按物理自洽模型计算。

包线(空载 20 kg):
  下界 = max(最低速度, 失速速度);上界 = min(最高速度, 气动加热);顶棚 48 km。
  - 最低速度:过 (20 km, 83 m/s) 与 (40 km, 182 m/s)   [卡, 电推羽推力下限]
  - 最高速度:过 (20 km, 465 m/s) 与 (40 km, 570 m/s)  [卡, 推力上限]
  - 失速速度:V = √(2 m g /(ρ S C_Lmax)), C_Lmax = 1.6
  - M0.9 线:V = 0.9 a(h)(变后掠延后波阻,仅作参考线)
  - 气动加热:q ∝ ρ V³,标定 20 km 处 500 m/s

航程(电推 Breguet, R = E·η·(L/D)/(m·g)):
  - 储能 E = 100 MJ(2 kg 能量脂 × 50 MJ/kg)
  - 推进效率 η(h) = clamp(0.9 + 0.0025·h_km, 0.9, 1.0)(低空 NH₃ 簇离子 → 高空 He⁺)
  - 升阻比取物理极曲线 L/D = C_L /(C_D0 + C_L²/(π AR e)),C_L = 2 m g/(ρ V² S);
    取 e 使 (L/D)max = 68,与正文「升阻比约 68:1」一致

只写 图片/飞行.png。运行: python3 脚本/绘制_飞行包线.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "LXGW WenKai"]
plt.rcParams["axes.unicode_minus"] = False

# ---------- 大气(与 附件/模块.typ 一致) ----------
g = 20.0
R_gas = 8.314462618
P0 = 1.013e5
海平面温 = 300.0
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
    ht = (海平面温 - 对流层顶温) / Γ
    if h <= ht:
        return 海平面温 - Γ * h
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
LD_max = 68.0
e_os = C_D0 / (np.pi * AR) * (2 * LD_max) ** 2   # 使 (L/D)max = 68
E_st = 100e6
m_空 = 20.0
η_0, η_k = 0.9, 0.0025


def η(h_km):
    return min(1.0, η_0 + η_k * h_km)


def 升阻比(V, h, m):
    CL = 2 * m * g / (密度(h) * V * V * S)
    CD = C_D0 + CL * CL / (np.pi * AR * e_os)
    return CL / CD


def 航程(V, h, m):
    """电推 Breguet: R = E·η·(L/D)/(m·g),返回 m"""
    return (E_st / m) * η(h / 1000.0) * 升阻比(V, h, m) / g


# ---------- 包线边界(高度→速度) ----------
def 推力下限(h_km):
    return 30.0 + 0.5556 * h_km ** 1.520


def 推力上限(h_km):
    return 300.0 + 19.55 * h_km ** 0.710


def 失速速度(h, m):
    return np.sqrt(2 * m * g / (密度(h) * S * C_Lmax))


q_热 = 密度(20e3) * 500.0 ** 3
def 气动加热(h):
    return (q_热 / 密度(h)) ** (1.0 / 3.0)
def 气动加热ρ(ρ):
    return (q_热 / np.asarray(ρ, dtype=float)) ** (1.0 / 3.0)


顶棚 = 48e3

# ---------- 航程场(空载 20 kg) ----------
Vs = np.linspace(20, 660, 340)
Hs = np.linspace(0, 50e3, 280)
ρ_h = np.array([密度(h) for h in Hs])
η_h = np.array([η(h / 1000.0) for h in Hs])

CL = 2 * m_空 * g / (ρ_h[:, None] * Vs[None, :] ** 2 * S)
CD = C_D0 + CL * CL / (np.pi * AR * e_os)
Rng = (E_st / m_空) * η_h[:, None] * (CL / CD) / g / 1000.0   # km

VV, HH = np.meshgrid(Vs, Hs)
hkm = HH / 1000.0
失速场 = np.sqrt(2 * m_空 * g / (ρ_h[:, None] * S * C_Lmax))
下界 = np.maximum(推力下限(hkm), 失速场)
上界 = np.minimum(推力上限(hkm), 气动加热ρ(ρ_h)[:, None])
有效 = (HH <= 顶棚) & (VV >= 下界) & (VV <= 上界)
Rng = np.where(有效, Rng, np.nan)

# ---------- 绘图 ----------
fig, ax = plt.subplots(figsize=(10, 6.4), dpi=150)
cmap = plt.get_cmap("turbo").copy()
cmap.set_bad(alpha=0.0)

levels = np.linspace(0, 17000, 60)
cf = ax.contourf(VV, HH / 1000.0, Rng, levels=levels, cmap=cmap, extend="max")
cb = fig.colorbar(cf, ax=ax, pad=0.015)
cb.set_label("航程 (空载 20 kg, km)")

hc = np.linspace(0, 顶棚, 400)
hkc = hc / 1000.0
ax.plot(推力下限(hkc), hkc, color="#C62828", lw=1.8, label="最低速度(推力下限)")
ax.plot(推力上限(hkc), hkc, color="#E8791A", lw=1.8, label="最高速度(推力上限)")
ax.plot([失速速度(h, m_空) for h in hc], hkc, color="#777777", lw=1.4, ls=(0, (6, 4)), label="失速速度")
ax.plot(0.9 * np.array([声速(h) for h in hc]), hkc, color="#111111", lw=1.3, ls=(0, (5, 3)), label="M0.9")
ax.plot([气动加热(h) for h in hc], hkc, color="#999999", lw=1.2, ls=":", label="气动加热")
ax.axhline(48, color="#00A6A6", lw=1.4, ls=(0, (4, 3)), label="升限 48 km")

R20 = 航程(83, 20e3, 45.0) / 1000.0
R40 = 航程(182, 40e3, m_空) / 1000.0
ax.plot([83, 182], [20, 40], "o", mfc="none", mec="white", mew=1.8, ms=9)
ax.plot([83, 182], [20, 40], "o", mfc="none", mec="black", mew=1.0, ms=9)
ax.annotate(f"20 km 满载 45 kg\n航程 {R20:.0f} km", (83, 20), xytext=(150, 14.0), color="white",
            fontsize=9, arrowprops=dict(arrowstyle="->", color="white", lw=1.2))
ax.annotate(f"40 km 空载 20 kg\n航程 {R40:.0f} km", (182, 40), xytext=(255, 44.5), color="white",
            fontsize=9, arrowprops=dict(arrowstyle="->", color="white", lw=1.2))

ax.set_xlim(0, 660)
ax.set_ylim(0, 50)
ax.set_xlabel("速度 (m/s)")
ax.set_ylabel("高度 (km)")
ax.set_title("怪动植物飞行参数")
ax.grid(True, alpha=0.25)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

fig.tight_layout()
fig.savefig("图片/飞行.png", transparent=True)
print("已写入 图片/飞行.png")

# ---------- 复核输出 ----------
print(f"  (L/D)max 设定 {LD_max:.1f}  e={e_os:.4f}")
print(f"  20 km 满载 45 kg @83 m/s: L/D={升阻比(83,20e3,45.0):.1f}  R={R20:.0f} km")
print(f"  40 km 空载 20 kg @182 m/s: L/D={升阻比(182,40e3,20.0):.1f}  R={R40:.0f} km")
print(f"  空载航程上限 ≈ {np.nanmax(Rng):.0f} km  (理论 E·η·(L/D)max/(m·g) = {E_st/20*68/g/1000:.0f} km)")
print(f"  20 km 上界 = {min(推力上限(20), 气动加热(20e3)):.0f} m/s (卡 465)")
print(f"  40 km 上界 = {min(推力上限(40), 气动加热(40e3)):.0f} m/s (卡 570)")
for hkm_ in (0, 5, 10, 20, 40, 48):
    print(f"  h={hkm_:>2} km: 下界={max(推力下限(hkm_), 失速速度(hkm_*1000, m_空)):.0f}  "
          f"上界={min(推力上限(hkm_), 气动加热(hkm_*1000)):.0f} m/s")