#!/bin/sh
# 网页后处理:抽公共样式表、连跨页元素、注入开合脚本、内嵌图片改外链、写 SEO 与 JSON-LD。
#
# 用法:sh 脚本/web_post.sh [dist]
# make web 逐页导出 HTML 后调用。做五件模板包本身不做的多页站点级优化
# (见 web.css / lib.typ 的说明):
#   1. 样式表抽出一份 /assets/underhell.css,各页由内联 <style> 换成 <link>,多页共用;
#   2. 定义在别页的元素,由 title="未定义" 的 span 改成指向定义页的链接;
#   3. 注入目录/评论的开合脚本;
#   4. Typst 内联成 base64 的 image() 抽成 dist/图片/ 外链并补 loading="lazy"
#      (交给 脚本/抽取内嵌图片.sh;首页是全量入口,同一批图原本在 4 个页面各嵌一份)。
#   5. 逐页 SEO:canonical / Open Graph / robots 标记 / 标题品牌后缀 / sitemap.xml / robots.txt,
#      外加按页注入 JSON-LD @graph(首页 Book,其余页 Article + BreadcrumbList)。
# 元素定义取自 内容/ 下的 #设定元素(level: n)[名]、显式标题标签 `= 标题 <标签>`,
# 以及 附件/元素系统.csv 的「默认」列别名:显示名与锚点 id 不同时,链接片段用 id
# (标题锚点是 id,页面上显示的却是「默认」列名,如 古龙→龙)。
#
# / Web post-processing: extract one shared /assets/underhell.css, rewrite
# cross-page element spans into links, inject the toggle script, turn Typst's
# inlined base64 images into /图片/ files, and write per-page SEO tags plus JSON-LD.
# Element definitions come from 内容/ and the 附件/元素系统.csv default column.

set -e

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
root=$(CDPATH= cd "$script_dir/.." && pwd)
target=${1:-dist}
case "$target" in
  /*) dist=$target ;;
  *)  dist=$root/$target ;;
esac

tab=$(printf '\t')
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
map=$tmpdir/map.tsv          # 显示名 \t 页 URL \t 锚点
: > "$map"

# 站点根与品牌名:canonical、og:url、sitemap.xml 用前者,非首页标题后缀用后者。
# 都直接读 配置.typ,不在脚本里重复维护。
# / Site root and brand name, read from 配置.typ.
site=$(sed -n 's/^#let 站点网址 *= *"\([^"]*\)".*/\1/p' "$root/配置.typ" | head -1)
brand=$(sed -n 's/.*品牌名: *"\([^"]*\)".*/\1/p' "$root/配置.typ" | head -1)
: > "$tmpdir/sitemap.urls"   # 已索引页的绝对 URL(sitemap 用)

# URL 百分号编码:sitemap 与 canonical 要求非 ASCII 字符编码,而站点路径是中文。
# 有 python3 时编码,没有就原样输出(浏览器与爬虫多能容忍 IRI)。
# / Percent-encode non-ASCII paths for sitemap/canonical; fall back to raw IRI.
urlenc() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=":/"))' "$1"
  else
    printf '%s' "$1"
  fi
}

# 登记元素(首次出现为准;同名以先扫到的页为准)
register() {
  name=$1
  if [ -z "$name" ]; then
    return 0
  fi
  # 按首字段精确比对(不能用 grep -F:短名会是长名前缀,如 龙 之于 古龙)
  if awk -F"$tab" -v n="$name" '$1 == n { f = 1 } END { exit !f }' "$map" 2>/dev/null; then
    return 0
  fi
  printf '%s\t%s\t%s\n' "$name" "$2" "$3" >> "$map"
}

# 扫正文里的元素定义:$1 文件,$2 该文件对应的页 URL
scan_file() {
  file=$1
  url=$2
  # #设定元素(level: n)[名]
  grep -oE '#设定元素\( *level *: *[0-9]+ *\)\[[^]]+\]' "$file" 2>/dev/null |
    while IFS= read -r m; do
      name=$(printf '%s\n' "$m" | sed -E 's/.*\[([^]]+)\]$/\1/')
      register "$name" "$url" "$name"
    done
  # 显式标题标签:= 标题 <标签>
  grep -oE '^=+ .*<[^<> 	]+>[ 	]*$' "$file" 2>/dev/null |
    while IFS= read -r m; do
      name=$(printf '%s\n' "$m" | sed -E 's/.*<([^<> 	]+)>[ 	]*$/\1/')
      register "$name" "$url" "$name"
    done
}

# 元素定义 → 所在页 URL。全量入口 内容/index.typ 即站点首页 "/"
if [ -f "$root/内容/index.typ" ]; then
  scan_file "$root/内容/index.typ" "/"
fi

# 各独立页:内容/**.typ(不含 .typ 的路径即 URL 段;目录页 内容/<目录>/index.typ → /<目录>/)
find "$root/内容" -name '*.typ' 2>/dev/null | sort > "$tmpdir/typs"
while IFS= read -r file; do
  rel=${file#"$root/内容/"}
  case "$rel" in
    index.typ)   continue ;;
    */index.typ) page=${rel%/index.typ} ;;
    *)           page=${rel%.typ} ;;
  esac
  scan_file "$file" "/$page/"
done < "$tmpdir/typs"

# CSV:元素 id 与「默认」显示名不同的,把显示名一并登记(HTML 里显示的是默认名),
# 锚点仍用 id。
csv=$root/附件/元素系统.csv
if [ -f "$csv" ]; then
  awk -F, 'NR > 1 { gsub(/\r/, "", $1); gsub(/\r/, "", $2); if ($1 != "") print $1 "\t" $2 }' "$csv" |
    while IFS="$tab" read -r eid disp; do
      if [ -z "$eid" ]; then
        continue
      fi
      if [ -z "$disp" ]; then
        disp=$eid
      fi
      if [ "$disp" != "$eid" ]; then
        url=$(awk -F"$tab" -v n="$eid" '$1 == n { print $2; exit }' "$map" 2>/dev/null || true)
        if [ -n "$url" ]; then
          register "$disp" "$url" "$eid"
        fi
      fi
    done
fi

find "$dist" -name '*.html' 2>/dev/null | sort > "$tmpdir/htmls"
if [ ! -s "$tmpdir/htmls" ]; then
  echo "web_post: 未找到 HTML 产物"
  exit 0
fi

# ---------- 页面标题表(供 JSON-LD 面包屑取各级显示名)----------
# 面包屑要显示"地狱之下 › 地理 › 主行星"这样的层级名,而每一级路径本身就是一个页面,
# 所以先扫一遍产物,收一份 页URL → <title> 的表,后面按祖先路径回查。
# / Ancestor paths are themselves pages, so collect page → title for breadcrumb labels.
: > "$tmpdir/titles"
while IFS= read -r file; do
  prel=${file#"$dist/"}
  case "$prel" in
    */*) tpage="/${prel%/*}/" ;;
    *)   tpage="/" ;;
  esac
  ttext=$(grep -oE '<title>[^<]*</title>' "$file" 2>/dev/null | head -1 |
          sed -E 's|<title>(.*)</title>|\1|' | tr -d '\t\n')
  penc="$site$tpage"
  penc=$(urlenc "$penc")
  printf '%s\t%s\t%s\n' "$tpage" "$ttext" "$penc" >> "$tmpdir/titles"
done < "$tmpdir/htmls"

# ---------- 内嵌网页样式 → 外部 /assets/underhell.css ----------
found=0
while IFS= read -r file; do
  if grep -qF '<style>/*uh-raw*/' "$file" 2>/dev/null; then
    awk '
      BEGIN { on = 0 }
      {
        if (!on) {
          i = index($0, "<style>/*uh-raw*/")
          if (i == 0) next
          on = 1
          s = substr($0, i + length("<style>"))
        } else {
          s = $0
        }
        j = index(s, "</style>")
        if (j > 0) { if (j > 1) print substr(s, 1, j - 1); exit }
        print s
      }
    ' "$file" > "$tmpdir/underhell.css"
    found=1
    break
  fi
done < "$tmpdir/htmls"

if [ "$found" = 1 ] && [ -s "$tmpdir/underhell.css" ]; then
  mkdir -p "$dist/assets"
  cp "$tmpdir/underhell.css" "$dist/assets/underhell.css"
elif [ ! -f "$dist/assets/underhell.css" ]; then
  echo "web_post: 未找到内嵌网页样式,跳过 CSS 抽取"
fi

# 交互脚本:目录/评论触发点点击开合(幂等,靠标记 uhTocToggle 判定)
JS="<script>(function(){var uhTocToggle=1;document.addEventListener('click', function(e){var head = e.target.closest('.uh-toc-head');if (head) {var toc = head.closest('.uh-toc');toc.classList.toggle('uh-open');head.setAttribute('aria-expanded', toc.classList.contains('uh-open'));return;}var tr = e.target.closest('.uh-comment-trigger');if (tr) {var panel = tr.nextElementSibling;if (panel) panel.classList.toggle('uh-open');}});})();</script>"

# ---------- 逐页:内嵌样式 → 外链,跨页元素 span → 链接 ----------
total=0
while IFS= read -r file; do
  rel=${file#"$dist/"}
  case "$rel" in
    */*) page="/${rel%/*}/" ;;
    *)   page="/" ;;
  esac
  n=$(awk -v map="$map" -v page="$page" -v out="$tmpdir/out.html" '
    BEGIN {
      while ((getline l < map) > 0) {
        k = index(l, "\t")
        if (k == 0) continue
        name = substr(l, 1, k - 1)
        rest = substr(l, k + 1)
        k2 = index(rest, "\t")
        if (k2 > 0) { URL[name] = substr(rest, 1, k2 - 1); ANCH[name] = substr(rest, k2 + 1) }
        else        { URL[name] = rest;                    ANCH[name] = rest }
      }
      close(map)
      SPAN = "<span class=\"uh-element\" title=\"未定义\">"
      ENDS = "</span>"
      STYOPEN = "<style>/*uh-raw*/"
      STYCLOSE = "</style>"
      link = "<link rel=\"stylesheet\" href=\"/assets/underhell.css\">"
      instyle = 0
      cnt = 0
    }
    # 未定义 span 若定义在别页,改成指向该页(锚点用 id)的链接;本页定义或无定义的保持原样
    function rewrite(s,   o, i, pre, rest, e, m, gt, name, tgt, anc) {
      o = ""
      while ((i = index(s, SPAN)) > 0) {
        pre = substr(s, 1, i - 1)
        rest = substr(s, i)
        e = index(rest, ENDS)
        if (e == 0) { o = o s; s = ""; break }
        m = substr(rest, 1, e + length(ENDS) - 1)
        s = substr(rest, e + length(ENDS))
        gt = index(m, ">")
        name = substr(m, gt + 1, length(m) - gt - length(ENDS))
        tgt = URL[name]
        if (tgt != "" && tgt != page) {
          anc = (name in ANCH && ANCH[name] != "") ? ANCH[name] : name
          o = o pre "<a href=\"" tgt "#" anc "\"><span class=\"uh-element\">" name "</span></a>"
          cnt++
        } else {
          o = o pre m
        }
      }
      return o s
    }
    {
      line = $0
      o = ""
      if (instyle) {
        j = index(line, STYCLOSE)
        if (j == 0) next
        instyle = 0
        line = substr(line, j + length(STYCLOSE))
      }
      i = index(line, STYOPEN)
      if (i > 0) {
        pre = substr(line, 1, i - 1)
        rest = substr(line, i)
        j = index(rest, STYCLOSE)
        if (j > 0) o = pre link substr(rest, j + length(STYCLOSE))
        else { o = pre link; instyle = 1 }
      } else {
        o = line
      }
      r = rewrite(o)
      print r > out
    }
    END { print cnt }
  ' "$file")
  mv "$tmpdir/out.html" "$file"

  # ---------- SEO:canonical / Open Graph / robots ----------
  # 有 description 的页才索引并写入 sitemap;未登记的页(无描述)标 noindex。
  # 非首页的 <title> 补品牌后缀,便于在搜索结果里区分。
  title=$(grep -oE '<title>[^<]*</title>' "$file" | head -1 | sed -E 's|<title>(.*)</title>|\1|')
  desc=$(grep -oE '<meta name="description" content="[^"]*">' "$file" | head -1 | sed -E 's|.*content="(.*)">|\1|')
  if [ "$page" = "/" ]; then canon="$site/"; else canon="$site$page"; fi
  canon=$(urlenc "$canon")
  if [ -n "$desc" ]; then
    robots="index,follow"
    printf '%s\n' "$canon" >> "$tmpdir/sitemap.urls"
  else
    robots="noindex,nofollow"
  fi
  if [ "$page" = "/" ]; then ogtype="website"; else ogtype="article"; fi
  if [ "$page" = "/" ] || [ -z "$brand" ]; then newtitle=""; else newtitle="$title · $brand"; fi

  # ---------- JSON-LD:Book / Article + BreadcrumbList ----------
  # 只给已索引页(有 description)生成,noindex 页不喂结构化数据。
  # 首页出 Book,其余页出 Article(isPartOf 指向首页那本书)+ 按 URL 层级还原的面包屑,
  # 面包屑各级显示名回查 页→标题 表,拿不到就退回路径段(路径段本身就是中文标题)。
  # dateModified 取该页源 .typ 的最后提交日期,拿不到就整个字段不写。
  # 幂等:靠独立标记 uh-jsonld 判定(不能拿 application/ld+json 当标记——附录页会把
  # SKILL.md 正文渲染进页面,文里就含那个字符串,会把注入误跳过)。
  ld=""
  if [ -n "$desc" ] && ! grep -q 'uh-jsonld' "$file" 2>/dev/null; then
    author=$(grep -oE '<meta name="authors" content="[^"]*">' "$file" 2>/dev/null | head -1 |
             sed -E 's|.*content="(.*)">|\1|')
    pdir=${page%/}
    mod=""
    for s in "$root/内容$pdir.typ" "$root/内容${page}index.typ"; do
      if [ -f "$s" ] && command -v git >/dev/null 2>&1; then
        mod=$(git -C "$root" log -1 --format=%cI -- "$s" 2>/dev/null | cut -c1-10)
        [ -n "$mod" ] && break
      fi
    done
    ld=$(awk -v titles="$tmpdir/titles" -v page="$page" -v canon="$canon" -v title="$title" \
             -v desc="$desc" -v author="$author" -v brand="$brand" -v site="$site" -v mod="$mod" '
      function jesc(s) {
        gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s)
        gsub(/</, "\\u003c", s); gsub(/>/, "\\u003e", s)
        gsub(/\r/, " ", s);  gsub(/\n/, " ", s); gsub(/\t/, " ", s)
        return s
      }
      function person(n) {
        if (n == "") return ""
        return "{\"@type\":\"Person\",\"name\":\"" jesc(n) "\"}"
      }
      BEGIN {
        while ((getline l < titles) > 0) {
          nf = split(l, f, "\t")
          if (nf < 2) continue
          TN[f[1]] = f[2]
          TU[f[1]] = (nf >= 3 ? f[3] : "")
        }
        close(titles)
        home = site "/"
        P = person(author)
        bookname = (brand == "" ? title : brand)

        if (page == "/") {
          node = "{\"@type\":\"Book\",\"@id\":\"" jesc(canon) "#book\""
          node = node ",\"name\":\"" jesc(bookname) "\""
          if (P != "") { node = node ",\"author\":" P ",\"publisher\":" P }
          node = node ",\"inLanguage\":\"zh-CN\",\"url\":\"" jesc(canon) "\""
          node = node ",\"description\":\"" jesc(desc) "\""
          if (mod != "") node = node ",\"dateModified\":\"" mod "\""
          node = node "}"
          graph = node
        } else {
          node = "{\"@type\":\"Article\",\"@id\":\"" jesc(canon) "#article\""
          node = node ",\"headline\":\"" jesc(title) "\",\"url\":\"" jesc(canon) "\""
          node = node ",\"inLanguage\":\"zh-CN\""
          if (P != "") node = node ",\"author\":" P
          node = node ",\"isPartOf\":{\"@type\":\"Book\",\"name\":\"" jesc(bookname) "\",\"url\":\"" jesc(home) "\"}"
          node = node ",\"description\":\"" jesc(desc) "\""
          if (mod != "") node = node ",\"dateModified\":\"" mod "\""
          node = node "}"

          items = "{\"@type\":\"ListItem\",\"position\":1,\"name\":\"" jesc(bookname) "\",\"item\":\"" jesc(home) "\"}"
          pos = 1
          acc = ""
          m = split(page, seg, "/")
          for (i = 2; i < m; i++) {
            if (seg[i] == "") continue
            acc = acc "/" seg[i] "/"
            nm = ((acc in TN) && TN[acc] != "") ? TN[acc] : seg[i]
            uu = ((acc in TU) && TU[acc] != "") ? TU[acc] : site acc
            pos = pos + 1
            items = items ",{\"@type\":\"ListItem\",\"position\":" pos ",\"name\":\"" jesc(nm) "\",\"item\":\"" jesc(uu) "\"}"
          }
          graph = "{\"@type\":\"BreadcrumbList\",\"@id\":\"" jesc(canon) "#breadcrumb\""
          graph = graph ",\"itemListElement\":[" items "]}"
          graph = graph "," node
        }
        printf "%s", "<!--uh-jsonld--><script type=\"application/ld+json\">"
        printf "%s", "{\"@context\":\"https://schema.org\",\"@graph\":[" graph "]}"
        printf "%s", "</script>"
      }
    ' </dev/null)
  fi

  {
    printf '<meta name="robots" content="%s">' "$robots"
    printf '<link rel="canonical" href="%s">' "$canon"
    printf '<meta property="og:type" content="%s">' "$ogtype"
    printf '<meta property="og:site_name" content="%s">' "$brand"
    printf '<meta property="og:title" content="%s">' "$title"
    printf '<meta property="og:url" content="%s">' "$canon"
    printf '<meta property="og:locale" content="zh_CN">'
    if [ -n "$desc" ]; then printf '<meta property="og:description" content="%s">' "$desc"; fi
    printf '<meta name="twitter:card" content="summary">'
    printf '<meta name="twitter:title" content="%s">' "$title"
    if [ -n "$desc" ]; then printf '<meta name="twitter:description" content="%s">' "$desc"; fi
    if [ -n "$ld" ]; then printf '%s' "$ld"; fi
  } > "$tmpdir/extra.html"
  awk -v extrafile="$tmpdir/extra.html" -v newtitle="$newtitle" '
    BEGIN {
      extra = ""
      while ((getline l < extrafile) > 0) extra = extra l
      close(extrafile)
      done = 0
    }
    # 只替换首个 <title>…</title> 的内容
    function retitle(s, t,   i, e) {
      i = index(s, "<title>")
      if (i == 0) return s
      e = index(s, "</title>")
      if (e <= i) return s
      return substr(s, 1, i + 6) t substr(s, e)
    }
    {
      line = $0
      if (newtitle != "") line = retitle(line, newtitle)
      if (!done) {
        i = index(line, "</head>")
        if (i > 0) {
          print substr(line, 1, i - 1) extra substr(line, i)
          done = 1
          next
        }
      }
      print line
    }
  ' "$file" > "$tmpdir/seo.html"
  mv "$tmpdir/seo.html" "$file"

  if ! grep -qF 'uhTocToggle' "$file" 2>/dev/null; then
    printf '%s\n' "$JS" >> "$file"
  fi
  total=$((total + ${n:-0}))
done < "$tmpdir/htmls"

# ---------- 内嵌图片 → /图片/ 外链 + loading="lazy" ----------
# Typst 的 HTML 导出把 image() 整个 base64 塞进页面,首页(全量入口)与章页各嵌一份。
# 抽成 dist/图片/ 下的文件后图片才谈得上 CDN 缓存、跨页复用和懒加载。
# 失败不阻断构建:页面保持内联也能正常显示,只是没吃到这些好处。
if sh "$script_dir/抽取内嵌图片.sh" "$dist" "$root/图片"; then
  :
else
  echo "web_post: 图片外链步骤失败,页面保持内联"
fi

# ---------- sitemap.xml / robots.txt ----------
# 只收录已索引页(有 description 的页),首页固定排在最前。
if [ -s "$tmpdir/sitemap.urls" ]; then
  {
    printf '<?xml version="1.0" encoding="UTF-8"?>\n'
    printf '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    first="$site/"
    printf '  <url><loc>%s</loc></url>\n' "$first"
    while IFS= read -r u; do
      if [ "$u" != "$first" ]; then printf '  <url><loc>%s</loc></url>\n' "$u"; fi
    done < "$tmpdir/sitemap.urls"
    printf '</urlset>\n'
  } > "$dist/sitemap.xml"
fi

{
  printf 'User-agent: *\n'
  printf 'Allow: /\n'
  if [ -n "$site" ]; then printf '\nSitemap: %s/sitemap.xml\n' "$site"; fi
} > "$dist/robots.txt"

echo "web: $(wc -l < "$tmpdir/htmls" | tr -d ' ') 页;CSS 抽取;跨页元素链接 $total 个;图片外链;SEO 标签与 sitemap"
