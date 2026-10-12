#import "../../配置.typ": *


= 怪物

#for (路径, 名) in 导航.filter(p => p.at(0).starts-with("怪物/")) [
  - #link("/" + 路径 + "/")[#名]
]