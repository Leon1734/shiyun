#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充导入缺失的诗词集：宋词、诗经、楚辞
修复原导入脚本的 bug:
1. 宋词无 title 字段（用词牌名 rhythmic 代替）
2. 诗经无 author 字段（用"佚名"）
3. content 为 list 格式未处理
"""

import json
import sqlite3
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("import")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"

try:
    from opencc import OpenCC
    cc = OpenCC('t2s')
    def to_simplified(text):
        return cc.convert(str(text))
    log.info("OpenCC 繁简转换已启用")
except ImportError:
    def to_simplified(text):
        return str(text)
    log.warning("OpenCC 未安装，跳过繁简转换")


def import_ci(conn):
    """导入宋词"""
    cursor = conn.cursor()
    ci_files = sorted((DATA_DIR / "宋词").glob("ci.song.*.json"))
    
    total = 0
    batch = []
    
    for f in ci_files:
        with open(f, encoding='utf-8') as fp:
            data = json.load(fp)
        
        if not isinstance(data, list):
            continue
        
        source = f.stem
        
        for poem in data:
            author = to_simplified(poem.get('author', '佚名').strip()) or '佚名'
            rhythmic = to_simplified(poem.get('rhythmic', '').strip())
            paragraphs = poem.get('paragraphs', [])
            
            if not paragraphs:
                continue
            
            content = '\n'.join(paragraphs) if isinstance(paragraphs, list) else str(paragraphs)
            content = to_simplified(content.strip())
            
            if not content:
                continue
            
            # 用词牌名作为标题
            title = rhythmic if rhythmic else '无题'
            
            batch.append((title, author, '宋', content, source, rhythmic, '宋词'))
            total += 1
            
            if len(batch) >= 5000:
                cursor.executemany(
                    'INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    batch
                )
                conn.commit()
                batch = []
    
    if batch:
        cursor.executemany(
            'INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection) VALUES (?, ?, ?, ?, ?, ?, ?)',
            batch
        )
        conn.commit()
    
    log.info(f"宋词导入完成: {total} 首")
    return total


def import_shijing(conn):
    """导入诗经"""
    cursor = conn.cursor()
    
    with open(DATA_DIR / "诗经" / "shijing.json", encoding='utf-8') as f:
        data = json.load(f)
    
    batch = []
    for poem in data:
        title = to_simplified(poem.get('title', '').strip())
        chapter = to_simplified(poem.get('chapter', '').strip())
        section = to_simplified(poem.get('section', '').strip())
        content_list = poem.get('content', [])
        
        if not title or not content_list:
            continue
        
        if isinstance(content_list, list):
            content = '\n'.join(content_list)
        else:
            content = str(content_list)
        
        content = to_simplified(content.strip())
        if not content:
            continue
        
        full_title = f"{chapter}·{section}·{title}" if chapter and section else title
        
        batch.append((full_title, '佚名', '先秦', content, 'shijing', '', '诗经'))
    
    if batch:
        cursor.executemany(
            'INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection) VALUES (?, ?, ?, ?, ?, ?, ?)',
            batch
        )
        conn.commit()
    
    log.info(f"诗经导入完成: {len(batch)} 篇")
    return len(batch)


def import_chuci(conn):
    """导入楚辞"""
    cursor = conn.cursor()
    
    with open(DATA_DIR / "楚辞" / "chuci.json", encoding='utf-8') as f:
        data = json.load(f)
    
    batch = []
    for poem in data:
        title = to_simplified(poem.get('title', '').strip())
        section = to_simplified(poem.get('section', '').strip())
        author = to_simplified(poem.get('author', '佚名').strip()) or '佚名'
        content_list = poem.get('content', [])
        
        if not title or not content_list:
            continue
        
        if isinstance(content_list, list):
            content = '\n'.join(content_list)
        else:
            content = str(content_list)
        
        content = to_simplified(content.strip())
        if not content:
            continue
        
        batch.append((title, author, '先秦', content, 'chuci', '', '楚辞'))
    
    if batch:
        cursor.executemany(
            'INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection) VALUES (?, ?, ?, ?, ?, ?, ?)',
            batch
        )
        conn.commit()
    
    log.info(f"楚辞导入完成: {len(batch)} 篇")
    return len(batch)


def add_collection_column(conn):
    """添加 collection 列"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(poems)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'collection' not in columns:
        log.info("添加 collection 列...")
        cursor.execute("ALTER TABLE poems ADD COLUMN collection TEXT DEFAULT ''")
        conn.commit()
    
    # 回填已有数据的 collection
    cursor.execute("UPDATE poems SET collection = '全唐诗' WHERE source LIKE 'poet.tang%' AND (collection = '' OR collection IS NULL)")
    cursor.execute("UPDATE poems SET collection = '全宋诗' WHERE source LIKE 'poet.song%' AND (collection = '' OR collection IS NULL)")
    cursor.execute("UPDATE poems SET collection = '元曲' WHERE source = 'yuanqu' AND (collection = '' OR collection IS NULL)")
    cursor.execute("UPDATE poems SET collection = '唐诗三百首' WHERE source LIKE '%tangshi%' AND (collection = '' OR collection IS NULL)")
    conn.commit()
    log.info("collection 列回填完成")


def main():
    log.info("=== 补充导入缺失诗词集 ===")
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 记录导入前的最大ID
    cursor.execute("SELECT MAX(id) FROM poems")
    max_id_before = cursor.fetchone()[0] or 0
    log.info(f"导入前最大ID: {max_id_before}")
    
    add_collection_column(conn)
    
    start = time.time()
    
    ci_count = import_ci(conn)
    sj_count = import_shijing(conn)
    cc_count = import_chuci(conn)
    
    elapsed = time.time() - start
    log.info(f"\n共导入 {ci_count + sj_count + cc_count} 条, 耗时 {elapsed:.1f}秒")
    
    # 更新 FTS 索引（增量：只添加导入后的新记录）
    log.info("更新全文搜索索引...")
    cursor.execute('''
        INSERT INTO poems_fts(rowid, title, author, content)
        SELECT id, title, author, content FROM poems WHERE id > ?
    ''', (max_id_before,))
    conn.commit()
    log.info("FTS 索引更新完成")
    
    # 统计
    cursor.execute('SELECT COUNT(*) FROM poems')
    total = cursor.fetchone()[0]
    log.info(f"\n数据库当前总数: {total:,}")
    
    cursor.execute('SELECT collection, COUNT(*) FROM poems GROUP BY collection ORDER BY COUNT(*) DESC')
    log.info("合集分布:")
    for row in cursor.fetchall():
        log.info(f"  {row[0] or '(未分类)'}: {row[1]:,}")
    
    conn.close()


if __name__ == "__main__":
    main()
