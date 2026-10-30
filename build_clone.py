#!/usr/bin/env python3
"""把原站 HTML 复刻为可离线双击打开的本地页面。

改动只有两处（其余字节保持与原站一致）：
1. 把 data/pose-zh.json 内联为 window.__POSE_DATA__，并在 fetch 前优先取用，
   使 file:// 协议下也能正常渲染（原站 fetch 在本地会被 CORS 拦截）。
2. 移除原站的第三方统计脚本（u.authbox.cn），避免本地副本向原站回传埋点。
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(ROOT), "site_raw.html")
OUT = os.path.join(ROOT, "index.html")

with open(SRC, encoding="utf-8") as fh:
    html = fh.read()
with open(os.path.join(ROOT, "data", "pose-zh.json"), encoding="utf-8") as fh:
    rows = json.load(fh)

payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

OLD_FETCH = """fetch('data/pose-zh.json')
  .then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
  .then(prepareData)"""
NEW_FETCH = """const dataSource = window.__POSE_DATA__
  ? Promise.resolve(window.__POSE_DATA__)
  : fetch('data/pose-zh.json').then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); });
dataSource
  .then(prepareData)"""
assert OLD_FETCH in html, "fetch block not found"
html = html.replace(OLD_FETCH, NEW_FETCH, 1)

OLD_TAG = "\n<script defer src=\"https://u.authbox.cn/script.js\" data-website-id=\"cde8a23b-4bf6-4ded-8cd9-2c9551dc8d38\"></script>"
assert OLD_TAG in html, "analytics tag not found"
html = html.replace(OLD_TAG, "", 1)

# 数据提前注入，紧跟 <body> 之后（脚本执行前）
ANCHOR = "<body>\n"
assert ANCHOR in html
html = html.replace(ANCHOR, ANCHOR + "<script>window.__POSE_DATA__=" + payload + ";</script>\n", 1)

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(html)

print("written:", OUT)
print("size: %.1f KB" % (os.path.getsize(OUT) / 1024))
print("rows:", len(rows))
