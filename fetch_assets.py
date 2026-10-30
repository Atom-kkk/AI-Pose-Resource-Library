#!/usr/bin/env python3
"""下载 AI 姿势参考库的全部缩略图与原图到本地镜像目录。"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://ai-pose-gallery.anhao.app/"
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "pose-zh.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def fetch(rel):
    dest = os.path.join(ROOT, rel)
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        return rel, "skip", os.path.getsize(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(BASE + rel, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read()
            if len(body) < 512:
                raise ValueError("too small: %d" % len(body))
            tmp = dest + ".part"
            with open(tmp, "wb") as fh:
                fh.write(body)
            os.replace(tmp, dest)
            return rel, "ok", len(body)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    return rel, "fail: %s" % last, 0


def main():
    with open(DATA, encoding="utf-8") as fh:
        rows = json.load(fh)
    jobs = sorted({r["缩略图"] for r in rows}) + sorted({r["原图"] for r in rows})
    print("total jobs:", len(jobs), flush=True)
    done = fails = 0
    bytes_total = 0
    started = time.time()
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(fetch, rel) for rel in jobs]
        for fut in as_completed(futures):
            rel, status, size = fut.result()
            done += 1
            bytes_total += size
            if status.startswith("fail"):
                fails += 1
                print("FAIL", rel, status, flush=True)
            if done % 100 == 0:
                el = time.time() - started
                print("%d/%d  %.1f MB  %.0fs" % (done, len(jobs), bytes_total / 1048576, el), flush=True)
    print("DONE done=%d fails=%d total=%.1f MB in %.0fs"
          % (done, fails, bytes_total / 1048576, time.time() - started), flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
