#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载《古文观止》222篇数据
来源: github.com/niuniu-869/guwenguanzhi (via gh-proxy)
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "guwen_raw"
OUT_DIR.mkdir(exist_ok=True)

TREE_FILE = Path(__file__).parent / "guwen_tree.json"

# gh-proxy 前缀
PROXY = "https://gh-proxy.com/https://raw.githubusercontent.com/niuniu-869/guwenguanzhi/main/"


def download_file(args):
    """下载单个文件"""
    rel_path, out_path = args
    
    if out_path.exists() and out_path.stat().st_size > 100:
        return (rel_path, 'skip', 0)
    
    url = PROXY + urllib.parse.quote(rel_path)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
        
        out_path.write_bytes(content)
        return (rel_path, 'ok', len(content))
    except Exception as e:
        return (rel_path, 'fail', str(e))


def main():
    # 读取文件树
    with open(TREE_FILE, encoding='utf-8') as f:
        tree = json.load(f)
    
    # 筛选文章文件
    articles = [
        t['path'] for t in tree['tree']
        if t['type'] == 'blob' and t['path'].startswith('data/articles/') and t['path'].endswith('.json')
    ]
    
    print(f"待下载: {len(articles)} 篇")
    
    # 准备任务
    tasks = []
    for rel_path in articles:
        # 输出路径: data/guwen_raw/song/158_岳阳楼记.json
        parts = rel_path.split('/')
        era = parts[2]
        filename = parts[3]
        out_dir = OUT_DIR / era
        out_dir.mkdir(exist_ok=True)
        tasks.append((rel_path, out_dir / filename))
    
    # 并发下载
    ok, skip, fail = 0, 0, 0
    failed = []
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_file, t): t for t in tasks}
        
        for i, future in enumerate(as_completed(futures)):
            rel_path, status, info = future.result()
            if status == 'ok':
                ok += 1
            elif status == 'skip':
                skip += 1
            else:
                fail += 1
                failed.append((rel_path, info))
            
            if (i + 1) % 20 == 0:
                print(f"进度: {i+1}/{len(tasks)} (ok={ok}, skip={skip}, fail={fail})")
    
    print()
    print(f"完成: 下载{ok}, 跳过{skip}, 失败{fail}")
    
    if failed:
        print("失败列表:")
        for f, e in failed[:10]:
            print(f"  {f}: {e}")
    
    # 统计
    total_files = len(list(OUT_DIR.rglob('*.json')))
    print(f"本地文件总数: {total_files}")


if __name__ == "__main__":
    main()
