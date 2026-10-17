#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
植物世代光合设计 —— 数值复核
只读,不改 内容/。运行: python3 脚本/设计_光合.py

依据:
  · 恒星辐照度 1360 W/m², G2V 黑体 5772 K,大气透过模型复用 设计_怪眼光谱.py
  · 15 种色素等能量排布,覆盖 300–1000 nm(通道间隔 dE≈0.193 eV)
  · 机制:植物世代细胞壁纤维素周期阵列光子晶体天线 + 微型Z方案
    + 储能电位匹配(高压H₂库) + 激子倍增(≥2.46 eV 光子推两电子)
  · 1000–1100 nm 低于产氢阈值,走 Fe²⁺ 供电子杂合产氢(共生微生物)
输出:
  各通道入射功率、损失账、绝对效率、产氢/固氮速率
"""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 设计_怪眼光谱 as sp

# ========== 通道设计 ==========
E_LO, E_HI = 1.24, 4.13          # eV, 300–1000 nm
N_CH = 15
DE = (E_HI - E_LO) / N_CH

def lam(e):                       # nm
    return sp.H * sp.C / (e * 1.602176634e-19) * 1e9

def e_of(l):
    return sp.H * sp.C / (l * 1e-9) / 1.602176634e-19

通道 = [(E_LO + i * DE, E_LO + (i + 1) * DE) for i in range(N_CH)]

# ========== 损失模型 ==========
REFLECT = 0.010        # 表面反射与漏吸收
RECOMB = 0.010         # 电荷复合(量子效率 99%)
OVERPOT = 0.015        # 过电位与膜电阻税
MULTI_LOSS = 0.025     # 激子倍增不完整(E>2.46 eV 通道)
FE_ROUTE = 0.90        # 远红外杂合产氢效率(设计值)

def 粒度损失(e_lo, e_hi):
    """通道内储能电位匹配残差:均匀分布方差 / 均值平方"""
    e_mid = 0.5 * (e_lo + e_hi)
    var = (e_hi - e_lo) ** 2 / 12.0
    return var / e_mid ** 2

def 通道效率(e_lo, e_hi):
    eta = (1 - REFLECT) * (1 - RECOMB) * (1 - OVERPOT)
    eta *= 1 - 粒度损失(e_lo, e_hi)
    if e_lo > 2.46:
        eta *= 1 - MULTI_LOSS
    return eta

# ========== 逐通道能量收支 ==========
def 通道功率(e_lo, e_hi, n=200):
    """地表入射功率 W/m²(对通道内平均)与光子加权平均能量"""
    l1, l2 = lam(e_hi), lam(e_lo)
    p_tot = 0.0; q_tot = 0.0
    for i in range(n):
        l = l1 + (l2 - l1) * (i + 0.5) / n
        f = sp.f_surf(l)
        p_tot += f * (l2 - l1) / n
        q_tot += f / (sp.H * sp.C / (l * 1e-9)) * (l2 - l1) / n
    return p_tot, q_tot

def 远红外功率():
    """1000–1100 nm 入射功率"""
    p = 0.0
    for i in range(200):
        l = 1000 + (i + 0.5) * 0.5
        p += sp.f_surf(l) * 0.5
    return p

if __name__ == "__main__":
    print("=" * 72)
    print("一、15 通道峰位与能量收支(地表,垂直入射)")
    print("=" * 72)
    print(f"{'通道':>4}{'峰位nm':>8}{'范围eV':>14}{'入射W/m²':>10}{'效率':>8}{'储存W/m²':>10}")
    p_sum = 0.0; s_sum = 0.0; q_sum = 0.0
    for i, (e1, e2) in enumerate(通道):
        p, q = 通道功率(e1, e2)
        eta = 通道效率(e1, e2)
        p_sum += p; s_sum += p * eta; q_sum += q
        print(f"{i+1:>4}{0.5*(lam(e1)+lam(e2)):>8.0f}"
              f"{e1:>6.2f}-{e2:<6.2f}{p:>10.1f}{eta:>8.3f}{p*eta:>10.1f}")
    print(f"合计入射 300–1000 nm:{p_sum:.1f} W/m²  储存:{s_sum:.1f} W/m²")

    print()
    print("=" * 72)
    print("二、总账")
    print("=" * 72)
    eta_abs = s_sum / p_sum
    # Landsberg(5772K 排向 315K 与 300K)
    for t0 in (315.0, 300.0):
        r = t0 / 5772.0
        print(f"  Landsberg 极限(T0={t0:.0f}K): {1 - 4/3*r + 1/3*r**4:.4f}")
    print(f"  300–1000 nm 入射 {p_sum:.1f} W/m² → 储存 {s_sum:.1f} W/m²")
    print(f"  绝对效率 = {eta_abs:.4f}")
    print(f"  相对极限(315K) = {eta_abs / 0.9272:.4f}")
    print(f"  量子效率要求:每秒 {(q_sum*(1-REFLECT)*eta_abs):.2e} 电子 → "
          f"{s_sum/eta_abs:.1f} W/m² 入射下光子通量 {q_sum:.2e} /m²/s")

    p_fe = 远红外功率()
    print()
    print("三、远红外 1000–1100 nm(Fe²⁺ 供电子杂合产氢,共生微生物)")
    print("=" * 72)
    dE_fe = e_of(1050)
    print(f"  入射 {p_fe:.1f} W/m²,光子 ~{dE_fe:.2f} eV")
    print(f"  Fe²⁺/Fe³⁺(+0.77V) → H⁺/H₂(−0.41V) 储能台阶 ΔE ≈ 1.18 eV,在段内")
    print(f"  杂合产氢功率 ≈ {p_fe * FE_ROUTE:.1f} W/m²(不计入绝对效率口径)")

    print()
    print("四、产量换算(满照,单位受光面)")
    print("=" * 72)
    h2_mol = s_sum * 3600 / 285.8e3     # mol/h/m²(H₂ 生成焓 285.8 kJ/mol)
    nh3 = h2_mol * 2 / 3                # N₂+3H₂→2NH₃
    print(f"  H₂ {h2_mol*1000:.0f} mmol/h/m²(≈{h2_mol*2.016:.1f} g/h/m²)")
    print(f"  折 NH₃ {nh3*1000:.0f} mmol/h/m²(≈{nh3*17.03:.1f} g/h/m²)")
