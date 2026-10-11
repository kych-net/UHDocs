"""复核: 微生物能否用 NH3 还原 PO4^3- 为 PH3 来获取能量

设想反应(以酸性条件书写):
   电子供体(氧化): 2NH4+ -> N2 + 8H+ + 6e-
   电子受体(还原): H3PO4 + 8H+ + 8e- -> PH3 + 4H2O
   配平(n=24): 8NH4+ + 3H3PO4 -> 4N2 + 3PH3 + 12H2O + 8H+

判据: 电池电动势 E°cell = E°(电子受体) - E°(电子供体) > 0 才自发产能
      ΔG° = -nF·E°cell
"""

F = 96485.0    # C/mol
R = 8.314

# --- 标准还原电位 (酸性, pH 0, vs SHE) ---
E_PO4_PH3 = -0.276   # H3PO4 + 8H+ + 8e- -> PH3 + 4H2O
E_N2_NH4 = +0.275    # N2 + 8H+ + 6e- -> 2NH4+
E_NO3_NH4 = +0.875   # NO3- + 10H+ + 8e- -> NH4+ + 3H2O
E_O2_H2O = +1.229    # O2 + 4H+ + 4e- -> 2H2O
E_H_H2 = 0.000       # 2H+ + 2e- -> H2

print("=" * 74)
print("1) 设想反应: NH4+ 还原 PO4^3- 为 PH3 (产 PH3 方向)")
print("=" * 74)
print(f"  电子受体 E°(PO4/PH3)  = {E_PO4_PH3:+.3f} V")
print(f"  电子供体 E°(N2/NH4+)  = {E_N2_NH4:+.3f} V")
Ecell = E_PO4_PH3 - E_N2_NH4
n = 24
dG = -n * F * Ecell
print(f"  E°cell = {Ecell:+.3f} V  -> {'自发产能' if Ecell > 0 else '非自发, 需输入能量'}")
print(f"  ΔG° = -nF·E°cell = {dG/1000:+.0f} kJ/mol (n={n})")
print(f"  折合每 mol PH3: {dG/3/1000:+.0f} kJ/mol PH3")
print("  => 电位差为负, 反应不能产能, 反而每产 1 mol PH3 需投入约 425 kJ")

print()
print("=" * 74)
print("2) 换更强的氮电子供体也不行")
print("=" * 74)
Ecell2 = E_PO4_PH3 - E_NO3_NH4
print(f"  NH4+ 直接氧化到 NO3- (E°={E_NO3_NH4:+.3f} V):")
print(f"    E°cell = {Ecell2:+.3f} V -> 更负, 更不可行")

print()
print("=" * 74)
print("3) pH 7 中性条件 (按 Nernst 校正)")
print("=" * 74)
pH = 7.0
E_PO4_pH = E_PO4_PH3 - (0.0592 * 8 / 8) * pH
E_N2_pH = E_N2_NH4 - (0.0592 * 8 / 6) * pH
E_H2_pH = E_H_H2 - 0.0592 * pH
print(f"  E(PO4/PH3, pH7) = {E_PO4_pH:+.3f} V")
print(f"  E(N2/NH4+, pH7) = {E_N2_pH:+.3f} V")
print(f"  E(H+/H2,   pH7) = {E_H2_pH:+.3f} V")
Ecell_pH = E_PO4_pH - E_N2_pH
print(f"  E°cell(pH7) = {Ecell_pH:+.3f} V -> 仍为负, 中性下同样不产能")
print(f"  注意: E(PO4/PH3)={E_PO4_pH:+.3f} V 比 E(H+/H2)={E_H2_pH:+.3f} V 更低,")
print("        即 PO4^3- 比 H2O 更难还原; 微生物会先去还原水(析氢), 轮不到磷酸盐")

print()
print("=" * 74)
print("4) 对比: 常见产能代谢的 E°cell (同为pH0, 用O2作受体)")
print("=" * 74)
常见 = [
    ("H2 氧化", 0.000, "2H+ + 2e- -> H2"),
    ("NH4+ 氧化", E_N2_NH4, "N2 + 8H+ + 6e- -> 2NH4+"),
    ("Fe2+ 氧化", 0.770, "Fe3+ + e- -> Fe2+"),
    ("PH3 氧化(反向)", E_PO4_PH3, "H3PO4 + 8H+ + 8e- -> PH3 + 4H2O"),
]
for 名, E, 半 in 常见:
    cell = E_O2_H2O - E
    print(f"  {名:14s} E°cell(配O2) = {cell:+.3f} V  ΔG = {-2*F*cell/1000:+6.0f} kJ/mol(2e)  [{半}]")
print("  => 只有把反应反过来(PH3 -> PO4^3-, 即氧化PH3)才是产能方向")

print()
print("== 结论 ==")
print("  1) 'NH3还原PO4为PH3' 热力学不可行: E°cell ≈ -0.55 V (pH0) / -0.41 V (pH7),")
print("     ΔG° ≈ +1276 kJ/mol (n=24), 需投入能量而非获取能量。")
print("  2) 根因: PO4^3-/PH3 的还原电位(-0.276V)低于所有常见氮电对, 甚至低于 H+/H2,")
print("     即磷酸盐比水还难还原; 微生物会优先还原水, 无法用此反应产能。")
print("  3) 可行方向是反过来的: PH3 氧化为 PO4^3- (配O2时 E°cell≈+1.51 V, 强产能),")
print("     这对应自然界 PH3 在氧化环境中的快速消失。")
print("  4) 若设定需要'磷循环微生物', 建议: 以 PH3 为电子供体氧化产能,")
print("     或用 NH3 作电子供体但搭配 O2/NO3-/Fe3+/SO4^2- 作受体(而非磷酸盐)。")