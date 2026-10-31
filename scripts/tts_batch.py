#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Breeze TTS 批量合成脚本
用法:
  set BREEZE_API_KEY=brz_xxx
  python tts_batch.py --input chapter.txt --out ./audio --max-chars 900
"""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid

API_BASE = os.environ.get("BREEZE_API_BASE", "https://api.breeze.blue/v1")
MODEL_ID = os.environ.get("BREEZE_TTS_MODEL", "breeze-tts-2")
VOICE_ID = os.environ.get("BREEZE_TTS_VOICE", "")  # voc_xxxx
OUT_FORMAT = os.environ.get("BREEZE_TTS_FORMAT", "mp3")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# 常见错字 / 不宜朗读符号，按需扩充
FIXES = {
    "白暂": "白皙",
    "仍由": "任由",
    "及其冒险": "极其冒险",
    "狐狸烫": "狐狸汤",
}


def clean(text: str) -> str:
    text = text.replace("\ufeff", "")
    for a, b in FIXES.items():
        text = text.replace(a, b)
    # 去掉书名号引号，改用逗号断句
    text = text.replace("「", "").replace("」", "，")
    text = text.replace("“", "").replace("”", "，")
    text = re.sub(r"[*#>`~\[\]]", "", text)
    text = re.sub(r"…{2,}", "……", text)
    text = re.sub(r"。{2,}", "。", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_segments(text: str, max_chars: int):
    """按段落聚合到 max_chars 以内，尽量在句号 / 场景处断开。"""
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    segs, buf = [], ""
    for p in paras:
        if len(buf) + len(p) <= max_chars:
            buf += p
            continue
        if buf:
            segs.append(buf)
        # 单段本身超长，按句号再切
        while len(p) > max_chars:
            cut = p.rfind("。", 0, max_chars)
            cut = cut + 1 if cut > max_chars * 0.5 else max_chars
            segs.append(p[:cut])
            p = p[cut:]
        buf = p
    if buf:
        segs.append(buf)
    return segs


def probe(api_key: str) -> bool:
    """3 字探活，返回 >5KB 视为可用。"""
    try:
        data = _synth(api_key, "测试一下", timeout=45)
        return len(data) > 5000
    except Exception as e:  # noqa: BLE001
        print(f"[probe] 不可用: {e}")
        return False


def _synth(api_key: str, text: str, timeout: int = 120) -> bytes:
    url = f"{API_BASE}/text-to-speech/{VOICE_ID}?output_format={OUT_FORMAT}"
    body = json.dumps({"text": text, "model_id": MODEL_ID}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def synth_with_retry(api_key: str, text: str, tries: int = 3) -> bytes:
    timeout = max(60, int(len(text) / 40))  # 约 40 字/秒
    last = None
    for i in range(tries):
        try:
            return _synth(api_key, text, timeout)
        except urllib.error.HTTPError as e:
            last = e
            detail = ""
            try:
                detail = e.read().decode("utf-8", "ignore")[:200]
            except Exception:  # noqa: BLE001
                pass
            print(f"[synth] HTTP {e.code} {detail}")
            if e.code == 503:  # 产能满，等久一点
                time.sleep(15 * (i + 1))
            else:
                time.sleep(3)
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"[synth] 失败: {e}")
            time.sleep(3)
    raise RuntimeError(f"合成失败: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="./audio")
    ap.add_argument("--max-chars", type=int, default=900)
    ap.add_argument("--gap", type=float, default=2.0, help="段间间隔秒，防止限流")
    args = ap.parse_args()

    api_key = os.environ.get("BREEZE_API_KEY", "")
    if not api_key:
        raise SystemExit("缺少环境变量 BREEZE_API_KEY")
    if not VOICE_ID:
        raise SystemExit("缺少环境变量 BREEZE_TTS_VOICE（形如 voc_xxxx）")

    os.makedirs(args.out, exist_ok=True)
    raw = open(args.input, encoding="utf-8-sig").read()
    segs = split_segments(clean(raw), args.max_chars)
    print(f"切分为 {len(segs)} 段")

    if not probe(api_key):
        print("探活未通过，仍继续尝试；若连续 503 请稍后再跑")

    manifest = []
    for i, seg in enumerate(segs, 1):
        name = f"seg{i:02d}_{uuid.uuid4().hex[:4]}.{OUT_FORMAT}"
        path = os.path.join(args.out, name)
        audio = synth_with_retry(api_key, seg)
        with open(path, "wb") as f:
            f.write(audio)
        item = {
            "index": i,
            "file": name,
            "chars": len(seg),
            "bytes": len(audio),
            "head": seg[:40],
            "tail": seg[-40:],
        }
        manifest.append(item)
        print(f"[{i}/{len(segs)}] {name} {len(seg)}字 {len(audio)}B")
        if i < len(segs):
            time.sleep(args.gap)

    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("完成，清单见 manifest.json")


if __name__ == "__main__":
    main()
