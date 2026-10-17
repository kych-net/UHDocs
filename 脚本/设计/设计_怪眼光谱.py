#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
怪眼感光光谱设计 —— 数值复核
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
绘图:曲线在 附件/模块.typ 用 cetz 直接绘制(峰位数据与本脚本一致)
"""

import math

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
