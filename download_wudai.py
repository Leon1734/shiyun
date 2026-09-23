#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载五代诗词（花间集、南唐二主词）"""
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PROXY = "https://gh-proxy.com/https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master/"
API = "https://gh-proxy.com/https://api.github.com/repos/chinese-poetry/chinese-poetry/contents/"


def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2)


def download_dir(rel_path):
    """递归下载目录"""
    url = API + urllib.parse.quote(rel_path)
    items = json.loads(fetch(url))
    
    total = 0
    for it in items:
        if it['type'] == 'dir':
            total += download_dir(f"{rel_path}/{it['name']}")
        elif it['name'].endswith('.json'):
            out_dir = DATA_DIR / rel_path
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / it['name']
            
            if out_path.exists() and out_path.stat().st_size > 50:
                total += 1
                continue
            
            raw_url = PROXY + urllib.parse.quote(f"{rel_path}/{it['name']}")
            try:
                out_path.write_bytes(fetch(raw_url))
                total += 1
                print(f"  ✓ {rel_path}/{it['name']}")
            except Exception as e:
                print(f"  ✗ {rel_path}/{it['name']}: {e}")
    return total


if __name__ == "__main__":
    print("下载五代诗词...")
    n = download_dir("五代诗词")
    print(f"完成: {n} 个文件")
    
    for sub in ['huajianji', 'nantang']:
        d = DATA_DIR / "五代诗词" / sub
        if d.exists():
            files = list(d.glob('*.json'))
            print(f"  {sub}: {len(files)} 文件")
