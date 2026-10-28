"""复核: 主行星 PH3(磷化氢)循环的源-汇收支与能量可行性

前提(沿用 复核_磷酸盐还原产能.py 的结论):
  - PO4^3- 还原为 PH3 热力学不可行(E°cell < 0), 微生物产 PH3 不产能,
    只能是耗能的"磷过载排磷"途径, 能量由有机质发酵提供
  - PH3 氧化回 PO4^3- 配 O2 是强产能方向(E°cell ≈ +1.51 V)

计算:
  1) 大气总质量与物质的量
  2) PH3 在 O2 大气中的 OH 氧化寿命(对流层光解可忽略, O2/CO2 挡短波 UV)
  3) 稳态浓度 <-> 源/汇通量对照表
  4) 海陆沉降通量密度, 与 Redfield 生物需求对照
  5) 排磷耗能功率占全球初级生产力的比例
  6) PH3 氧化产能

行星参数取自 内容/地理/主行星.typ:
  R = 1.5e4 km, g = 20 m/s^2, P0 = 1.013e5 Pa,
  平均摩尔质量 0.0106 kg/mol (He76%, O2 20%...)
"""
import math

# ---------- 1) 大气总量 ----------
R = 1.5e7            # m
g = 20.0             # m/s^2
P0 = 1.013e5         # Pa
M_mol = 0.0106       # kg/mol
Area = 4 * math.pi * R**2                 # m^2
M_atm = P0 * Area / g                     # kg (静力学)
n_atm = M_atm / M_mol                     # mol
print(f"1) 面积 {Area:.3e} m^2, 大气总质量 {M_atm:.3e} kg, {n_atm:.3e} mol")
print(f"   (地球大气 5.15e18 kg, 本行星约 {M_atm/5.15e18:.1f} 倍)")

# ---------- 2) PH3 大气寿命 ----------
# PH3 + OH -> 产物,  k(298K) 文献范围 1.5~2.6e-13 cm^3/(molecule*s)
# 对流层 OH 典型 1e6 molec/cm^3 (地球), 本行星 O2 20%, 取 1e6~3e6
k_oh = 2.6e-13
k_oh_lo = 1.5e-13
print("2) PH3 OH 氧化寿命:")
taus = {}
for oh in (1e6, 3e6):
    tau = 1.0 / (k_oh * oh)
    taus[oh] = tau
    print(f"   [OH]={oh:.0e}: {tau/86400:.1f} 天 (k=2.6e-13), "
          f"{1.0/(k_oh_lo*oh)/86400:.1f} 天 (k=1.5e-13)")
tau = taus[1e6]   # 代表值: [OH]=1e6, k=2.6e-13
print(f"   取代表值 tau = {tau/86400:.0f} 天 = {tau:.2e} s")

# ---------- 3) 浓度 <-> 通量 ----------
# 摩尔质量: PH3 = 34 g/mol, 其中 P = 31 g/mol
M_P = 0.031          # kg P/mol
sec_yr = 365 * 86400
print(f"3) 稳态浓度 <-> 源汇通量 (tau = {tau/86400:.0f} 天):")
print("   ppb(体积)   大气库存 Gg P   源=汇 mol/s   沉降 Tg P/yr")
rows = []
for ppb in (0.01, 0.1, 1.0):
    n = n_atm * ppb * 1e-9          # mol PH3
    F = n / tau                     # mol/s
    Tg = F * M_P * sec_yr / 1e9     # Tg P/yr  (kg->Gg->? 见下)
    # F mol/s * 0.031 kg/mol = kg/s; *sec_yr = kg/yr; /1e6 = Gg; *1e3/1e6?
    kg_yr = F * M_P * sec_yr
    Tg = kg_yr / 1e9                # 1 Tg = 1e9 kg?  1 Tg=1e12 g=1e9 kg ✓
    Gg_stock = n * M_P / 1e6        # mol*kg/mol = kg; /1e6 -> Gg
    print(f"   {ppb:>8}    {Gg_stock:>10.1f}   {F:>10.3e}   {Tg:>10.1f}")
    rows.append((ppb, F, Tg))

# ---------- 4) 沉降密度与 Redfield 对照 ----------
print("4) 沉降通量密度 (取 0.1 ppb 档):")
ppb, F, Tg = rows[1]
f_oc = 0.75          # 海洋占比(70-80% 取中)
ocean_Tg = Tg * f_oc
land_Tg = Tg * (1 - f_oc)
ocean_A = Area * f_oc
land_A = Area * (1 - f_oc)
# g/yr -> mg/m^2/yr
ocean_d = ocean_Tg * 1e12 * 1e3 / ocean_A   # Tg->g(*1e12), g->mg(*1e3)
land_d = land_Tg * 1e12 * 1e3 / land_A
print(f"   海面 {ocean_d:.1f} mg P/m^2/yr ({ocean_Tg:.1f} Tg/yr), "
      f"陆地 {land_d:.1f} mg P/m^2/yr ({land_Tg:.1f} Tg/yr)")

# Redfield: 海洋新生产参照地球 50 Gt C/yr, C:P = 106 (mol)
C_yr = 50e15              # g C/yr
P_need = C_yr / (106 * 12.01) * 30.97 / 1e12   # Tg P/yr
print(f"   海洋生物磷总需求(Redfield, 地球参照): {P_need:.0f} Tg P/yr")
print(f"   其中绝大部分由再生磷供给(地球河流新输入仅 ~1.5 Tg/yr);")
print(f"   新输入只需补净埋藏 -> 0.1 ppb 海面沉降 {ocean_d:.0f} mg/m^2/yr")
print(f"   是否过剩取决于回流: 沉积物排磷把部分磷以 PH3 再挥发, 闭合循环")

# ---------- 5) 排磷耗能功率 ----------
print("5) 沉积物排磷产 PH3 的能量账:")
dG_prod = 425e3         # J/mol PH3, 耗能, 来自 复核_磷酸盐还原产能.py
W_src = F * dG_prod      # W
print(f"   源强 F = {F:.2e} mol/s, 排磷耗能 {W_src:.2e} W = {W_src/1e9:.1f} GW")
# 全球初级生产力功率 (参照地球): 50 Gt C/yr, 有机质 ~15.6 kJ/g
W_pp = 50e15 * 15.6e3 / sec_yr    # W
print(f"   全球初级生产力功率(参照) {W_pp:.2e} W = {W_pp/1e12:.1f} TW")
if W_src < W_pp:
    print(f"   占比 {W_src/W_pp*100:.3f}% -> 沉积物有机质发酵可支撑")
else:
    print("   占比 >100% -> 不可行")
# 若用 1 ppb 档
_, F1, _ = rows[2]
print(f"   (若取 1 ppb: {F1:.2e} mol/s -> {F1*dG_prod/1e9:.0f} GW, "
      f"占比 {F1*dG_prod/W_pp*100:.2f}%)")

# ---------- 6) PH3 氧化产能 ----------
print("6) PH3 氧化产能 (PH3 + O2 -> PO4^3-):")
n_e, F_const, Ecell = 8, 96485, 1.51
dG = -n_e * F_const * Ecell
print(f"   E°cell = +{Ecell} V, 每 mol PH3 氧化 dG = {dG/1e3:.0f} kJ")
print(f"   每氧化 1 kg PH3 约 {-dG/1000/0.034/1000:.1f} MJ (对照有机质 ~16 MJ/kg)")

# ---------- 7) 循环闭合: 回流率与外部源 ----------
print("7) 闭合 (取 0.1 ppb, 沉降 34.3 Tg P/yr):")
F_ext = 1.0            # 假设火山/深部排气等外部补给 1 Tg P/yr
r = 1 - F_ext / Tg
W_back = (F * r) * dG_prod
print(f"   外部源 {F_ext:.1f} Tg/yr 支撑净埋藏, 则沉积物回流率 {r*100:.0f}%")
print(f"   回流源强 {F*r:.2e} mol/s, 排磷耗能 {W_back/1e9:.1f} GW "
      f"(占初级生产力 {W_back/W_pp*100:.3f}%)")
print(f"   -> 内部大循环 {Tg:.0f} Tg/yr 自持, 外部净输出 {F_ext:.0f} Tg/yr")

# ---------- 8) 光保护供能对照 (参考氨氧光合的光保护机制) ----------
# 光合微生物光强过高时把过剩还原力用于磷酸盐还原产 PH3,
# 反应吸能 425 kJ/mol, 由过剩光能承担 —— 光保护本来就是挥霍能量.
print("8) 光保护排磷的供能对照 (透光层过剩光能):")
I0 = 1360.0           # W/m^2 恒星辐照度 (内容/地理/主行星.typ)
alb = 0.3             # 行星反照率
f_par = 0.45          # 光合有效辐射占比
ocean_A = Area * f_oc
P_abs = I0 * (1 - alb) / 2 * ocean_A      # 昼夜平均吸收
PAR = P_abs * f_par
print(f"   海洋平均吸收 {P_abs:.2e} W, PAR {PAR:.2e} W")
print(f"   排磷耗能(全量 34 Tg/yr) {W_src:.2e} W, 占 PAR 的 {W_src/PAR*100:.1e}%")
# 海洋净初级生产功率参照地球 ~1e13 W
NPP = 1.0e13
print(f"   即便全部 PAR 用于光合({NPP:.0e} W 档), 过剩 {PAR-NPP:.2e} W")
print(f"   过剩 / 需求 = {(PAR-NPP)/W_src:.1e} -> 远大于需求, 光过剩可承担")
