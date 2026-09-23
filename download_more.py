#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 chinese-poetry 仓库缺失合集
- 纳兰性德 (清)
- 五代诗词 (花间集/南唐二主词)
- 曹操诗集 (三国)
- 蒙学 (三字经/千字文等)
- 四书五经
- 幽梦影
"""

import json
import time
import urllib.request
import urllib.parse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("download")

DATA_DIR = Path(__file__).parent / "data"
PROXY = "https://gh-proxy.com/https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master/"
API = "https://gh-proxy.com/https://api.github.com/repos/chinese-poetry/chinese-poetry/contents/"

# 要下载的合集
COLLECTIONS = ['纳兰性德', '五代诗词', '曹操诗集', '蒙学', '四书五经', '幽梦影']


def fetch_json(url, retries=3):
    """带重试的请求"""
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2)


def download_collection(collection):
    """下载单个合集的JSON文件"""
    log.info(f"=== {collection} ===")
    
    out_dir = DATA_DIR / collection
    out_dir.mkdir(exist_ok=True)
    
    # 列出目录内容
    url = API + urllib.parse.quote(collection)
    try:
        content = fetch_json(url)
        items = json.loads(content)
    except Exception as e:
        log.warning(f"  列出失败: {e}")
        return 0
    
    if not isinstance(items, list):
        log.warning(f"  非目录: {items}")
        return 0
    
    json_files = [it for it in items if it['type'] == 'file' and it['name'].endswith('.json')]
    log.info(f"  JSON文件: {len(json_files)} 个")
    
    downloaded = 0
    for it in json_files:
        name = it['name']
        out_path = out_dir / name
        
        if out_path.exists() and out_path.stat().st_size > 50:
            downloaded += 1
            continue
        
        # 用 raw 下载
        raw_url = PROXY + urllib.parse.quote(f"{collection}/{name}")
        try:
            data = fetch_json(raw_url)
            out_path.write_bytes(data)
            downloaded += 1
        except Exception as e:
            log.warning(f"  下载失败 {name}: {e}")
    
    log.info(f"  完成: {downloaded}/{len(json_files)}")
    return downloaded


def main():
    total = 0
    for coll in COLLECTIONS:
        try:
            n = download_collection(coll)
            total += n
        except Exception as e:
            log.error(f"{coll} 失败: {e}")
        time.sleep(1)
    
    log.info(f"\n总下载: {total} 个文件")
    
    # 验证
    for coll in COLLECTIONS:
        d = DATA_DIR / coll
        if d.exists():
            files = list(d.glob('*.json'))
            total_size = sum(f.stat().st_size for f in files) / 1024
            log.info(f"  {coll}: {len(files)} 文件, {total_size:.0f} KB")


if __name__ == "__main__":
    main()
