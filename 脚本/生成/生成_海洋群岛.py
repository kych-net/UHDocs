#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主行星 深海盆 O1–O4 与群岛 A1–A3 定位

深海盆:海底高程 < -1500 m 的连通区(经度周期),面积≥0.2%,按球面面积降序取前四 → O1–O4。
群岛:高程 > 0 但不属前六大块的陆块,列出各岛并归入 A1–A3。
只读, 输出属性表。运行: python3 脚本/生成/生成_海洋群岛.py
"""

import os
import importlib.util
import numpy as np
from scipy.ndimage import label

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "气候模型", os.path.join(ROOT, "脚本", "生成", "生成_气候图.py"))
气候 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(气候)

阈值 = -1500.0
结构 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])


def 周期连通掩(条件, NY, NX):
    """经度周期连通的连通区标号(已合并首末列)"""
    ext = np.concatenate([条件, 条件[:, :1]], axis=1)
    标, n = label(ext, structure=结构)
    标 = 标[:, :-1]
    par = list(range(n + 1))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for j in range(NY):
        a, b = 标[j, 0], 标[j, -1]
        if a and b:
            ra, rb = find(a), find(b)
            if ra != rb:
                par[rb] = ra
    roots = {}
    for k in range(1, n + 1):
        roots.setdefault(find(k), len(roots) + 1)
    return np.vectorize(lambda v: roots[find(v)] if v else 0)(标)


def 属性(m, 高程, lon, lat, W, 总):
    ys, xs = np.where(m)
    a = W[m].sum() / 总
    φ = np.radians(lat[ys]); λ = np.radians(lon[xs])
    v = np.stack([np.cos(φ) * np.cos(λ), np.cos(φ) * np.sin(λ), np.sin(φ)], -1)
    v = (v * W[m][:, None]).sum(0); v /= np.linalg.norm(v)
    最i = np.argmin(高程[m])
    return dict(面=a, φ=float(np.degrees(np.arcsin(v[2]))),
                λ=float(np.degrees(np.arctan2(v[1], v[0]))),
                纬=(float(lat[ys].min()), float(lat[ys].max())),
                均=float(高程[m].mean()), 峰=float(高程[m].max()),
                最深=float(高程[m].min()),
                最深φ=float(lat[ys[最i]]), 最深λ=float(lon[xs[最i]]))


def 主():
    高程, lon, lat = 气候.读地形()
    NY, NX = 高程.shape
    W = np.cos(np.radians(lat))[:, None] * np.ones((1, NX))
    总 = W.sum()
    块 = 气候.大陆块(高程, lon, lat)
    大陆 = np.zeros_like(高程, bool)
    for b in 块[:6]:
        大陆 |= b["掩"]

    print("=" * 96)
    print("一、深海盆(高程 < -1500 m, 面积≥0.2%)")
    print("=" * 96)
    标 = 周期连通掩(高程 < 阈值, NY, NX)
    盆 = []
    for k in np.unique(标):
        if k == 0:
            continue
        m = 标 == k
        r = 属性(m, 高程, lon, lat, W, 总)
        if r["面"] < 0.002:
            continue
        盆.append((r, m))
    盆.sort(key=lambda t: -t[0]["面"])
    print(f"{'序':>3}{'占表面%':>9}{'中心':>17}{'纬度范围':>14}{'均深m':>8}{'最深m':>8}"
          f"{'最深点':>17}")
    print("-" * 96)
    for i, (r, _) in enumerate(盆[:8], 1):
        c = f"{r['λ']:.0f}°{'E' if r['λ']>=0 else 'W'}, {r['φ']:.0f}°{'N' if r['φ']>=0 else 'S'}"
        d = f"{r['最深λ']:.0f}°{'E' if r['最深λ']>=0 else 'W'},{r['最深φ']:.0f}°{'N' if r['最深φ']>=0 else 'S'}"
        print(f"{i:>3}{r['面']*100:>9.2f}{c:>17}"
              f"{f'{r[chr(32428)][0]:.0f}~{r[chr(32428)][1]:.0f}':>14}"
              f"{r['均']:>8.0f}{r['最深']:>8.0f}{d:>17}")

    print()
    print("=" * 96)
    print("二、岛屿(高程 > 0, 不属前六大块)")
    print("=" * 96)
    标岛 = 周期连通掩((高程 > 0.0) & (~大陆), NY, NX)
    岛 = []
    for k in np.unique(标岛):
        if k == 0:
            continue
        m = 标岛 == k
        r = 属性(m, 高程, lon, lat, W, 总)
        岛.append((r, m))
    岛.sort(key=lambda t: -t[0]["面"])
    print(f"共 {len(岛)} 个岛块, 合计 {sum(r['面'] for r,_ in 岛)*100:.2f}%")
    print(f"{'占表面%':>9}{'中心':>17}{'纬度范围':>14}{'均海拔m':>9}{'峰m':>8}")
    print("-" * 96)
    for r, _ in 岛[:30]:
        c = f"{r['λ']:.0f}°{'E' if r['λ']>=0 else 'W'}, {r['φ']:.0f}°{'N' if r['φ']>=0 else 'S'}"
        print(f"{r['面']*100:>9.3f}{c:>17}"
              f"{f'{r[chr(32428)][0]:.0f}~{r[chr(32428)][1]:.0f}':>14}"
              f"{r['均']:>9.0f}{r['峰']:>8.0f}")

    print("\n六大块中心(供群岛方位参照):")
    for i, b in enumerate(块[:6], 1):
        print(f"  L{i}: {b['λ']:.0f}°,{b['φ']:.0f}°  纬 {b['φ1']:.0f}~{b['φ2']:.0f}  面积 {b['面积']*100:.1f}%")

    # ---- 群岛分组:按最近锚点(L1 / L2 / O2深盆)归入 A3 / A1 / A2 ----
    def 单位(λ, φ):
        λ, φ = np.radians(λ), np.radians(φ)
        return np.array([np.cos(φ) * np.cos(λ), np.cos(φ) * np.sin(λ), np.sin(φ)])
    锚 = {
        "A1": 单位(块[1]["λ"], 块[1]["φ"]),          # L2 东缘弧形岛链
        "A2": 单位(盆[1][0]["λ"], 盆[1][0]["φ"]),    # O2 西侧散岛
        "A3": 单位(块[0]["λ"], 块[0]["φ"]),          # L1 北缘环极岛链
    }
    print("\n" + "=" * 96)
    print("三、群岛分组(归最近锚点)")
    print("=" * 96)
    组 = {k: [] for k in 锚}
    for r, _ in 岛:
        v = 单位(r["λ"], r["φ"])
        名 = max(锚, key=lambda k: np.dot(v, 锚[k]))
        组[名].append(r)
    for k in ("A1", "A2", "A3"):
        rs = 组[k]
        合计 = sum(r["面"] for r in rs)
        c = A = 0.0
        vv = np.zeros(3)
        for r in rs:
            vv += 单位(r["λ"], r["φ"]) * r["面"]
        vv /= np.linalg.norm(vv)
        print(f"\n{k}: {len(rs)} 个岛块, 合计 {合计*100:.2f}%  "
              f"中心 {np.degrees(np.arctan2(vv[1], vv[0])):.0f}°,{np.degrees(np.arcsin(vv[2])):.0f}°")
        for r in rs:
            print(f"    {r['面']*100:6.3f}%  {r['λ']:6.0f}°,{r['φ']:5.0f}°  "
                  f"纬 {r['纬'][0]:.0f}~{r['纬'][1]:.0f}  峰 {r['峰']:.0f}m")


if __name__ == "__main__":
    主()