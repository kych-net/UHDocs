#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主行星 地形草稿生成
—— 球面分形随机场(固定种子可复现)生成海底与陆地地形,
   按球面面积加权确定海平面,使海洋占比落在 70–80%。
输出 图片/星球地图草稿.svg(矢量)。运行: python3 脚本/生成_星球地图.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_SVG = os.path.join(ROOT, "图片", "星球地图草稿.svg")
OUT_PNG = "/tmp/星球地图_预览.png"

SEED = 634734342231276         # 随机种子(固定)
NX, NY = 480, 240        # 经度 × 纬度 网格
TARGET_OCEAN = 0.85      # 目标海洋面积占比

# 多尺度权重:压低最大尺度(避免单一超级大陆),抬高中小尺度(大陆 + 群岛)
SCALES = (1, 2, 4, 8, 16, 32)
WEIGHTS = (0.40, 0.85, 1.00, 0.85, 0.65, 0.50)
BASE = 20                # 每尺度基础特征数


def sphere_fbm(nx, ny, seed, scales=SCALES, weights=WEIGHTS, base=BASE):
    """球面高斯随机场叠加(fBm),在单位球面上采样,无极点伪影。"""
    rng = np.random.default_rng(seed)
    lon = np.linspace(-180.0, 180.0, nx, endpoint=False)
    lat = np.linspace(90.0, -90.0, ny)
    LON, LAT = np.meshgrid(np.radians(lon), np.radians(lat))
    P = np.stack([np.cos(LAT) * np.cos(LON),
                  np.cos(LAT) * np.sin(LON),
                  np.sin(LAT)], axis=-1).reshape(-1, 3)
    out = np.zeros(P.shape[0])
    for s, wgt in zip(scales, weights):
        K = base * s
        w = 0.35 / (s * s)
        dirs = rng.normal(size=(K, 3))
        nrm = np.linalg.norm(dirs, axis=1, keepdims=True)
        dirs = dirs / np.where(nrm > 0.0, nrm, 1.0)
        amp = wgt * rng.normal(size=K)
        for i in range(0, P.shape[0], 20000):
            d = P[i:i + 20000] @ dirs.T
            out[i:i + 20000] += (amp * np.exp((d - 1.0) / w)).sum(axis=1)
    out -= out.mean()
    out /= out.std()
    return out.reshape(ny, nx), lon, lat


def sea_level(h, lat, target):
    """按面积权重(cos φ)求海平面阈值,使海洋占比 = target。"""
    W = np.cos(np.radians(lat))[:, None] * np.ones((1, h.shape[1]))
    hs, ws = h.ravel(), W.ravel()
    order = np.argsort(hs)
    cum = np.cumsum(ws[order]) / ws.sum()
    thr = hs[order][np.searchsorted(cum, target)]
    frac = (ws * (hs < thr)).sum() / ws.sum()
    return thr, frac


def main():
    h, lon, lat = sphere_fbm(NX, NY, SEED)
    if not np.isfinite(h).all():
        raise RuntimeError("地形场含 NaN/Inf")
    thr, ocean = sea_level(h, lat, TARGET_OCEAN)
    land = 1.0 - ocean
    print(f"种子 {SEED} · 网格 {NX}×{NY}")
    print(f"海平面阈值 h = {thr:.3f}(归一化)")
    print(f"海洋面积占比 = {ocean*100:.2f}%   陆地 = {land*100:.2f}%")

    LON, LAT = np.meshgrid(lon, lat)
    hmin, hmax = float(h.min()), float(h.max())

    # 海洋:按深度分 4 级;陆地:按高度分 4 级
    ocean_levels = [hmin - 0.1, thr - 1.5, thr - 0.8, thr - 0.35, thr]
    ocean_colors = ["#08203A", "#0E2E50", "#16406B", "#2E6E9E"]
    land_levels = [thr, thr + 0.4, thr + 0.9, thr + 1.6, hmax + 0.1]
    land_colors = ["#4E7A3F", "#6E8446", "#96884F", "#C4B48C"]

    # 纯地形底图:无标题、图例、坐标、经纬网、气候带线(那些属独立图层)
    fig = plt.figure(figsize=(12, 6), dpi=110)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_axis_off()
    ax.set_facecolor(ocean_colors[0])

    ax.contourf(LON, LAT, h, levels=ocean_levels, colors=ocean_colors, zorder=1)
    ax.contourf(LON, LAT, h, levels=land_levels, colors=land_colors, zorder=2)
    ax.contour(LON, LAT, h, levels=[thr], colors="#08131F", linewidths=0.4, zorder=3)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)

    fig.savefig(OUT_SVG, format="svg")
    fig.savefig(OUT_PNG, dpi=110)
    plt.close(fig)
    print(f"已写出 {OUT_SVG}")
    print(f"预览 {OUT_PNG}")


if __name__ == "__main__":
    main()