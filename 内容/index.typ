// 模板成员与站点配置统一从配置.typ取(它再导出模板/lib.typ),全项目不再直接引模板。
// / Template members come via 配置.typ, which re-exports 模板/lib.typ.
#import "../配置.typ": *

// 评论/待办用瘦金书(FZZhaoJiShouJinShuS)。判断 PDF 是否真正用上它,
// 以 Chrome/系统阅读器为准:它们能正确显示内嵌的该字库(CID/GB1 子集)。
// VS Code 的 pdf.js 预览会对该子集回退为本机楷体,把评论显示成与正文一致,是查看器行为而非文档缺陷,勿据此判断字体未生效。

// 正文标点按语言渲染:标点替换函数在模板中,默认读取按 lang 写入的_语言标点_映射。
// 数字两侧的源标点(如 50:1、小数)与多字符源(如 ...)除外,链接内文本不受影响。
#show text: 标点替换

// PDF 封面图:web 模式不渲染整页封面(仅标题块),print 模式走纯白省墨封面,
// 因此此图只出现在普通版与屏幕版的 PDF 上。
// / Cover image: web renders no full-page cover, print uses an ink-saving white cover,
// so this image only shows up in the normal and screen PDF builds.
#show: 网页模板.with(cover: image("../图片/地狱之下.jpg", width: 100%, height: 100%, fit: "cover"), 页脚链接: 站点链接("/index.pdf"))

// 站内导航(仅网页):导航栏只保留"首页"与外链,分页入口做成卡片放在这里(只列顶层页,子页见各目录页)。
// / In-site nav (web only): the top nav keeps only 首页 + external links; the page
// entries are cards here. Printed PDF skips it (links are useless on paper).
#if 网页编译() [
  #html.elem("nav", attrs: (class: "uh-navcards",))[
    #for (路径, 名) in 导航.filter(p => not p.at(0).contains("/")) [
      #html.elem("a", attrs: (class: "uh-navcard", href: "/" + 路径 + "/"))[#名]
    ]
  ]
]

#目录()

#set heading(numbering: "1.")

= 星球

#设定元素(level: 2)[主行星]

#导入("内容/地理/主行星.typ", 偏移: 2)

#设定元素(level: 2)[天堂]

#导入("内容/地理/天堂.typ", 偏移: 2)

#设定元素(level: 1)[特殊系统]

提供给#元素[特殊能力者]#元素[特殊能力]

#设定元素(level: 2)[特殊能力]

#设定元素(level: 2)[特殊能力者]

#设定元素(level: 2)[供能网络]

由#元素[特殊植物]和#元素[特殊真菌]组成的网络,#元素[特殊植物]负责光合,#元素[特殊真菌]负责传递能量.

#设定元素(level: 2)[执行网络]

接收#元素[供能网络]的能量供#元素[特殊能力者]进行操作.

同时对#元素[特殊能力者]有能量和功率#元素[限额],#元素[限额]可通过#元素[修炼]提升.

#元素[执行网络]通过#元素[接口]与#元素[特殊能力者]连接,不同#元素[特殊能力者]对接口的适配能力不同.适配能力可有单基因,多基因,表观遗传或配置数据决定

#设定元素(level: 3)[执行指令]

一种非常基础的指令集

#设定元素(level: 2)[接口]

#TODO[接口]

== 底层实现

#TODO[底层实现]

#导入("内容/怪物/index.typ", 偏移: 1)

#导入("内容/生物/index.typ", 偏移: 1)

#设定元素(level: 1)[神明]

*等级由高到低排列*,但同一分类内部无高低贵贱

#设定元素(level: 2)[真神]

真正的神明,具有#元素[编制]

万能,没有属性/范围等分类

#设定元素(level: 3)[组织者]

具有#元素[编制编制]

负责管理#元素[编制]

#设定元素(level: 4)[管理员]

#设定元素(level: 3)[支配者]

具有#元素[奴隶主编制]

可以创造和拥有奴隶_但不一定_,且奴隶的数量与生死影响不到自身

#设定元素(level: 4)[旧日支配者]

被封印,休眠或者被干掉的#元素[神明]

#设定元素(level: 5)[克苏鲁]

#设定元素(level: 4)[新时代支配者]

现在依旧活跃的#元素[神明],虽然大多数都被架空或者边缘化了

===== #元素[天堂]

#设定元素(level: 3)[被支配者]

具有#元素[奴隶编制]

#元素[支配者]创造的#元素[奴隶],可以被赠与,租借,买卖给任何生物_不限于#元素[神明]_,也可以被赏赐给#元素[神棍]和#元素[资产]作为奖励

必须被支配,否则无法存活.也不能拥有#元素[奴隶],只能拥有#元素[资产]

#评论[虽然没有自由,但确实是不折不扣的#元素[真神]]

==== #元素[怪动植物]

#评论[没有自由,但过得确实是神仙日子]

#设定元素(level: 2)[神棍]

具有#元素[编外编制],就是没有#元素[编制]

#元素[支配者]的#元素[代理],本质上也是#元素[真神]的#元素[资产]

==== #元素[仙子]

==== #元素[精灵]

#设定元素(level: 2)[伪神]

同样是#元素[资产],本身也并无任何本质上特别之处,只是自行或者被其它生物#元素[神化]

而#元素[真神]完全懒得理它们.#评论[其实是被架空了]

具有特定的属性/负责范围

常见的有各种宗教的神明

// 附录: 使用模板内置 appendix 函数(字母编号 + 计数器重置)/
// Appendix: use the built-in appendix helper from the template
#附录[
  #include "附录.typ"
]

#pagebreak()

#set page(columns: 1)

#block[
  #set heading(numbering: none)
  = 元素总表
]

下列表格汇总了本设定中全部核心概念在各元素系统下的对应名词.空白单元格表示该元素在该系统中未定义,自动回退到普通名词_即元素本身_.

#元素总表()

#block[
  #set heading(numbering: none)
  = TODO
]

#TODO表格()
