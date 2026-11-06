#!/usr/bin/env python3
"""恒星与公转候选复算。只读现有模型，不修改正文或图片；仅用标准库。"""

import argparse
import ast
import json
import math
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
G = 6.67430e-11
SIGMA = 5.670374419e-8
AU = 149597870700.0
SOLAR_MASS = 1.9885e30
SOLAR_RADIUS = 6.957e8
SOLAR_LUMINOSITY = 3.828e26
GAS_CONSTANT = 8.314462618


def existing_environment():
    text = (ROOT / "附件/模块.typ").read_text(encoding="utf-8")

    def number(name):
        match = re.search(r"^#let " + re.escape(name) + r" = ([\d.e+-]+)\s*$", text, re.M)
        if not match:
            raise ValueError(f"无法读取环境参数：{name}")
        return float(match[1])

    species = re.findall(
        r'\(名: "([^"]+)", 质量: ([\d.]+), 自由度: (\d+), 初比: ([\d.]+),', text
    )
    if len(species) != 6:
        raise ValueError("大气物种表结构已变，需复核读取方式")
    total = sum(float(row[3]) for row in species)
    fractions = {name: float(x) / total for name, _, _, x in species}
    molar_mass = sum(float(m) * fractions[name] for name, m, _, _ in species)
    # 原表的“自由度”字段实际作为 2*Cp/R 使用，沿用其比热计算。
    cp = sum(fractions[name] * float(f) / 2 * GAS_CONSTANT
             for name, _, f, _ in species) / molar_mass
    env = {name: number(name) for name in (
        "重力", "海平面气压", "对流层顶温", "平流层顶温", "平流层顶高",
        "中间层顶温", "中间层顶高",
    )}
    env.update(molar_mass=molar_mass, cp=cp, fractions=fractions)
    return env


def existing_aircraft():
    tree = ast.parse((ROOT / "脚本/生成/绘制_飞行包线.py").read_text(encoding="utf-8"))
    names = {"b", "AR", "C_Lmax", "C_D0", "LD_max", "E_st", "m_空"}
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in names:
                values[target.id] = float(ast.literal_eval(node.value))
    if set(values) != names:
        raise ValueError("飞行常数结构已变，需复核读取方式")
    return values


def atmosphere(env, surface_temperature, altitude):
    lapse = env["重力"] / env["cp"]
    top = (surface_temperature - env["对流层顶温"]) / lapse

    def temperature(z):
        if z <= top:
            return surface_temperature - lapse * z
        if z <= env["平流层顶高"]:
            return env["对流层顶温"] + (env["平流层顶温"] - env["对流层顶温"]) * (
                z - top) / (env["平流层顶高"] - top)
        if z < env["中间层顶高"]:
            return env["平流层顶温"] + (env["中间层顶温"] - env["平流层顶温"]) * (
                z - env["平流层顶高"]) / (env["中间层顶高"] - env["平流层顶高"])
        return env["中间层顶温"]

    steps = max(1, math.ceil(altitude / 50))
    dz = altitude / steps
    exponent = sum(env["重力"] * env["molar_mass"] * dz / (
        GAS_CONSTANT * (temperature(k * dz) + temperature((k + 1) * dz)) / 2)
        for k in range(steps))
    pressure = env["海平面气压"] * math.exp(-exponent)
    temp = temperature(altitude)
    density = pressure * env["molar_mass"] / (GAS_CONSTANT * temp)
    gamma = env["cp"] / (env["cp"] - GAS_CONSTANT / env["molar_mass"])
    return temp, pressure, density, math.sqrt(gamma * GAS_CONSTANT * temp / env["molar_mass"])


def calculate(args):
    env, wing = existing_environment(), existing_aircraft()
    radius = args.radius_solar * SOLAR_RADIUS
    luminosity = 4 * math.pi * radius**2 * SIGMA * args.temperature**4
    star_mass = args.mass_solar * SOLAR_MASS
    # 沿用行星半径；重力及大气参数从现有模型读取。
    planet_radius = 1.5e7
    planet_mass = env["重力"] * planet_radius**2 / G
    e = args.eccentricity
    # 椭圆轨道的时间平均辐照：L/(4πa²√(1-e²))。
    a = math.sqrt(luminosity / (4 * math.pi * args.irradiance * math.sqrt(1 - e**2)))
    period = 2 * math.pi * math.sqrt(a**3 / (G * (star_mass + planet_mass)))
    peri, apo = a * (1 - e), a * (1 + e)
    hill = peri * (planet_mass / (3 * star_mass))**(1 / 3)
    spin = 2 * math.pi / 86400  # 沿用现有 24 h 自转角速度。
    solar_day = 2 * math.pi / (spin - 2 * math.pi / period)
    result = {
        "状态": "候选设计；未验证气候平衡、长期轨道稳定性或完整飞行可行性",
        "恒星": {
            "质量kg": star_mass, "半径m": radius, "有效温度K": args.temperature,
            "光度W": luminosity, "光度_太阳": luminosity / SOLAR_LUMINOSITY,
            "黑体峰值nm": 2.897771955e6 / args.temperature,
        },
        "公转": {
            "半长轴AU": a / AU, "偏心率": e, "周期d": period / 86400,
            "近日点AU": peri / AU, "远日点AU": apo / AU,
            "时间平均辐照W_m2": args.irradiance,
            "近日点辐照W_m2": luminosity / (4 * math.pi * peri**2),
            "远日点辐照W_m2": luminosity / (4 * math.pi * apo**2),
            "平太阳日h": solar_day / 3600,
            "恒星视直径deg_半长轴处": math.degrees(2 * math.asin(radius / a)),
            "近日点希尔半径km": hill / 1000,
            "天堂半长轴占近日点希尔半径": 2.29e8 / hill,
        },
        "气候检查": {
            "固定反照率0.3的有效温度K": (args.irradiance * .7 / (4 * SIGMA))**.25,
            "现有纬温公式面积均温K": 300 - 60 / 5,
            "说明": "两者之差不构成独立温室模型，不能据此宣布气候平衡。",
        },
        "60km空载巡航": [],
    }
    area = wing["b"]**2 / wing["AR"]
    # 沿用旧极曲线：使最大升阻比等于 LD_max。
    induced = 1 / (4 * wing["C_D0"] * wing["LD_max"]**2)
    cl_power = min(wing["C_Lmax"], math.sqrt(3 * wing["C_D0"] / induced))
    for surface in (300, 240):
        temp, pressure, density, sound = atmosphere(env, surface, 60000)
        weight = wing["m_空"] * env["重力"]
        stall = math.sqrt(2 * weight / (density * area * wing["C_Lmax"]))
        speed = math.sqrt(2 * weight / (density * area * cl_power))
        ld = cl_power / (wing["C_D0"] + induced * cl_power**2)
        mechanical = weight * speed / ld
        result["60km空载巡航"].append({
            "海平面温度K": surface, "当地温度K": temp, "压强Pa": pressure,
            "氧分压Pa": pressure * env["fractions"]["O2"], "密度kg_m3": density,
            "声速m_s": sound, "失速速度m_s": stall,
            "旧极曲线最小功率速度m_s": speed, "马赫数": speed / sound,
            "最小机械功率W": mechanical,
            "总效率0.85所需储能输出W": mechanical / .85,
            "总效率0.70所需储能输出W": mechanical / .70,
            "说明": "效率仅为敏感性试算；未计波阻、辅助负载、呼吸、热管理或光合供能。",
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temperature", type=float, default=5772)
    parser.add_argument("--radius-solar", type=float, default=1)
    parser.add_argument("--mass-solar", type=float, default=1)
    parser.add_argument("--eccentricity", type=float, default=.01)
    parser.add_argument("--irradiance", type=float, default=1360)
    args = parser.parse_args()
    if not 0 <= args.eccentricity < 1:
        parser.error("偏心率须在 [0, 1) 内")
    if min(args.temperature, args.radius_solar, args.mass_solar, args.irradiance) <= 0:
        parser.error("温度、半径、质量与辐照必须为正")
    print(json.dumps(calculate(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
