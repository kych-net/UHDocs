#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
气候调节 —— 4 张维度矩阵表: 赤道温度 / 极点温度 / 气候(冰线) / 季节(45°年较差)
每张表 行=倾角, 列=光照. 只读. 运行: python3 脚本/设计/设计_气候调节表格.py

设定锚点(内容/地理/主行星.typ):
  · T0(φ) = 300 − 60·sin⁴φ, 均温约 280 K, 反照率 0.3, 温室 25 K
模型:
  · 年均日射 F(φ;ε) 数值积分(逐日太阳赤纬 δ=ε·sin(2πt/Y))
  · 温度场 T(φ;ε,x) = 25 + a·q + c·q² + b, q = 0.3·F(φ;ε)·(1+x)
  · a/c/b 由当前态(ε=23.44°, x=0)三条件校准: T(0)=300, T(90)=240, 加权均温=280
  · 季节指标: 45° 纬度夏至-冬至温度差
  · 气候指标: 年均 273 K 冰线纬度
"""

import math

S0 = 1360.0
T_G = 25.0
EPS0 = 23.44
A = 0.3

EPSILONS = (0, 10, 23.44, 35, 45)
XS = (-0.05, -0.01, 0.0, 0.05, 0.15)
XTAGS = ("-5%", "-1%", "0", "+5%", "+15%")


def daily_F(phi_deg, delta_deg, S):
    p, d = math.radians(phi_deg), math.radians(delta_deg)
    cosH = -math.tan(p) * math.tan(d)
    if cosH <= -1:
        return S / math.pi * math.sin(p) * math.sin(d) * math.pi
    if cosH >= 1:
        return 0.0
    H = math.acos(cosH)
    return S / math.pi * (H * math.sin(p) * math.sin(d)
                          + math.cos(p) * math.cos(d) * math.sin(H))


def mean_F(phi_deg, eps_deg, S=S0, n=365):
    return sum(daily_F(phi_deg, eps_deg * math.sin(2 * math.pi * i / n), S)
               for i in range(n)) / n


def area_avg(vals):
    w = [math.cos(math.radians(p)) for p in range(len(vals))]
    return sum(v * ww for v, ww in zip(vals, w)) / sum(w)


# ---- 校准(克莱姆法则解 3x3) ----
F0 = [A * mean_F(p, EPS0) for p in range(91)]
F0m, F0m2 = area_avg(F0), area_avg([f * f for f in F0])


def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


M = [[F0[0], F0[0] ** 2, 1.0],
     [F0[-1], F0[-1] ** 2, 1.0],
     [F0m, F0m2, 1.0]]
rhs = [300 - T_G, 240 - T_G, 280 - T_G]
D0 = det3(M)
a, c, b = [(det3([r[:j] + [rhs[i]] + r[j + 1:] for i, r in enumerate(M)]) / D0)
           for j in range(3)]
print(f"校准: a={a:.4f}  c={c:.3e}  b={b:.1f}  "
      f"(验证 T(0)={T_G+a*F0[0]+c*F0[0]**2+b:.1f}, "
      f"T(90)={T_G+a*F0[-1]+c*F0[-1]**2+b:.1f})\n")


def temp_field(eps_deg, x, n=91):
    """年均温度场 = 设定分布 + 映射差分.
    基线 T0(φ)=300−60sin⁴φ(设定); 增量 Δ = [a·q+c·q²] − [a·q₀+c·q₀²], q=A·F(1+x)."""
    k = 1 + x
    out = []
    for p in range(n):
        q = A * mean_F(p, eps_deg) * k
        q0 = A * mean_F(p, EPS0)
        base = 300 - 60 * math.sin(math.radians(p)) ** 4
        out.append(base + (a * q + c * q * q) - (a * q0 + c * q0 * q0))
    return out


def ice_line(Ts):
    if Ts[0] < 273:
        return None          # 全球冻结
    return next((p for p, t in enumerate(Ts) if t < 273), 90)


def season_range(eps_deg, x):
    """45° 夏至-冬至温度差"""
    k = 1 + x
    fs, fw = A * daily_F(45, eps_deg, S0), A * daily_F(45, -eps_deg, S0)
    t = lambda q: T_G + a * q + c * q * q + b
    return t(fs * k) - t(fw * k)


# ---- 输出 4 张矩阵 ----
fields = {}
print("表A 赤道温度 (K)      行=倾角 列=光照")
hdr = "倾角\\光照  " + "  ".join(f"{t:>7}" for t in XTAGS)
for name, fn in (
    ("赤道温度", lambda e, x: temp_field(e, x)[0]),
    ("极点温度", lambda e, x: temp_field(e, x)[-1]),
    ("冰线纬度", lambda e, x: (lambda il: "全球冻结" if il is None
                               else (f"{il}°" if il < 90 else "无冰"))(ice_line(temp_field(e, x)))),
    ("季节(45°年较差 K)", lambda e, x: season_range(e, x)),
):
    print()
    print(f"◆ {name}")
    print(hdr)
    for e in EPSILONS:
        row = "  ".join(f"{fn(e, x):>7.1f}" if isinstance(fn(e, x), float) else f"{fn(e, x):>7}"
                        for x in XS)
        print(f"{e:>7.2f}°  {row}")

print()
print("注: 温度含温室 25 K; 冰线为年均 273 K 纬度; 季节为 45° 夏至-冬至温度差.")
