// cetz 绘图模块:集中定义全部绘图数据、配色、图例与绘图函数
// 内容文件 #import 本模块后直接调用绘图函数,不再各自 import cetz
#import "@preview/cetz:0.4.0": canvas
#import "@preview/cetz-plot:0.1.2": plot, chart


// 按栏宽等比缩放:图宽超出栏宽时缩到栏宽
#let 适配栏宽(图) = layout(尺寸 => {
  let 限宽 = 尺寸.width
  let 实宽 = measure(图).width
  if 实宽 > 限宽 { scale(图, 限宽 / 实宽 * 100%) } else { 图 }
})


// ========== 主行星 · 大气 ==========
// 解析模型:低空湍流混合主导,均质层顶(约 100 km)以下成分均匀,故文档覆盖范围内成分恒定;
// 温度分三段:对流层(干绝热 Γ=g/c_p)、平流层(升温)、中间层(降温至中间层顶),以上为热层。
// 密度取理想气体 ρ = P·M̄/(R T),声速 a = √(γ R T / M̄)

#let 重力 = 20.0
#let 气体常数 = 8.314462618
#let 海平面气压 = 1.013e5
#let 对流层顶温 = 216.65
#let 平流层顶温 = 270.0
#let 平流层顶高 = 47.0e3
#let 中间层顶温 = 183.0
#let 中间层顶高 = 85.0e3

// 物种:(名, 摩尔质量 kg/mol, 自由度 f, 海平面体积比, 色);c_p,i = (f/2)·R/M
#let 大气物种 = (
  (名: "He", 质量: 0.004003, 自由度: 5, 初比: 0.759, 色: rgb("#F58518")),
  (名: "O2", 质量: 0.032000, 自由度: 7, 初比: 0.200, 色: rgb("#4C78A8")),
  (名: "N2", 质量: 0.028013, 自由度: 7, 初比: 0.019, 色: rgb("#54A24B")),
  (名: "CO2", 质量: 0.044010, 自由度: 7, 初比: 0.010, 色: rgb("#BAB0AC")),
  (名: "H2O", 质量: 0.018015, 自由度: 8, 初比: 0.010, 色: rgb("#72B7B2")),
  (名: "NH3", 质量: 0.017031, 自由度: 8, 初比: 0.001, 色: rgb("#E45756")),
)
#let 物种数 = 大气物种.len()

// 低空湍流混合,均质层顶以下成分均匀;海平面体积比即全程体积比(归一化)
#let 海平面比 = {
  let 总 = range(物种数).map(i => 大气物种.at(i).初比).sum()
  range(物种数).map(i => 大气物种.at(i).初比 / 总)
}
// 平均摩尔质量 kg/mol
#let 平均摩尔质量 = range(物种数).map(i => 海平面比.at(i) * 大气物种.at(i).质量).sum()
// 质量加权定压比热 J/(kg·K)
#let 定压比热 = {
  let m = range(物种数).map(i => 海平面比.at(i) * 大气物种.at(i).质量)
  let 总 = m.sum()
  range(物种数).map(i => m.at(i) / 总 * (大气物种.at(i).自由度 / 2) * 气体常数 / 大气物种.at(i).质量).sum()
}
#let 干绝热率 = 重力 / 定压比热
#let 比热比 = 定压比热 / (定压比热 - 气体常数 / 平均摩尔质量)

// 区域参数:海平面温度、配色
#let 赤道参数 = (海平面温: 300.0, 色: rgb("#C62828"))
#let 极点参数 = (海平面温: 240.0, 色: rgb("#1565C0"))

// 对流层顶:干绝热降温至对流层顶温的高度
#let 对流层顶(区) = (区.海平面温 - 对流层顶温) / 干绝热率

// 温度:h(m) → K
#let 大气温度(区, h) = {
  let 顶高 = 对流层顶(区)
  if h <= 顶高 { 区.海平面温 - 干绝热率 * h }
  else if h <= 平流层顶高 { 对流层顶温 + (平流层顶温 - 对流层顶温) * (h - 顶高) / (平流层顶高 - 顶高) }
  else if h < 中间层顶高 { 平流层顶温 + (中间层顶温 - 平流层顶温) * (h - 平流层顶高) / (中间层顶高 - 平流层顶高) }
  else { 中间层顶温 }
}

// 压强 Pa:静力平衡 dP/P = −g·M̄/(R·T) dh,数值积分
#let 大气压强(区, h) = {
  let 步长 = 100.0
  let n = calc.max(1, calc.ceil(h / 步长))
  let dh = h / n
  range(n).fold(海平面气压, (P, k) => {
    let z = k * dh
    let Tm = 0.5 * (大气温度(区, z) + 大气温度(区, z + dh))
    P * calc.exp(-重力 * 平均摩尔质量 / (气体常数 * Tm) * dh)
  })
}

// 密度 kg/m³
#let 大气密度(区, h) = 大气压强(区, h) * 平均摩尔质量 / (气体常数 * 大气温度(区, h))

// 声速 m/s
#let 大气声速(区, h) = calc.sqrt(比热比 * 气体常数 * 大气温度(区, h) / 平均摩尔质量)

// 大气成分(海平面体积比)与饼图配色
#let 大气成分 = (
  (名: [$"He"$], 占比: 75.9, 色: rgb("#F58518")),
  (名: [$"O"_2$], 占比: 20.0, 色: rgb("#4C78A8")),
  (名: [$"N"_2$], 占比: 1.9, 色: rgb("#54A24B")),
  (名: [$"CO"_2$], 占比: 1.0, 色: rgb("#BAB0AC")),
  (名: [$"H"_2 "O"$], 占比: 1.0, 色: rgb("#72B7B2")),
  (名: [$"NH"_3$], 占比: 0.1, 色: rgb("#E45756")),
)

// 大气成分饼图(cetz-plot 内置)
#let 大气成分饼图 = canvas({
  chart.piechart(
    大气成分,
    value-key: "占比",
    label-key: "名",
    slice-style: 大气成分.map(项 => 项.色),
    radius: 1.2,
    gap: 0deg,
    outer-label: (content: none),
  )
})

// 曲线说明:替代图内图例,与曲线同色
#let 曲线图例 = text(size: .85em)[
  #text(fill: 赤道参数.色)[━ 赤道]　#text(fill: 极点参数.色)[━ 极点]
  #h(1em)#text(fill: rgb("#B0B0B0"))[┄ 对流层顶]　#text(fill: rgb("#B0B0B0"))[┄ 平流层顶]
]

// 剖面图:取(区, h) 返回横轴值,随高度变化;超出栏宽时等比缩放
#let 剖面图(取, 轴参数) = 适配栏宽(canvas({
  plot.plot(
    size: (7.5, 4.6),
    axis-style: "scientific",
    ..轴参数,
    y-min: 0, y-max: 60, y-tick-step: 10, y-label: [高度 (km)], y-grid: true,
    {
      plot.add(h => (取(赤道参数, h * 1000), h), domain: (0, 60), samples: 300,
        mark: none, style: (stroke: 赤道参数.色 + 1.6pt))
      plot.add(h => (取(极点参数, h * 1000), h), domain: (0, 60), samples: 300,
        mark: none, style: (stroke: 极点参数.色 + 1.6pt))
      let 分界 = (paint: rgb("#B0B0B0"), thickness: .7pt, dash: "dashed")
      plot.add-hline(对流层顶(赤道参数) / 1000, axes: ("x", "y"), style: (stroke: 分界))
      plot.add-hline(对流层顶(极点参数) / 1000, axes: ("x", "y"), style: (stroke: 分界))
      plot.add-hline(平流层顶高 / 1000, axes: ("x", "y"), style: (stroke: 分界))
    }
  )
}))

// 组分剖面图:He/O₂/N₂ 体积比随高度;低空均匀,故为水平线
#let 组分色 = (He: rgb("#F58518"), O2: rgb("#4C78A8"), N2: rgb("#54A24B"))
#let 组分图例 = text(size: .85em)[
  #text(fill: 组分色.He)[━ He]　#text(fill: 组分色.O2)[━ $"O"_2$]　#text(fill: 组分色.N2)[━ $"N"_2$]
]
#let 组分剖面图 = 适配栏宽(canvas({
  plot.plot(
    size: (7.5, 4.6),
    axis-style: "scientific",
    x-min: 0, x-max: 100, x-tick-step: 20, x-label: [体积比 (%)], x-grid: true,
    y-min: 0, y-max: 60, y-tick-step: 10, y-label: [高度 (km)], y-grid: true,
    {
      plot.add(h => (海平面比.at(0) * 100, h), domain: (0, 60), samples: 2,
        mark: none, style: (stroke: 组分色.He + 1.6pt))
      plot.add(h => (海平面比.at(1) * 100, h), domain: (0, 60), samples: 2,
        mark: none, style: (stroke: 组分色.O2 + 1.6pt))
      plot.add(h => (海平面比.at(2) * 100, h), domain: (0, 60), samples: 2,
        mark: none, style: (stroke: 组分色.N2 + 1.6pt))
    }
  )
}))


// ========== 怪动植物 · 声纳 ==========

// 声纳定位误差:海平面与巡航高度(20km);距离/误差单位 m
// 由经典吸收模型 α = k(h)·f²(k 随密度与声速修正)求各距离的最优频率后换算
// 生成脚本:脚本/复核_声纳模型.py(海平面实用距离 345 m,巡航 230 m)
#let 海平面色 = rgb("#C62828")
#let 巡航色 = rgb("#1565C0")
#let 海平面声纳 = (
  (2, 0.0118), (4, 0.0333), (6, 0.0612), (8, 0.0943), (10, 0.1317),
  (12, 0.1732), (15, 0.2420), (20, 0.3726), (25, 0.5207), (30, 0.6845),
  (40, 1.0539), (50, 1.4729), (60, 1.9361), (80, 2.9809), (100, 4.1659),
  (120, 5.4762), (150, 7.6533), (180, 10.0605), (200, 11.7830), (230, 14.5312),
  (260, 17.4651), (300, 21.6467), (345, 26.6956),
)
#let 巡航声纳 = (
  (2, 0.0324), (4, 0.0916), (6, 0.1683), (8, 0.2592), (10, 0.3622),
  (12, 0.4761), (15, 0.6654), (20, 1.0244), (25, 1.4316), (30, 1.8819),
  (40, 2.8974), (50, 4.0493), (60, 5.3229), (80, 8.1952), (100, 11.4531),
  (120, 15.0555), (150, 21.0408), (180, 27.6588), (200, 32.3944), (230, 39.9500),
)

#let 声纳图例 = text(size: .85em)[
  #text(fill: 海平面色)[━ 海平面]　#text(fill: 巡航色)[━ 巡航 $2 times 10^4 "m"$]
]

#let 声纳曲线 = 适配栏宽(canvas({
  plot.plot(
    size: (7.5, 4.6),
    axis-style: "scientific",
    x-min: 0, x-max: 360, x-tick-step: 60, x-label: [距离 (m)], x-grid: true,
    y-min: 0.005, y-max: 50, y-mode: "log", y-tick-step: 1, y-label: [定位误差 (m)], y-grid: true,
    {
      plot.add(海平面声纳, mark: none, style: (stroke: 海平面色 + 1.6pt))
      plot.add(巡航声纳, mark: none, style: (stroke: 巡航色 + 1.6pt))
    }
  )
}))

#let 纬度温(φ) = {
  let s = calc.sin(φ * 1deg)
  赤道参数.海平面温 - (赤道参数.海平面温 - 极点参数.海平面温) * s * s
}