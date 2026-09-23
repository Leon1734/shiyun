#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传 Release asset（诗韵-v7.0-win64.zip）"""
import subprocess, ssl, urllib.request, urllib.error, json, time, sys
from pathlib import Path
from urllib.parse import quote

r = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                   capture_output=True, text=True, cwd=str(Path(__file__).parent))
token = [l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('password=')][0]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

release_id = Path(__file__).parent / '.release_id'
rid = release_id.read_text().strip()

asset = Path(__file__).parent / 'release' / 'shiyun-v7.0-win64.zip'
size_mb = asset.stat().st_size / 1024 / 1024
print(f"准备上传: {asset.name} ({size_mb:.0f}MB)")
sys.stdout.flush()

data = asset.read_bytes()
print(f"已读入内存，开始上传...")
sys.stdout.flush()

t0 = time.time()
name = 'shiyun-v7.0-win64.zip'  # ASCII 文件名（中文经反代会被过滤）
url = f'https://uploads.github.com/repos/Leon1734/shiyun/releases/{rid}/assets?name={name}'

req = urllib.request.Request(url, data=data, method='POST', headers={
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
    'Content-Type': 'application/zip',
    'User-Agent': 'shiyun-release',
    'Content-Length': str(len(data)),
})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=3600) as resp:
        d = json.load(resp)
        elapsed = time.time() - t0
        print(f"✓ 上传成功!")
        print(f"  URL: {d['browser_download_url']}")
        print(f"  大小: {d['size']/1024/1024:.0f}MB, 耗时: {elapsed:.0f}秒 ({size_mb/elapsed:.1f}MB/s)")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"✗ HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"✗ 异常: {type(e).__name__}: {e}")
