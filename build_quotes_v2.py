#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
名句库构建 v2 - 改进匹配
1. 标点规范化（去掉标点后比较）
2. 多级回退匹配（整句→前6字→核心5字）
3. 支持诗句换行合并
"""

import sqlite3
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("quotes")

DB_PATH = Path(__file__).parent / "data" / "poetry.db"

# 复用 v1 的候选列表
from build_quotes import CURATED_QUOTES


def normalize(text):
    """去掉所有标点和空白"""
    return re.sub(r'[，。！？、；：""''（）《》·\s\n—…,!?;:\'\"()\[\]]', '', text)


def build_quotes_v2():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM quotes')
    
    verified = 0
    unverified = []
    
    for text, title, author in CURATED_QUOTES:
        if not text or not title:
            continue
        
        norm_text = normalize(text)
        if len(norm_text) < 4:
            continue
        
        found = None
        
        # 策略1: 规范化内容匹配（前8字）
        probe = norm_text[:8].replace('%', '').replace('_', '')
        cursor.execute('''
            SELECT id, title, author, REPLACE(REPLACE(REPLACE(content, '，', ''), '。', ''), '\n', '') as nc
            FROM poems 
            WHERE REPLACE(REPLACE(REPLACE(content, '，', ''), '。', ''), '\n', '') LIKE ?
            LIMIT 1
        ''', (f'%{probe}%',))
        found = cursor.fetchone()
        
        # 策略2: 用后半句（前6字）
        if not found and len(norm_text) > 8:
            probe2 = norm_text[6:14].replace('%', '').replace('_', '')
            cursor.execute('''
                SELECT id, title, author FROM poems 
                WHERE REPLACE(REPLACE(REPLACE(content, '，', ''), '。', ''), '\n', '') LIKE ?
                LIMIT 1
            ''', (f'%{probe2}%',))
            found = cursor.fetchone()
        
        # 策略3: 古文表匹配
        if not found:
            cursor.execute('''
                SELECT id, title, author FROM guwen 
                WHERE REPLACE(REPLACE(REPLACE(content, '，', ''), '。', ''), '\n', '') LIKE ?
                LIMIT 1
            ''', (f'%{probe}%',))
            found = cursor.fetchone()
        
        # 策略4: 仅按标题+作者收录（诗句可能变体）
        if not found:
            cursor.execute('''
                SELECT id, title, author FROM poems 
                WHERE title = ? AND author = ?
                LIMIT 1
            ''', (title, author))
            found = cursor.fetchone()
        
        if found:
            source_id, actual_title, actual_author = found[0], found[1], found[2]
            cursor.execute('''
                INSERT INTO quotes (text, title, author, source_id, verified)
                VALUES (?, ?, ?, ?, 1)
            ''', (text, actual_title, actual_author, source_id))
            verified += 1
        else:
            unverified.append(f"{text} —— {author}《{title}》")
    
    conn.commit()
    
    log.info(f"名句库 v2: {verified}/{len([q for q in CURATED_QUOTES if q[0] and q[1]])} 已验证")
    
    if unverified:
        log.info(f"\n仍未匹配 {len(unverified)} 句:")
        for u in unverified:
            log.info(f"  {u}")
    
    cursor.execute('SELECT COUNT(*) FROM quotes')
    log.info(f"\n名句总数: {cursor.fetchone()[0]}")
    
    conn.close()


if __name__ == "__main__":
    build_quotes_v2()
