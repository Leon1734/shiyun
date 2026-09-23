#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为新增数据（宋词、诗经、楚辞）分类
- 宋词：词（小令/中调/长调）
- 诗经：四言古诗
- 楚辞：楚辞体
"""

import sqlite3
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("classify_new")

DB_PATH = Path(__file__).parent / "data" / "poetry.db"

try:
    from poem_classifier import classify_poem
    log.info("题材分类模块已加载")
except ImportError:
    log.warning("poem_classifier 未找到")
    def classify_poem(title, content, author=""):
        return {'primary': '其他', 'secondary': '', 'imagery': [], 'confidence': 0}


def classify_ci(word_count):
    """词按字数分类：小令、中调、长调"""
    if word_count <= 58:
        return '词·小令'
    elif word_count <= 90:
        return '词·中调'
    else:
        return '词·长调'


def classify_new_poems():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取未分类的新数据
    cursor.execute("""
        SELECT id, title, author, content, collection, source 
        FROM poems 
        WHERE (poem_form = '' OR poem_form IS NULL) 
          AND collection IN ('宋词', '诗经', '楚辞')
    """)
    poems = cursor.fetchall()
    log.info(f"待分类: {len(poems)} 条")
    
    stats = {}
    
    for i, poem in enumerate(poems):
        poem_id = poem['id']
        title = poem['title'] or ''
        author = poem['author'] or ''
        content = poem['content'] or ''
        collection = poem['collection']
        
        # 计算总字数
        clean_content = re.sub(r'[，。！？、；：""''（）《》\s\n·]', '', content)
        word_count = len(clean_content)
        
        # 按合集分类
        if collection == '宋词':
            form = classify_ci(word_count)
            chars_per_line = 0
            line_count = len([l for l in content.split('\n') if l.strip()])
            is_regular = False
        elif collection == '诗经':
            form = '诗经·四言'
            chars_per_line = 4
            line_count = len([l for l in content.split('\n') if l.strip()])
            is_regular = False
        elif collection == '楚辞':
            form = '楚辞体'
            chars_per_line = 0
            line_count = len([l for l in content.split('\n') if l.strip()])
            is_regular = False
        else:
            continue
        
        # 题材分类
        result = classify_poem(title, content, author)
        theme = result['primary'] if result else '其他'
        
        # 更新
        cursor.execute("""
            UPDATE poems SET 
                poem_form = ?, 
                chars_per_line = ?, 
                line_count = ?, 
                is_regular = ?,
                word_count = ?,
                theme = ?
            WHERE id = ?
        """, (form, chars_per_line, line_count, 1 if is_regular else 0, word_count, theme, poem_id))
        
        stats[form] = stats.get(form, 0) + 1
        
        if (i + 1) % 5000 == 0:
            conn.commit()
            log.info(f"已分类: {i+1}/{len(poems)}")
    
    conn.commit()
    
    # 打印统计
    log.info("\n=== 新数据分类结果 ===")
    for form, count in sorted(stats.items(), key=lambda x: -x[1]):
        log.info(f"  {form}: {count} 条")
    
    # 全库最终统计
    cursor.execute('SELECT COUNT(*) FROM poems')
    log.info(f"\n数据库总数: {cursor.fetchone()[0]:,}")
    
    conn.close()


if __name__ == "__main__":
    log.info("=== 新数据分类 ===")
    classify_new_poems()
