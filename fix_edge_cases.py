#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复边缘数据：45条元曲标题 + 1条空标题"""
import sqlite3
import re
from pathlib import Path

DB = Path(__file__).parent / "data" / "poetry.db"

conn = sqlite3.connect(str(DB))
c = conn.cursor()

print("=== 修复1: 空标题（韩愈琴曲歌辞→岐山操）===")
c.execute("UPDATE poems SET title='岐山操' WHERE id=255751 AND (title='' OR title IS NULL)")
print(f"  影响: {c.rowcount} 条")

print()
print("=== 修复2: 45条元曲标题 ===")
c.execute("SELECT id, title, content FROM poems WHERE title LIKE '·%' OR title LIKE '・%'")
rows = c.fetchall()
print(f"  找到 {len(rows)} 条")

fixed = 0
for pid, title, content in rows:
    t = title.lstrip('・· ').strip()
    
    # 尝试识别末尾题目注（最后一段，短且无句号）
    segs = re.split(r'[，。；？！]', t)
    last = segs[-1].strip() if segs else ''
    has_note = False
    note = ''
    main = t
    if last and len(last) <= 14 and last != segs[0]:
        # 检查last确实是结尾部分
        idx = t.rfind(last)
        if idx > 0:
            note = last
            main = t[:idx].rstrip('，。； ・')
            has_note = True
    
    if has_note and main:
        new_title = note
        new_content = main + '\n' + (content or '')
    else:
        # 无题目注：整条作为内容，标题用"无题"
        new_title = '无题'
        new_content = t + ('\n' + (content or '') if content else '')
    
    new_title = new_title.strip('・· ')
    if not new_title:
        new_title = '无题'
    
    c.execute("UPDATE poems SET title=?, content=? WHERE id=?", (new_title, new_content, pid))
    fixed += 1
    print(f"  [{pid}] {title[:40]!r}...")
    print(f"       → 《{new_title}》")

conn.commit()
print()
print(f"修复完成: {fixed} 条")

# 验证
c.execute("SELECT COUNT(*) FROM poems WHERE title LIKE '·%' OR title LIKE '・%'")
print(f"剩余·开头: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM poems WHERE title='' OR title IS NULL")
print(f"剩余空标题: {c.fetchone()[0]}")

conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
conn.commit()
print("FTS已重建")
conn.close()
