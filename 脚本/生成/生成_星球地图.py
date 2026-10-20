#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主行星 地形草稿生成
—— 球面分形随机场(固定种子可复现)生成基础海底与陆地地形,
   再沿若干随机大圆弧段叠加线状构造脊: 落在陆地上的段隆起为山脉,
   落在海洋中的段断续露出海面成为岛链。
   按球面面积加权确定海平面,使海洋占比落在 70–80%。
输出 图片/星球地图草稿.svg(矢量)。运行: python3 脚本/生成_星球地图.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from scipy.ndimage import gaussian_filter, map_coordinates

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_SVG = os.path.join(ROOT, "图片", "星球地图草稿.svg")
OUT_PNG = "/tmp/星球地图_预览.png"

SEED = 6347447676         # 随机种子(固定)
NX, NY = 480, 240        # 经度 × 纬度 网格
TARGET_OCEAN = 0.80      # 目标海洋面积占比

# 多尺度权重:压低最大尺度(避免单一超级大陆),抬高中小尺度(大陆 + 群岛)
SCALES = (1, 2, 4, 8, 16, 32)
WEIGHTS = (0.40, 0.85, 1.00, 0.85, 0.65, 0.50)
BASE = 20                # 每尺度基础特征数

# ---- 线状构造(山脉 / 岛链)参数 ----
脊SEED = SEED + 7         # 构造曲线独立随机流
曲线数 = 18               # 随机曲线条数
脊宽 = (0.050, 0.100)     # 脊的横向半宽(弧度,附近似高斯:约 2.9°–5.7°)
脊幅 = (0.60, 1.00)       # 单条曲线脊的相对强度(最终归一化)
脊强 = 1.6                # 脊隆起整体倍率(在 fBm 归一化后的尺度上)
曲线长 = (0.6, 2.6)       # 单条曲线弧长(弧度,约 34°–150°)
步角 = (0.18, 0.45)       # 曲线每步转角(弧度), 越大越蜿蜒(非大圆)
采样步长 = 0.012          # 曲线离散采样点间距(弧度)
平滑 = 3.0                # 定曲线走向用的地形平滑尺度(格), 压掉小噪保留大陆轮廓
段数 = (3, 7)             # 单条曲线上纵向起伏段个数(山脉峰谷 / 岛链断续)


def sphere_fbm(nx, ny, seed, scales=SCALES, weights=WEIGHTS, base=BASE, 脊带=None):
    """球面高斯随机场叠加(fBm),在单位球面上采样,无极点伪影。

    脊带: 可选 (ny,nx) 脊隆起场。在归一化前与 fBm 同场相加,
    使脊成为地形场内生的组成部分, 而非事后叠加的独立一层。
    """
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
    if 脊带 is not None:                       # 脊隆起并入地形场(内生), 再统一成一场
        out = out + 脊带.reshape(-1)
    return out.reshape(ny, nx), lon, lat


def 地形梯度场(Hs, lon, lat):
    """由平滑地形场构造球面梯度查询: 输入单位向量 p, 返回该点最陡上升的球面切向。

    曲线沿"垂直于梯度"的方向(即等高线)行进, 因而走向与大陆/海洋轮廓协调。
    """
    latr = np.radians(lat)
    dlon = np.radians(lon[1] - lon[0])
    gLon = (np.roll(Hs, -1, axis=1) - np.roll(Hs, 1, axis=1)) / (2 * dlon)
    东 = gLon / np.maximum(np.cos(latr)[:, None], 0.05)   # 地面东向梯度
    北 = np.gradient(Hs, latr, axis=0)                    # 地面北向梯度
    NY, NX = Hs.shape
    lon0, lat0, dlat = lon[0], lat[0], lat[1] - lat[0]

    def 查(p):
        φ = np.degrees(np.arcsin(np.clip(p[2], -1.0, 1.0)))
        λ = np.degrees(np.arctan2(p[1], p[0]))
        row = (lat0 - φ) / (-dlat) if dlat < 0 else (φ - lat0) / dlat
        col = (λ - lon0) / 360.0 * NX
        col %= NX
        coords = np.array([[row], [col]])
        ge = float(map_coordinates(东, coords, order=1, mode="nearest")[0])
        gn = float(map_coordinates(北, coords, order=1, mode="nearest")[0])
        λr, φr = np.radians(λ), np.radians(φ)
        e_east = np.array([-np.sin(λr), np.cos(λr), 0.0])
        e_north = np.array([-np.sin(φr) * np.cos(λr),
                            -np.sin(φr) * np.sin(λr), np.cos(φr)])
        return ge * e_east + gn * e_north
    return 查


def _随机切向(rng, p):
    e = np.cross(p, rng.normal(size=3))
    n = np.linalg.norm(e)
    if n < 1e-9:
        e = np.cross(p, np.array([1.0, 0.0, 0.0]))
        n = np.linalg.norm(e)
    return e / n


def _地形曲线(rng, 梯):
    """生成一条与地形协调的球面曲线: 每步沿等高线方向(垂直于地形梯度)前进,
    带惯性(不折返)与随机扰动; 再用 slerp 细分成密集采样点。

    返回 (采样点 (M,3), 沿曲线累积弧长 (M,))。
    """
    L = rng.uniform(*曲线长)
    n = max(2, int(round(L / rng.uniform(*步角))))
    每步 = L / n
    p = rng.normal(size=3)
    p /= np.linalg.norm(p)
    ctrl = [p]
    前向 = None
    for _ in range(n):
        g = 梯(p)
        g = g - (g @ p) * p
        ng = np.linalg.norm(g)
        if ng > 1e-9:
            沿 = np.cross(p, g / ng)                      # 等高线方向
            候选 = 沿 if (前向 is None or (沿 @ 前向) >= 0.0) else -沿
        else:
            候选 = _随机切向(rng, p)
        方向 = 0.6 * 候选 + 0.5 * _随机切向(rng, p)       # 扰动避免死贴轮廓
        方向 = 方向 - (方向 @ p) * p
        方向 /= np.linalg.norm(方向)
        α = 每步 * rng.uniform(0.4, 1.6)
        p = p * np.cos(α) + 方向 * np.sin(α)
        p /= np.linalg.norm(p)
        前向 = 方向
        ctrl.append(p)

    点 = [ctrl[0][None, :]]
    弧 = [0.0]
    acc = 0.0
    for i in range(len(ctrl) - 1):                       # slerp 细分
        a, b = ctrl[i], ctrl[i + 1]
        Ω = float(np.arccos(np.clip(a @ b, -1.0, 1.0)))
        m = max(1, int(np.ceil(Ω / 采样步长)))
        f = np.linspace(0.0, 1.0, m + 1)[1:]
        if Ω > 1e-6:
            段 = (np.sin((1 - f) * Ω)[:, None] * a + np.sin(f * Ω)[:, None] * b) / np.sin(Ω)
        else:
            段 = np.tile(a, (m, 1))
        点.append(段)
        弧.extend(acc + f * Ω)
        acc += Ω
    return np.vstack(点), np.array(弧)


def 脊带场(nx, ny, seed, 梯):
    """由沿等高线行进的曲线生成脊隆起场(归一化到 [0,1])。

    脊是地形场的内生构造: 结果并入 sphere_fbm 的同一场(归一化前), 不是事后叠加。
    脊宽取数度, 使脊成为宽缓的山系 / 岛链, 与地形平滑衔接, 不割裂地形。
    """
    rng = np.random.default_rng(seed)
    lon = np.linspace(-180.0, 180.0, nx, endpoint=False)
    lat = np.linspace(90.0, -90.0, ny)
    LON, LAT = np.meshgrid(np.radians(lon), np.radians(lat))
    P = np.stack([np.cos(LAT) * np.cos(LON),
                  np.cos(LAT) * np.sin(LON),
                  np.sin(LAT)], axis=-1).reshape(-1, 3).astype(np.float32)

    采样, 幅, 宽, 调制 = [], [], [], []
    for _ in range(曲线数):
        点, 弧 = _地形曲线(rng, 梯)
        L = 弧[-1] if 弧[-1] > 0.0 else 1.0
        σ = rng.uniform(*脊宽)
        幅i = rng.uniform(*脊幅)
        k = 2 * np.pi * rng.integers(*段数) / L
        相位 = rng.uniform(0.0, 2 * np.pi)
        t = 弧 / L
        采样.append(点)
        幅.append(np.full(len(点), 幅i))
        宽.append(np.full(len(点), σ))
        调制.append(np.sin(np.pi * np.clip(t, 0.0, 1.0)) ** 0.7    # 两端渐隐
                    * (0.5 + 0.5 * np.sin(k * 弧 + 相位)))        # 沿脊起伏
    C = np.vstack(采样).astype(np.float32)
    Cf = np.concatenate(幅).astype(np.float32)
    Cσ = np.concatenate(宽).astype(np.float32)
    Cm = np.concatenate(调制).astype(np.float32)
    Cv = np.ascontiguousarray(C.T)                       # (3, K)

    R = np.zeros(P.shape[0], dtype=np.float32)
    块 = 4096
    for i in range(0, P.shape[0], 块):                   # 分块取最近采样点
        dot = P[i:i + 块] @ Cv
        idx = np.argmax(dot, axis=1)
        cos = dot[np.arange(len(idx)), idx]
        δ = np.arccos(np.clip(cos, -1.0, 1.0))
        R[i:i + 块] = Cf[idx] * Cm[idx] * np.exp(-(δ / Cσ[idx]) ** 2)
    R = R.reshape(ny, nx)
    return R / max(float(R.max()), 1e-9)                 # 归一化到 [0,1]


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
    h, lon, lat = sphere_fbm(NX, NY, SEED)                # 基础 fBm, 定曲线走向
    Hs = gaussian_filter(h, sigma=平滑, mode="nearest")
    梯 = 地形梯度场(Hs, lon, lat)
    脊 = 脊带场(NX, NY, 脊SEED, 梯)
    h, lon, lat = sphere_fbm(NX, NY, SEED, 脊带=脊强 * 脊)   # 脊并入地形场(内生)
    if not np.isfinite(h).all():
        raise RuntimeError("地形场含 NaN/Inf")
    thr, ocean = sea_level(h, lat, TARGET_OCEAN)
    land = 1.0 - ocean
    print(f"种子 {SEED} · 网格 {NX}×{NY}")
    print(f"内生脊带 {曲线数} 条 · 脊强 {脊强} · 地形范围 {h.min():.2f}~{h.max():.2f}")
    print(f"海平面阈值 h = {thr:.3f}(归一化)")
    print(f"海洋面积占比 = {ocean*100:.2f}%   陆地 = {land*100:.2f}%")

    LON, LAT = np.meshgrid(lon, lat)
    hmin, hmax = float(h.min()), float(h.max())

    # 按高度连续设色: 深海 → 浅海 → 海岸 → 陆地 → 高山(无分层)
    t = (thr - hmin) / (hmax - hmin)          # 海平面在 0–1 色标上的位置
    cmap = LinearSegmentedColormap.from_list("uh地形", [
        (0.0,                 "#01070F"),   # 深渊
        (t * 0.28,            "#062A4A"),   # 深海
        (t * 0.52,            "#0B4E7A"),   # 中深
        (t * 0.74,            "#1478A8"),   # 中浅
        (t * 0.90,            "#2FA8CC"),   # 浅海
        (t * 0.97,            "#6FD0DE"),   # 礁湖(亮青)
        (t,                   "#E8DCA8"),   # 海岸(沙)
        (t + (1 - t) * 0.06,  "#3E7D2E"),   # 平原(深绿)
        (t + (1 - t) * 0.18,  "#5C9333"),   # 草地(绿)
        (t + (1 - t) * 0.32,  "#8FA845"),   # 丘陵(黄绿)
        (t + (1 - t) * 0.46,  "#C3A85C"),   # 高地(黄棕)
        (t + (1 - t) * 0.60,  "#9C7B48"),   # 山地(棕)
        (t + (1 - t) * 0.72,  "#8A8478"),   # 裸岩(灰)
        (t + (1 - t) * 0.86,  "#CFC8BC"),   # 高山(浅岩)
        (1.0,                 "#FFFFFF"),   # 雪线(白)
    ])

    # 纯地形底图:无标题、图例、坐标、经纬网、气候带线(那些属独立图层)
    fig = plt.figure(figsize=(12, 6), dpi=110)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_axis_off()
    ax.set_facecolor("#08203A")

    ax.pcolormesh(LON, LAT, h, cmap=cmap, norm=Normalize(hmin, hmax),
                  shading="auto", zorder=1, rasterized=True)
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