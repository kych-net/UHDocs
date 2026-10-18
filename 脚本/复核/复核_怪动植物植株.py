#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《地狱之下》怪动植物 植株(植物世代)设计 数值复核
复核草稿 草稿/草稿_怪动植物植株.typ 中的关键数字:
  1. 光合能量一致性: 19 g/h/m² H2 ↔ 750 W/m²
  2. 羽面热负荷与蒸腾耗水(色素只覆盖200–1000nm,>1000nm红外变热)
  3. 花粉终端下落速度与飘移距离(He大气 ρ≈0.43 kg/m³, g=20)
  4. 主干抗弯: 风暴风速 展叶vs折叶; 抗压; 欧拉屈曲
  5. NH3 大气存量 vs 植株固持通量(寿命敏感性)
  6. 植株季能量收支 vs 果实需求
只读, 不改 内容/。运行: python3 脚本/复核/复核_怪动植物植株.py
"""

import math

g = 20.0
R = 8.314462618
P0 = 1.013e5
Mbar = 0.0106          # kg/mol, He76/O2 20体系
T = 300.0
rho_air = P0*Mbar/(R*T)
print("="*70)
print(f"零、海平面大气密度 ρ = {rho_air:.3f} kg/m³ (对照地球1.225)")

print()
print("="*70)
print("一、光合能量一致性")
print("="*70)
HHV_H2 = 142e6         # J/kg
r_H2 = 19e-3/3600      # kg/s/m²
P_store = r_H2*HHV_H2
print(f"  19 g/h/m² H2 × HHV {HHV_H2/1e6:.0f} MJ/kg = {P_store:.0f} W/m²  [卡 750]  "
      f"{'✓' if abs(P_store-750)<15 else '✗'}")

print()
print("="*70)
print("二、羽面热负荷与蒸腾")
print("="*70)
I_surf = 1000.0        # 地表满照 ~ W/m² (恒星1360, 大气削弱后)
frac_IR = 0.25         # 太阳谱 >1000nm 份额 (5778K黑体约24%)
q_IR = I_surf*frac_IR
q_res = 0.05*I_surf*(1-frac_IR)   # 受光带95%效率的5%损耗
q_heat = q_IR + q_res
L_vap = 2.44e6
m_w = q_heat/L_vap
print(f"  红外负荷 {q_IR:.0f} + 光合损耗 {q_res:.0f} = {q_heat:.0f} W/m²")
print(f"  全蒸腾: {m_w*3600:.2f} kg/h/m²;  冠20 m² → {m_w*3600*20:.1f} kg/h")
print(f"  90天植物季(每天12h照) 耗水 ≈ {m_w*20*12*3600*90/1000:.1f} t/株")
print(f"  对照年降水 470–1700 mm: 20 m²冠面承接 {0.47*20:.0f}–{1.7*20:.0f} t 雨水, 可行")

print()
print("="*70)
print("三、花粉下落 (He大气)")
print("="*70)
r_p, t_p, rho_cell = 0.5e-3, 1e-6, 1500.0
m_shell = 4*math.pi*r_p**2*t_p*rho_cell
V = 4/3*math.pi*r_p**3
m_He = V*0.084
m_net = m_shell + m_He - V*rho_air
W = m_net*g
Cd = 1.0
A = math.pi*r_p**2
v_t = math.sqrt(2*W/(rho_air*Cd*A))
Re = rho_air*v_t*2*r_p/2e-5
print(f"  粒径0.5mm 膜厚1µm: 壳质量 {m_shell*1e9:.2f} ng, 净重 {W:.2e} N")
print(f"  终端速度 v = {v_t:.2f} m/s (Re≈{Re:.0f}, 取Cd=1)")
for h in (4.0, 6.0):
    t_fall = h/v_t
    for w in (2.0, 5.0):
        print(f"    自{h:.0f} m 落下 {t_fall:.1f} s, 风{w:.0f} m/s 飘移 {t_fall*w:.0f} m")
print("  → 有效授粉距离 10–30 m, 植株需集群生长")

print()
print("="*70)
print("四、主干强度 (g=20)")
print("="*70)
r_o, r_i, H = 0.075, 0.050, 4.0
A_sec = math.pi*(r_o**2-r_i**2)
Z = math.pi*(r_o**4-r_i**4)/(4*r_o)
I_sec = math.pi*(r_o**4-r_i**4)/4
M_total = 100.0
W_body = M_total*g
sig_c = W_body/A_sec
print(f"  主干: 外径{r_o*100:.0f}cm 壁厚{(r_o-r_i)*100:.1f}cm 高{H:.0f}m, 植株总重 {W_body:.0f} N")
print(f"  压应力 {sig_c/1e6:.2f} MPa (材料~40 MPa) ✓")
E = 15e9
P_cr = math.pi**2*E*I_sec/(4*H**2)
print(f"  欧拉屈曲临界 {P_cr/1e3:.0f} kN, 安全系数 {P_cr/W_body:.0f}")
arm = 3.0
for v in (30, 40, 50):
    q = 0.5*rho_air*v*v
    for label, A_d in (("展叶", 4.0), ("折叶", 0.4)):
        sig_b = q*A_d*arm/Z
        print(f"  风{v} m/s {label}: q={q:.0f} Pa  弯应 {sig_b/1e6:.1f} MPa"
              f"  {'✓' if sig_b<2e7 else '✗ 需折叶'}")

print()
print("="*70)
print("四b、性二态株型强度 (男单株 5m/Ø12cm 圆锥稀冠; 女小株 1m/Ø5cm)")
print("="*70)
for label, H2, ro, ri, A_d, arm2 in (("男株", 5.0, 0.06, 0.04, 2.0, 4.0),
                                      ("女小株", 1.0, 0.025, 0.015, 0.15, 0.8)):
    Z2 = math.pi*(ro**4-ri**4)/(4*ro)
    for fold in (False, True):
        A = A_d if not fold else A_d*0.1
        sig = 0.5*rho_air*50*50*A*arm2/Z2
        print(f"  {label} 风50 m/s {'折叶' if fold else '展叶'}: 弯应 {sig/1e6:.1f} MPa"
              f"  {'✓' if sig<2e7 else '✗近/超材料极限'}")

print()
print("="*70)
print("五、NH3 循环耦合")
print("="*70)
R_p = 1.5e7
M_atm = 4*math.pi*R_p**2*P0/g
x_NH3 = 0.001
inv = M_atm*x_NH3*0.017/Mbar
per_plant_yr = r_H2*20*3600*24*365*(17/3)   # 全部H2固持为NH3
print(f"  大气质量 {M_atm:.2e} kg, NH3存量(0.1%) {inv:.2e} kg")
print(f"  单株(20 m²满固持) {per_plant_yr:.1e} kg NH3/yr")
for life_yr in (1/12, 1, 10):
    n = inv/(per_plant_yr*life_yr)
    land = 4*math.pi*R_p**2*0.2
    print(f"  寿命{life_yr*12 if life_yr<1 else life_yr:.0f}{'月' if life_yr<1 else '年'}: "
          f"需 {n:.1e} 株 → 陆地均摊 1株/{land/n/1e3:.1f} km²"
          f"{'  ← 与种植园规模相符' if 1e-1 < land/n/1e3 < 1e4 else ''}")

print()
print("="*70)
print("六、植株季能量收支 (男10m²/女小株0.5m²/网络1e5m²)")
print("="*70)
E_fruit = 100e6 + 20*1e6             # 能量脂100 MJ + 幼体结构~20 kg干物
for label, area in (("男株", 10.0), ("女小株", 0.5), ("单群网络", 1e5)):
    E = 750*area*6*90*3600           # 每天6满照小时, 90天
    print(f"  {label} {area:.0e} m²: 90天储量 {E/1e9:.1f} GJ, 可结果 {E/E_fruit:.2e} 枚")
