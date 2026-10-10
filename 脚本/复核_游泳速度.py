"""复核: 嗜血仙子游泳最高速度 25 m/s 的推力与功率需求
参数: 体长 2 m, 体重 25 kg

射流推进: 净推力 F = ρ A U_jet (U_jet - U), 推进效率 η = 2U / U_jet
阻力:     F_drag = ½ ρ C_d S U²
"""
import math

rho_w = 1000.0
L = 2.0            # 体长 m
m = 25.0           # 体重 kg
rho_body = 1000.0  # 体密度假设(近水)
C_d = 0.08         # 流线型阻力系数
U = 25.0           # 游泳速度 m/s

# 由质量与体长估迎流面积(椭球近似)
V = m / rho_body
D = math.sqrt(6 * V / (math.pi * L))
S = math.pi * D**2 / 4
print(f"体积 ≈ {V:.3f} m³, 最大直径 ≈ {D*100:.1f} cm, 迎流面积 ≈ {S:.4f} m²\n")

F = 0.5 * rho_w * C_d * S * U**2
print(f"25 m/s: 阻力 ≈ {F:.0f} N, 有用功率 ≈ {F*U/1000:.1f} kW\n")

eta = 0.5
U_jet = 2 * U / eta
A_jet = F / (rho_w * U_jet * (U_jet - U))
P_jet = 0.5 * rho_w * A_jet * U_jet**3
print(f"射流参数(取 η = {eta}):")
print(f"  喷射速度 {U_jet:.0f} m/s, 喷口面积 {A_jet*1e4:.2f} cm²")
print(f"  射流功率 ≈ {P_jet/1000:.0f} kW\n")

P_elec = 370 * 5
print(f"设定电能输入(DC 370V×5A) ≈ {P_elec:.0f} W")
print(f"功率缺口 ≈ {P_jet/P_elec:.0f} 倍\n")

U_cont = (2 * P_elec / (rho_w * C_d * S)) ** (1/3)
print(f"若推进功率限于 {P_elec:.0f} W, 可持续速度 ≈ {U_cont:.1f} m/s")