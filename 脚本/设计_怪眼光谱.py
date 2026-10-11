#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怪眼感光光谱设计 —— 数值复核 + SVG 绘图
只读,不改 内容/。运行: python3 脚本/设计_怪眼光谱.py

依据:
  · 恒星辐照度 1360 W/m²(内容/地理/主行星.typ);设定未给光谱型,
    按与地球相同的总辐照度取 G2V, Teff=5772 K 黑体(可改 ST_T 换光谱型重算)
  · 大气 He .759 / O2 .200 / N2 .019 / CO2 .010 / H2O .010 / NH3 .001
    P=101300 Pa, 赤道海平面 T=300 K, 标高 11.76 km(复核_主行星与怪动植物.py)
  · O2=20% 成臭氧层(复核_氨稳定性.py),取 300 DU
  · 怪眼三层视网膜 + 辅助眼(内容/怪物/怪动植物.typ)
输出:
  终端:窗口透过率、峰位、光子通量、红外端热噪声
  图片/怪眼-感光光谱.svg
"""

import math
import html

# ========== 物理常数 ==========
H = 6.62607015e-34      # J s
C = 2.99792458e8        # m/s
K = 1.380649e-23        # J/K
NA = 6.02214076e23
SIGMA = 5.670374419e-8  # W/m^2/K^4

ST_T = 5772.0           # 恒星有效温度 K
ST_S = 1360.0           # 恒星辐照度 W/m²
P0, T0 = 101300.0, 300.0
T_BODY = 315.0          # 怪动植物体温 42°C
O3_DU = 300.0           # 臭氧柱

# ========== 1. 恒星黑体谱 ==========
def b_lambda(lam_nm, t=ST_T):
    """黑体光谱辐出度 W/m²/m(波长)"""
    lam = lam_nm * 1e-9
    x = H * C / (lam * K * t)
    return 2.0 * H * C**2 / lam**5 / (math.exp(x) - 1.0)

# 数值积分求缩放(黑体总辐射 → 1360 W/m²)
_ls = [i * 1.0 for i in range(50, 200001)]
_bint = sum(b_lambda(0.5 * (l1 + l2)) * (l2 - l1) * 1e-9
            for l1, l2 in zip(_ls[:-1], _ls[1:]))
_F_SCALE = ST_S / _bint

def f_am0(lam):
    """大气外恒星辐照度 W/m²/nm"""
    return b_lambda(lam) * _F_SCALE * 1e-9

# ========== 2. 大气透过率(天顶) ==========
# 2.1 Rayleigh: 地球空气经验式 × (n比) × (Σxα²比);
#     α(1e-30 m³): He .205  O2 1.58  N2 1.74  CO2 2.91  H2O 1.45  NH3 2.26
_a2 = (0.759 * .205**2 + 0.200 * 1.58**2 + 0.019 * 1.74**2
       + 0.010 * 2.91**2 + 0.010 * 1.45**2 + 0.001 * 2.26**2)
_a2e = 0.78 * 1.74**2 + 0.21 * 1.58**2 + 0.01 * 1.45**2
_ray_f = (P0 / T0) / (101325.0 / 288.0) * _a2 / _a2e   # ≈ 0.23

def tau_ray(lam):
    u = lam / 1000.0
    return _ray_f * 0.008569 * u**-4 * (1 + 0.0113 * u**-2 + 0.00013 * u**-4)

# 2.2 臭氧吸收截面 cm²/molecule(Hartley/Huggins 陡沿 + Chappuis 弱带)
_sig_o3 = {
    250: 1.15e-17, 260: 8.0e-18, 270: 3.8e-18, 280: 1.1e-18, 285: 4.0e-19,
    290: 3.0e-19, 295: 5.0e-19, 300: 2.0e-19, 305: 6.0e-20, 310: 1.6e-20,
    315: 5.0e-21, 320: 1.5e-21, 330: 5.0e-23, 350: 5.0e-23,
    400: 1.0e-22, 450: 1.5e-21, 500: 3.0e-21, 550: 4.5e-21, 600: 5.2e-21,
    650: 3.5e-21, 700: 1.2e-21, 750: 3.0e-22, 800: 1.0e-22,
}
_o3_lam = sorted(_sig_o3)
_n_o3 = O3_DU * 2.687e16     # molecules/cm² (1 DU = 2.687e16)

def sig_o3(lam):
    if lam <= _o3_lam[0] or lam >= _o3_lam[-1]:
        return _sig_o3[_o3_lam[0 if lam <= _o3_lam[0] else -1]]
    for l1, l2 in zip(_o3_lam[:-1], _o3_lam[1:]):
        if l1 <= lam <= l2:
            # 陡沿按对数插值
            import math as _m
            w = (lam - l1) / (l2 - l1)
            return _m.exp((1 - w) * _m.log(_sig_o3[l1]) + w * _m.log(_sig_o3[l2]))

def tau_o3(lam):
    return sig_o3(lam) * _n_o3

# 2.3 气体吸收带: 高斯凹口 (中心nm, 中心τ, FWHM nm)
def _gauss_band(lam, c, t0, fwhm):
    sig = fwhm / 2.3548
    return t0 * math.exp(-0.5 * ((lam - c) / sig) ** 2)

# H2O 可降水 51 mm(设定值); O2 20% 振转带; NH3 0.1% 窄带(估计值)
_bands = [
    ("H2O", 720, 0.12, 25), ("H2O", 820, 0.35, 35),
    ("H2O", 940, 1.60, 70), ("H2O", 1130, 2.00, 90),
    ("O2", 628, 0.30, 3), ("O2", 687, 1.20, 4), ("O2", 761, 3.50, 4),
    ("O2", 1064, 1.50, 12),
    ("NH3", 552, 0.10, 5), ("NH3", 650, 0.12, 6),
    ("NH3", 790, 0.90, 10), ("NH3", 1050, 2.20, 35),
]

def tau_bands(lam, species=None):
    return sum(_gauss_band(lam, c, t, w)
               for s, c, t, w in _bands if species is None or s == species)

def trans(lam):
    """地表垂直天顶透过率"""
    return math.exp(-(tau_ray(lam) + tau_o3(lam) + tau_bands(lam)))

def f_surf(lam):
    return f_am0(lam) * trans(lam)

# ========== 3. 视色素吸收模板 ==========
# α 带:波数对数空间高斯(A1 视色素经验形,FWHM≈0.19 λmax)
# β 带(短波肩):Govardovskii 2000 参数,对短波色素并入主带
_LOGW = 0.115

def _gov_beta(lam, lmax):
    lb = 189.6 + 0.315 * lmax
    db = abs(-20.5 + 0.041 * lmax)
    return 0.26 * math.exp(-((lam - lb) / db) ** 2)

_l_grid = [i * 0.5 for i in range(400, 3001)]
_g_norm = {}

def pigment(lam, lmax):
    """归一化吸收曲线, α 带峰值 1"""
    if lmax not in _g_norm:
        xs = [x for x in _l_grid if abs(lmax - x) < 250]
        _g_norm[lmax] = max(math.exp(-(math.log(x / lmax) / _LOGW) ** 2)
                            + _gov_beta(x, lmax) for x in xs)
    sa = math.exp(-(math.log(lam / lmax) / _LOGW) ** 2)
    return (sa + _gov_beta(lam, lmax)) / _g_norm[lmax]

# ========== 4. 峰位设计 ==========
普通 = (375, 460, 525, 600)
辅助 = (360, 445, 520, 585, 675, 860)
# 松果体 24 色: 等波数(等色差)覆盖 320–980 nm
_kl, _kh = 1.0 / 980.0, 1.0 / 320.0
松果 = tuple(sorted(round(1.0 / (_kl + i * (_kh - _kl) / 23))
                    for i in range(24)))
# 松果旁体 3 种宽基底色素(扫描 300–1100)
基底 = (450, 700, 950)
扫描 = (300, 1100)

# ========== 5. 红外热噪声(Barlow 活化能 + Arrhenius) ==========
def ea(lam):
    return 0.37 * H * C / (lam * 1e-9)      # J

# 标定: 500 nm 色素 @310 K 单分子暗异构化 ~1e-11 /s
_EA0, _T0K = ea(500), 310.0
_A = 1e-11 * math.exp(_EA0 / (K * _T0K))

def k_dark(lam, t=T_BODY):
    return _A * math.exp(-ea(lam) / (K * t))

# ========== 输出复核 ==========
if __name__ == "__main__":
    print("=" * 70)
    print("一、恒星与大气窗口(天顶)")
    print("=" * 70)
    print(f"Teff={ST_T} K 黑体归一化至 {ST_S} W/m²  "
          f"(黑体全积分 {_bint:.3e} → 缩放 {_F_SCALE:.3e})")
    print(f"Rayleigh 缩放系数 = {_ray_f:.3f}(地球空气为 1,He 主导天空更透)")
    print(f"臭氧柱 {O3_DU:.0f} DU = {_n_o3:.2e} molecules/cm²")
    print(f"{'λ nm':>6}{'大气外':>9}{'Rayleigh':>10}{'O3':>9}"
          f"{'气体带':>9}{'透过率':>8}{'地表光子通量':>14}")
    for lam in (250, 280, 300, 310, 320, 350, 400, 500, 550, 600, 687, 761,
                820, 940, 980, 1050, 1100):
        eph = H * C / (lam * 1e-9)
        nf = f_surf(lam) / eph
        print(f"{lam:>6}{f_am0(lam):>9.3f}{math.exp(-tau_ray(lam)):>10.3f}"
              f"{math.exp(-tau_o3(lam)):>9.3f}{math.exp(-tau_bands(lam)):>9.3f}"
              f"{trans(lam):>8.3f}{nf:>14.3e}")

    print()
    print("=" * 70)
    print("二、感光色素峰位(Govardovskii A1 模板)")
    print("=" * 70)
    print("普通视网膜 4 色:", 普通)
    print("辅助眼     6 色:", 辅助)
    n = len(松果)
    print(f"松果体视网膜 {n} 色(等波数 320–980 nm):")
    print("  " + " ".join(f"{v}" for v in 松果))
    # 相邻间距与模板 FWHM
    gaps = [松果[i + 1] - 松果[i] for i in range(n - 1)]
    print(f"  相邻峰间距 {min(gaps)}–{max(gaps)} nm(短波密、长波疏)")
    for lmax in (松果[0], 松果[8], 松果[16], 松果[-1]):
        half = 0.5
        lo = next(l for l in _l_grid if l >= lmax - 300 and pigment(l, lmax) >= half)
        hi = next(l for l in reversed(_l_grid)
                  if l <= lmax + 300 and pigment(l, lmax) >= half)
        print(f"  λmax={lmax:4d} 模板 FWHM ≈ {hi-lo:4.0f} nm")
    print("松果旁体基底色素:", 基底, " 扫描范围:", 扫描,
          " R=λ/Δλ≈300(Δλ≈2 nm @600)")
    # 松果体窄带色素: α 带 σ=0.055 (FWHM≈0.09λ), 无 β 带
    print()
    print("松果体窄带色素(σ=0.055, FWHM≈0.09λ)与相邻间距:")
    for i in (0, 8, 16, 23):
        l = 松果[i]
        # ln 高斯半高半宽(波长): Δλ = λmax·sinh(σ√ln2); FWHM=2Δλ
        fwhm = 2 * l * math.sinh(.055 * math.sqrt(math.log(2)))
        gap = (松果[i + 1] - l) if i < 23 else (l - 松果[i - 1])
        print(f"  λ={l:4d}  FWHM≈{fwhm:6.1f} nm  相邻间距={gap:3d} nm  "
              f"FWHM/间距={fwhm/gap:.2f}")

    print()
    print("=" * 70)
    print("三、红外端热噪声(体温 315 K;单分子暗事件速率)")
    print("=" * 70)
    print("阈值:每细胞 100 事件/s 时,色素分子数上限 = 100/k")
    for lam in (700, 800, 860, 900, 950, 980, 1050, 1100):
        k315 = k_dark(lam, 315)
        k280 = k_dark(lam, 280)
        print(f"λ={lam:4d}  Ea={ea(lam)/1.602e-19:.3f} eV  "
              f"k@315K={k315:.2e}/s  拷贝上限@315K={100/k315:.2e}   "
              f"k@280K={k280:.2e}/s  拷贝上限@280K={100/k280:.2e}")

    print()
    print("=" * 70)
    print("四、各通道峰位处地表光子通量(photons/m²/s/nm)")
    print("=" * 70)
    for name, peaks in (("普通", 普通), ("辅助", 辅助), ("松果", 松果)):
        vals = [f_surf(l) / (H * C / (l * 1e-9)) for l in peaks]
        print(f"{name}: 最小 {min(vals):.2e} @ {peaks[vals.index(min(vals))]} nm"
              f"  最大 {max(vals):.2e} @ {peaks[vals.index(max(vals))]} nm")


# ========== 6. SVG 绘图(4 张独立小图) ==========
WL0, WL1 = 250, 1150
W, HGT = 760, 300
ML, MR = 52, 18
MT, MB = 30, 46
PX0, PX1 = ML, W - MR
PW = PX1 - PX0
PY0, PY1 = MT, HGT - MB
PH = PY1 - PY0

def sx(lam):
    return PX0 + (lam - WL0) / (WL1 - WL0) * PW

def sy(v, vmax):
    return PY1 - v / vmax * PH

def wl_color(lam):
    """波长→sRGB(Tanner Helland 近似, UV/IR 外推为紫/暗红灰)"""
    if lam < 350:
        r, g, b = 0.42 - (350 - lam) / 350 * 0.4, 0.0, 0.62
    elif lam < 440:
        r, g, b = -(lam - 440) / (440 - 350), 0.0, 1.0
    elif lam < 490:
        r, g, b = 0.0, (lam - 440) / (490 - 440), 1.0
    elif lam < 510:
        r, g, b = 0.0, 1.0, -(lam - 510) / (510 - 490)
    elif lam < 580:
        r, g, b = (lam - 510) / (580 - 510), 1.0, 0.0
    elif lam < 645:
        r, g, b = 1.0, -(lam - 645) / (645 - 580), 0.0
    elif lam <= 780:
        r, g, b = 1.0, 0.0, 0.0
    else:
        f = max(0.0, 1.0 - (lam - 780) / 300)
        r, g, b = 0.55 * f, 0.0, 0.0
    if 350 <= lam < 420:
        f = 0.3 + 0.7 * (lam - 350) / 70
        r, g, b = r * f, g * f, b * f
    elif 700 < lam <= 780:
        f = 0.3 + 0.7 * (780 - lam) / 80
        r *= f
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(255 * v)))
                                   for v in (r, g, b))

def esc(s):
    return html.escape(str(s))

STYLE = ('<style>.ts{fill:#1f1a14;font-size:10px}'
         '.th{fill:#14110d;font-size:13px;font-weight:bold}'
         '.ax{stroke:#4a443b;stroke-width:.8}.gd{stroke:#8f887c;stroke-width:.7}'
         '.band{fill:#000;opacity:.10}</style>')

def svg_head(title):
    return {
        "body": [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{HGT}" '
            f'viewBox="0 0 {W} {HGT}" font-family="Songti SC, STSong, serif">',
            STYLE,
            f'<text x="{PX0}" y="18" class="th">{esc(title)}</text>',
        ],
        "defs": [
            '<defs>',
            f'<clipPath id="plot"><rect x="{PX0}" y="{PY0-4}" width="{PW}" '
            f'height="{PH+8}"/></clipPath>',
            f'<linearGradient id="spec" x1="0" y1="0" x2="1" y2="0">'
            + "".join(f'<stop offset="{(l-WL0)/(WL1-WL0):.4f}" stop-color="{wl_color(l)}"/>'
                      for l in range(WL0, WL1 + 1, 10))
            + '</linearGradient>',
        ],
    }

def x_axis(doc, ticks=range(300, 1151, 100), ribbon=True, bands=()):
    a = doc["body"].append
    for lo, hi in bands:
        a(f'<rect x="{sx(lo):.1f}" y="{PY0}" width="{sx(hi)-sx(lo):.1f}" '
          f'height="{PH}" class="band"/>')
    for lam in range(WL0, WL1 + 1, 50):
        x = sx(lam)
        a(f'<line x1="{x:.1f}" y1="{PY0}" x2="{x:.1f}" y2="{PY1}" class="gd"/>')
    a(f'<line x1="{PX0}" y1="{PY1}" x2="{PX1}" y2="{PY1}" class="ax"/>')
    for lam in ticks:
        x = sx(lam)
        a(f'<line x1="{x:.1f}" y1="{PY1}" x2="{x:.1f}" y2="{PY1+4}" class="ax"/>')
        a(f'<text x="{x:.1f}" y="{PY1+16}" class="ts" text-anchor="middle">{lam}</text>')
    if ribbon:
        ry = PY1 + 22
        a(f'<rect x="{PX0}" y="{ry}" width="{PW}" height="7" fill="url(#spec)" '
          f'stroke="#8a8177" stroke-width=".5"/>')
    a(f'<text x="{(PX0+PX1)/2:.0f}" y="{HGT-6}" class="ts" text-anchor="middle">'
      f'波长 (nm)</text>')

def write_svg(doc, path):
    out = doc["body"][:2] + doc["defs"] + ["</defs>"] + doc["body"][2:]
    out.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

# ---- 曲线抽稀(RDP)与 Catmull-Rom 三次贝塞尔平滑 ----
def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    d0 = dx * dx + dy * dy
    im, dm = 0, 0.0
    for i, (x, y) in enumerate(pts[1:-1], 1):
        d = (abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.sqrt(d0)) if d0 else 0.0
        if d > dm:
            im, dm = i, d
    if dm > eps:
        return rdp(pts[:im + 1], eps)[:-1] + rdp(pts[im:], eps)
    return [pts[0], pts[-1]]

def smooth_d(pts):
    """M + Catmull-Rom→三次贝塞尔, 坐标取整"""
    p = [(round(x), round(y)) for x, y in pts]
    d = [f"M {p[0][0]} {p[0][1]}"]
    n = len(p)
    for i in range(n - 1):
        p0 = p[max(0, i - 1)]; p1 = p[i]; p2 = p[i + 1]; p3 = p[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C {c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {p2[0]} {p2[1]}")
    return " ".join(d)

def curve_paths(pts, fill_d=None):
    """返回 (描边 d, 填充闭合 d);填充仅在给 fill_d 前缀点时生成"""
    line = smooth_d(pts)
    closed = (line + f" L {round(pts[-1][0])} {PY1} L {round(pts[0][0])} {PY1} Z")
    return line, closed

# ---------- 图1 入射光谱与大气窗口 ----------
def fig1(path):
    doc = svg_head("入射光谱与大气窗口（赤道海平面，天顶）")
    o = doc["body"].append
    x_axis(doc, bands=((250, 318), (684, 691), (756, 767), (898, 985)))
    fmax = max(f_am0(l) for l in range(300, 1150, 2))
    def dense(f):
        return [(sx(i), sy(f(i), fmax)) for i in range(WL0, WL1 + 1, 2)]
    p0 = rdp(dense(f_am0), 0.8)
    p1 = rdp(dense(f_surf), 0.35)
    pt = rdp([(sx(i), PY1 - trans(i) * PH) for i in range(WL0, WL1 + 1, 2)], 0.35)
    o('<g clip-path="url(#plot)">')
    o(f'<path d="{smooth_d(p0)} L {PX1} {PY1} L {PX0} {PY1} Z" '
      f'fill="#6f6a60" fill-opacity=".08" stroke="none"/>')
    o(f'<path d="{smooth_d(p0)}" fill="none" stroke="#6f6a60" stroke-width="1.3"/>')
    o(f'<path d="{smooth_d(p1)}" fill="none" stroke="#C62828" stroke-width="1.6"/>')
    o(f'<path d="{smooth_d(pt)}" fill="none" stroke="#1565C0" stroke-width="1.1" '
      f'stroke-dasharray="4 3" opacity=".9"/>')
    o('</g>')
    o(f'<text x="{PX1}" y="{PY0+12}" class="ts" text-anchor="end">'
      f'<tspan fill="#6f6a60">━ 大气外</tspan>　'
      f'<tspan fill="#C62828">━ 地表</tspan>　'
      f'<tspan fill="#1565C0">┄ 透过率</tspan></text>')
    for x, t in ((sx(284), "O₃"), (sx(687), "O₂"), (sx(761), "O₂"), (sx(940), "H₂O")):
        o(f'<text x="{x:.1f}" y="{PY0+26}" class="ts" text-anchor="middle" '
          f'fill="#3a352d">{t}</text>')
    write_svg(doc, path)

# ---------- 色素峰 ----------
SX_NM = PW / (WL1 - WL0)     # px / nm

def shared_pigment_defs(doc, key, width):
    """无 β 带色素在 u=(λ-λmax)/λmax 坐标下形状与 λmax 无关,
    24 个峰只存一条归一化路径,用 transform 复用。"""
    us = [-.60 + i * .008 for i in range(154)]
    def r(u):
        return math.exp(-(math.log(1 + u) / width) ** 2)
    top = " ".join(f"{u:.3f},{r(u):.3f}" for u in us)
    doc["defs"].append(f'<path id="pf{key}" d="M {us[0]:.3f} 0 L {top} '
                       f'L {us[-1]:.3f} 0 Z"/>')
    doc["defs"].append(f'<path id="pl{key}" d="M {top.replace(",", " ")}"/>')

def draw_peaks_shared(doc, peaks, key, lw, alpha, labels, hfrac=.92):
    o = doc["body"].append
    hi = PH * hfrac
    o('<g clip-path="url(#plot)">')
    for lmax in peaks:
        tr = (f"translate({sx(lmax):.1f},{PY1}) scale({SX_NM*lmax:.2f},{-hi:.1f})")
        c = wl_color(lmax)
        o(f'<use href="#pf{key}" transform="{tr}" fill="{c}" fill-opacity="{alpha}"/>')
        o(f'<use href="#pl{key}" transform="{tr}" fill="none" stroke="{c}" '
          f'stroke-width="{lw}"/>')
    o('</g>')
    for lmax in labels:
        o(f'<text x="{sx(lmax):.1f}" y="{PY0+12}" class="ts" text-anchor="middle" '
          f'fill="{wl_color(lmax)}">{lmax}</text>')

def draw_peaks(doc, peaks, lw, alpha, labels, hfrac=.92, width=.115):
    """带 β 带的普通视色素:每峰形状不同,密集采样后 RDP 抽稀为贝塞尔。"""
    o = doc["body"].append
    hi = PH * hfrac
    o('<g clip-path="url(#plot)">')
    for lmax in peaks:
        lo, hi_l = max(250, lmax - 180), min(1150, lmax + 260)
        def resp(v):
            return math.exp(-(math.log(v / lmax) / width) ** 2) + _gov_beta(v, lmax)
        nmax = max(resp(v) for v in range(lo, hi_l))
        dense = [(sx(v), PY1 - resp(v) / nmax * hi) for v in range(lo, hi_l, 2)]
        pts = rdp(dense, 0.4)
        line, closed = curve_paths(pts)
        c = wl_color(lmax)
        o(f'<path d="{closed}" fill="{c}" fill-opacity="{alpha}" stroke="none"/>')
        o(f'<path d="{line}" fill="none" stroke="{c}" stroke-width="{lw}"/>')
    o('</g>')
    for lmax in labels:
        o(f'<text x="{sx(lmax):.1f}" y="{PY0+12}" class="ts" text-anchor="middle" '
          f'fill="{wl_color(lmax)}">{lmax}</text>')

# ---------- 图2 普通视网膜 ----------
def fig2(path):
    doc = svg_head("普通视网膜 · 四色")
    x_axis(doc)
    draw_peaks(doc, 普通, 2.0, .32, set(普通))
    write_svg(doc, path)

# ---------- 图3 松果体视网膜(窄带色素, 24 峰共享路径) ----------
def fig3(path):
    doc = svg_head("松果体视网膜 · 24 色")
    x_axis(doc, bands=((250, 318), (756, 767)))
    shared_pigment_defs(doc, "n", .055)
    draw_peaks_shared(doc, 松果, "n", 1.1, .32,
                      {松果[0], 松果[6], 松果[12], 松果[18], 松果[-1]})
    write_svg(doc, path)

# ---------- 图4 松果旁体(分光光度细胞) ----------
def fig4(path):
    doc = svg_head("松果旁体 · 分光光度细胞")
    o = doc["body"].append
    x_axis(doc, bands=((250, 300),))
    colors = ("#54A24B", "#F58518", "#E45756")
    hi = PH * .8
    o('<g clip-path="url(#plot)">')
    for lmax, c in zip(基底, colors):
        lo, hi_l = max(250, lmax - 180), min(1150, lmax + 260)
        dense = [(sx(v), PY1 - pigment(v, lmax) * hi) for v in range(lo, hi_l, 2)]
        pts = rdp(dense, 0.4)
        line, closed = curve_paths(pts)
        o(f'<path d="{closed}" fill="{c}" fill-opacity=".16" stroke="none"/>')
        o(f'<path d="{line}" fill="none" stroke="{c}" stroke-width="1.4"/>')
    o('</g>')
    o(f'<line x1="{sx(300):.1f}" y1="{PY0+6}" x2="{sx(300):.1f}" y2="{PY1}" '
      f'stroke="#1565C0" stroke-width="1" stroke-dasharray="3 3"/>')
    o(f'<line x1="{sx(1100):.1f}" y1="{PY0+6}" x2="{sx(1100):.1f}" y2="{PY1}" '
      f'stroke="#1565C0" stroke-width="1" stroke-dasharray="3 3"/>')
    o(f'<text x="{sx(700):.1f}" y="{PY0+12}" class="ts" text-anchor="middle" '
      f'fill="#1565C0">扫描 300–1100，R≈300</text>')
    write_svg(doc, path)

# 辅助眼单图(6 色)
def fig5(path):
    doc = svg_head("辅助眼 · 六色")
    x_axis(doc, bands=((756, 767),))
    draw_peaks(doc, 辅助, 1.6, .28, set(辅助))
    write_svg(doc, path)



if __name__ == "__main__":
    figs = [
        (fig1, "图片/大气光谱.svg"),
        (fig2, "图片/普通视网膜.svg"),
        (fig3, "图片/松果体视网膜.svg"),
        (fig4, "图片/松果旁体.svg"),
        (fig5, "图片/辅助眼.svg"),
    ]
    for fn, p in figs:
        fn(p)
        print("已写出", p)
