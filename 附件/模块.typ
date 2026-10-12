// cetz 绘图模块:集中定义全部绘图数据、配色、图例与绘图函数
// 内容文件 #import 本模块后直接调用绘图函数,不再各自 import cetz
#import "@preview/cetz:0.4.0": canvas, draw
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
  赤道参数.海平面温 - (赤道参数.海平面温 - 极点参数.海平面温) * s * s * s * s
}


// ========== 怪眼 · 感光光谱 ==========
// 物理模型与峰位设计见 脚本/设计_怪眼光谱.py(数值复核脚本);曲线由 cetz-plot 直接绘制,不再生成外链 SVG。
// 定量输出:终端表见该脚本(恒星黑体归一化、大气透过率、视色素 FWHM、红外热噪声)。

#let 光谱常数 = (
  H: 6.62607015e-34, C: 2.99792458e8, K: 1.380649e-23,
  恒星温: 5772.0,   // 按 1360 W/m² 取 G2V
  缩放: 6.788e-5,    // 黑体辐亮度式 ∫b_λdλ = 2.003e7 W/m²,归一到 1360 W/m²
  雷利: 0.231,       // Rayleigh 缩放(He 主导,空气更透;地球空气为 1)
  臭氧数: 8.06e18,   // molecules/cm²(300 DU)
)

// 恒星黑体谱(辐亮度式) → 大气外辐照度 W/m²/nm
#let 黑体谱(λ) = {
  let l = λ * 1e-9
  let hc = 光谱常数.H * 光谱常数.C
  2 * hc * 光谱常数.C / (calc.pow(l, 5) * (calc.exp(hc / (l * 光谱常数.K * 光谱常数.恒星温)) - 1))
}
#let 恒星谱(λ) = 黑体谱(λ) * 光谱常数.缩放 * 1e-9

// 大气透过率(赤道海平面,天顶):Rayleigh + 臭氧(Hartley/Huggins 陡沿)+ 气体吸收带
#let 雷利τ(λ) = {
  let u = λ / 1000.0
  光谱常数.雷利 * 0.008569 * calc.pow(u, -4) * (1 + 0.0113 * calc.pow(u, -2) + 0.00013 * calc.pow(u, -4))
}

#let 臭氧截面表 = (
  (250, 1.15e-17), (260, 8.0e-18), (270, 3.8e-18), (280, 1.1e-18), (285, 4.0e-19),
  (290, 3.0e-19), (295, 5.0e-19), (300, 2.0e-19), (305, 6.0e-20), (310, 1.6e-20),
  (315, 5.0e-21), (320, 1.5e-21), (330, 5.0e-23), (350, 5.0e-23),
  (400, 1.0e-22), (450, 1.5e-21), (500, 3.0e-21), (550, 4.5e-21), (600, 5.2e-21),
  (650, 3.5e-21), (700, 1.2e-21), (750, 3.0e-22), (800, 1.0e-22),
)
#let 臭氧截面(λ) = {
  let t = 臭氧截面表
  if λ <= t.first().at(0) { return t.first().at(1) }
  if λ >= t.last().at(0) { return t.last().at(1) }
  let r = 0.0
  for i in range(t.len() - 1) {
    let (l1, v1) = t.at(i)
    let (l2, v2) = t.at(i + 1)
    if l1 <= λ and λ <= l2 {
      let w = (λ - l1) / (l2 - l1)
      r = calc.exp((1 - w) * calc.ln(v1) + w * calc.ln(v2))   // 对数插值,保陡沿
    }
  }
  r
}
#let 臭氧τ(λ) = 臭氧截面(λ) * 光谱常数.臭氧数

#let 吸收带表 = (
  ("H2O", 720, 0.12, 25), ("H2O", 820, 0.35, 35), ("H2O", 940, 1.60, 70), ("H2O", 1130, 2.00, 90),
  ("O2", 628, 0.30, 3), ("O2", 687, 1.20, 4), ("O2", 761, 3.50, 4), ("O2", 1064, 1.50, 12),
  ("NH3", 552, 0.10, 5), ("NH3", 650, 0.12, 6), ("NH3", 790, 0.90, 10), ("NH3", 1050, 2.20, 35),
)
#let 吸收带τ(λ) = 吸收带表.fold(0.0, (acc, b) => {
  let s = b.at(3) / 2.3548
  acc + b.at(2) * calc.exp(-0.5 * calc.pow((λ - b.at(1)) / s, 2))
})
#let 透过率(λ) = calc.exp(-(雷利τ(λ) + 臭氧τ(λ) + 吸收带τ(λ)))
#let 地表谱(λ) = 恒星谱(λ) * 透过率(λ)

// 视色素吸收模板:α 带(波数对数空间高斯)+ β 带肩(Govardovskii 2000 参数)
#let 视色素(λ, λmax, 宽度: 0.115, 带: true) = {
  let a = calc.exp(-calc.pow(calc.ln(λ / λmax) / 宽度, 2))
  if 带 {
    let lb = 189.6 + 0.315 * λmax
    let db = calc.abs(-20.5 + 0.041 * λmax)
    a + 0.26 * calc.exp(-calc.pow((λ - lb) / db, 2))
  } else { a }
}

// 峰位(λmax, nm):普通视网膜四色;辅助眼六色;松果体 24 色(等波数 320–980);松果旁体三基底
#let 峰普通 = (375, 460, 525, 600)
#let 峰辅助 = (360, 445, 520, 585, 675, 860)
#let 峰松果 = (320, 330, 340, 351, 362, 375, 388, 402, 418, 435, 452, 472,
  493, 517, 542, 571, 602, 637, 677, 721, 772, 831, 899, 980)
#let 峰基底 = (450, 700, 950)

// 波长 → sRGB(Tanner Helland 近似;UV / 红外外推为紫 / 暗红)
#let 波长色(λ) = {
  let c = if λ < 350 { (0.42 - (350 - λ) / 350 * 0.4, 0.0, 0.62) }
    else if λ < 440 { (-(λ - 440) / (440 - 350), 0.0, 1.0) }
    else if λ < 490 { (0.0, (λ - 440) / (490 - 440), 1.0) }
    else if λ < 510 { (0.0, 1.0, -(λ - 510) / (510 - 490)) }
    else if λ < 580 { ((λ - 510) / (580 - 510), 1.0, 0.0) }
    else if λ < 645 { (1.0, -(λ - 645) / (645 - 580), 0.0) }
    else if λ <= 780 { (1.0, 0.0, 0.0) }
    else { let f = calc.max(0.0, 1.0 - (λ - 780) / 300); (0.55 * f, 0.0, 0.0) }
  let (r, g, b) = if 350 <= λ and λ < 420 {
    let f = 0.3 + 0.7 * (λ - 350) / 70
    (c.at(0) * f, c.at(1) * f, c.at(2) * f)
  } else if 700 < λ and λ <= 780 {
    let f = 0.3 + 0.7 * (780 - λ) / 80
    (c.at(0) * f, c.at(1), c.at(2))
  } else { c }
  rgb(int(calc.round(calc.clamp(r, 0, 1) * 255)),
      int(calc.round(calc.clamp(g, 0, 1) * 255)),
      int(calc.round(calc.clamp(b, 0, 1) * 255)))
}

// 画布:统一 x 轴(250–1150 nm),y 归一化(彩带占底部负区间,故隐去 y 刻度);
// 宽度随栏宽铺满,再交 适配栏宽 兜住标签外溢
#let 光谱画布(体, 比: 0.55) = layout(尺寸 => {
  let 宽 = 尺寸.width / 1cm
  适配栏宽(canvas({
    plot.plot(
      体,
      size: (宽, 宽 * 比),
      axis-style: "scientific",
      x-min: 250, x-max: 1150, x-tick-step: 200, x-label: [波长 (nm)], x-grid: true,
      y-min: -0.12, y-max: 1.06, y-tick-step: none, y-label: none,
    )
  }))
})

// 底部光谱彩带
#let 光谱彩带() = plot.annotate({
  let 段 = 90
  let 步 = (1150.0 - 250.0) / 段
  for i in range(段) {
    let lo = 250.0 + i * 步
    draw.rect((lo, -0.085), (lo + 步, -0.005), fill: 波长色(lo + 步 / 2), stroke: none)
  }
}, resize: false)

// 吸收带底纹
#let 吸收带底纹(带) = plot.annotate({
  for (lo, hi) in 带 {
    draw.rect((lo, 0), (hi, 1.0), fill: black.transparentize(90%), stroke: none)
  }
}, resize: false, background: true)

// 入射光谱与大气窗口
#let 大气光谱图 = {
  let 通量序列 = range(300, 1150, step: 2).map(λ => 恒星谱(λ))
  let 峰 = calc.max(..通量序列)
  光谱画布({
    吸收带底纹(((250, 318), (684, 691), (756, 767), (898, 985)))
    光谱彩带()
    plot.annotate({
      for (x, t) in ((284, [O₃]), (687, [O₂]), (761, [O₂]), (940, [H₂O])) {
        draw.content((x, 1.02), text(size: 6.5pt, fill: rgb("#3a352d"), t))
      }
    }, resize: false)
    plot.add(λ => 恒星谱(λ) / 峰, domain: (250, 1150), samples: 1100,
      fill: true, fill-type: "axis",
      style: (stroke: rgb("#6f6a60") + 1.3pt, fill: rgb("#6f6a60").transparentize(92%)))
    plot.add(λ => 地表谱(λ) / 峰, domain: (250, 1150), samples: 1100,
      style: (stroke: rgb("#C62828") + 1.6pt))
    plot.add(透过率, domain: (250, 1150), samples: 1100,
      style: (stroke: (paint: rgb("#1565C0"), thickness: 1.1pt, dash: "dashed")))
  })
}
#let 大气光谱图例 = text(size: .85em)[
  #text(fill: rgb("#6f6a60"))[━ 大气外]　#text(fill: rgb("#C62828"))[━ 地表]　#text(fill: rgb("#1565C0"))[┄ 透过率]
]

// 普通视网膜(四色,带 β 带)
#let 普通视网膜图 = 光谱画布({
  光谱彩带()
  for p in 峰普通 {
    let c = 波长色(p)
    plot.add(λ => 视色素(λ, p) * 0.92, domain: (calc.max(250, p - 190), calc.min(1150, p + 270)), samples: 160,
      fill: true, fill-type: "axis",
      style: (stroke: c + 1.6pt, fill: c.transparentize(72%)))
    plot.annotate(draw.content((p, 0.98), text(size: 6.5pt, fill: c, str(p))), resize: false)
  }
})

// 松果体视网膜(24 色,窄带色素 σ=0.055,无 β 带)
#let 松果体视网膜图 = 光谱画布({
  吸收带底纹(((250, 318), (756, 767)))
  光谱彩带()
  for p in 峰松果 {
    let c = 波长色(p)
    plot.add(λ => 视色素(λ, p, 宽度: 0.055, 带: false) * 0.94,
      domain: (calc.max(250, p * 0.62), calc.min(1150, p * 1.5)), samples: 60,
      fill: true, fill-type: "axis",
      style: (stroke: c + 1.0pt, fill: c.transparentize(66%)))
  }
  for i in (0, 6, 12, 18, 23) {
    let p = 峰松果.at(i)
    plot.annotate(draw.content((p, 1.0), text(size: 6pt, fill: 波长色(p), str(p))), resize: false)
  }
})

// 松果旁体(分光光度细胞,三宽基底色素,扫描 300–1100)
#let 松果旁体视网膜图 = 光谱画布({
  吸收带底纹(((250, 300),))
  光谱彩带()
  let 基底色 = (rgb("#54A24B"), rgb("#F58518"), rgb("#E45756"))
  for (i, p) in 峰基底.enumerate() {
    let c = 基底色.at(i)
    plot.add(λ => 视色素(λ, p) * 0.8, domain: (calc.max(250, p - 190), calc.min(1150, p + 270)), samples: 200,
      fill: true, fill-type: "axis",
      style: (stroke: c + 1.4pt, fill: c.transparentize(84%)))
  }
  plot.annotate({
    draw.line((300, 0), (300, 1.0), stroke: (paint: rgb("#1565C0"), thickness: 1pt, dash: "dashed"))
    draw.line((1100, 0), (1100, 1.0), stroke: (paint: rgb("#1565C0"), thickness: 1pt, dash: "dashed"))
    draw.content((700, 0.5), text(size: 6.5pt, fill: rgb("#1565C0"), [扫描 300–1100,R≈300]))
  }, resize: false)
})

// 辅助眼(六色)
#let 辅助眼图 = 光谱画布({
  吸收带底纹(((756, 767),))
  光谱彩带()
  for p in 峰辅助 {
    let c = 波长色(p)
    plot.add(λ => 视色素(λ, p) * 0.92, domain: (calc.max(250, p - 190), calc.min(1150, p + 270)), samples: 160,
      fill: true, fill-type: "axis",
      style: (stroke: c + 1.5pt, fill: c.transparentize(72%)))
    plot.annotate(draw.content((p, 0.98), text(size: 6.5pt, fill: c, str(p))), resize: false)
  }
})