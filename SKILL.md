---
name: "uheg"
description: "UHEg 项目模板仓库的正文写作与编译规范。涵盖 make pdf/web/watch 编译、内容/ 章节结构与独立页入口、元素系统(附件/元素系统.csv)、地狱之下模板中文函数调用、Markdown 导入、图片 Git LFS、网页发布(web 分支)、白描直陈的中文语法规范与常见编译坑。在编写或修改 内容/ 下 .typ、配置.typ、附件/元素系统.csv,或编译正文、发布网页时调用。"
---

# UHEg 正文写作规范

UHEg 是基于[地狱之下](https://typst.app/universe/package/underhell)模板（UnderHell Template）
整理的项目模板仓库,用于快速创建设定集/冒险/规则文档项目。仓库没有子模块,模板以 Typst 包
`@preview/underhell:<版本>` 形式引入(版本号见 `配置.typ`)。模板函数实现细节见模板包自身,
本技能只讲**用这套结构写正文**。

## 文件结构

| 路径 | 说明 |
|------|------|
| `配置.typ` | 站点配置:`#import "@preview/underhell:<版本>": *` 再导出模板;定义 `元素数据`(读 CSV) 与 `网页模板 = 地狱之下模板.with(...)`(标题/副标题/作者/品牌名/元素系统数据等) |
| `内容/index.typ` | 全量入口:`#show: 网页模板` + `#outline` + 各章 `#include` |
| `内容/<名>.typ` | 各章正文,**自带 `#import "../配置.typ": *`**;路径即 URL 段 |
| `内容/<目录>/index.typ` | 目录页正文 → URL `/<目录>/` |
| `脚本/页面.typ` | 网页各独立页的统一入口,`make` 传 `--input 页=<路径> --input 源=<路径>` |
| `脚本/web_post.sh` | 网页后处理:抽公共 CSS、跨页元素连成链接、注入目录/评论开合脚本 |
| `附件/元素系统.csv` | 元素系统宽表(首列=元素 id,其后每列=一个系统) |
| `图片/` | 图片素材,已配置 Git LFS |
| `Makefile` | 编译脚本 |
| `.github/workflows/web.yml` | 推送 `main` → 构建并强推 `web` 分支 |

## 编译

```sh
make pdf    # 内容/ 下全部 .typ → dist/*.pdf
make web    # 多页站点 → dist/(含 /assets/underhell.css)
make watch  # 监听 内容/index.typ,自动重编 dist/index.pdf
make clean  # rm -rf dist
```

直接 typst(关键:`--root .` 让项目根成为路径基准):

```sh
typst compile --root . 内容/index.typ dist/index.pdf
typst compile --root . --features html --input web=true --format html 内容/index.typ dist/index.html
```

网页是多页站点:入口 `内容/index.typ` → `dist/index.html`;其余 `内容/<路径>.typ` 经
`脚本/页面.typ` 套模板 → `dist/<路径>/index.html`;目录页 `内容/<目录>/index.typ` →
`dist/<目录>/index.html`。逐页导出后由 `sh 脚本/web_post.sh dist` 收尾。

## 章节写法

- 每章必须以 `#import "{具体的相对路径}/配置.typ": *` 开头——模板成员经 `配置.typ` 再导出,**正文只引
  `配置.typ`,不直接引 `@preview/underhell`**,站点配置也走同一出口。
- 标题直接用 `= / == …`;新增章节后在 `内容/index.typ` 里加 `#include "新章.typ"`。
- 章节是"只管正文"的片段,不自己 `#show`——模板由 `脚本/页面.typ` 统一套用,这样同一份正文
  既能被整份 `#include`,也能单独成一页。

## 元素系统(`附件/元素系统.csv`)

- 宽表:首行是系统名(如 `id,默认,别名,学术`),首列是元素 id,单元格为该元素在该系统下的
  名词,**留空则回退到 id 本身**。
- `配置.typ` 用 `csv("附件/元素系统.csv")` 读入,作为 `元素系统数据` 传给模板。
- 正文引用用 `#元素[id]`(如 `#元素[古龙]`);正文中直接写 `#元素(…)`,**不要用 `[ ]` 包裹**;
  仅在函数参数位置(如 `#表格(...)`、`name:`)用 `[...]` 包成 content。
- 定义某概念的章节标题用 `#设定元素(level: n)[名]`(标题 + 锚点),`@名` 可交叉引用。
- 只要用了 `#元素("xxx")`,就必须把 `xxx` 写进 CSV 的 id 列。
- `#元素总表()` 列出全部元素。
- 编译时用 `--input 元素系统=<列名>` 切换系统(如 `--input 元素系统=学术`)。

## 模板函数(调用中文名)

`地狱之下模板`(文档初始化/网页模板)、`元素`、`设定元素`、`设置元素系统`、`表格`、`提示框`、
`属性框`、`人物框`、`法术`、`附录`、`顶部图` / `底部图`、`品牌`、`评论`。调用一律用中文名,
勿用英文旧名。示例见 `内容/概述.typ`(表格、提示框)与 `内容/示例.typ`(属性框、人物框、法术)。

## Markdown 导入

`内容/关于.typ` 演示把 Markdown 渲染进正文:`cmarker` 负责转译,`mitex` 让 `$…$` / `$$…$$`
里的 LaTeX 公式也能渲染,`scope` 把 Markdown 图片变成带题注的 `figure`。仓库根 `README.md`
即由它渲染进文档,故改动 README 会同步反映到「关于」页。

## 图片与 Git LFS

- `图片/` 下常见图片格式(png/jpg/jpeg/gif/webp/bmp/tif/tiff/avif/heic/heif/ico/psd)
  由根目录 `.gitattributes` 配置了 Git LFS。
- clone 前需装 `git lfs`,否则拿到的是指针文件;新图放进 `图片/` 即自动走 LFS。
- 引用图片用 `image("图片/xxx.png")`(路径相对当前 `.typ` 文件解析)。

## 语法规范

中文:以直陈、白描为基本写法。少用状语、补语和副词,只保留有实际信息的修饰。
优先保留原本自然的语言习惯,不为深刻、优美、完整而润色。保持自然的长短句变化,
拒绝套用总分总结构,不强行总结或升华。

反例:「这个方法值得继续研究」不要写成「这个方法还有值得深入挖掘的空间」。

English: Use direct statements and plain prose. Minimize adverbials, complements,
and adverbs; use them only when they add concrete information. Preserve the
writer's natural voice. Do not polish simple language to sound deeper, more
elegant, or more complete. Keep natural variation in sentence length. Avoid rigid
summary structures and forced conclusions.

## 发布网页

`make web` 的 `dist/` 是纯静态站点。推送 `main` 后 `.github/workflows/web.yml` 会重建并
强推 `web` 分支;托管平台(Cloudflare Pages / EdgeOne Pages)绑定 `web` 分支并**关闭平台侧
构建**即可。分平台步骤见根 `README.md`「部署网页」。

## 已知坑

1. `--root .` 必需——`配置.typ` 在项目根,正文以 `../配置.typ` 引用。
2. `#include` 的相对路径以**被 include 文件所在位置**解析(非调用处),且**不继承父文件作用域**,
   故每个 `内容/<路径>.typ` 必须自带 `#import "…/配置.typ": *`。
3. 正文顶层不能出现裸 `#p`——`#` 后必须是已定义符号,否则编译失败。
4. Typst 函数参数/变量名用简体中文(如 `基础层级`),勿混繁体。
5. 交叉引用标签用中文名或名词元素(id),`@标签` 需与 `<标签>` 一致。
6. 网页专属内容用 `#if is_web() [ … ]` 包裹(模板导出),PDF 编译时整段跳过。
7. `set heading(offset:)` 只对标记标题(`= ×N`)生效,不作用于 `#heading(level: N)`。