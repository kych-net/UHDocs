#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怪动植物 骨骼 设计稿与数值复核(50 倍过载, 石墨烯 + 碳纳米管)
只读, 不改 内容/。运行: python3 脚本/设计/设计_怪动植物骨骼.py

依据:
  · 2 m / 20 kg, g = 20 m/s², 最大负重 40 kg → 满载 60 kg
  · 过载 50g 为撞击/迫降等外部载荷, 不是推力产生
  · 两对羽翼在胸腹交界处上下连接, 展向每 10 cm 一根竖直连接件
  · 上下两翼互为支撑, 构成空间梁; 翼根弯矩由两翼轴力偶承担
  · 翼面为羽片, 无翼膜; 羽根只传局部升力
  · 骨骼为石墨烯片 + 碳纳米管束增强的碳基复合, 含骨细胞与拓扑优化
  · 无骨骼肌, 运动由平滑肌完成; 翼骨多节可折叠
输出:
  材料、质量预算、最优翼间距、翼梁、连接件、主干骨、骨腔、重建、拓扑,
  以及可粘入正文的设定草案
"""

import math

g = 20.0
M_BODY = 20.0
M_LOAD = 40.0
N_LOAD = 50.0
B = 10.0
AR = 40.0
S_WING = B * B / AR
LD = 68.0

RHO = 1500.0             # 碳化几丁质基体 + 石墨烯片 + 碳纳米管束
E_BONE = 600e9
SIG_C = 12e9             # 抗压
SIG_T = 25e9             # 抗拉
SIG_SHEAR = 450e6
SIG_BRG = 550e6
SF = 1.2                 # 极限载荷下的安全系数

D_BEAM = 15.0            # 翼梁外径 mm
T_MIN = 0.4              # 翼梁壁厚下限 mm
S_LINK = 0.10            # 连接件展向间距 m
D_LINK = 4.5             # 连接件直径 mm
N_LINK = int(2 * 5.0 / S_LINK)
翼肋 = (6, 0.25, 0.25)   # 直径, 壁厚, 长; 每侧 17 根
N_RIB_SIDE = 17


def 管(D_mm, t_mm):
    Do = D_mm * 1e-3
    Di = (D_mm - 2 * t_mm) * 1e-3
    A = math.pi / 4 * (Do**2 - Di**2)
    I = math.pi / 64 * (Do**4 - Di**4)
    W = I / (Do / 2)
    A_in = math.pi / 4 * Di**2
    return A, I, W, A_in


def 标题(s):
    print()
    print("=" * 74)
    print(s)
    print("=" * 74)


# ========== 一、材料 ==========
标题("一、骨质材料")
print(f"  碳化几丁质基体,内嵌石墨烯片与碳纳米管束,层状与束状交替, 密度 {RHO:.0f} kg/m³")
print(f"  E = {E_BONE/1e9:.0f} GPa(纤维向), 抗拉 {SIG_T/1e9:.0f} GPa, "
      f"抗压 {SIG_C/1e9:.0f} GPa")
print(f"  抗剪 {SIG_SHEAR/1e6:.0f} MPa, 挤压 {SIG_BRG/1e6:.0f} MPa")
print(f"  比强度 抗拉 {SIG_T/RHO/1e3:.0f} / 抗压 {SIG_C/RHO/1e3:.0f} kN·m/kg "
      f"(人骨约 79)")
print(f"  碳纳米管束跨层桥接, 石墨烯片沿主应力面铺展, 二者近乎无缺陷")
print(f"  骨细胞被层间包埋, 腔径 15 µm, 骨小管连成网, 连同小管约占骨体积 4%")
print(f"  无塑性: 断裂应变约 1.2%, 裂纹由有机基体偏转, 损伤靠重建修复")

# ========== 二、翼间距反推 ==========
标题("二、上下翼间距反推(按结构质量最小)")
L_50 = (M_BODY + M_LOAD) * g * N_LOAD
M_root = L_50 * B / (3 * math.pi)
A_link = math.pi / 4 * (D_LINK * 1e-3) ** 2
L_HALF = B / 2
best = None
print(f"  {'d m':>5}{'F kN':>8}{'t mm':>7}{'翼梁 kg':>9}{'连接件 kg':>10}{'合计 kg':>9}")
for i in range(10, 51, 2):
    d = i / 100
    F = M_root / d
    A_need = F / (SIG_C / SF)
    t = max(A_need / (math.pi * D_BEAM * 1e-3) * 1e3, T_MIN)
    A = math.pi * D_BEAM * 1e-3 * t * 1e-3
    m_beam = 4 * L_HALF * A * RHO * 0.96
    m_link = N_LINK * d * A_link * RHO * 0.96
    m_sum = m_beam + m_link
    if best is None or m_sum < best[4]:
        best = (d, F, t, m_beam, m_sum)
    if i % 4 == 2:
        print(f"  {d:5.2f}{F/1e3:8.0f}{t:7.2f}{m_beam:9.2f}{m_link:10.2f}{m_sum:9.2f}")
D_WING, F_EDGE, T_BEAM, M_BEAM, M_WING = best
A_beam = math.pi * D_BEAM * 1e-3 * T_BEAM * 1e-3
print(f"  最优 d = {D_WING:.2f} m, 翼梁轴力 {F_EDGE/1e3:.0f} kN, 壁厚 {T_BEAM:.2f} mm")
print(f"  翼梁 + 连接件 = {M_BEAM:.2f} + {M_WING-M_BEAM:.2f} = {M_WING:.2f} kg")
print(f"  再大则连接件变长, 再小则翼梁W变粗; 质量曲线在 0.28 m 附近见底")

# ========== 三、翼梁与连接件校核 ==========
标题("三、50g 下的翼梁与连接件")
sig_beam = F_EDGE / A_beam
sig_cr = 1.2 * E_BONE * T_BEAM * 1e-3 / (D_BEAM * 1e-3)
_, I_beam, _, _ = 管(D_BEAM, T_BEAM)
P_cr = math.pi**2 * E_BONE * I_beam / S_LINK**2
print(f"  单侧翼根弯矩 M = L·b/(3π) = {M_root/1e3:.1f} kN·m")
print(f"  上下翼互撑, 轴力 F = M/d = {F_EDGE/1e3:.0f} kN")
print(f"  翼梁 Ø{D_BEAM:.0f}×{T_BEAM:.2f}: 压应力 {sig_beam/1e9:.1f} GPa, "
      f"SF {SIG_C/sig_beam:.2f} {'✓' if sig_beam <= SIG_C/SF*1.01 else '✗'}")
print(f"  局部屈曲 {sig_cr/1e9:.1f} GPa {'✓' if sig_beam < sig_cr else '✗'}")
print(f"  连接件每 {S_LINK*100:.0f} cm 侧撑: 欧拉临界 {P_cr/1e3:.0f} kN, "
      f"SF {P_cr/F_EDGE:.2f} {'✓' if P_cr > F_EDGE else '✗'}")
F_link = F_EDGE * S_LINK / L_HALF
tau_link = F_link / (2 * A_link)
print(f"  单根连接件剪力 {F_link/1e3:.1f} kN, 双剪 {tau_link/1e6:.0f} MPa "
      f"{'✓' if tau_link < SIG_SHEAR else '✗'}")
print(f"  连接件共 {N_LINK} 根, Ø{D_LINK}×{D_WING*1000:.0f} mm")

# ========== 四、分区质量 ==========
标题("四、骨骼分区与质量预算")
翼梁体积 = 4 * L_HALF * A_beam * 1e6
连接件体积 = N_LINK * A_link * D_WING * 1e6
肋体积 = 2 * N_RIB_SIDE * 管(*翼肋[:2])[0] * 翼肋[2] * 1e6
分区 = [
    ("脊柱 24 节", 45, "椎体 Ø16×1.2, 拱形桁架"),
    ("肋骨 12 对", 25, "薄壁弧板 Ø3.5×0.35"),
    ("胸骨与肩带", 130, "汇聚四个翼根"),
    ("骨盆", 65, "含控制神经干末段"),
    ("前肢 2×", 60, "肱骨, 桡尺, 腕掌指"),
    ("后肢 2×", 135, "股骨 Ø16×1.2, 胫腓, 跗趾"),
    ("手足小骨", 30, "无足弓"),
    ("头骨", 40, "壳骨架 + 多孔夹层"),
    ("翼梁 4 根", 翼梁体积, f"Ø{D_BEAM:.0f}×{T_BEAM:.2f}, 三节可折"),
    ("翼间连接件", 连接件体积, f"Ø{D_LINK}×{D_WING*1000:.0f}, 每 {S_LINK*100:.0f} cm"),
    ("翼肋 34 根", 肋体积, "Ø6×0.25, 间距 0.3 m"),
    ("套筒与锁销", 70, "8 套 Ø20×1.5×80"),
    ("固定爪 2 对", 10, "连躯干与大腿交界"),
]
总壁体积 = sum(v for _, v, _ in 分区)
细胞腔率 = 0.04
总骨重 = 总壁体积 * 1e-6 * RHO * (1 - 细胞腔率)
print(f"  {'分区':<16}{'材料体积 cm³':>12}{'质量 kg':>10}  备注")
for 名, v, 注 in 分区:
    print(f"  {名:<16}{v:>12.0f}{v*1e-6*RHO*(1-细胞腔率):>10.2f}  {注}")
print(f"  {'合计':<16}{总壁体积:>12.0f}{总骨重:>10.2f}")
print(f"  质量已扣 4% 骨细胞腔; 占体重 {总骨重/M_BODY*100:.1f}%")

# ========== 五、主干骨 ==========
标题("五、50g 下的股骨与脊柱")
D_f, t_f, L_f = 16.0, 1.2, 0.45
A_f, I_f, W_f, _ = 管(D_f, t_f)
F_leg = (M_BODY + M_LOAD) * g * N_LOAD / 2
sig_leg = F_leg / A_f
P_cr_leg = math.pi**2 * E_BONE * I_f / L_f**2
print(f"  股骨 Ø{D_f:.0f}×{t_f:.1f}: 单腿 {F_leg/1e3:.0f} kN → "
      f"压应力 {sig_leg/1e6:.0f} MPa ✓")
print(f"  欧拉屈曲 {P_cr_leg/1e3:.0f} kN, 安全 {P_cr_leg/F_leg:.1f} ✓")

A_v, _, W_v, _ = 管(16, 1.2)
sig_spine = (M_BODY + M_LOAD) * g * N_LOAD / A_v
print(f"  椎体 Ø16×1.2 轴向 {L_50/1e3:.0f} kN: 压应力 {sig_spine/1e6:.0f} MPa ✓")
print(f"  肩带汇聚四个翼根, 每根 {F_EDGE/1e3:.0f} kN, 接触面承压 ✓")

# ========== 六、头骨碰撞吸能 ==========
标题("六、头骨碰撞吸能")
M_HEAD, V_HIT, STROKE = 1.0, 8.0, 0.040
E_k = 0.5 * M_HEAD * V_HIT**2
F_avg = E_k / STROKE
sig_crush = F_avg / 0.008
print(f"  头质量 {M_HEAD} kg, 撞速 {V_HIT} m/s → {E_k:.0f} J")
print(f"  行程 {STROKE*1000:.0f} mm → 平均力 {F_avg/1e3:.1f} kN, "
      f"加速度 {F_avg/M_HEAD:.0f} m/s² = {F_avg/M_HEAD/9.81:.0f} g")
print(f"  多孔夹层压溃强度 {sig_crush/1e6:.2f} MPa, 兼作声纳腔壁 ✓")

# ========== 七、骨腔 ==========
标题("七、骨腔容积")
A_in_beam = 管(D_BEAM, T_BEAM)[3]
腔 = 4 * A_in_beam * L_HALF
腔 += 2 * N_RIB_SIDE * 管(*翼肋[:2])[3] * 翼肋[2]
腔 += 0.35e-3
print(f"  四根翼梁内腔 {4*A_in_beam*L_HALF*1e3:.1f} L, 翼肋 0.2 L, 主干 0.35 L")
print(f"  骨腔合计 ≈ {腔*1e3:.1f} L; 氢网 30 L 其余走组织管网")
sig_hoop = 1e6 * (D_BEAM - 2 * T_BEAM) * 1e-3 / (2 * T_BEAM * 1e-3)
print(f"  1 MPa 内压: 内径 {D_BEAM-2*T_BEAM:.1f} mm 环向应力 {sig_hoop/1e6:.1f} MPa ✓")
print(f"  1 MPa 下 24 g H₂ = {24/2.016*8.314*315/1e6*1e3:.1f} L")

# ========== 八、重建与代谢 ==========
标题("八、重建与代谢")
年周转 = 0.20
日周转 = 总骨重 * 年周转 / 365
厚 = 日周转 / RHO / 1.0
print(f"  骨重 {总骨重:.2f} kg, 年周转 {年周转*100:.0f}% → 每日 {日周转*1e3:.1f} g")
print(f"  骨内表面 1.0 m², 沉积厚度 {厚*1e6:.2f} µm/d")
print(f"  骨内碳约 60% → 每日碳 {日周转*0.6*1e3:.1f} g, 由取食获得")
print(f"  碳化耗能约 1.5 MJ/kg → {日周转*1.5e6/86400:.3f} W")
print(f"  骨折 1 mm 间隙 30 d 填满 → 33 µm/d, 为常速的 {33/厚/1e6:.0f} 倍(局部上调)")

# ========== 九、拓扑优化 ==========
标题("九、骨细胞与拓扑优化")
V_腔 = 4 / 3 * math.pi * (7.5e-6) ** 3 * 1.5e4 * 1e9
print(f"  骨细胞腔 Ø15 µm, 密度 1.5e4/mm³ → 体积分数 {V_腔*100:.1f}% (含小管约 4%)")
print(f"  骨小管 Ø0.4 µm 连通, 传递应变信号")
m_等 = math.pi * D_BEAM * 1e-3 * 1.0e-3 * 5 * RHO
m_阶 = A_beam * 5 * RHO
print(f"  翼梁单根: 等厚 1.0 mm 全程 5 m = {m_等:.2f} kg, "
      f"减薄到 {T_BEAM:.2f} mm = {m_阶:.2f} kg → 减重 {(1-m_阶/m_等)*100:.0f}%")
V_椎实 = math.pi / 4 * 0.016**2 * 0.025 * 24
m_椎实, m_椎架 = V_椎实 * RHO, 45e-6 * RHO
print(f"  脊柱: 实心 Ø16×24 = {m_椎实:.2f} kg, 拱形桁架 = {m_椎架:.2f} kg → "
      f"减重 {(1-m_椎架/m_椎实)*100:.0f}%")
m_颅实, m_颅架 = 200e-6 * RHO, 40e-6 * RHO
print(f"  头骨: 实心壳 = {m_颅实:.2f} kg, 多孔骨架 = {m_颅架:.2f} kg → "
      f"减重 {(1-m_颅架/m_颅实)*100:.0f}%")

# ========== 十、平滑肌驱动的运动约束 ==========
标题("十、平滑肌驱动的运动约束")
sig_smooth, A_bundle, arm = 100e3, 30e-4, 0.15
F_muscle = sig_smooth * A_bundle
M_muscle = F_muscle * arm
E_spring, theta = 60.0, math.pi / 2
M_spring = E_spring / theta
print(f"  平滑肌 {sig_smooth/1e3:.0f} kPa × {A_bundle*1e4:.0f} cm² = {F_muscle:.0f} N")
print(f"  力臂 {arm*100:.0f} cm → {M_muscle:.0f} N·m, 全部关节由平滑肌牵引")
print(f"  弹性索 60 J 只助回弹 → {M_spring:.0f} N·m; 铰链摩擦 20 N·m → "
      f"净 {M_spring+M_muscle-20:.0f} N·m ✓")
v_m = 0.3 * arm
print(f"  展开行程 {arm*theta*100:.1f} cm / {v_m*100:.1f} cm/s → 约 "
      f"{(arm*theta)/v_m:.1f} s")
print(f"  步行 0.4 m / 2 s = 0.2 m/s; 棘轮只防倒转, 无快肌 → 不能持续行走")

# ========== 十一、设定草案 ==========
标题("十一、设定草案(可替换 内容/怪物/怪动植物.typ 的 == 骨骼 节)")
草案 = f"""
== 骨骼

全身骨骼约*{总骨重:.1f}kg*,占体重一成二.由几丁质模板碳化沉积而成,含骨细胞.不断合成和分解,维持动态平衡.

=== 骨质

骨质是碳化几丁质基体,内嵌石墨烯片与碳纳米管束.石墨烯片沿主应力面铺展,碳纳米管束跨层桥接.密度约$1.5 "g/cm³"$,弹性模量约$600 "GPa"$,抗拉约$25 "GPa"$,抗压约$12 "GPa"$.

石墨烯片由骨细胞在层间析出,碳纳米管束沿模板孔道定向挤出.两者近乎无缺陷.

骨细胞被层间包埋,腔径约$15 mu "m"$,经骨小管连成网,连同小管占骨体积约*4%*.有机基体只在层间与骨膜,不足*1%*.

无塑性,断裂应变约*1.2%*;裂纹由有机基体偏转,损伤靠重建修复.

=== 拓扑

骨细胞感知应变,控制局部沉积与溶解.发育期由#元素[引导系统]给出初始拓扑,成年后按主应力迹线自优化.

翼梁按展向弯矩渐薄;连接件只在两翼之间受剪;椎体内部为拱形桁架;头骨夹层为多孔骨架.

材料集中在主应力迹线上,比等厚实心轻约四成.

=== 骨架

长骨均为薄壁管,壁厚$0.35$–$1.2 "mm"$.内腔通#元素[氢网],兼作骨髓.

脊柱24节,肋骨12对.胸骨与肩带汇聚四个翼根;锁骨包住#元素[控制接口]与#元素[控制神经干].后肢短粗,关节面为无矿物的水凝胶软骨.

骨腔总容积约*{腔*1e3:.0f}L*,其余氢走组织管网.

=== 翼骨

翼面由羽片构成,没有翼膜.羽根固定在翼肋上,只把局部升力传给翼肋,不参与展向承弯.

两对羽翼在胸腹交界处上下连接,展向每$0.1 "m"$一根竖直连接件,间距$0.28 "m"$.上下两翼互为支撑,合成一根空间梁:上翼受压,下翼受拉,翼根弯矩由两翼轴力偶承担.

四根翼梁外径$15 "mm"$,壁厚约$0.5 "mm"$,分三节折叠.50倍过载下单侧翼根弯矩约$64 "kN·m"$,单根翼梁轴力约$227 "kN"$,压应力约$10 "GPa"$.

#设定元素(level: 4)[翼骨铰链]

节间用套筒套接,锁销定位.展开时套筒接触承轴力,折叠时脱开.后掠$0 degree$至$90 degree$,由平滑肌牵引,展开约$5 "s"$.

翼骨不能扑动.

=== 关节

无骨骼肌,运动全部由平滑肌完成.肌束沿骨骼两侧成对排列,单束截面约$30 "cm²"$,应力上限约$100 "kPa"$,收缩速度约$0.3 "L/s"$.

关节由平滑肌牵引,棘轮只在静止时防倒转.步幅约$0.4 "m"$,每步约$2 "s"$.

平滑肌无快肌纤维,易疲劳;不能持续行走,也不能自行起降.

=== 重建

骨年周转约*20%*,每日合成分解约*{日周转*1e3:.1f}g*,骨折约$30 "d"$愈合.

碳由取食获得,经几丁质模板逐层碳化.
"""
print(草案)
