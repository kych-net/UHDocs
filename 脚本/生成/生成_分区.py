#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按气候与地形细化大陆分区

把 L1–L6 各自切成若干次级区:对(气候型 × 海拔带)做连通区,按球面面积筛选。
输出 图片/主行星分区图.svg 与分区属性表(中心/面积/海拔/气温/降水/气候)。
运行: python3 脚本/生成/生成_分区.py
"""

import os
import importlib.util
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from scipy.ndimage import label, distance_transform_edt
from matplotlib.patches import Patch

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 复用 生成_气候图.py 的地形/气候模型(模块导入不会执行其 main)
_spec = importlib.util.spec_from_file_location(
    "气候模型", os.path.join(ROOT, "脚本", "生成", "生成_气候图.py"))
气候 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(气候)

海拔界 = [300.0, 1000.0, 2000.0]                      # 低地/台地/高原/高山
海拔名 = ["低地", "台地", "高原", "高山"]
plt.rcParams["font.family"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "LXGW WenKai"]
plt.rcParams["axes.unicode_minus"] = False


def 主():
    F = 气候.场()
    LON, LAT = F["LON"], F["LAT"]
    高程, 气候码 = F["高程"], F["气候"]
    温度, 降水 = F["温度"], F["降水"]
    W = np.cos(np.radians(F["lat"]))[:, None] * np.ones_like(LON)
    总 = W.sum()
    带 = np.digitize(高程, 海拔界)                     # 0..3
    key = 气候码 * 4 + 带
    块 = F["块"][:6]

    分区 = np.zeros_like(气候码)                       # 分区编号(仅用于出图)
    编号 = 0
    候选表 = []
    for i, b in enumerate(块):
        m = b["掩"]
        候选 = []
        for v in np.unique(key[m]):
            cm = m & (key == v)
            lab, n = label(cm)                         # 同键值的连通区
            for k in range(1, n + 1):
                sub = lab == k
                a = W[sub].sum() / 总                  # 占行星表面
                if a < 0.03 * b["面积"]:                # 小于大陆面积 3% 的碎块不单列
                    continue
                候选.append((a, sub))
        候选.sort(key=lambda t: -t[0])
        for a, sub in 候选[:8]:
            编号 += 1
            分区[sub] = 编号
            候选表.append((编号, i, a))

    # 大陆内部未列入的陆地按最近邻并入已有区(填满六块大陆,不留飞白)
    六大 = np.zeros(气候码.shape, bool)
    for b in 块:
        六大 |= b["掩"]
    陆 = 六大
    if (陆 & (分区 == 0)).any():
        近 = distance_transform_edt(分区 == 0, return_indices=True)[1]
        分区 = np.where(陆 & (分区 == 0), 分区[近[0], 近[1]], 分区)

    记录 = []                                          # (区名, 属性)
    for i, b in enumerate(块):
        本 = [(k, a) for k, ii, a in 候选表 if ii == i]
        print("=" * 108)
        print(f"L{i+1}  面积 {b['面积']*100:.2f}%  中心 {b['φ']:.0f}°,{b['λ']:.0f}°  "
              f"纬度 {b['φ1']:.0f}°~{b['φ2']:.0f}°  均海拔 {b['均海拔']/1000:.2f} km")
        print(f"{'区':>5}{'占大陆%':>9}{'占表面%':>9}{'中心':>16}{'纬度范围':>13}"
              f"{'均海拔km':>9}{'峰km':>7}{'均温K':>8}{'年降水mm':>10}{' Köppen':>9}{'  地形'}")
        print("-" * 108)
        for j, (k, _) in enumerate(本, 1):
            sub = (分区 == k) & b["掩"]
            w = W[sub]
            a = w.sum() / 总
            ys, xs = np.where(sub)
            φv = np.radians(F["lat"][ys]); λv = np.radians(LON[ys, xs])
            vec = np.stack([np.cos(φv) * np.cos(λv), np.cos(φv) * np.sin(λv),
                            np.sin(φv)], -1)
            vec = (vec * w[:, None]).sum(0); vec /= np.linalg.norm(vec)
            码c = np.array([w[气候码[sub] == c].sum() for c in range(1, len(气候.类别) + 1)])
            气候c = int(np.argmax(码c)) + 1
            带c = int(round((w * 带[sub]).sum() / w.sum()))
            r = dict(面=a, φ=float(np.degrees(np.arcsin(vec[2]))),
                     λ=float(np.degrees(np.arctan2(vec[1], vec[0]))),
                     纬=f"{F['lat'][ys].min():.0f}°~{F['lat'][ys].max():.0f}°",
                     海拔=float((高程[sub] * w).sum() / w.sum()),
                     峰=float(高程[sub].max()),
                     温=float((温度[sub] * w).sum() / w.sum()),
                     降=float((降水[sub] * w).sum() / w.sum()))
            名 = f"L{i+1}-{j}"
            记录.append((名, r))
            码str = 气候.类别[气候c - 1][0]
            print(f"{名:>5}{a/b['面积']*100:>9.1f}{a*100:>9.2f}"
                  f"{f'{r[chr(966)]:.0f}' + chr(176) + ', ' + f'{r[chr(955)]:.0f}' + chr(176):>16}"
                  f"{r['纬']:>13}{r['海拔']/1000:>9.2f}{r['峰']/1000:>7.2f}"
                  f"{r['温']:>8.1f}{r['降']:>10.0f}{码str:>9}  {海拔名[带c]}")

    # ---- 出图 ----
    色 = np.vstack([plt.get_cmap(n)(np.linspace(0, 1, 20))[:, :3]
                   for n in ("tab20", "tab20b", "tab20c")])
    cmap = {k: 色[(k - 1) % len(色)] for k in range(1, 编号 + 1)}
    fig = plt.figure(figsize=(12.0, 6.8), dpi=110)
    ax = fig.add_axes([0.085, 0.10, 0.775, 0.79])
    ax.set_facecolor("#DCE6EC")
    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 30)); ax.set_yticks(np.arange(-90, 91, 15))
    ax.set_xticklabels([f"{x}°" for x in np.arange(-180, 181, 30)], fontsize=7.5)
    ax.set_yticklabels([f"{y}°" for y in np.arange(-90, 91, 15)], fontsize=7.5)
    ax.grid(color="#4A4A4A", alpha=0.3, lw=0.6, zorder=2)
    for k in range(1, 编号 + 1):
        ax.contourf(LON, LAT, (分区 == k).astype(float), levels=[0.5, 1.5],
                    colors=[cmap[k]], zorder=3)
    ax.contour(LON, LAT, F["陆掩"].astype(float), levels=[0.5],
               colors="#111111", linewidths=0.6, zorder=4)
    for 名, r in 记录:
        ax.text(r["λ"], r["φ"], 名, fontsize=7.5, fontweight="bold", color="#111111",
                ha="center", va="center", zorder=7,
                path_effects=[pe.withStroke(linewidth=2.0, foreground="#ffffff")])
    for i, b in enumerate(块):
        ax.text(b["λ"], b["φ"], f"L{i+1}", fontsize=15, fontweight="bold", color="#B02020",
                ha="center", va="center", zorder=8,
                path_effects=[pe.withStroke(linewidth=3.0, foreground="#ffffff")])
    ax.set_title("主行星 大陆分区草图 · 气候型 × 海拔带", fontsize=13, pad=10)
    out = os.path.join(ROOT, "图片", "主行星分区图.svg")
    fig.savefig(out, format="svg", transparent=True)
    fig.savefig("/tmp/主行星分区图.svg.png", dpi=110)
    plt.close(fig)
    气候.压缩svg(out)
    print(f"\n已写出 {out}")
    print(f"预览 /tmp/主行星分区图.svg.png  共 {编号} 个次级区")


if __name__ == "__main__":
    主()