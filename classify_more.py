#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为新导入合集执行题材+诗体分类"""
import sqlite3
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("classify_new")

DB_PATH = Path(__file__).parent / "data" / "poetry.db"

from poem_classifier import classify_poem

NEW_COLLECTIONS = ['纳兰性德', '花间集', '南唐二主词', '曹操诗集', '蒙学', '中学古诗']


def detect_form(content, collection):
    """检测诗体"""
    if collection == '纳兰性德':
        return '词·小令' if len(content) <= 60 else ('词·中调' if len(content) <= 100 else '词·长调'), False
    if collection in ('花间集', '南唐二主词'):
        return '词·小令', False
    if collection == '曹操诗集':
        return '乐府', False
    if collection == '蒙学':
        return '蒙学', False
    
    # 中学古诗 - 用规则检测
    sentences = re.split(r'[，。！？、；：\n]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return '未知', False
    
    lens = [len(s) for s in sentences]
    avg = sum(lens) / len(lens)
    n = len(sentences)
    
    is5 = all(4 <= l <= 6 for l in lens)
    is7 = all(6 <= l <= 8 for l in lens)
    
    if is5:
        if n == 4: return '五言绝句', True
        if n == 8: return '五言律诗', True
        return '五言古诗', False
    if is7:
        if n == 4: return '七言绝句', True
        if n == 8: return '七言律诗', True
        return '七言古诗', False
    return '杂言', False


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 统计未分类
    placeholders = ','.join('?' * len(NEW_COLLECTIONS))
    cursor.execute(f'''
        SELECT COUNT(*) FROM poems 
        WHERE collection IN ({placeholders}) 
          AND (theme = '' OR theme IS NULL OR poem_form = '' OR poem_form IS NULL)
    ''', NEW_COLLECTIONS)
    todo = cursor.fetchone()[0]
    log.info(f"待分类: {todo} 条")
    
    cursor.execute(f'''
        SELECT id, title, author, content, collection FROM poems 
        WHERE collection IN ({placeholders}) 
          AND (theme = '' OR theme IS NULL OR poem_form = '' OR poem_form IS NULL)
    ''', NEW_COLLECTIONS)
    rows = cursor.fetchall()
    
    updated = 0
    for row in rows:
        poem_id = row['id']
        title = row['title'] or ''
        author = row['author'] or ''
        content = row['content'] or ''
        collection = row['collection']
        
        # 题材
        result = classify_poem(title, content, author)
        theme = result['primary'] if result else '其他'
        
        # 诗体
        form, is_regular = detect_form(content, collection)
        
        # 字数
        clean = re.sub(r'[，。！？、；：""''（）《》\s\n·]', '', content)
        word_count = len(clean)
        line_count = len([l for l in content.split('\n') if l.strip()])
        
        cursor.execute('''
            UPDATE poems SET theme = ?, poem_form = ?, word_count = ?, 
                             line_count = ?, chars_per_line = ?
            WHERE id = ?
        ''', (theme, form, word_count, line_count, 
              5 if '五言' in form else (7 if '七言' in form else 0), poem_id))
        updated += 1
        
        if updated % 200 == 0:
            conn.commit()
            log.info(f"已分类: {updated}/{todo}")
    
    conn.commit()
    log.info(f"完成: {updated} 条")
    
    # 统计
    cursor.execute(f'SELECT collection, COUNT(*) FROM poems WHERE collection IN ({placeholders}) GROUP BY collection', NEW_COLLECTIONS)
    log.info("\n合集统计:")
    for r in cursor.fetchall():
        log.info(f"  {r[0]}: {r[1]:,}")
    
    conn.close()


if __name__ == "__main__":
    main()
