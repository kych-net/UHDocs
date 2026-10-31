#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主行星 洋流 / 温度 / 降水 三张图

地形取自 附件/主行星地形.csv(首行经度、首列纬度,值=高度 m,海面=0)。
不再用球面帽近似,直接按地图上的真实陆块形状计算:
  陆块识别(经度周期连通) → 按面积降序取前六块对应 L1–L6(正文标称)。
  温度 T = 纬向温(φ) − Γ_env·h(陆地海拔) + 洋流海温异常(近岸向陆地扩散);
  洋流 由纬向风带驱动的地转流函数 ψ(∇²ψ=ζ,陆地 ψ=0)在真实海陆掩上求解;
  降水 由纬向雨带 × 海陆(海洋性) × 地形(迎风抬升/背风雨影)给出。

输出 图片/主行星洋流图.svg、主行星温度图.svg、主行星降水图.svg。
运行: python3 脚本/生成/生成_气候图.py
"""

import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import lsqr
from scipy.ndimage import distance_transform_edt, gaussian_filter, label
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
import matplotlib.patheffects as pe

plt.rcParams["font.family"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "LXGW WenKai"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
图片 = os.path.join(ROOT, "图片")
地形CSV = os.path.join(ROOT, "附件", "主行星地形.csv")

# ---------- 基本参数 ----------
# 大气成分(取自 附件/模块.typ):He 76% 主导,平均摩尔质量 0.01062 kg/mol,
# 质量加权定压比热 c_p≈2150 J/(kg·K) → 对流层干绝热递减率 Γ_干=g/c_p
# 环境递减率取干绝热的一部分(水汽凝结释放潜热,环境率低于干绝热;此星水汽仅 1%,取 3/4)
重力, c_p = 20.0, 2150.8
κ_凝结 = 0.75
Γ_env = κ_凝结 * 重力 / c_p        # ≈6.98 K/km

T_赤道, T_极点 = 300.0, 240.0      # K 海平面纬向年均温
Φ_热 = np.degrees(np.arcsin(((T_赤道 - 293.0) / (T_赤道 - T_极点)) ** 0.25))   # ≈36°
Φ_寒 = np.degrees(np.arcsin(((T_赤道 - 273.0) / (T_赤道 - T_极点)) ** 0.25))   # ≈55°

风带 = [(0.0, 10.0, "赤道辐合带"), (10.0, 25.0, "信风带"), (25.0, 35.0, "副热带高压"),
      (35.0, 55.0, "西风带"), (55.0, 90.0, "极地东风")]

# 纬向雨带(相对值,mm/yr 量级):赤道多雨、副热带干旱、中纬锋面、极地干冷
雨带_φ = [0, 10, 20, 28, 35, 45, 55, 70, 90]
雨带_P = [2200, 1500, 900, 350, 450, 850, 650, 300, 100]

# 完整 Köppen 气候类型(0 = 海洋;其余按此顺序编号)
# 配色按气候族分色系:A 绿 / B 橙黄 / C 蓝青 / D 紫 / E 灰白,族内再用明度区分
类别 = [
    ("Af", "热带雨林", "#12762A"),
    ("Am", "热带季风", "#3E9E33"),
    ("Aw", "热带草原", "#8DC63F"),
    ("As", "热带夏干", "#B6CE4A"),
    ("BWh", "热沙漠", "#E07B33"),
    ("BWk", "冷沙漠", "#C7915A"),
    ("BSh", "热草原", "#EFC63A"),
    ("BSk", "冷草原", "#D8C68A"),
    ("Cfa", "亚热带湿润热夏", "#2F7DC8"),
    ("Cfb", "温带海洋暖夏", "#5DA6DC"),
    ("Cfc", "温带海洋冷夏", "#9BCBEA"),
    ("Cwa", "亚热带季风热夏", "#159E9E"),
    ("Cwb", "亚热带季风暖夏", "#45BEB0"),
    ("Cwc", "亚热带季风冷夏", "#86D2C6"),
    ("Csa", "地中海热夏", "#B0629B"),
    ("Csb", "地中海暖夏", "#C68CB4"),
    ("Csc", "地中海冷夏", "#D8B4CE"),
    ("Dfa", "大陆湿润热夏", "#6A4C99"),
    ("Dfb", "大陆湿润暖夏", "#8A6BB6"),
    ("Dfc", "大陆湿润冷夏", "#AB90D2"),
    ("Dfd", "大陆湿润极冷夏", "#C6B2E2"),
    ("Dwa", "大陆冬干热夏", "#4553A8"),
    ("Dwb", "大陆冬干暖夏", "#6875C4"),
    ("Dwc", "大陆冬干冷夏", "#929CDA"),
    ("Dwd", "大陆冬干极冷夏", "#B8BFEA"),
    ("Dsa", "大陆夏干热夏", "#8A3F7A"),
    ("Dsb", "大陆夏干暖夏", "#A45D92"),
    ("Dsc", "大陆夏干冷夏", "#BE83AE"),
    ("Dsd", "大陆夏干极冷夏", "#D3A9C7"),
    ("ET", "苔原", "#9AA6AE"),
    ("EF", "冰原", "#F2F6FA"),
]
海色 = "#DCE6EC"                                     # 0 号:海洋
气候名 = [c[1] for c in 类别]
气候色 = [c[2] for c in 类别]
码 = {c[0]: i + 1 for i, c in enumerate(类别)}       # 类型码 → 索引(1..N)


def 纬向温(φ):
    return T_赤道 - (T_赤道 - T_极点) * np.sin(np.radians(φ)) ** 4


def 纬向雨(φ):
    return np.interp(np.abs(φ), 雨带_φ, 雨带_P)


def 纬向风(φ):
    a = np.abs(φ)
    return np.interp(a, [0, 10, 17, 30, 45, 60, 75, 90], [0.0, -0.15, -1.0, -0.2, 1.0, 0.9, -0.5, -0.4])


def 风应力(φ):
    u = 纬向风(φ)
    return -u * np.abs(u)


def 读地形():
    """读 附件/主行星地形.csv → 高程(m), lon(°), lat(°)"""
    with open(地形CSV, encoding="utf-8") as f:
        head = f.readline().strip().split(",")
    lon = np.array([float(x) for x in head[1:]])
    data = np.loadtxt(地形CSV, delimiter=",", skiprows=1)
    lat = data[:, 0]
    高程 = data[:, 1:]
    return 高程, lon, lat


def 大陆块(高程, lon, lat):
    """经度周期连通的陆块(仅真实陆地,高程>0);返回按球面面积降序的块列表"""
    NY, NX = 高程.shape
    陆 = 高程 > 0.0
    ext = np.concatenate([陆, 陆[:, :1]], axis=1)               # 复制首列到末尾,打通 180°
    结构 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    标, 数 = label(ext, structure=结构)
    标 = 标[:, :-1]                                             # 去掉复制列
    # 合并首末列(同一行上,两标号若都属陆则视为同块)
    parent = list(range(数 + 1))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    for j in range(NY):
        a, b = 标[j, 0], 标[j, -1]
        if a and b: union(a, b)
    # 重映射
    roots = {r: i + 1 for i, r in enumerate(sorted({find(k) for k in range(1, 数 + 1)}))}
    标 = np.vectorize(lambda v: roots[find(v)] if v else 0)(标)
    # 面积(球面, cosφ 加权)
    W = np.cos(np.radians(lat))[:, None] * np.ones((1, NX))
    总 = W.sum()
    块 = []
    for k in np.unique(标):
        if k == 0: continue
        m = 标 == k
        面 = W[m].sum() / 总
        ys, xs = np.where(m)
        # 球面质心(向量平均,经度圆均值)
        φ = np.radians(lat[ys]); λ = np.radians(lon[xs])
        v = np.stack([np.cos(φ) * np.cos(λ), np.cos(φ) * np.sin(λ), np.sin(φ)], -1)
        v = (v * W[m][:, None]).sum(0)
        v /= np.linalg.norm(v)
        块.append(dict(标=k, 面积=面, 掩=m,
                       φ=float(np.degrees(np.arcsin(v[2]))),
                       λ=float(np.degrees(np.arctan2(v[1], v[0]))),
                       φ1=float(lat[ys].min()), φ2=float(lat[ys].max()),
                       峰=float(高程[m].max()), 均海拔=float(高程[m].mean())))
    块.sort(key=lambda b: b["面积"], reverse=True)
    return 块


def 解洋流(陆掩, lat, LON):
    """∇²ψ = ζ(风应力旋度),陆地 ψ=0;返回流函数 ψ"""
    NY, NX = 陆掩.shape
    dλ = np.radians(360.0 / NX)
    dφ = np.radians(180.0 / (NY - 1))
    c = np.maximum(np.cos(np.radians(lat))[:, None] * np.ones((1, NX)), 1e-2)
    τλ = 风应力(lat)[:, None] * np.ones((1, NX))
    ζ = -np.gradient(τλ * c, axis=0) / (c * dφ)
    ζ = np.where(陆掩, 0.0, ζ)
    海 = ~陆掩
    while True:
        邻 = np.roll(海, 1, 0) + np.roll(海, -1, 0) + np.roll(海, 1, 1) + np.roll(海, -1, 1)
        孤 = 海 & (邻 == 0)
        if not 孤.any(): break
        海 &= ~孤
    陆掩 = ~海
    idx = -np.ones((NY, NX), int)
    oy, ox = np.where(~陆掩)
    idx[oy, ox] = np.arange(len(oy))
    rows, cols, vals = [], [], []
    for k in range(len(oy)):
        j, i = oy[k], ox[k]
        diag = 0.0
        for (jj, ii) in ((j - 1, i), (j + 1, i), (j, (i - 1) % NX), (j, (i + 1) % NX)):
            if jj < 0 or jj >= NY or 陆掩[jj, ii]: continue
            wgt = (1.0 / (c[j, 0] ** 2 * dλ ** 2) if ii != i
                   else np.cos(np.radians(0.5 * (lat[j] + lat[jj]))) / (c[j, 0] * dφ ** 2))
            rows.append(k); cols.append(idx[jj, ii]); vals.append(wgt); diag -= wgt
        rows.append(k); cols.append(k); vals.append(diag)
    A = coo_matrix((vals, (rows, cols)), shape=(len(oy),) * 2).tocsr()
    ψ = np.zeros((NY, NX))
    ψ[oy, ox] = lsqr(A, ζ[oy, ox], atol=1e-10, btol=1e-10, iter_lim=8000)[0]
    return ψ


def 场():
    高程, lon, lat = 读地形()
    NY, NX = 高程.shape
    LON, LAT = np.meshgrid(lon, lat)
    块 = 大陆块(高程, lon, lat)
    陆掩 = 高程 > 0.0

    ψ = 解洋流(陆掩, lat, LON)
    dλ = np.radians(360.0 / NX); dφ = np.radians(180.0 / (NY - 1))
    c = np.maximum(np.cos(np.radians(LAT)), 1e-2)
    u = -np.gradient(ψ, axis=0) / dφ
    v = np.gradient(ψ, axis=1) / (c * dλ)
    尺 = np.sqrt(u ** 2 + v ** 2)
    u, v = u / 尺.max(), v / 尺.max()
    u = np.where(陆掩, 0.0, u); v = np.where(陆掩, 0.0, v)

    # dT/dφ(rad) = -240·sin³φ·cosφ  (T = 300 − 60·sin⁴φ)
    dTdφ = -240.0 * np.sin(np.radians(LAT)) ** 3 * np.cos(np.radians(LAT)) * np.pi / 180.0
    异常海 = np.where(陆掩, 0.0, np.clip(-3.0 * v * dTdφ, -5.0, 5.0))
    海温 = 纬向温(LAT) + 异常海
    # 近岸海温异常向陆地扩散(归一化高斯外推)
    海 = ~陆掩
    σ = 6.0
    w = gaussian_filter(海.astype(float), σ)
    异常陆 = gaussian_filter(异常海, σ) / (w + 1e-6)
    陆温 = 纬向温(LAT) - Γ_env * 高程 + np.where(陆掩, 异常陆, 0.0)
    温度 = np.where(陆掩, 陆温, 海温)

    # 降水:纬向雨带 × 海洋性 × 地形抬升/雨影
    dy = np.radians(180.0 / (NY - 1)) * 6371.0                  # km/格(纬向)
    dx = np.radians(360.0 / NX) * 6371.0                        # km/格(经向,赤道)
    距海 = distance_transform_edt(陆掩, sampling=(dy, dx * 0.7))  # 陆地到海的距离 km
    海洋性 = np.where(陆掩, 1.0 / (1.0 + 距海 / 1300.0), 1.0)
    坡向 = np.gradient(高程, axis=1) / (c * np.radians(360.0 / NX) * 6371.0)
    抬升 = 纬向风(LAT) * 坡向
    抬升 = 抬升 / (np.std(抬升[陆掩]) + 1e-9)
    地形因子 = np.where(陆掩, np.clip(1.0 + 0.6 * 抬升, 0.2, 3.0), 1.0)
    降水 = np.clip(纬向雨(LAT) * 海洋性 * 地形因子, 10.0, 4000.0)

    # ---- 完整 Köppen 分类 ----
    # 月温:年均温 ± 半年较差(纬度决定基础较差,大陆性放大;海洋年较差小)
    tC = 温度 - 273.15
    A基 = np.interp(np.abs(LAT), [0.0, 20.0, 45.0, 90.0], [3.0, 8.0, 20.0, 40.0])
    大陆性 = np.where(陆掩, np.clip(1.0 - 海洋性, 0.0, 1.0), 0.0)
    A年差 = A基 * (1.0 + 0.6 * 大陆性)
    月 = np.arange(12)[:, None, None]
    位相 = np.where(LAT >= 0.0, 6.0, 0.0)[None]              # 最暖月:北半球 7 月,南半球 1 月
    月温 = 温度[None] + (A年差 / 2.0)[None] * np.cos(2.0 * np.pi * (月 - 位相) / 12.0)
    Tw = 月温.max(0) - 273.15                                # 最暖月均温
    Tc = 月温.min(0) - 273.15                                # 最冷月均温
    N10 = (月温 >= 283.15).sum(0)                            # ≥10℃ 的月数

    # 月降水:纬向雨带随赤道辐合带季节移动(±15°),再按年总量归一
    高日 = np.where(LAT[None] >= 0.0, (月 >= 3) & (月 <= 8), (月 < 3) | (月 > 8))
    φ_ITCZ = 15.0 * np.cos(2.0 * np.pi * (月 - 6.0) / 12.0)
    月雨基 = 纬向雨(LAT[None] - φ_ITCZ)
    月雨 = np.clip(月雨基 * (降水 / 月雨基.mean(0))[None], 0.0, None)
    大 = 1e9
    夏月最大 = np.where(高日, 月雨, -大).max(0)
    夏月最小 = np.where(高日, 月雨, 大).min(0)
    冬月最大 = np.where(~高日, 月雨, -大).max(0)
    冬月最小 = np.where(~高日, 月雨, 大).min(0)
    P年 = 降水
    夏雨 = (月雨 * 高日).sum(0)
    冬雨 = P年 - 夏雨

    气候 = np.zeros_like(温度, dtype=int)
    未定 = 陆掩.copy()

    # E 极地:最暖月 < 10℃(EF < 0℃)
    极 = 未定 & (Tw < 10.0)
    气候[极 & (Tw < 0.0)] = 码["EF"]
    气候[极 & (Tw >= 0.0)] = 码["ET"]
    未定 &= ~极

    # B 干旱:年降水 < 干旱阈值(夏雨集中抬高阈值、冬雨集中压低)
    夏占比 = 夏雨 / np.maximum(P年, 1e-6)
    P阈 = 20.0 * tC + np.where(夏占比 >= 0.7, 280.0, np.where(夏占比 <= 0.3, 140.0, 0.0))
    干 = 未定 & (P年 < P阈)
    沙漠 = P年 < 0.5 * P阈
    气候[干 & 沙漠 & (tC >= 18.0)] = 码["BWh"]
    气候[干 & 沙漠 & (tC < 18.0)] = 码["BWk"]
    气候[干 & ~沙漠 & (tC >= 18.0)] = 码["BSh"]
    气候[干 & ~沙漠 & (tC < 18.0)] = 码["BSk"]
    未定 &= ~干

    # A 热带:最冷月 ≥ 18℃
    热 = 未定 & (Tc >= 18.0)
    Pm = 月雨.min(0)
    Af = Pm >= 60.0
    Am = (~Af) & (Pm >= 100.0 - P年 / 25.0)
    气候[热 & Af] = 码["Af"]
    气候[热 & Am] = 码["Am"]
    气候[热 & ~Af & ~Am & (夏雨 >= 冬雨)] = 码["Aw"]        # 冬干
    气候[热 & ~Af & ~Am & (夏雨 < 冬雨)] = 码["As"]          # 夏干
    未定 &= ~热

    # C 温带 / D 大陆:最冷月 > −3℃ 为 C,否则 D
    夏干 = (夏月最小 < 40.0) & (夏月最小 < 冬月最大 / 3.0)
    冬干 = 冬月最小 < 夏月最大 / 10.0
    季节 = np.where(夏干, "s", np.where(冬干, "w", "f"))
    温C = np.where(Tw >= 22.0, 0, np.where(N10 >= 4, 1, 2))
    温D = np.where(Tc <= -38.0, 3, 温C)
    季表 = {
        "C": {"f": ["Cfa", "Cfb", "Cfc"], "w": ["Cwa", "Cwb", "Cwc"], "s": ["Csa", "Csb", "Csc"]},
        "D": {"f": ["Dfa", "Dfb", "Dfc", "Dfd"], "w": ["Dwa", "Dwb", "Dwc", "Dwd"],
              "s": ["Dsa", "Dsb", "Dsc", "Dsd"]},
    }
    for 基, 掩 in (("C", 未定 & (Tc > -3.0)), ("D", 未定 & (Tc <= -3.0))):
        级 = 温C if 基 == "C" else 温D
        for 季, 码表 in 季表[基].items():
            for k, 类型 in enumerate(码表):
                气候[掩 & (季节 == 季) & (级 == k)] = 码[类型]
    气候 = np.where(陆掩, 气候, 0)

    return dict(LON=LON, LAT=LAT, 陆掩=陆掩, 高程=高程, u=u, v=v, 块=块, 气候=气候,
                海温=海温, 温度=温度, 异常海=异常海, 降水=降水, lat=lat)


# ---------- SVG 压缩(抽稀 0.5 pt + 0.5 网格 + 相对坐标 + 删未用字形) ----------
_SVG记号 = re.compile(r"[MmLlZzCcSsQqTtAaHhVv]|-?\d+(?:\.\d+)?(?:e[-+]?\d+)?")
网格 = 0.5
抽稀容差 = 0.5


def _抽稀(pts, eps):
    """Douglas-Peucker:删掉偏离首尾连线不到 eps 的点。"""
    if len(pts) < 3:
        return pts
    留 = [False] * len(pts)
    留[0] = 留[-1] = True
    栈 = [(0, len(pts) - 1)]
    while 栈:
        i, j = 栈.pop()
        if j <= i + 1:
            continue
        x1, y1 = pts[i]
        x2, y2 = pts[j]
        dx, dy = x2 - x1, y2 - y1
        长 = np.hypot(dx, dy)
        最远, 最远i = -1.0, -1
        for k in range(i + 1, j):
            x0, y0 = pts[k]
            if 长 == 0:
                偏 = np.hypot(x0 - x1, y0 - y1)
            else:
                偏 = abs(dx * (y1 - y0) - (x1 - x0) * dy) / 长
            if 偏 > 最远:
                最远, 最远i = 偏, k
        if 最远 > eps:
            留[最远i] = True
            栈.append((i, 最远i))
            栈.append((最远i, j))
    return [p for p, k in zip(pts, 留) if k]


def _数格式(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _数列(值):
    """连写坐标:负数自带分隔符,正数前留一个空格。"""
    出 = ""
    for s in 值:
        if 出 and not s.startswith("-"):
            出 += " "
        出 += s
    return 出


def _压缩路径(d):
    """M/L/z 折线:0.5 网格取整、0.5 pt 抽稀、转相对坐标;含曲线命令则原样返回。"""
    记号 = _SVG记号.findall(d)
    if any(t.isalpha() and t not in "MmLlZz" for t in 记号):
        return d
    出, i, n = [], 0, len(记号)
    当前 = (0.0, 0.0)
    while i < n:
        t = 记号[i]
        if t in "Zz":
            出.append("z")
            i += 1
            continue
        if t not in "MmLl":
            return d
        相对 = t.islower()
        i += 1
        pts = []
        while i < n:
            if 记号[i] in "MmLl":
                if 记号[i] in "Mm":
                    break
                相对 = 记号[i].islower()
                i += 1
                continue
            if 记号[i] in "Zz":
                break
            if 记号[i].isalpha() or i + 1 >= n:
                return d
            x, y = float(记号[i]), float(记号[i + 1])
            if 相对:
                x += 当前[0]
                y += 当前[1]
            当前 = (x, y)
            pts.append((round(x / 网格) * 网格, round(y / 网格) * 网格))
            i += 2
        if not pts:
            return d
        pts = _抽稀(pts, 抽稀容差)
        出.append("M" + _数列([_数格式(pts[0][0]), _数格式(pts[0][1])]))
        if len(pts) > 1:
            相 = []
            上 = pts[0]
            for x, y in pts[1:]:
                相 += [_数格式(x - 上[0]), _数格式(y - 上[1])]
                上 = (x, y)
            出.append("l" + _数列(相))
    return "".join(出)


def 压缩svg(路径):
    s = open(路径, encoding="utf-8").read()
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    引用 = set(re.findall(r'(?:xlink:href|href)="#([^"]+)"', s)) | \
        set(re.findall(r"url\(#([^)]+)\)", s))
    s = re.sub(r'<path id="([^"]+)"[^>]*/>',
               lambda m: m.group(0) if m.group(1) in 引用 else "", s)
    s = re.sub(r' d="([^"]*)"', lambda m: ' d="%s"' % _压缩路径(m.group(1)), s)
    s = re.sub(r">\s+<", "><", s).replace("\n", "")
    open(路径, "w", encoding="utf-8").write(s)


# ---------- 图幅公共设置 ----------
def 底图(ax, F, 标题, 线色="#ffffff"):
    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 30)); ax.set_yticks(np.arange(-90, 91, 15))
    ax.set_xticklabels([f"{x}°" for x in np.arange(-180, 181, 30)], fontsize=7.5)
    ax.set_yticklabels([f"{y}°" for y in np.arange(-90, 91, 15)], fontsize=7.5)
    ax.grid(color=线色, alpha=0.35, lw=0.6, zorder=2)
    ax.contour(F["LON"], F["LAT"], F["陆掩"].astype(float), levels=[0.5],
               colors="#111111", linewidths=0.6, zorder=4)
    for lo, hi, 名 in 风带:
        for s in (-1, 1):
            ax.axhline(s * hi, color=线色, lw=0.7, ls=":", alpha=0.7, zorder=3)
        ax.text(-0.05, (lo + hi) / 2.0, 名, fontsize=7, color="#555555",
                ha="right", va="center", transform=ax.get_yaxis_transform(), clip_on=False)
    for i, b in enumerate(F["块"][:6]):
        名 = f"L{i+1}"
        ax.text(b["λ"], b["φ"], 名, fontsize=11, fontweight="bold", color="#111111",
                ha="center", va="center", zorder=7,
                path_effects=[pe.withStroke(linewidth=2.2, foreground="#ffffff")])
    ax.set_title(标题, fontsize=13, pad=10)


def 出图(文件名, 体):
    out = os.path.join(图片, 文件名)
    fig = plt.figure(figsize=(12.0, 6.8), dpi=110)
    ax = fig.add_axes([0.085, 0.17, 0.775, 0.73])
    体(ax)
    fig.savefig(out, format="svg", transparent=True)
    fig.savefig("/tmp/" + os.path.basename(out) + ".png", dpi=110)
    plt.close(fig)
    压缩svg(out)
    print("已写出", out)


def main():
    F = 场()
    LON, LAT = F["LON"], F["LAT"]
    W = np.cos(np.radians(F["lat"]))[:, None] * np.ones_like(LON)   # 面积权重 cosφ

    print("=" * 100)
    print(f"纬向温 T=300-60·sin⁴φ;热带界 {Φ_热:.1f}°,寒带界 {Φ_寒:.1f}°;Γ_env={Γ_env*1000:.1f} K/km")
    print("=" * 100)
    print(f"{'块':>3}{'大陆':>5}{'面积%':>8}{'中心纬':>8}{'中心经':>9}{'纬度范围':>16}"
          f"{'均海拔km':>9}{'峰值km':>8}{'地表均温K':>10}{'年降水mm':>10}  {'主气候(Köppen)':<16}")
    print("-" * 120)
    for i, b in enumerate(F["块"][:6]):
        m = b["掩"]
        纬程 = f"{b['φ1']:.0f}°~{b['φ2']:.0f}°"
        w = W[m]
        均温 = (F["温度"][m] * w).sum() / w.sum()
        均降 = (F["降水"][m] * w).sum() / w.sum()
        众 = np.array([w[F["气候"][m] == k].sum() for k in range(len(类别) + 1)])
        k = int(np.argmax(众[1:])) + 1
        主 = f"{类别[k-1][0]} {气候名[k-1]}"
        print(f"{b['标']:>3}{'L'+str(i+1):>5}{b['面积']*100:>8.2f}{b['φ']:>8.1f}{b['λ']:>9.1f}"
              f"{纬程:>16}{b['均海拔']/1000:>9.2f}{b['峰']/1000:>8.2f}"
              f"{均温:>10.1f}{均降:>10.0f}  {主}")
    print("-" * 120)
    # 全行星陆地气候构成(面积加权)
    陆W = W[F["陆掩"]]
    构成 = [(气候名[k-1], 类别[k-1][0], 陆W[F["气候"][F["陆掩"]] == k].sum() / 陆W.sum())
            for k in range(1, len(类别) + 1)]
    构成 = [c for c in 构成 if c[2] > 0]
    构成.sort(key=lambda c: c[2], reverse=True)
    print("陆地气候构成(面积占比):  " + "  ".join(f"{c[1]}{c[0]} {c[2]*100:.1f}%" for c in 构成))
    总 = sum(b["面积"] for b in F["块"][:6])
    print(f"前六块合计面积 {总*100:.2f}%  (正文标称 9.9+7.8+3.0+1.3+0.9+0.4 = {9.9+7.8+3.0+1.3+0.9+0.4:.1f}%)")

    # ---- 图1 洋流 ----
    def 画洋流(ax):
        m = ax.pcolormesh(LON, LAT, F["异常海"], cmap="coolwarm", vmin=-5, vmax=5,
                          shading="auto", rasterized=True)
        step = 9
        qx, qy = LON[::step, ::step], LAT[::step, ::step]
        qu, qv = F["u"][::step, ::step], F["v"][::step, ::step]
        g = np.hypot(qu, qv) > 1e-6
        ax.quiver(qx[g], qy[g], qu[g] / np.hypot(qu, qv)[g], qv[g] / np.hypot(qu, qv)[g],
                  color="#101010", scale_units="xy", scale=0.12, width=0.0045, zorder=5)
        底图(ax, F, "主行星 洋流图 · 表层流(箭头)与海温异常(底色)")
        cb = plt.colorbar(m, ax=ax, pad=0.015, fraction=0.03)
        cb.set_label("海温异常 (K):红=暖流加温,蓝=寒流降温", fontsize=8)
    出图("主行星洋流图.svg", 画洋流)

    # ---- 图2 温度 ----
    def 画温度(ax):
        m = ax.pcolormesh(LON, LAT, F["温度"], cmap="RdYlBu_r", vmin=230, vmax=300,
                          shading="auto", rasterized=True)
        for φ, 名 in ((Φ_热, f"293 K · 热带界 {Φ_热:.0f}°"), (Φ_寒, f"273 K · 寒带界 {Φ_寒:.0f}°")):
            for s in (-1, 1):
                ax.axhline(s * φ, color="#111111", lw=0.9, ls=(0, (7, 4)), zorder=6)
            ax.text(-178, φ + 1.5, 名, fontsize=7.5, color="#111111", zorder=7)
        底图(ax, F, "主行星 温度图 · 地形 + 洋流修正后的年均温")
        cb = plt.colorbar(m, ax=ax, pad=0.015, fraction=0.03)
        cb.set_label("年均温 (K)", fontsize=8.5)
    出图("主行星温度图.svg", 画温度)

    # ---- 图3 降水 ----
    def 画降水(ax):
        m = ax.pcolormesh(LON, LAT, F["降水"], cmap="YlGnBu", vmin=0, vmax=2500,
                          shading="auto", rasterized=True)
        cs = ax.contour(LON, LAT, F["降水"], levels=[250, 500, 1000, 2000],
                        colors="#333333", linewidths=0.5, zorder=6)
        ax.clabel(cs, fmt="%d", fontsize=6.5)
        底图(ax, F, "主行星 降水图 · 纬向雨带 × 海洋性 × 地形抬升/雨影")
        cb = plt.colorbar(m, ax=ax, pad=0.015, fraction=0.03)
        cb.set_label("年降水量 (mm)", fontsize=8.5)
    出图("主行星降水图.svg", 画降水)

    # ---- 图4 气候 ----
    def 画气候(ax):
        色表 = [海色] + 气候色                                # 0=海洋,其后依次为各气候类型
        cmap = ListedColormap(色表)
        norm = BoundaryNorm(np.arange(-0.5, len(色表) + 0.5, 1.0), len(色表))
        ax.pcolormesh(LON, LAT, F["气候"], cmap=cmap, norm=norm,
                      shading="auto", rasterized=True)
        底图(ax, F, "主行星 气候图 · 完整 Köppen 分类", 线色="#4A4A4A")
        现码 = sorted(set(np.unique(F["气候"][F["陆掩"]])) - {0})
        图例 = [Patch(facecolor=气候色[k - 1], edgecolor="#666666",
                      label=f"{类别[k-1][0]}  {气候名[k-1]}") for k in 现码]
        ncol = 6 if len(图例) > 10 else 4
        ax.legend(handles=图例, loc="upper center", bbox_to_anchor=(0.5, -0.04),
                  ncol=ncol, fontsize=6.8, frameon=False, handlelength=1.1,
                  columnspacing=1.0, handletextpad=0.5)
    出图("主行星气候图.svg", 画气候)


if __name__ == "__main__":
    main()