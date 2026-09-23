#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复元曲"截断式标题"：
  源数据格式: title = "曲牌·正文前半段(截断)", content = "正文后半段"
  修复为:     title = "曲牌·首句",            content = "完整正文"
用法: python fix_yuanqu_titles.py preview | apply
"""
import sqlite3
import re
import sys
from pathlib import Path

DB = Path(__file__).parent / "data" / "poetry.db"


def analyze(title, content):
    """分析截断式标题，返回 (曲牌, 拼接正文, 首句) 或 None"""
    if '·' not in title:
        return None
    part1, part2 = title.split('·', 1)
    part2 = part2.strip()
    # 判断 part2 是否是正文（含标点且较长）
    if len(part2) < 12:
        return None
    if not re.search(r'[，。、；：？！]', part2):
        return None
    # 拼接完整正文
    full = part2 + (content or '')
    # 曲牌名处理
    qupai = part1.strip()
    if qupai == '幺':
        qupai = '幺篇'
    elif re.fullmatch(r'[一二三四五六七八九十]+', qupai):
        # 煞曲编号残名：二 → 二煞
        qupai = qupai + '煞'
    # 首句：到第一个句读为止
    m = re.match(r'^([^，。、；：？！]{1,12})', full)
    first = m.group(1) if m else full[:9]
    return qupai, full, first


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    c.execute("SELECT id, title, author, content FROM poems WHERE collection='元曲'")
    rows = c.fetchall()

    fixes = []
    for pid, title, author, content in rows:
        r = analyze(title, content)
        if r:
            qupai, full, first = r
            fixes.append((pid, title, author, content, qupai, full, first))

    print(f"需要修复: {len(fixes)} / {len(rows)} 条")
    print()

    if action == 'preview':
        print("=== 抽样30条预览 ===")
        for pid, title, author, content, qupai, full, first in fixes[:30]:
            new_title = f"{qupai}·{first}"
            print(f"[{pid}] {author}")
            print(f"   旧标题: {title[:65]!r}")
            print(f"   新标题: 《{new_title}》")
            print(f"   旧内容: {(content or '')[:40]!r}")
            print(f"   新内容: {full[:70]!r}")
            print()

        # 检查曲牌分布
        from collections import Counter
        qupai_counter = Counter(f[4] for f in fixes)
        print("=== 曲牌 TOP15 ===")
        for q, n in qupai_counter.most_common(15):
            print(f"   {q}: {n}")

        # 检查是否有异常
        print()
        bad = [f for f in fixes if len(f[5]) < 15]
        print(f"修复后正文<15字的: {len(bad)}")
        for f in bad[:5]:
            print(f"   [{f[0]}] {f[1][:50]!r} → {f[5]!r}")

    elif action == 'apply':
        print("=== 正式修复 ===")
        for pid, title, author, content, qupai, full, first in fixes:
            new_title = f"{qupai}·{first}"
            c.execute("UPDATE poems SET title=?, content=? WHERE id=?", (new_title, full, pid))
        conn.commit()
        print(f"已修复 {len(fixes)} 条")

        # 验证
        c.execute("SELECT COUNT(*) FROM poems WHERE collection='元曲' AND (title LIKE '%，' OR title LIKE '%、')")
        print(f"剩余截断标题: {c.fetchone()[0]}")

        # 重建FTS
        conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
        conn.commit()
        print("FTS已重建")

    conn.close()


if __name__ == '__main__':
    main()
