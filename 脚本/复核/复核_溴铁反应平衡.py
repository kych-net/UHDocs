"""复核: Br2 与 Fe2+ 反应的限度(平衡常数与平衡位置)

反应: Br2 + 2Fe2+ ⇌ 2Br- + 2Fe3+   (n = 2)
  E°(Br2/Br-)   = +1.07 V
  E°(Fe3+/Fe2+) = +0.77 V
  E°cell = 1.07 - 0.77 = +0.30 V

判据: ΔG° = -nF·E°cell,  K = exp(-ΔG°/(RT))
      反应可逆, K 有限 -> 不能说"完全还原", 只能看平衡位置
"""

import math

F = 96485.0
R = 8.314
E_Br = 1.07
E_Fe = 0.77
n = 2
Ecell = E_Br - E_Fe

print("=" * 74)
print("1) 电动势与平衡常数")
print("=" * 74)
dG = -n * F * Ecell
print(f"  E°cell = {Ecell:+.2f} V")
print(f"  ΔG° = -nF·E°cell = {dG/1000:+.1f} kJ/mol")
for T in (298.0, 280.0, 240.0):
    K = math.exp(-dG / (R * T))
    print(f"  T = {T:.0f} K : K = {K:.2e}")

print()
print("=" * 74)
print("2) 平衡位置: 液溴层(纯相, a≈1)存在时, 海水 Fe2+ 被氧化到什么程度")
print("=" * 74)
K = math.exp(-dG / (R * 280.0))
Br = 8.1e-4          # 海水 Br- ≈ 65 mg/L = 8.1e-4 mol/L
print(f"  K = {K:.2e}, 海水 [Br-] ≈ {Br:.1e} mol/L")
print("  由 K = [Br-]^2[Fe3+]^2 / ([Br2][Fe2+]^2), 取 [Br2]≈1(纯液相):")
ratio = math.sqrt(K) / Br     # [Fe3+]/[Fe2+]
print(f"  [Fe3+]/[Fe2+] = sqrt(K)/[Br-] = {ratio:.2e}")
print("  => 平衡强烈偏右, Fe2+ 会被氧化到几乎耗尽(残留活度极低)")

print()
print("=" * 74)
print("3) 但消耗量按化学计量, 不是无限消耗")
print("=" * 74)
print("  每 1 mol Fe2+ 只消耗 0.5 mol Br2")
for c_Fe2 in (1e-6, 1e-4, 1e-3, 1e-2):
    mol_Br2 = 0.5 * c_Fe2
    vol_Br2 = mol_Br2 * 0.160 / 3.102 * 1000   # mol/L -> mL/L (M=160 g/mol, ρ=3.1)
    print(f"  海水 Fe2+ = {c_Fe2:.0e} mol/L -> 消耗液溴 {mol_Br2:.1e} mol/L = {vol_Br2*1000:.2f} mL 液溴/L 海水")
print("  => 痕量 Fe2+ 对液溴层影响可忽略; 只有持续且巨大的 Fe2+ 通量才会显著削层")

print()
print("=" * 74)
print("4) 可逆性与 Fe3+ 去向")
print("=" * 74)
print("  - 反应可逆: 若 [Fe3+]/[Br-] 积累升高, 平衡左移, 反向氧化 Br- 又可进行")
print("  - 海水中 Fe3+ 极易水解沉淀为 Fe(OH)3, 移除 Fe3+ 会拉动反应向右(更彻底氧化 Fe2+)")
print("  - 酸性/富氧海水中 Fe2+ 本身也易被 O2 氧化, 与 Br2 是竞争关系")

print()
print("== 结论 ==")
print("  1) 反应确为可逆且有平衡常数: E°cell=+0.30 V, ΔG°=-57.9 kJ/mol,")
print("     K ≈ 1.4e10 (298K) / 6.3e10 (280K) —— 有限但很大, 平衡强烈偏右。")
print("  2) 因此'Fe2+ 会破坏液溴层'应修正为: 只要有液溴层, Fe2+ 会被氧化至近乎耗尽,")
print("     但消耗量严格按 0.5 mol Br2/mol Fe2+, 痕量 Fe2+ 影响可忽略。")
print("  3) 真正的限度: 液溴层被消耗的速率取决于 Fe2+ 的供给通量,")
print("     而非一个'完全反应'。要显著削层需持续、大量的还原性输入。")
print("  4) 反过来, Fe2+/Fe3+ 可作为电子穿梭: 铁还原细菌还原 Fe3+->Fe2+,")
print("     Fe2+ 再还原 Br2 -> 构成间接'溴呼吸'路径(需 Fe 循环)。")