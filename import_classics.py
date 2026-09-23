#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导入论语、孟子全文到古文库 + 清理重复"""
import json
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("import_classics")

DB_PATH = Path(__file__).parent / "data" / "poetry.db"

try:
    from opencc import OpenCC
    cc = OpenCC('t2s')
    def to_simplified(t):
        return cc.convert(str(t))
except ImportError:
    def to_simplified(t):
        return str(t)


def import_lunyu_mengzi(conn):
    """导入论语和孟子"""
    cursor = conn.cursor()
    
    # 检查是否已导入
    cursor.execute("SELECT COUNT(*) FROM guwen WHERE collection = '论语'")
    if cursor.fetchone()[0] > 0:
        log.info("论语已导入，跳过")
    else:
        p = Path('data/论语/lunyu.json')
        if p.exists():
            with open(p, encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            for chapter in data:
                title = to_simplified(chapter.get('chapter', ''))
                paras = chapter.get('paragraphs', [])
                if not title or not paras:
                    continue
                content = to_simplified('\n'.join(paras))
                
                cursor.execute('''
                    INSERT INTO guwen (title, author, dynasty, era, content, translation,
                                       background, appreciation, tags, author_bio, paragraphs_json, char_count, collection)
                    VALUES (?, ?, ?, ?, ?, '', '', '', '[]', '', '', ?, '论语')
                ''', (f'论语·{title}', '孔子及弟子', '先秦', 'pre_qin', content, len(content)))
                count += 1
            conn.commit()
            log.info(f"论语导入: {count} 篇")
    
    # 孟子
    cursor.execute("SELECT COUNT(*) FROM guwen WHERE collection = '孟子'")
    if cursor.fetchone()[0] > 0:
        log.info("孟子已导入，跳过")
    else:
        p = Path('data/四书五经/mengzi.json')
        if p.exists():
            with open(p, encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            for chapter in data:
                title = to_simplified(chapter.get('chapter', ''))
                paras = chapter.get('paragraphs', [])
                if not title or not paras:
                    continue
                content = to_simplified('\n'.join(paras))
                
                cursor.execute('''
                    INSERT INTO guwen (title, author, dynasty, era, content, translation,
                                       background, appreciation, tags, author_bio, paragraphs_json, char_count, collection)
                    VALUES (?, ?, ?, ?, ?, '', '', '', '[]', '', '', ?, '孟子')
                ''', (f'孟子·{title}', '孟子', '先秦', 'pre_qin', content, len(content)))
                count += 1
            conn.commit()
            log.info(f"孟子导入: {count} 篇")


def dedupe_poems(conn):
    """清理完全重复的诗词"""
    cursor = conn.cursor()
    
    # 找出完全重复（同标题+同作者+同内容）
    cursor.execute('''
        SELECT MIN(id) as keep_id, COUNT(*) as cnt
        FROM poems
        GROUP BY title, author, content
        HAVING cnt > 1
    ''')
    groups = cursor.fetchall()
    
    total_deleted = 0
    for keep_id, cnt in groups:
        # 获取该组的所有id
        cursor.execute('''
            SELECT id FROM poems
            WHERE (title, author, content) = (
                SELECT title, author, content FROM poems WHERE id = ?
            )
            AND id != ?
        ''', (keep_id, keep_id))
        dup_ids = [r[0] for r in cursor.fetchall()]
        
        for dup_id in dup_ids:
            cursor.execute('DELETE FROM poems WHERE id = ?', (dup_id,))
            total_deleted += 1
    
    conn.commit()
    log.info(f"去重: 删除 {total_deleted} 条重复 (涉及 {len(groups)} 组)")


def main():
    conn = sqlite3.connect(str(DB_PATH))
    
    # 1. 导入论语孟子
    import_lunyu_mengzi(conn)
    
    # 2. 去重
    dedupe_poems(conn)
    
    # 3. 重建FTS
    log.info("重建FTS索引...")
    conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO guwen_fts(guwen_fts) VALUES('rebuild')")
    conn.commit()
    
    # 4. 统计
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM poems')
    total_poems = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM guwen')
    total_guwen = cursor.fetchone()[0]
    cursor.execute('SELECT collection, COUNT(*) FROM guwen GROUP BY collection ORDER BY COUNT(*) DESC')
    
    log.info(f"\n诗词: {total_poems:,}")
    log.info(f"古文: {total_guwen}")
    log.info("古文合集:")
    for r in cursor.fetchall():
        log.info(f"  {r[0]}: {r[1]}")
    
    conn.close()


if __name__ == "__main__":
    main()
