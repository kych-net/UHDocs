"""复核: (1) Fe2+/Fe3+ 能否催化 O2 氧化 Br-
        (2) "热带深海Br层 + 寒带深海CO2层" 的纬向设计是否成立

行星参数: g = 20 m/s^2, 大气富氧(O2 20%), 海面 赤道300K / 极点240K
"""

F = 96485.0   # 法拉第常数 C/mol

# --- 标准电极电位 (V) ---
E_Fe = 0.77   # Fe3+ + e-  -> Fe2+
E_Br = 1.07   # Br2  + 2e- -> 2Br-
E_O2 = 1.23   # O2 + 4H+ + 4e- -> 2H2O
E_OH = 2.80   # ·OH + e- -> OH-

print("=" * 72)
print("1) Fe2+/Fe3+ 能否直接催化 O2 氧化 Br-")
print("=" * 72)
print(f"  E°(Fe3+/Fe2+) = {E_Fe} V")
print(f"  E°(Br2/Br-)   = {E_Br} V")
dE = E_Fe - E_Br
print(f"  Fe3+ + Br- -> Fe2+ + ½Br2 的 ΔE = {dE:+.2f} V -> {'可行' if dE > 0 else '不可行(非自发)'}")
print(f"  ΔG = -nFΔE = {-2*F*dE/1000:+.0f} kJ/mol -> Fe3+ 电位低于 Br2/Br-, 无法直接氧化 Br-")

dE_rev = E_Br - E_Fe
print(f"  反向 Br2 + 2Fe2+ -> 2Br- + 2Fe3+ 的 ΔE = {dE_rev:+.2f} V -> 自发")
print("  => Fe2+ 会把 Br2 还原掉; 铁还原细菌产出的 Fe2+ 反而破坏液溴层")

print()
print("=" * 72)
print("1b) 间接路径: Fe 活化 O2 产生自由基")
print("=" * 72)
print("  Fenton: Fe2+ + H2O2 -> Fe3+ + ·OH + OH-")
print(f"  E°(·OH/OH-) = {E_OH} V > E°(Br2/Br-) = {E_Br} V -> ·OH 可氧化 Br-")
print("  但需 H2O2 来源(生物代谢/光化学), Fe 只是循环媒介, 并非直接催化 O2")
print("  自然界主路径是溴过氧化物酶(钒中心 V-BrPO), 不是简单 Fe2+/Fe3+")

print()
print(f"  O2 直接氧化 Br-: ΔE = {E_O2-E_Br:+.2f} V -> 热力学可行, 动力学慢")
print("  => 结论: Fe2+/Fe3+ 既不能直接催化, 还会被 Br2 氧化; 需生物酶/光催化")

print()
print("=" * 72)
print("2) 纬向设计: 热带深海Br层 + 寒带深海CO2层")
print("=" * 72)

T_melt_Br = 265.8


def rho_Br2(T):
    return (3.102 - 0.0043 * (T - 293.0)) * 1000.0


def rho_sw(T, S, h):
    rho0 = 1000.0 + 0.78 * S - 0.15 * (T - 277.0)
    return rho0 * (1 + 4.5e-10 * rho0 * 20.0 * h)


co2_T = [216.6, 240.0, 250.0, 260.0, 273.0, 283.0, 293.0, 304.1]
co2_rho = [1178.0, 1085.0, 1040.0, 990.0, 928.0, 850.0, 773.0, 468.0]


def co2_density(T):
    if T <= co2_T[0] or T >= co2_T[-1]:
        return None
    for i in range(len(co2_T) - 1):
        if co2_T[i] <= T <= co2_T[i + 1]:
            f = (T - co2_T[i]) / (co2_T[i + 1] - co2_T[i])
            return co2_rho[i] + f * (co2_rho[i + 1] - co2_rho[i])
    return None


for 名, T, h, S in (("热带深海", 280.0, 4000, 35), ("寒带深海", 240.0, 4000, 35)):
    rs = rho_sw(T, S, h)
    print(f"\n  {名}: T = {T:.0f} K, 深度 {h} m, 海水密度 = {rs:.0f} kg/m^3")
    if T > T_melt_Br:
        rb = rho_Br2(T)
        print(f"    液溴  : 液态, ρ = {rb:.0f}, 密度比 {rb/rs:.2f} -> 沉底 可成层")
    else:
        print(f"    液溴  : 固态 (T < 熔点 {T_melt_Br} K) -> 不能成层")
    d = co2_density(T)
    if d is None:
        print("    液态CO2: 无 (超临界/气)")
    else:
        print(f"    液态CO2: ρ = {d:.0f}, 密度比 {d/rs:.2f} -> {'沉底 可成层' if d > rs else '上浮 不能成层'}")

print()
print("=" * 72)
print("温度窗口核对")
print("=" * 72)
print(f"  液溴层   : 需 {T_melt_Br} K < T < 332 K (暖海)")
print("  液态CO2层: 需 T < ~250 K (冷海)")
print("  => 二者温度窗口无交集, 但地理上分处热带/寒带, 可以并存")

print()
print("== 结论 ==")
print("  1) Fe2+/Fe3+ 不能催化 O2 氧化 Br-: Fe3+ 电位(0.77V)低于 Br2/Br-(1.07V),")
print("     且 Br2 会氧化 Fe2+。Br- 氧化的自然路径是溴过氧化物酶或光催化。")
print("  2) 纬向设计在温度/密度上成立: 热带深海(>265.8K)可得液溴层,")
print("     寒带深海(<250K)可得液态CO2层, 两者互斥但地理分离, 可并存。")
print("  3) 两个残留约束: (a) 热带深海必须暖到 >265.8K; (b) 液溴层需局部Br富集;")
print("     且热带深海生物活跃, Br2 会被有机物/Fe2+ 还原消耗, 需持续氧化补充。")