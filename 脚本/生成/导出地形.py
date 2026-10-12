#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出主行星地形为 CSV(附件/主行星地形.csv)

与 脚本/生成/生成_星球地图.py 同种子、同网格重算分形地形,按面积加权定海平面。
高度指固体地形(不含水):海平面为 0,陆地 0–4800 m(最高峰约 4.8 km),
海底为负值(最深海沟约 -5.3 km)。
表格:首行=经度(°),首列=纬度(°),单元格为高度(m)。

运行: python3 脚本/生成/导出地形.py
"""

import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "附件", "主行星地形.csv")
OUT_PNG = "/tmp/地形_csv_预览.png"

SEED = 6347447676
NX, NY = 480, 240
TARGET_OCEAN = 0.80
SCALES = (1, 2, 4, 8, 16, 32)
WEIGHTS = (0.40, 0.85, 1.00, 0.85, 0.65, 0.50)
BASE = 20
最高峰 = 4800.0   # m
最深海沟 = 5300.0  # m


def sphere_fbm():
    rng = np.random.default_rng(SEED)
    lon = np.linspace(-180.0, 180.0, NX, endpoint=False)
    lat = np.linspace(90.0, -90.0, NY)
    LON, LAT = np.meshgrid(np.radians(lon), np.radians(lat))
    P = np.stack([np.cos(LAT) * np.cos(LON), np.cos(LAT) * np.sin(LON), np.sin(LAT)], -1).reshape(-1, 3)
    out = np.zeros(P.shape[0])
    for s, wgt in zip(SCALES, WEIGHTS):
        K = BASE * s
        w = 0.35 / (s * s)
        dirs = rng.normal(size=(K, 3))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        amp = wgt * rng.normal(size=K)
        for i in range(0, P.shape[0], 20000):
            out[i:i + 20000] += (amp * np.exp((P[i:i + 20000] @ dirs.T - 1.0) / w)).sum(1)
    out = (out - out.mean()) / out.std()
    return out.reshape(NY, NX), lon, lat


def 海平面(h, lat, target):
    W = np.cos(np.radians(lat))[:, None] * np.ones((1, h.shape[1]))
    hs, ws = h.ravel(), W.ravel()
    order = np.argsort(hs)
    cum = np.cumsum(ws[order]) / ws.sum()
    thr = hs[order][np.searchsorted(cum, target)]
    return thr, (ws * (hs < thr)).sum() / ws.sum()


def main():
    h, lon, lat = sphere_fbm()
    thr, ocean = 海平面(h, lat, TARGET_OCEAN)
    高程 = np.where(h > thr, (h - thr) / (h.max() - thr) * 最高峰,
                     -(thr - h) / (thr - h.min()) * 最深海沟)
    高程 = np.round(高程, 1)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("纬度\\经度," + ",".join(f"{x:.1f}" for x in lon) + "\n")
        for j in range(NY):
            f.write(f"{lat[j]:.1f}," + ",".join(f"{v:g}" for v in 高程[j]) + "\n")

    陆 = 高程 > 0
    print(f"网格 {NY}×{NX}  海平面阈值 {thr:.3f}  海洋占比 {ocean*100:.2f}%  陆地 {陆.mean()*100:.2f}%")
    print(f"陆地最高 {高程.max():.0f} m  平均海拔(陆地) {高程[陆].mean():.0f} m")
    print(f"已写出 {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)")

    # 连通陆块(经纬相邻,经向周期)概览:面积占比、中心经纬、最高
    from scipy import ndimage
    结构 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    标号, 数 = ndimage.label(陆, structure=结构)
    print(f"连通陆块数 {数}")
    面 = np.bincount(标号.ravel())[1:]
    for i in np.argsort(面)[::-1][:12]:
        k = i + 1
        ys, xs = np.where(标号 == k)
        纬, 经 = lat[int(ys.mean())], lon[int(xs.mean())]
        print(f"  块{k:>3}  面积 {面[i]/陆.size*100:5.2f}%  中心约 {纬:5.1f}°, {经:6.1f}°  峰值 {高程[标号 == k].max():.0f} m")


if __name__ == "__main__":
    main()