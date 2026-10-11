"""复核: 嗜血仙子假胸部鳃丝喷射推进(空气/水中均可)

结构(见 内容/生物/仙子/index.typ):
  鳃部移到颈部下方形成假胸部, 鳃丝藏于腔内不外露, 在水或空气中均可呼吸。

机制:
  鳃丝阵列在假胸部内腔做行波摆动, 把介质经入口瓣膜单向吸入,
  再从喷口高速喷出, 以射流反作用推进。
  推力 F = ρ A_jet U_jet²
  射流功率 P_jet = ½ ρ A_jet U_jet³
  推进效率 η = 2 U_swim / U_jet  (射流推进, U_swim < U_jet)
"""
import math

介质 = {"水": 1000.0, "空气": 1.2}
A_jet = 0.002       # 喷口总面积 m^2

模式 = {
    "水中(主推进)": {"介质": "水",   "U_jet": 3.0,  "U_swim": 1.0},
    "空气(辅助)":   {"介质": "空气", "U_jet": 60.0, "U_swim": 10.0},
}

print(f"假胸部喷口面积 ≈ {A_jet*1e4:.0f} cm²\n")
for 名, p in 模式.items():
    rho = 介质[p["介质"]]
    Uj, Us = p["U_jet"], p["U_swim"]
    F = rho * A_jet * Uj**2          # 推力 N
    Pj = 0.5 * rho * A_jet * Uj**3   # 射流功率 W
    eta = 2 * Us / Uj                # 推进效率
    Q = A_jet * Uj                   # 体积流量 m^3/s
    print(f"{名}")
    print(f"  喷射速度 {Uj:.0f} m/s, 前进速度 {Us:.0f} m/s")
    print(f"  流量 {Q*1e3:.1f} L/s, 推力 ≈ {F:.1f} N")
    print(f"  射流功率 ≈ {Pj:.0f} W, 推进效率 ≈ {eta:.2f}")
    print()

print(f"等推力喷射速度比 空气/水 ≈ √(ρ_w/ρ_a) = {math.sqrt(1000/1.2):.1f} 倍")
print("→ 水中低速喷射即得大推力; 空气需高速喷射, 功率高, 宜作辅助。")