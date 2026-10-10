#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复核:NH3 在这个行星大气里能否稳定存在?(只读,不改文档)
运行: python3 脚本/复核_氨稳定性.py

三条汇:
  1) 热力学: 4 NH3 + 3 O2 -> 2 N2 + 6 H2O,看 ΔG 是否自发。
  2) OH 自由基氧化: NH3 + OH -> NH2 + H2O, k=1.7e-13 cm³/(molecule·s),寿命 τ=1/(k·[OH])。
  3) UV 光解: NH3 + hν(λ<230 nm),寿命 τ=1/J。
结论用"寿命 vs 行星时间"判断是否需要生物源补充。
"""

R = 8.314462618

# ---------- 1 热力学 ----------
# ΔG°f (kJ/mol, 298 K, 气态)
dGf = {"NH3": -16.45, "O2": 0.0, "N2": 0.0, "H2O": -228.57}
dG_rxn = 2 * dGf["N2"] + 6 * dGf["H2O"] - 4 * dGf["NH3"] - 3 * dGf["O2"]      # 4NH3+3O2->2N2+6H2O
dG_per_NH3 = dG_rxn / 4
dH_rxn = 2 * 0 + 6 * (-241.82) - 4 * (-46.11) - 0                            # 用 ΔH°f
print("=" * 84)
print("一、热力学:4 NH3 + 3 O2 -> 2 N2 + 6 H2O")
print("=" * 84)
print(f"  ΔG°(整反应) = {dG_rxn:+.1f} kJ/mol   ΔG°(每 mol NH3) = {dG_per_NH3:+.1f} kJ/mol")
print(f"  ΔH°(整反应) = {dH_rxn:+.1f} kJ/mol")
print(f"  → ΔG° 强负,NH3 在 20% O2 大气里热力学上必然被氧化(不稳)。")

# ---------- 2 OH 氧化 ----------
k_OH = 1.7e-13   # cm³ molecule⁻¹ s⁻¹
print()
print("=" * 84)
print("二、OH 自由基氧化:NH3 + OH -> NH2 + H2O,  k = 1.7e-13 cm³/(molecule·s)")
print("=" * 84)
print(f"  {'[OH] cm⁻³':>12} {'τ = 1/(k[OH])':>18}")
for OH in (1e5, 1e6, 1e7, 1e8):
    tau = 1.0 / (k_OH * OH)
    if tau > 3.15e7:
        s = f"{tau/3.156e7:.1f} 年"
    elif tau > 86400:
        s = f"{tau/86400:.1f} 天"
    else:
        s = f"{tau/3600:.2f} 小时"
    print(f"  {OH:12.0e} {s:>18}")
print("  (地球清洁对流层 OH ~1e6,污染/热带可到 1e7)")

# ---------- 3 光解 ----------
print()
print("=" * 84)
print("三、UV 光解:NH3 + hν (λ<230 nm)")
print("=" * 84)
print(f"  {'J s⁻¹':>10} {'τ = 1/J':>14}")
for J in (1e-7, 1e-6, 1e-5, 1e-4):
    tau = 1.0 / J
    s = f"{tau/86400:.1f} 天" if tau > 86400 else f"{tau/3600:.2f} 小时"
    print(f"  {J:10.0e} {s:>14}")
print("  (有臭氧层屏蔽 <242 nm 时 J 大幅下降;20% O2 足以成 O3 层)")

print()
print("=" * 84)
print("四、结论")
print("=" * 84)
print("  低空(有水/有 OH/有电晕放电): 寿命约 1 天 ~ 2 个月,必须有源持续补充。")
print("  高空(无水、低压、三体碰撞少 → OH 生成少): 寿命长得多,可近似稳定。")
print("  行星时间尺度(≥1e6 年)下,全大气 NH3 不靠生物循环必然耗尽。")