#!/bin/sh
# 把 Typst HTML 导出内联的 data URI 图片换成 dist/图片/ 下的外链文件,并给外链图补懒加载。
# 只依赖 sh + awk + base64 + tr,不用 Python。
#
# 为什么要抽:typst --format html 把 image() 的字节 base64 内联进每一页,而 内容/index.typ
# 是整本全量入口,同一批图在首页和各章独立页里各嵌一遍(实测 9 张图在 4 个页面重复内嵌共
# 4.1MB,base64 又比原图大三分之一)。抽成 /图片/xxx.svg 之后:走 CDN 缓存、跨页复用、
# 能加 loading="lazy"。
#
# 用法:sh 脚本/抽取内嵌图片.sh [dist] [图片源目录]   由 脚本/web_post.sh 收尾时调用。
#
# 两条出路,按 base64 文本查表(源图先编码一次建索引,免掉逐图解码比对):
#   1. 内联串与 图片/ 下某文件编码后逐字相同(matplotlib 出的 SVG 就是这种)→ URL 用源文件名,
#      文件直接从源目录复制,不解码;
#   2. 对不上号(Typst 会重新编码位图,内嵌那份与源图尺寸、字节都不同的 JPEG)→ 解码落盘,
#      名字取自内容本身(长度 + 前缀净化串),避免"同名但不同图"被源文件或浏览器缓存顶掉。
# 可重复执行:页面里没有 data URI 就原样不动,dist/图片/ 只删页面不再引用的残留。
#
# / Replaces Typst's inlined data-URI images with files under dist/图片/ and makes them lazy.
# Needs only sh, awk, base64, tr. Payloads byte-identical to a file in 图片/ keep that file's
# name and are copied, never re-encoded; the rest are decoded to disk under a content-derived
# name, so a same-named source file can never shadow a different image.

set -e

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
root=$(CDPATH= cd "$script_dir/.." && pwd)
target=${1:-dist}
case "$target" in
  /*) dist=$target ;;
  *)  dist=$root/$target ;;
esac
src=${2:-$root/图片}
out="$dist/图片"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# 找一个能用的 base64 解码器:-d 是 GNU 与新 libmd,-D 是老 BSD,最后退到 openssl
if printf 'aGk=' | base64 -d >/dev/null 2>&1; then
  dec="base64 -d"
elif printf 'aGk=' | base64 -D >/dev/null 2>&1; then
  dec="base64 -D"
elif command -v openssl >/dev/null 2>&1 && printf 'aGk=' | openssl base64 -d >/dev/null 2>&1; then
  dec="openssl base64 -d"
else
  dec=""
  echo "抽取内嵌图片:没有 base64 解码器,只对得上源文件的图做外链"
fi

# 索引:源目录里每张图的 base64(压成单行)→ 文件名
: > "$tmpdir/map.tsv"
if [ -d "$src" ]; then
  find "$src" -maxdepth 1 -type f \
    \( -iname '*.svg' -o -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \
       -o -iname '*.gif' -o -iname '*.webp' -o -iname '*.avif' -o -iname '*.tif' -o -iname '*.tiff' \) \
    2>/dev/null | sort | while IFS= read -r f; do
      b=$(base64 < "$f" | tr -d '\n\r')
      [ -n "$b" ] && printf '%s\t%s\n' "$b" "${f##*/}" >> "$tmpdir/map.tsv"
    done
fi

find "$dist" -name '*.html' 2>/dev/null | sort > "$tmpdir/htmls"
if [ ! -s "$tmpdir/htmls" ]; then
  echo "抽取内嵌图片:未找到 HTML 产物"
  exit 0
fi

: > "$tmpdir/copy.txt"   # 需要复制的源文件名(与内联串逐字相同的那些)

# ---------- 逐页:data URI → /图片/ 外链,外链图补 loading="lazy" ----------
while IFS= read -r file; do
  before=$(wc -c < "$file" | tr -d ' ')
  awk -v map="$tmpdir/map.tsv" -v outdir="$out" -v dec="$dec" \
      -v copylist="$tmpdir/copy.txt" -v new="$file.new" '
    BEGIN {
      sq = sprintf("%c", 39)                     # 单引号:拼 shell 命令时用,别写死转义
      while ((getline l < map) > 0) {
        k = index(l, "\t")
        if (k == 0) continue
        NAME[substr(l, 1, k - 1)] = substr(l, k + 1)   # base64 全文 → 源文件名
      }
      close(map)
      n = 0
    }
    # mime → 扩展名;未知 mime 用净化后的 mime 兜底
    function ext_of(m,   e) {
      e = tolower(m)
      if (e == "svg+xml") return "svg"
      if (e == "jpeg" || e == "jpg" || e == "pjpeg") return "jpg"
      if (e == "png") return "png"
      if (e == "webp") return "webp"
      if (e == "gif") return "gif"
      if (e == "avif") return "avif"
      if (e == "tiff") return "tif"
      if (e == "bmp") return "bmp"
      gsub(/[^a-z0-9]/, "", e)
      return (e == "" ? "bin" : e)
    }
    # 内容指纹:取 base64 结尾 40 位里的字母数字再截 12 位(/ 和 + 不进文件名)。
    # 取尾巴而不是开头:开头的 /9j/4AAQSkZJRg 是每个 JPEG 共有的头,区分不出不同图。
    function stamp(p,   s) {
      s = length(p) > 40 ? substr(p, length(p) - 39) : p
      gsub(/[^A-Za-z0-9]/, "", s)
      return substr(s, 1, 12)
    }
    function ensure_dir() {
      if (donedir) return
      donedir = 1
      system("mkdir -p " sq outdir sq)
    }
    # 对不上源文件的内联图:解码写到 dist/图片/,返回文件名;没有解码器就返回空串(页面保持原样)
    # 名字只由内容决定,所以同一张图在首页和章页上算出来是同一个 URL,跨页共用一份缓存
    function dump_inline(p, mime,   e, name, cmd, clash) {
      if (dec == "") return ""
      if (p in SEEN) return SEEN[p]
      e = ext_of(mime)
      name = "内嵌-" length(p) "-" stamp(p) "." e
      clash = 0
      while ((name in OWNER) && OWNER[name] != p) {
        clash++
        name = "内嵌-" length(p) "-" stamp(p) "-" clash "." e
      }
      OWNER[name] = p
      ensure_dir()
      cmd = dec " > " sq outdir "/" name sq
      printf "%s", p | cmd
      close(cmd)
      SEEN[p] = name
      return name
    }
    # 给 <img> 补 loading="lazy" decoding="async"(已有 loading= 的不动)
    function add_lazy(tag) {
      if (tag ~ /loading=/) return tag
      sub(/^<img[ \t]/, "<img loading=\"lazy\" decoding=\"async\" ", tag)
      return tag
    }
    # 把 tag 里的 src="data:image/<mime>;base64,P" 换成 src="/图片/<名>"
    # 一个 <img> 只有一个 src,所以命中第一个就返回
    function externalize(tag,   i, head, j, mime, st, q, p, name) {
      i = index(tag, "src=\"data:image/")
      if (i == 0) return tag
      head = substr(tag, i)
      j = index(head, ";base64,")
      if (j <= 17) return tag                          # 无 ;base64, 或写法非标准,原样留着
      mime = substr(head, 17, j - 17)                  # src="data:image/ 共 16 字符,mime 从第 17 位起
      st = i + j + 7                                   # payload 起点 = i + (j - 1) + 8
      q = index(substr(tag, st), "\"")
      if (q == 0) return tag                           # 属性引号没闭合,别动
      p = substr(tag, st, q - 1)
      name = NAME[p]
      if (name == "") {
        name = dump_inline(p, mime)
        if (name == "") return tag                     # 解不了 → 保留内联,页面照常显示
      } else {
        print name >> copylist                         # 与源文件逐字相同 → 交给 sh 复制(>> 才不会被上一行截断)
        close(copylist)
      }
      n++
      return substr(tag, 1, i - 1) "src=\"/图片/" name "\"" substr(tag, st + q)
    }
    {
      line = $0
      o = ""
      while ((i = index(line, "<img")) > 0) {
        rest = substr(line, i)
        e = index(rest, ">")
        if (e == 0) break                              # 本行没有闭合的 >,余下原样输出
        tag = substr(rest, 1, e)
        old = tag
        tag = externalize(tag)
        if (tag != old) tag = add_lazy(tag)             # 只给真外链出去的图补属性
        o = o substr(line, 1, i - 1) tag
        line = substr(rest, e + 1)
      }
      print o line > new
    }
    END {
      printf "%d\n", n > (new ".stat")
      close(new ".stat")
    }
  ' "$file"
  if [ -f "$file.new" ]; then
    mv "$file.new" "$file"
    after=$(wc -c < "$file" | tr -d ' ')
    ct=$(cat "$file.new.stat" 2>/dev/null || echo 0)
    rm -f "$file.new.stat"
    if [ "$ct" != 0 ]; then
      echo "  ${file#"$dist/"}:外链 $ct 张,$before B → $after B"
    fi
  fi
done < "$tmpdir/htmls"

# 复制与内联串逐字相同的源图(直接 cp,不重编码,保证字节一致)
sort -u "$tmpdir/copy.txt" 2>/dev/null | while IFS= read -r name; do
  [ -n "$name" ] || continue
  mkdir -p "$out"
  if [ -f "$src/$name" ]; then
    cp -f "$src/$name" "$out/$name"
  else
    echo "抽取内嵌图片:源文件缺失 $name"
  fi
done

# 页面实际引用的文件名(用于清理残留和自检)
grep -rho 'src="/图片/[^"]*"' "$dist" --include='*.html' 2>/dev/null |
  sed 's|^src="/图片/||; s|"$||' | sort -u > "$tmpdir/refs" || true

# 清理 dist/图片/ 下页面不再引用的残留(上次构建的产物)
if [ -d "$out" ] && [ -s "$tmpdir/refs" ]; then
  find "$out" -maxdepth 1 -type f 2>/dev/null | sort | while IFS= read -r f; do
    grep -qxF "${f##*/}" "$tmpdir/refs" 2>/dev/null || rm -f "$f"
  done
fi

# 自检:引用的文件是否都在,还有没有漏掉的内联图
missing=0
if [ -s "$tmpdir/refs" ]; then
  while IFS= read -r name; do
    if [ ! -s "$out/$name" ]; then
      echo "抽取内嵌图片:缺文件 /图片/$name"
      missing=$((missing + 1))
    fi
  done < "$tmpdir/refs"
fi
refs=$(wc -l < "$tmpdir/refs" | tr -d ' ')
size=$(du -sk "$out" 2>/dev/null | cut -f1)
left=$(grep -rho 'data:image/[a-z+]*;base64' "$dist" --include='*.html' 2>/dev/null | wc -l | tr -d ' ')
echo "抽取内嵌图片:外链 $refs 个引用(dist/图片/ 共 ${size:-0}KB,缺 $missing),页面仍内联 $left 处"
