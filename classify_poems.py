#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有诗词添加题材分类
"""

import sqlite3
import logging
from pathlib import Path
from poem_classifier import classify_poem

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("classify")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"

def add_theme_column():
    """添加题材列到数据库"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 检查是否已存在theme列
    cursor.execute("PRAGMA table_info(poems)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'theme' not in columns:
        log.info("添加theme列...")
        cursor.execute("ALTER TABLE poems ADD COLUMN theme TEXT DEFAULT ''")
        conn.commit()
    
    conn.close()

def classify_all_poems():
    """对所有诗词进行题材分类"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取总数
    cursor.execute("SELECT COUNT(*) FROM poems")
    total = cursor.fetchone()[0]
    log.info(f"诗词总数: {total}")
    
    # 获取未分类的诗词
    cursor.execute("SELECT id, title, author, content FROM poems WHERE theme = '' OR theme IS NULL")
    poems = cursor.fetchall()
    log.info(f"待分类: {len(poems)} 首")
    
    # 批量分类
    batch_size = 1000
    classified = 0
    
    for i in range(0, len(poems), batch_size):
        batch = poems[i:i+batch_size]
        
        for poem in batch:
            poem_id = poem['id']
            title = poem['title'] or ''
            author = poem['author'] or ''
            content = poem['content'] or ''
            
            # 分类
            result = classify_poem(title, content, author)
            theme = result['primary']
            
            # 更新数据库
            cursor.execute("UPDATE poems SET theme = ? WHERE id = ?", (theme, poem_id))
        
        conn.commit()
        classified += len(batch)
        log.info(f"已分类: {classified}/{len(poems)} ({classified*100//len(poems)}%)")
    
    conn.close()
    log.info("分类完成!")

def create_theme_index():
    """创建题材索引"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    log.info("创建题材索引...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme ON poems(theme)")
    conn.commit()
    
    # 统计各题材数量
    cursor.execute("SELECT theme, COUNT(*) as cnt FROM poems WHERE theme != '' GROUP BY theme ORDER BY cnt DESC")
    stats = cursor.fetchall()
    
    log.info("\n=== 题材分布 ===")
    for row in stats:
        log.info(f"  {row[0]}: {row[1]} 首")
    
    conn.close()

if __name__ == "__main__":
    log.info("=== 古诗词题材分类 ===")
    
    # 1. 添加theme列
    add_theme_column()
    
    # 2. 分类所有诗词
    classify_all_poems()
    
    # 3. 创建索引并统计
    create_theme_index()
    
    log.info("全部完成!")
