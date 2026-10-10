"""复核: 怪动植物电推羽能否在水中使用

机制(见 内容/怪物/怪动植物.typ):
  翼骨上下各附一层羽级,层间加高压,电离空气产生离子风,沿翼面加速气流。
即气相电晕放电的电液动力(EHD)推进,工质是空气。

判据:
  1) 有无可电离的气体工质
  2) 能否维持电晕放电(介质电导率/击穿)
  3) 离子迁移率是否够高,能把动量有效传给工质
  4) 工质密度与功耗
"""

# --- 离子迁移率 μ, m^2/(V·s) ---
mu_air = 2.0e-4        # 空气中典型小离子
mu_water = 3.6e-7      # 水中最快的 H+, 已是上限
print("== 离子迁移率 ==")
print(f"  空气 μ ≈ {mu_air:.1e} m^2/(V·s)")
print(f"  水   μ ≈ {mu_water:.1e} m^2/(V·s)  (H+ 上限)")
print(f"  比值 空气/水 ≈ {mu_air / mu_water:.0f} 倍")
# 相同电场下离子漂移速度 v = μE, 水中低同样倍数

# --- 电导率 σ, S/m ---
sigma_dry_air = 1e-15
sigma_fresh = 5e-4     # 淡水
sigma_sea = 4.0        # 海水
print("\n== 电导率 ==")
print(f"  干燥空气 σ ≈ {sigma_dry_air:.0e} S/m")
print(f"  淡水     σ ≈ {sigma_fresh:.0e} S/m")
print(f"  海水     σ ≈ {sigma_sea:.0e} S/m")
print(f"  淡水/空气 ≈ {sigma_fresh / sigma_dry_air:.0e} 倍")
print(f"  海水/空气 ≈ {sigma_sea / sigma_dry_air:.0e} 倍")
# 层间高压在水里被体相电导短路, 电流走电解/欧姆加热, 不形成定向离子风

# --- 电晕起始场强 ---
E_corona_air = 3.0e6   # 大气压空气, V/m
print("\n== 放电条件 ==")
print(f"  空气电晕起始场强 ≈ {E_corona_air:.1e} V/m, 可在气隙中形成稳定电晕")
print("  水中: 无气隙, 先发生电解(分解电压 1.23 V)与欧姆加热, 无法形成电晕离子风")

# --- 工质密度 ---
rho_air = 1.2          # 海平面附近 kg/m^3
rho_water = 1000.0
print("\n== 工质密度 ==")
print(f"  空气 ρ ≈ {rho_air:.1f} kg/m^3")
print(f"  水   ρ ≈ {rho_water:.0f} kg/m^3")
print(f"  比值 水/空气 ≈ {rho_water / rho_air:.0f} 倍")

print("\n== 结论 ==")
print("  电推羽依赖气相工质(空气)+可维持的电晕+高离子迁移率, 三项在水中全部不成立。")
print("  水中无法使用电推羽推进。")