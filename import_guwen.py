#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入《古文观止》222篇到数据库
创建独立表 guwen（含有别于诗词的富文本结构）
"""

import json
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("guwen")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"
GUWEN_DIR = DATA_DIR / "guwen_raw"

# 朝代映射
DYNASTY_MAP = {
    'pre_qin': '先秦',
    'han': '汉',
    'wei_jin': '魏晋',
    'tang': '唐',
    'song': '宋',
    'ming': '明',
}

# 繁简转换
try:
    from opencc import OpenCC
    cc = OpenCC('t2s')
    def to_simplified(text):
        return cc.convert(str(text))
except ImportError:
    def to_simplified(text):
        return str(text)


def create_table(conn):
    """创建古文表"""
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guwen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            dynasty TEXT,
            era TEXT,
            content TEXT,
            translation TEXT,
            background TEXT,
            appreciation TEXT,
            tags TEXT,
            author_bio TEXT,
            paragraphs_json TEXT,
            char_count INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_guwen_author ON guwen(author)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_guwen_dynasty ON guwen(dynasty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_guwen_title ON guwen(title)')
    
    # FTS5
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS guwen_fts USING fts5(
            title, author, content, translation,
            content=guwen, content_rowid=id
        )
    ''')
    
    conn.commit()


def import_articles(conn):
    """导入所有文章"""
    cursor = conn.cursor()
    
    # 清空旧数据
    cursor.execute('DELETE FROM guwen')
    cursor.execute("INSERT INTO guwen_fts(guwen_fts) VALUES('delete-all')")
    
    files = sorted(GUWEN_DIR.rglob('*.json'))
    log.info(f"找到 {len(files)} 篇文章")
    
    imported = 0
    for f in files:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
            
            title = to_simplified(data.get('title', '').strip())
            if not title:
                continue
            
            # 作者信息
            author_data = data.get('author', {})
            if isinstance(author_data, dict):
                author = to_simplified(author_data.get('name', '佚名'))
                author_bio = to_simplified(author_data.get('bio', ''))
            else:
                author = to_simplified(str(author_data)) or '佚名'
                author_bio = ''
            
            # 朝代
            era = data.get('dynasty', '')
            dynasty = DYNASTY_MAP.get(era, era)
            
            # 正文 + 译文
            paragraphs = data.get('paragraphs', [])
            original_parts = []
            translation_parts = []
            
            for p in paragraphs:
                if isinstance(p, dict):
                    org = p.get('original', '')
                    trans = p.get('translation', '')
                    if org:
                        original_parts.append(to_simplified(org))
                    if trans:
                        translation_parts.append(to_simplified(trans))
                elif isinstance(p, str):
                    original_parts.append(to_simplified(p))
            
            content = '\n'.join(original_parts)
            translation = '\n'.join(translation_parts)
            
            if not content:
                continue
            
            # 其他元数据
            background = to_simplified(data.get('background', ''))
            appreciation = to_simplified(data.get('appreciation', ''))
            tags = json.dumps(data.get('tags', []), ensure_ascii=False)
            paragraphs_json = json.dumps(paragraphs, ensure_ascii=False) if paragraphs else ''
            char_count = len(content.replace('\n', ''))
            
            cursor.execute('''
                INSERT INTO guwen (title, author, dynasty, era, content, translation, 
                                   background, appreciation, tags, author_bio, paragraphs_json, char_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, dynasty, era, content, translation,
                  background, appreciation, tags, author_bio, paragraphs_json, char_count))
            
            imported += 1
        except Exception as e:
            log.warning(f"导入失败 {f.name}: {e}")
    
    conn.commit()
    log.info(f"导入完成: {imported} 篇")
    return imported


def build_fts(conn):
    """构建全文索引"""
    log.info("构建古文全文索引...")
    conn.execute('''
        INSERT INTO guwen_fts(rowid, title, author, content, translation)
        SELECT id, title, author, content, translation FROM guwen
    ''')
    conn.commit()
    log.info("完成")


def print_stats(conn):
    """统计"""
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM guwen')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT dynasty, COUNT(*) FROM guwen GROUP BY dynasty ORDER BY COUNT(*) DESC')
    dynasties = cursor.fetchall()
    
    log.info(f"\n=== 古文观止统计 ===")
    log.info(f"总篇数: {total}")
    for d, c in dynasties:
        log.info(f"  {d}: {c} 篇")


def main():
    log.info("=== 导入《古文观止》 ===")
    
    conn = sqlite3.connect(str(DB_PATH))
    
    create_table(conn)
    import_articles(conn)
    build_fts(conn)
    print_stats(conn)
    
    conn.close()


if __name__ == "__main__":
    main()
