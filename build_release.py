#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 Release 发行包：诗韵-v7.0-win64.zip"""
import zipfile
import os
import time
from pathlib import Path

base = Path(__file__).parent
src = base / 'dist' / '诗韵'
out = base / 'release' / 'shiyun-v7.0-win64.zip'
out.parent.mkdir(exist_ok=True)

if out.exists():
    out.unlink()

t0 = time.time()
total = 0
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    # 1. 主程序
    zf.write(src / '诗韵.exe', '诗韵/诗韵.exe')
    print(f"  + 诗韵.exe")
    # 2. _internal 全部
    n = 0
    for root, dirs, files in os.walk(src / '_internal'):
        for f in files:
            fp = Path(root) / f
            arc = '诗韵/' + str(fp.relative_to(src)).replace('\\', '/')
            zf.write(fp, arc)
            n += 1
    print(f"  + _internal/ ({n} 个文件)")
    # 3. data 必要文件
    for df in ['poetry.db', 'rhyme.json', 'translations.db']:
        fpath = base / 'data' / df
        if fpath.exists():
            zf.write(fpath, f'诗韵/data/{df}')
            print(f"  + data/{df}")

size_mb = out.stat().st_size / 1024 / 1024
elapsed = time.time() - t0
print(f"\n完成: {out}")
print(f"大小: {size_mb:.0f} MB, 耗时: {elapsed:.0f} 秒")
