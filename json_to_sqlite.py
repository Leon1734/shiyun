#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON → SQLite 一次性转换脚本（带繁简转换）
将 340 个 JSON 文件合并为单个 SQLite 数据库
"""

import json
import sqlite3
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"

# 繁简转换
try:
    from opencc import OpenCC
    cc = OpenCC('t2s')
    def to_simplified(text):
        return cc.convert(text)
    print("✓ OpenCC 繁简转换已启用")
except ImportError:
    def to_simplified(text):
        return text
    print("✗ OpenCC 未安装，跳过繁简转换")


def create_database():
    """创建 SQLite 数据库"""
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 性能优化
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    
    # 创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            dynasty TEXT DEFAULT '未知',
            content TEXT NOT NULL,
            source TEXT,
            rhythmic TEXT
        )
    ''')
    
    # 索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_author ON poems(author)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_dynasty ON poems(dynasty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON poems(title)')
    
    # FTS5 全文搜索索引
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS poems_fts USING fts5(
            title, author, content, 
            content=poems, content_rowid=id
        )
    ''')
    
    conn.commit()
    return conn


def load_json_files():
    """收集所有 JSON 文件"""
    json_files = []
    
    for dir_name, dynasty in [
        ("全唐诗", None), ("宋词", None), ("诗经", "先秦"),
        ("论语", "先秦"), ("楚辞", "先秦"), ("元曲", "元")
    ]:
        d = DATA_DIR / dir_name
        if d.exists():
            json_files.extend(d.glob("*.json"))
    
    return json_files


def get_dynasty(filename):
    """从文件名推断朝代"""
    name = str(filename).lower()
    if 'tang' in name:
        return '唐'
    elif 'song' in name:
        return '宋'
    elif 'yuan' in name:
        return '元'
    elif '诗经' in str(filename) or 'shijing' in name:
        return '先秦'
    elif '论语' in str(filename) or 'lunyu' in name:
        return '先秦'
    elif '楚辞' in str(filename) or 'chuci' in name:
        return '先秦'
    return '未知'


def import_data(conn, json_files):
    """导入数据（带繁简转换）"""
    cursor = conn.cursor()
    
    total = len(json_files)
    total_poems = 0
    batch = []
    batch_size = 5000
    
    start_time = time.time()
    
    for idx, json_file in enumerate(json_files):
        try:
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                continue
            
            dynasty = get_dynasty(json_file)
            source = json_file.stem
            
            for poem in data:
                if 'title' not in poem or 'author' not in poem:
                    continue
                
                title = to_simplified(poem['title'].strip())
                author = to_simplified(poem['author'].strip())
                
                if not title or not author:
                    continue
                
                # 提取内容
                if 'paragraphs' in poem:
                    content = '\n'.join(poem['paragraphs']) if isinstance(poem['paragraphs'], list) else str(poem['paragraphs'])
                elif 'content' in poem:
                    content = poem['content']
                else:
                    continue
                
                content = to_simplified(content.strip())
                if not content:
                    continue
                
                rhythmic = to_simplified(poem.get('rhythmic', ''))
                
                batch.append((title, author, dynasty, content, source, rhythmic))
                total_poems += 1
                
                if len(batch) >= batch_size:
                    cursor.executemany(
                        'INSERT INTO poems (title, author, dynasty, content, source, rhythmic) VALUES (?, ?, ?, ?, ?, ?)',
                        batch
                    )
                    conn.commit()
                    batch = []
            
            if (idx + 1) % 20 == 0 or idx + 1 == total:
                elapsed = time.time() - start_time
                print(f"\r进度: {idx+1}/{total} 文件 | {total_poems:,} 首诗 | {elapsed:.1f}秒", end='', flush=True)
        
        except Exception as e:
            if 'list' not in str(e):  # 忽略楚辞格式问题
                print(f"\n警告: {json_file.name}: {e}")
    
    if batch:
        cursor.executemany(
            'INSERT INTO poems (title, author, dynasty, content, source, rhythmic) VALUES (?, ?, ?, ?, ?, ?)',
            batch
        )
        conn.commit()
    
    print()
    return total_poems


def build_fts(conn):
    """构建 FTS 索引"""
    print("构建全文搜索索引...")
    conn.execute('INSERT INTO poems_fts(rowid, title, author, content) SELECT id, title, author, content FROM poems')
    conn.commit()
    print("完成")


def print_stats(conn):
    """打印统计"""
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM poems')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT dynasty, COUNT(*) FROM poems GROUP BY dynasty ORDER BY COUNT(*) DESC')
    dynasties = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(DISTINCT author) FROM poems')
    authors = cursor.fetchone()[0]
    
    db_size = DB_PATH.stat().st_size / (1024 * 1024)
    
    print()
    print("=" * 50)
    print(f"  诗词总数: {total:,} 首")
    print(f"  诗人数:   {authors:,} 位")
    print(f"  朝代分布:")
    for d, c in dynasties:
        print(f"    {d}: {c:,} 首")
    print(f"  数据库大小: {db_size:.1f} MB")
    print("=" * 50)


def main():
    print("=" * 50)
    print("JSON → SQLite 转换（带繁简转换）")
    print("=" * 50)
    print()
    
    json_files = load_json_files()
    print(f"找到 {len(json_files)} 个 JSON 文件")
    print()
    
    conn = create_database()
    
    print("导入数据...")
    import_data(conn, json_files)
    
    build_fts(conn)
    print_stats(conn)
    
    conn.close()
    
    print(f"\n数据库: {DB_PATH} ({DB_PATH.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == '__main__':
    main()
