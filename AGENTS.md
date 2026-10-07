# AGENTS.md

技能在 `SKILL.md` , 有问题看一下

所有思考一律强制使用中文,别管输入的是什么语言。

大文件用lfs

编码一律用unicode

不懂就问我,除非我明说否则不要替我做决定

## 元素系统(文档/附件/元素系统.csv)

- 每个核心概念用 `#元素[正式名]` 引用(普通系统直接读 ID 值本身)。
- CSV 只需存非普通系统的映射行(列 `id,system,term`),如 `怪动植物,别名,黑白怪物`、`超级系统,academic,生物能量超级系统`。
- 其他系统缺失某元素时回退到普通名词(ID)。

## 模板函数已中文化(模板/lib.typ)

`表格`(uhtab)、`提示框`(breakoutbox)、`属性框`(statbox)、`人物框`(npcbox)、`法术`(spell)、`附录`(appendix)、`顶部图`/`底部图`、`品牌`(uhbrand)等。文档中调用的是中文名,不要用英文旧名。

## 字体(模板/languages/zh.toml)

`lang: "zh"` 才加载中文配置。`[fonts]` 分三组:`header`(标题=段宁毛笔小楷)、`body`(正文=霞鹜文楷等宽)、`italic`(斜体=等距更纱黑体 SC)。斜体 show rule 只设 `font` 不设 `style`——emph 自带 italic,显式 style 会破坏字体变体选择。

## 常用坑

## 语法规范

参考 文档/内容/附录.typ

字数能省就省,不要说废话

中文： 以直陈、白描为基本写法。少用状语、补语和副词，只保留有实际信息的修饰。优先保留原本自然的语言习惯，不为深刻、优美、完整而润色。保持自然的长短句变化，拒绝套用总分总结构，不强行总结或升华。
反例：「这个方法值得继续研究」不要写成「这个方法还有值得深入挖掘的空间」。

English: Use direct statements and plain prose. Minimize adverbials, complements, and adverbs; use them only when they add concrete information. Preserve the writer’s natural voice. Do not polish simple language to sound deeper, more elegant, or more complete. Keep natural variation in sentence length. Avoid rigid summary structures and forced conclusions. 
Anti-pattern: Do not turn “This method is worth studying further” into “This method offers significant room for deeper exploration.”
