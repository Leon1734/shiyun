#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古文译文补全
从古文观止复制译文到重叠的中学文言文
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("fill_trans")

DB_PATH = Path(__file__).parent / "data" / "poetry.db"

# 手动映射（中学课文名 → 古文观止篇名）
MANUAL_MAP = {
    '陋室铭': '陋室铭',
    '出师表': '前出师表',
    '唐雎不辱使命': '唐雎不辱使命',
    '曹刿论战': '曹刿论战',
    '邹忌讽齐王纳谏': '邹忌讽齐王纳谏',
    '赤壁赋': '前赤壁赋',
    '六国论': '六国论',  # 注意：苏洵vs苏辙
    '谏太宗十思疏': '谏太宗十思疏',
    '岳阳楼记': '岳阳楼记',
    '醉翁亭记': '醉翁亭记',
    '师说': '师说',
    '爱莲说': None,  # 古文观止无
    '三峡': None,
    '马说': '杂说四',  # 韩愈《马说》即《杂说四》
    '桃花源记': '桃花源记',
    '小石潭记': None,
    '记承天寺夜游': None,
    '核舟记': None,
    '口技': None,
    '狼': None,
}


def fill_translations():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取缺译文的中学文言文
    cursor.execute("""
        SELECT id, title, author FROM guwen 
        WHERE collection = '中学文言文' AND (translation = '' OR translation IS NULL)
    """)
    missing = cursor.fetchall()
    log.info(f"待补译文: {len(missing)} 篇")
    
    filled = 0
    still_missing = []
    
    for mid, title, author in [(m['id'], m['title'], m['author']) for m in missing]:
        source_title = MANUAL_MAP.get(title)
        
        if source_title is None:
            still_missing.append((title, author, '无对应古文观止篇目'))
            continue
        
        # 查找古文观止版本
        cursor.execute("""
            SELECT translation, background, appreciation, paragraphs_json, tags, author_bio
            FROM guwen 
            WHERE collection = '古文观止' AND title = ?
            LIMIT 1
        """, (source_title,))
        source = cursor.fetchone()
        
        if not source or not source['translation']:
            still_missing.append((title, author, '古文观止版本也无译文'))
            continue
        
        # 复制译文（仅当目标缺译文时）
        cursor.execute("""
            UPDATE guwen SET 
                translation = ?,
                background = COALESCE(NULLIF(background, ''), ?),
                appreciation = COALESCE(NULLIF(appreciation, ''), ?),
                paragraphs_json = COALESCE(NULLIF(paragraphs_json, ''), ?),
                tags = COALESCE(NULLIF(tags, '[]'), ?),
                author_bio = COALESCE(NULLIF(author_bio, ''), ?)
            WHERE id = ?
        """, (source['translation'], source['background'], source['appreciation'],
              source['paragraphs_json'], source['tags'], source['author_bio'], mid))
        filled += 1
        log.info(f"  ✓ 《{title}》← 《{source_title}》")
    
    conn.commit()
    
    log.info(f"\n补全译文: {filled} 篇")
    
    if still_missing:
        log.info(f"\n仍缺译文: {len(still_missing)} 篇")
        for title, author, reason in still_missing:
            log.info(f"  《{title}》{author} - {reason}")
    
    # 统计
    cursor.execute("SELECT COUNT(*) FROM guwen WHERE translation != '' AND translation IS NOT NULL")
    has_trans = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM guwen")
    total = cursor.fetchone()[0]
    log.info(f"\n古文译文覆盖: {has_trans}/{total}")
    
    conn.close()


if __name__ == "__main__":
    fill_translations()
