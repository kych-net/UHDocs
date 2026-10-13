#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主行星 群岛生成（按标注图）

在原地形（附件/主行星地形.csv）基础上叠加群岛，只增不减，不改动原陆地与深海沟：
  · 红色标注线 → 沿线生成岛链（路径上等间距布置岛）
  · 黑色标注圈 → 椭圆范围内撒布群岛（随机小岛）
输出 附件/主行星地形_群岛.csv 与 图片/主行星群岛草图.svg。
运行: python3 脚本/生成/生成_群岛.py

坐标约定：经度 −180~180°，纬度 90~−90°。标注来自手绘截图，
按 图片 x∈[0,377]→经度、y∈[0,188]→纬度 线性映射。
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Patch
import matplotlib.patheffects as pe

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
地形CSV = os.path.join(ROOT, "附件", "主行星地形.csv")
输出CSV = os.path.join(ROOT, "附件", "主行星地形_群岛.csv")
输出SVG = os.path.join(ROOT, "图片", "主行星群岛草图.svg")
预览PNG = "/tmp/主行星群岛草图.png"

SEED = 20261013           # 固定种子，结果可复现
plt.rcParams["font.family"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "LXGW WenKai"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 黑色圈（椭圆）：(中心经度, 中心纬度, 经向半径, 纬向半径) ----
# 本轮只按红线生成岛链，不用圈。
圈 = []

# ---- 红色线（路径）：从新标注图自动提取的折线，(经,纬) ----
线 = [
    [(5, 66), (27, 51), (46, 45), (58, 44), (69, 39), (67, 24), (65, 6), (63, -13), (62, -31)],
    [(-118, 23), (-129, 20), (-139, 11), (-141, 6), (-138, -2), (-143, -10), (-148, -16),
     (-148, -23), (-139, -34), (-144, -44), (-159, -44)],
    [(-53, -8), (-56, -15), (-58, -20), (-60, -25), (-57, -32), (-58, -42), (-57, -47),
     (-46, -52), (-55, -55), (-66, -53)],
    [(120, -28), (127, -32), (135, -34), (142, -33), (149, -31), (156, -33), (161, -36),
     (165, -42), (171, -43), (175, -40)],
    [(9, -8), (4, -12), (0, -16), (-7, -20), (-15, -15), (-23, -11), (-25, -10), (-31, -16)],
    [(104, -24), (105, -18), (105, -11), (106, -4), (108, 2), (111, 8), (115, 15), (119, 22), (124, 28)],
    [(-83, 22), (-87, 18), (-92, 20), (-102, 20)],
    [(-108, 48), (-112, 44), (-113, 38), (-114, 34), (-115, 32)],
]

间距范围 = (1.5, 4.0)       # 岛链上相邻岛的随机中心间距（度）
圈密度 = 1.0 / (7.0 ** 2)   # 圈内每平方度岛数（约 7° 见方一个）
半径范围 = (0.8, 2.8)       # 单岛经/纬半径随机范围（度）
峰高范围 = (250.0, 1500.0)  # 岛峰高出海平面范围（m）


def 读地形():
    with open(地形CSV, encoding="utf-8") as f:
        head = f.readline().strip().split(",")
    经 = np.array([float(x) for x in head[1:]])
    数据 = np.loadtxt(地形CSV, delimiter=",", skiprows=1)
    纬 = 数据[:, 0]
    高程 = 数据[:, 1:]
    return 高程, 经, 纬


def 加岛(H, H_原, clon, clat, rlon, rlat, 峰高, rot, 相位, LO, LA):
    """在 (clon,clat) 叠加一个不规则山包：旋转椭圆 + 极角谐波扭曲，
    峰顶海拔 = 峰高(m)。以原地形为背景，近处隆起、远处回落，只增高不降低。"""
    c = np.cos(np.radians(clat))
    dx = (LO - clon) * c
    dy = LA - clat
    ca, sa = np.cos(rot), np.sin(rot)
    x = dx * ca + dy * sa
    y = -dx * sa + dy * ca
    D = np.hypot(x / rlon, y / rlat)
    θ = np.arctan2(y, x)
    扭曲 = (1.0 + 0.30 * np.sin(3 * θ + 相位[0])
                + 0.22 * np.sin(5 * θ + 相位[1])
                + 0.15 * np.sin(2 * θ + 相位[2]))
    g = np.exp(-2.0 * (D * 扭曲) ** 2)
    场 = H_原 + (峰高 - H_原) * g
    return np.maximum(H, 场)


def 底高(H_原, 经, 纬, clon, clat):
    j = int(np.argmin(np.abs(纬 - clat)))
    i = int(np.argmin(np.abs(经 - clon)))
    return float(H_原[j, i])


def 平滑(路径, 每段=24):
    """Catmull-Rom 样条把折线插值成平滑曲线，返回密集 (经,纬) 点。"""
    P = np.array(路径, float)
    if len(P) < 2:
        return P
    P = np.vstack([P[0], P, P[-1]])          # 端点外插
    段 = []
    for k in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[k - 1], P[k], P[k + 1], P[k + 2]
        t = np.linspace(0, 1, 每段, endpoint=False)[:, None]
        段.append(0.5 * ((2 * p1)
                         + (-p0 + p2) * t
                         + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                         + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    段.append(P[-2][None, :])
    return np.vstack(段)


def 沿线取岛(密点, rng, 间距范围):
    """沿平滑曲线按随机间距取岛中心点。"""
    lon, lat = 密点[:, 0], 密点[:, 1]
    段长 = np.hypot(np.diff(lon) * np.cos(np.radians((lat[:-1] + lat[1:]) / 2)),
                    np.diff(lat))
    s = np.concatenate([[0.0], np.cumsum(段长)])
    总 = s[-1]
    点 = []
    pos = 0.0
    while pos <= 总:
        点.append((float(np.interp(pos, s, lon)), float(np.interp(pos, s, lat))))
        pos += rng.uniform(*间距范围)
    return 点


def 画图(H, H_原, LO, LA):
    海界 = [-6000, -3000, -1500, -500, 0]
    海色 = ["#08203A", "#0E2E50", "#16406B", "#2E6E9E"]
    陆界 = [0, 300, 1000, 2000, 8000]
    陆色 = ["#4E7A3F", "#6E8446", "#96884F", "#C4B48C"]
    RGB = np.zeros(H.shape + (3,))
    for k in range(len(海界) - 1):
        m = (H >= 海界[k]) & (H < 海界[k + 1])
        RGB[m] = matplotlib.colors.to_rgb(海色[k])
    for k in range(len(陆界) - 1):
        m = (H >= 陆界[k]) & (H < 陆界[k + 1])
        RGB[m] = matplotlib.colors.to_rgb(陆色[k])
    RGB[H >= 陆界[-1]] = matplotlib.colors.to_rgb(陆色[-1])

    fig, ax = plt.subplots(figsize=(12, 6.4), dpi=110)
    ax.imshow(RGB, extent=[-180, 180, -90, 90], origin="upper", aspect="auto", zorder=1)

    # 新增陆地（原来海底、现在露出）用洋红半透明填充 + 描边突出
    新陆 = ((H > 0) & (H_原 <= 0)).astype(float)
    rgba = np.zeros(H.shape + (4,))
    rgba[..., 0] = 1.0; rgba[..., 2] = 0.65
    rgba[..., 3] = 新陆 * 0.6
    ax.imshow(rgba, extent=[-180, 180, -90, 90], origin="upper", aspect="auto", zorder=3)
    ax.contour(LO, LA, 新陆, levels=[0.5], colors="#FF00AA", linewidths=1.0, zorder=4)

    for i, (clon, clat, rlon, rlat) in enumerate(圈, 1):
        ax.add_patch(Ellipse((clon, clat), 2 * rlon, 2 * rlat, fill=False,
                             edgecolor="#000000", lw=2.0, zorder=6))
        ax.text(clon, clat, f"C{i}", fontsize=9, fontweight="bold", color="#000000",
                ha="center", va="center", zorder=7,
                path_effects=[pe.withStroke(linewidth=2.2, foreground="#ffffff")])
    for i, 路径 in enumerate(线, 1):
        密 = 平滑(路径)
        ax.plot(密[:, 0], 密[:, 1], color="#D01010", lw=1.8, ls="--", zorder=6)
        ax.text(路径[0][0], 路径[0][1], f"L{i}", fontsize=9, fontweight="bold", color="#D01010",
                ha="center", va="center", zorder=7,
                path_effects=[pe.withStroke(linewidth=2.2, foreground="#ffffff")])

    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 30)); ax.set_yticks(np.arange(-90, 91, 30))
    ax.set_xticklabels([f"{x}°" for x in np.arange(-180, 181, 30)], fontsize=8)
    ax.set_yticklabels([f"{y}°" for y in np.arange(-90, 91, 30)], fontsize=8)
    ax.set_title("主行星 群岛草图 · 红虚线=岛链路径，洋红=新增陆地", fontsize=12)
    fig.tight_layout()
    fig.savefig(输出SVG, format="svg", transparent=True)
    fig.savefig(预览PNG, dpi=110)
    plt.close(fig)


def main():
    H_原, 经, 纬 = 读地形()
    LO, LA = np.meshgrid(经, 纬)
    W = np.cos(np.radians(纬))[:, None] * np.ones_like(LO)
    总 = W.sum()
    rng = np.random.default_rng(SEED)
    H = H_原.copy()
    岛数 = 0

    # 红线 → 平滑曲线上的随机岛链
    for 路径 in 线:
        密点 = 平滑(路径)
        for clon, clat in 沿线取岛(密点, rng, 间距范围):
            h0 = 底高(H_原, 经, 纬, clon, clat)
            峰高 = max(-h0, 0.0) + rng.uniform(*峰高范围)
            rlon = rng.uniform(*半径范围); rlat = rng.uniform(*半径范围)
            rot = rng.uniform(0.0, np.pi)
            相位 = rng.uniform(0.0, 2 * np.pi, 3)
            H = 加岛(H, H_原, clon, clat, rlon, rlat, 峰高, rot, 相位, LO, LA)
            岛数 += 1

    # 黑圈 → 圈内撒岛
    for clon, clat, rlon, rlat in 圈:
        个数 = max(4, int(np.pi * rlon * rlat * 圈密度))
        for _ in range(个数):
            # 椭圆内均匀采样（半径开方保证面元均匀）
            r = np.sqrt(rng.random()); th = rng.random() * 2 * np.pi
            clon_i = clon + rlon * r * np.cos(th)
            clat_i = np.clip(clat + rlat * r * np.sin(th), -89.0, 89.0)
            h0 = 底高(H_原, 经, 纬, clon_i, clat_i)
            峰高 = max(-h0, 0.0) + rng.uniform(*峰高范围)
            rr = rng.uniform(*半径范围, size=2)
            rot = rng.uniform(0.0, np.pi)
            相位 = rng.uniform(0.0, 2 * np.pi, 3)
            H = 加岛(H, H_原, clon_i, clat_i, rr[0], rr[1], 峰高, rot, 相位, LO, LA)
            岛数 += 1

    新陆 = (H > 0) & (H_原 <= 0)
    print(f"种子 {SEED}")
    print(f"生成岛屿 {岛数} 个")
    print(f"原陆地(面积加权) {(W*(H_原>0)).sum()/总*100:.2f}%  →  新陆地 {(W*(H>0)).sum()/总*100:.2f}%")
    print(f"新增陆地(面积加权) {W[新陆].sum()/总*100:.3f}%   新增最高海拔 {H[新陆].max() if 新陆.any() else 0:.0f} m")

    H = np.round(H, 1)
    with open(输出CSV, "w", encoding="utf-8") as f:
        f.write("纬度\\经度," + ",".join(f"{x:.1f}" for x in 经) + "\n")
        for j in range(H.shape[0]):
            f.write(f"{纬[j]:.1f}," + ",".join(f"{v:g}" for v in H[j]) + "\n")
    print(f"已写出 {输出CSV}  ({os.path.getsize(输出CSV)/1e6:.2f} MB)")

    画图(H, H_原, LO, LA)
    print(f"已写出 {输出SVG}\n预览 {预览PNG}")


if __name__ == "__main__":
    main()