#!/usr/bin/env python3
"""季节气候候选：纬向能量平衡、蓄热和热输送。只输出结果，不修改正文或图片。"""

import argparse
import importlib.util
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SIGMA = 5.670374419e-8
YEAR = 365.49040838192656 * 86400


def environment():
    path = Path(__file__).with_name("设计_恒星与公转.py")
    spec = importlib.util.spec_from_file_location("star_design", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.existing_environment()


def terrain(n):
    data = np.loadtxt(ROOT / "附件/主行星地形.csv", delimiter=",", skiprows=1)
    lat, height = data[:, 0], data[:, 1:]
    weight = np.cos(np.radians(lat))
    bins = np.clip(((np.sin(np.radians(lat)) + 1) * n / 2).astype(int), 0, n - 1)
    denominator = np.bincount(bins, weights=weight, minlength=n)
    numerator = np.bincount(bins, weights=weight * (height > 0).mean(1), minlength=n)
    good = denominator > 1e-10
    land = np.interp(np.arange(n), np.where(good)[0], numerator[good] / denominator[good])
    return land, lat, height


def insolation(x, tilt, eccentricity, steps=360):
    """真近点角由开普勒方程求出；近日点暂放在北半球冬至。"""
    mean = (np.arange(steps) + .5) / steps * 2 * np.pi
    anomaly = mean.copy()
    for _ in range(8):
        anomaly -= (anomaly - eccentricity * np.sin(anomaly) - mean) / (
            1 - eccentricity * np.cos(anomaly))
    true = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(anomaly / 2),
                           np.sqrt(1 - eccentricity) * np.cos(anomaly / 2))
    declination = np.arcsin(np.sin(np.radians(tilt)) * np.sin(true - np.pi / 2))
    flux = 1360 * np.sqrt(1 - eccentricity**2) / (1 - eccentricity * np.cos(anomaly))**2
    phi = np.arcsin(x)
    cosh = np.clip(-np.tan(declination[:, None]) * np.tan(phi), -1, 1)
    hour = np.arccos(cosh)
    return flux[:, None] / np.pi * (hour * np.sin(declination[:, None]) * x
           + np.cos(declination[:, None]) * np.sqrt(1 - x*x) * np.sin(hour))


def factor_matrix(capacity, dt, diffusion, x):
    """有限体积零通量边界；输送项隐式求解，南北极不交换热量。"""
    n, dx = len(x), 2 / len(x)
    edge = np.linspace(-1, 1, n + 1)
    conductance = diffusion * (1 - edge**2) / dx**2
    left = -dt / capacity * conductance[:-1]
    right = -dt / capacity * conductance[1:]
    diagonal = 1 - left - right
    reduced = diagonal.copy()
    upper = np.zeros(n)
    upper[0] = right[0] / reduced[0]
    for i in range(1, n):
        reduced[i] -= left[i] * upper[i-1]
        upper[i] = right[i] / reduced[i]
    return left, reduced, upper


def solve(rhs, factors):
    left, diagonal, upper = factors
    out = np.empty(len(rhs))
    out[0] = rhs[0] / diagonal[0]
    for i in range(1, len(rhs)):
        out[i] = (rhs[i] - left[i] * out[i-1]) / diagonal[i]
    for i in range(len(rhs) - 2, -1, -1):
        out[i] -= upper[i] * out[i+1]
    return out


def run(args):
    env = environment()
    n = args.latitudes
    x = -1 + (np.arange(n) + .5) * 2 / n
    phi = np.degrees(np.arcsin(x))
    land, terrain_lat, height = terrain(n)
    atm_capacity = env["cp"] * env["海平面气压"] / env["重力"]
    capacity = atm_capacity + (1 - land) * 1000 * 4184 * args.mixed_layer + land * 2e6
    q = insolation(x, args.tilt, args.eccentricity) * args.flux
    dt = YEAR / len(q)
    factors = factor_matrix(capacity, dt, args.diffusion, x)
    temp = 300 - 60 * x**4 if args.initial == "warm" else np.full(n, 235.)
    last = None
    drift = float("inf")
    for year in range(args.years):
        record = []
        absorbed, emitted = [], []
        start = temp.copy()
        for incoming in q:
            # 格点有效反照率含云与地表；冰雪是温度控制的诊断代理。
            frozen = np.clip((273.15 - temp) / 10, 0, 1)
            warm_albedo = .26 + .06 * land
            cold_albedo = .52 + .12 * land
            albedo = warm_albedo + (cold_albedo - warm_albedo) * frozen
            asr = incoming * (1 - albedo)
            olr = SIGMA * temp**4 / (1 + .75 * args.tau)
            temp = solve(temp + dt / capacity * (asr - olr), factors)
            record.append(temp.copy())
            absorbed.append(asr.mean())
            emitted.append(olr.mean())
        record = np.array(record)
        if last is not None:
            drift = float(np.max(np.abs(record - last)))
            if drift < args.tolerance:
                break
        last = record.copy()
    mean = record.mean(0)
    monthly = record.reshape(12, len(q) // 12, n).mean(1)
    minimum, maximum = monthly.min(0), monthly.max(0)
    asr_mean, olr_mean = float(np.mean(absorbed)), float(np.mean(emitted))
    storage = float(np.mean(capacity * (temp - start)) / YEAR)
    checks = {
        "最近两年同相位最大温差K": drift,
        "周期收敛": drift < args.tolerance,
        "全球平均日照W_m2": float(q.mean()),
        "吸收短波W_m2": asr_mean, "向外长波W_m2": olr_mean,
        "年度蓄热W_m2": storage,
        "全球能量收支残差W_m2": asr_mean - olr_mean - storage,
    }
    selected = []
    for latitude in (0, 15, 30, 45, 60, 75):
        for sign in ((1,) if latitude == 0 else (1, -1)):
            loc = sign * latitude
            selected.append({
                "纬度": loc,
                "年均K": float(np.interp(loc, phi, mean)),
                "最冷月均K": float(np.interp(loc, phi, minimum)),
                "最暖月均K": float(np.interp(loc, phi, maximum)),
                "年较差K": float(np.interp(loc, phi, maximum - minimum)),
            })
    # 将纬向结果按 7 K/km 的候选地面海拔订正分配到真实陆块。
    # 这是下推方案，不是三维大气或洋流计算；不修改自由大气温度剖面。
    continents = []
    for coords in land_blocks(height):
        ys, xs = coords
        weights = np.cos(np.radians(terrain_lat[ys]))
        annual = np.interp(terrain_lat[ys], phi, mean) - .007 * height[ys, xs]
        cold = np.interp(terrain_lat[ys], phi, minimum) - .007 * height[ys, xs]
        hot = np.interp(terrain_lat[ys], phi, maximum) - .007 * height[ys, xs]
        total_area = np.cos(np.radians(terrain_lat)).sum() * height.shape[1]
        continents.append({
            "占表面百分比": float(weights.sum() / total_area * 100),
            "年均K": float(np.average(annual, weights=weights)),
            "年均温第10百分位K": float(np.percentile(annual, 10)),
            "年均温第90百分位K": float(np.percentile(annual, 90)),
            "各月月均均低于冰点面积比例": float(weights[hot < 273.15].sum() / weights.sum()),
            "存在月均越过冰点面积比例": float(weights[(cold < 273.15) & (hot >= 273.15)].sum() / weights.sum()),
        })
    continents.sort(key=lambda row: -row["占表面百分比"])
    for i, row in enumerate(continents[:6], 1):
        row["大陆"] = f"L{i}"
    result = {
        "状态": "候选灰大气季节能量平衡模型，不等于辐射传输或三维气候验证",
        "参数": vars(args), "运行年数": year + 1, "检查": checks,
        "全球海平面年均K": float(mean.mean()),
        "纬向格点": [{"纬度": float(lat), "年均K": float(t),
                      "最冷月均K": float(lo), "最暖月均K": float(hi)}
                     for lat, t, lo, hi in zip(phi, mean, minimum, maximum)],
        "纬度温度": selected, "六大陆": continents[:6],
        "边界": "海冰与积雪为反照率代理，未计算潜热、冰流和积雪质量；未模拟降水。",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def land_blocks(height):
    """经向周期、四邻连通，与原图六大陆的划分规则一致。"""
    ny, nx = height.shape
    visited = np.zeros(height.shape, dtype=bool)
    for y, x in zip(*np.where(height > 0)):
        if visited[y, x]:
            continue
        visited[y, x] = True
        stack, coords = [(y, x)], []
        while stack:
            j, i = stack.pop()
            coords.append((j, i))
            for jj, ii in ((j-1, i), (j+1, i), (j, (i-1) % nx), (j, (i+1) % nx)):
                if 0 <= jj < ny and not visited[jj, ii] and height[jj, ii] > 0:
                    visited[jj, ii] = True
                    stack.append((jj, ii))
        yield tuple(np.array(v) for v in zip(*coords))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau", type=float, default=.85, help="有效灰光学厚度，尚非组分推导值")
    parser.add_argument("--diffusion", type=float, default=.25, help="有效热输送系数 W/(m² K)")
    parser.add_argument("--mixed-layer", type=float, default=20, help="海洋有效混合层深度 m")
    parser.add_argument("--tilt", type=float, default=23.44)
    parser.add_argument("--eccentricity", type=float, default=.01)
    parser.add_argument("--flux", type=float, default=1, help="天堂调光后平均辐照倍率，仅检验气候响应")
    parser.add_argument("--latitudes", type=int, default=90)
    parser.add_argument("--years", type=int, default=100)
    parser.add_argument("--tolerance", type=float, default=.01)
    parser.add_argument("--initial", choices=("warm", "cold"), default="warm")
    parser.add_argument("--output")
    args = parser.parse_args()
    if not (args.tau >= 0 and args.diffusion >= 0 and args.mixed_layer >= 0
            and 0 <= args.tilt <= 90 and 0 <= args.eccentricity < 1 and args.flux > 0
            and args.latitudes >= 6 and args.years >= 2 and args.tolerance > 0):
        parser.error("参数超出物理或数值有效范围")
    print(json.dumps(run(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
