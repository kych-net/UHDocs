# 地狱之下文档

## 项目结构

- `配置.typ` —— 站点配置：标题、作者、品牌名、元素系统数据
- `Makefile` —— 编译命令（`pdf` / `web` / `watch` / `clean`）
- `内容/` —— 分章正文，每个 `.typ` 都会编译出一份文档；`index.typ` 是入口
- `脚本/` —— 独立页入口 `页面.typ` 与网页后处理 `web_post.sh`
- `附件/` —— 元素系统数据 `元素系统.csv`
- `图片/` —— 图片素材，已配置 Git LFS（见 `.gitattributes`）
- `.webfonts/` —— 自托管网页字体目录（`.` 开头，默认隐藏），默认只有说明文件；字体由使用者自行放入（见 `.webfonts/README.md`）
- `SKILL.md` —— AI 写作与编译规范（技能说明）
- `.github/workflows/web.yml` —— 已启用的网页构建与发布工作流
- `LICENSE` —— 许可证，创建项目后请改成你的名字
- `README.md` —— 本文件，同时被 `内容/关于.typ` 渲染进正文

## Make

```sh
make pdf    # 内容/ 下全部 .typ → PDF（逐页套用模板）
make web    # 多页站点：各页共用一份 CSS，跨页元素连成链接
make watch  # 监听入口，自动重编
```
