"""复核: 怪动植物主动制冷系统的量级

设定(见 内容/怪物/怪动植物.typ, 温控节):
  - 制冷机制: 固态制冷, 由共生"发电细菌"供电, 内部供电不受对外 50V 1A 限制
  - 体温级: 冷端 315K(体温 42°C), 热端接翼面, 热沉为飞行气流
  - 过热级: 深海热泉过热水比体温热, 热端需高于过热水才能排热

本脚本只核算热力学量级(卡诺极限与实际热电效率), 判断机制是否自洽。
"""

# 体温级: 冷端=体内, 热端=翼面(被气流冷到低于体温)
Tc_body = 315.0          # 冷端, 体温 42°C
Th_wing = 330.0          # 热端, 翼面温度(需略高于冷端)

# 过热级: 热沉=深海热泉过热水(远高于体温)
Tc_hot = 315.0
Th_vent = [500.0, 570.0, 650.0]   # 过热水温度候选(未在设定中给定)

# 现实热电(珀尔帖)器件效率约为卡诺极限的 30%~50%
ETA_REAL = 0.40


def cop_carnot(Tc, Th):
    return Tc / (Th - Tc)


def cop_real(Tc, Th, eta=ETA_REAL):
    return eta * cop_carnot(Tc, Th)


print("=" * 74)
print("体温级: 冷端 315K -> 热端接翼面(气流散热)")
print("=" * 74)
print(f"  热端温度 {Th_wing:.0f}K")
print(f"  卡诺 COP上限 = {cop_carnot(Tc_body, Th_wing):.1f}")
print(f"  实际热电 COP ~ {cop_real(Tc_body, Th_wing):.1f}")
print(f"  每搬运 1W 热量, 需电功 ~ {1 / cop_real(Tc_body, Th_wing):.2f} W")
print("  -> 温差小, 效率高, 机制可行")

print()
print("=" * 74)
print("过热级: 冷端 315K -> 热端须高于过热水, 把热量排进更热的介质")
print("=" * 74)
print(f"  过热水温度候选: {', '.join(f'{t:.0f}K' for t in Th_vent)}")
print(f"  {'过热水':>8s}  {'热端需>':>8s}  {'卡诺COP':>8s}  {'实际COP':>8s}  {'电功/制冷':>10s}")
for Th in Th_vent:
    print(f"  {Th:6.0f}K  {Th:6.0f}K  {cop_carnot(Tc_hot, Th):8.2f}  "
          f"{cop_real(Tc_hot, Th):8.2f}  {1 / cop_real(Tc_hot, Th):8.2f} W/W")
print("  -> 排热到比自身更热的介质, 热端温度必须高于该介质;")
print("     温差达 200~350K, COP 远低于 1, 电功为制冷量的数倍。")
print("     单级热电堆温差不足, 需多级级联逐级抬升热端温度。")

print()
print("== 结论 ==")
print("  1. 机制物理上成立: 热电制冷可把热量从低温搬到高温, 不违反第二定律,")
print("     只是向更热介质排热时 COP<1, 耗电为制冷量的数倍至十数倍。")
print(f"  2. 对外 50V1A=50W 远不够; 但设定明确内部供电不受此限,")
print("     由发电细菌(含核能共生)体内供电, 能量来源不构成瓶颈。")
print("  3. 过热级需多级热电堆累加热端温度; 现实热电材料热端上限~1000K,")
print("     排入 500~650K 过热水在材料允许范围内。")
print("  4. 原设定'加压'属蒸气压缩循环用语, 固态制冷无压缩机, 应删除。")