#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入缺失合集 v2
- 纳兰性德 (清) → poems
- 花间集 / 南唐二主词 (五代) → poems  
- 曹操诗集 (汉) → poems
- 蒙学 (三字经/千字文等) → poems
- 四书五经 (大学/中庸/孟子) → guwen
- 幽梦影 → guwen
"""

import json
import sqlite3
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("import2")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"

try:
    from opencc import OpenCC
    cc = OpenCC('t2s')
    def to_simplified(t):
        return cc.convert(str(t))
except ImportError:
    def to_simplified(t):
        return str(t)


def get_max_id(conn, table='poems'):
    cursor = conn.cursor()
    cursor.execute(f'SELECT MAX(id) FROM {table}')
    return cursor.fetchone()[0] or 0


def insert_poems(conn, rows, collection, dynasty):
    """批量插入诗词"""
    cursor = conn.cursor()
    # 确保 collection 列存在
    cursor.executemany('''
        INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [(t, a, dynasty, c, collection, r, collection) for t, a, c, r in rows])
    conn.commit()
    return len(rows)


def import_nalan(conn):
    """纳兰性德"""
    p = DATA_DIR / '纳兰性德' / '纳兰性德诗集.json'
    if not p.exists():
        return 0
    
    with open(p, encoding='utf-8') as f:
        data = json.load(f)
    
    rows = []
    for item in data:
        title = to_simplified(item.get('title', '').strip())
        author = to_simplified(item.get('author', '纳兰性德'))
        paras = item.get('para', []) or item.get('paragraphs', [])
        if not title or not paras:
            continue
        content = to_simplified('\n'.join(paras))
        # 词牌从标题提取
        rhythmic = title.split('·')[0] if '·' in title else ''
        rows.append((title, author, content, rhythmic))
    
    n = insert_poems(conn, rows, '纳兰性德', '清')
    log.info(f"纳兰性德: {n} 首")
    return n


def import_huajianji(conn):
    """花间集"""
    total = 0
    for f in sorted((DATA_DIR / '五代诗词' / 'huajianji').glob('*.json')):
        with open(f, encoding='utf-8') as fp:
            data = json.load(fp)
        if not isinstance(data, list):
            continue
        
        rows = []
        for item in data:
            title = to_simplified(item.get('title', '').strip())
            author = to_simplified(item.get('author', '佚名').strip()) or '佚名'
            paras = item.get('paragraphs', [])
            if not title or not paras:
                continue
            content = to_simplified('\n'.join(paras))
            rhythmic = to_simplified(item.get('rhythmic', ''))
            notes = item.get('notes', [])
            
            # 注释附加到内容（可选，暂存 rhythmic）
            rows.append((title, author, content, rhythmic))
        
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [(t, a, '五代', c, f.stem, r, '花间集') for t, a, c, r in rows])
        conn.commit()
        total += len(rows)
    
    log.info(f"花间集: {total} 首")
    return total


def import_nantang(conn):
    """南唐二主词"""
    p = DATA_DIR / '五代诗词' / 'nantang' / 'poetrys.json'
    if not p.exists():
        return 0
    
    with open(p, encoding='utf-8') as f:
        data = json.load(f)
    
    rows = []
    for item in data:
        title = to_simplified(item.get('title', item.get('rhythmic', '')).strip())
        author = to_simplified(item.get('author', '李煜').strip()) or '佚名'
        paras = item.get('paragraphs', [])
        if not title or not paras:
            continue
        content = to_simplified('\n'.join(paras))
        rhythmic = to_simplified(item.get('rhythmic', ''))
        rows.append((title, author, content, rhythmic))
    
    n = insert_poems(conn, rows, '南唐二主词', '五代')
    log.info(f"南唐二主词: {n} 首")
    return n


def import_caocao(conn):
    """曹操诗集"""
    p = DATA_DIR / '曹操诗集' / 'caocao.json'
    if not p.exists():
        return 0
    
    with open(p, encoding='utf-8') as f:
        data = json.load(f)
    
    rows = []
    for item in data:
        title = to_simplified(item.get('title', '').strip())
        paras = item.get('paragraphs', [])
        if not title or not paras:
            continue
        content = to_simplified('\n'.join(paras))
        rows.append((title, '曹操', content, ''))
    
    n = insert_poems(conn, rows, '曹操诗集', '汉')
    log.info(f"曹操诗集: {n} 首")
    return n


def extract_text_deep(obj):
    """递归提取任意嵌套结构中的文本"""
    if obj is None:
        return ''
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, list):
        parts = [extract_text_deep(x) for x in obj]
        return '\n'.join(p for p in parts if p)
    if isinstance(obj, dict):
        # 优先 content/paragraphs
        for key in ['content', 'paragraphs', 'text']:
            if key in obj:
                return extract_text_deep(obj[key])
        # 其他情况拼接所有值
        parts = []
        for k, v in obj.items():
            if k in ('title', 'chapter', 'type', 'author'):
                continue  # 跳过元数据
            t = extract_text_deep(v)
            if t:
                parts.append(t)
        return '\n'.join(parts)
    return str(obj)


def import_mengxue(conn):
    """蒙学经典"""
    mengxue_dir = DATA_DIR / '蒙学'
    if not mengxue_dir.exists():
        return 0
    
    # 名家映射
    name_map = {
        'baijiaxing': ('百家姓', '佚名', '北宋'),
        'dizigui': ('弟子规', '李毓秀', '清'),
        'qianjiashi': ('千家诗', '佚名', '宋'),
        'qianziwen': ('千字文', '周兴嗣', '南北朝'),
        'sanzijing-new': ('三字经', '王应麟', '南宋'),
        'shenglvqimeng': ('声律启蒙', '车万育', '清'),
        'tangshisanbaishou': ('唐诗三百首', '佚名', '清'),
        'wenzimengqiu': ('文字蒙求', '王筠', '清'),
        'youxueqionglin': ('幼学琼林', '程登吉', '明'),
        'zengguangxianwen': ('增广贤文', '佚名', '明清'),
        'zhuzijiaxun': ('朱子家训', '朱柏庐', '明末清初'),
    }
    
    total = 0
    for f in sorted(mengxue_dir.glob('*.json')):
        stem = f.stem
        if stem not in name_map:
            continue
        title, author, dynasty = name_map[stem]
        
        with open(f, encoding='utf-8') as fp:
            data = json.load(fp)
        
        if not isinstance(data, dict):
            continue
        
        # 获取正文（兼容 content / paragraphs 两种键，递归处理嵌套）
        body = data.get('content')
        if body is None:
            body = data.get('paragraphs', [])
        
        content = extract_text_deep(body)
        content = to_simplified(content)
        
        if not content.strip():
            continue
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO poems (title, author, dynasty, content, source, rhythmic, collection)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, author, dynasty, content, stem, '', '蒙学'))
        conn.commit()
        total += 1
        log.info(f"  蒙学·{title}: {len(content)}字")
    
    log.info(f"蒙学合计: {total} 部")
    return total


def import_sishu(conn):
    """四书五经 + 幽梦影 → guwen 表"""
    total = 0
    
    # 大学/中庸
    for stem, title in [('daxue', '大学'), ('zhongyong', '中庸')]:
        p = DATA_DIR / '四书五经' / f'{stem}.json'
        if not p.exists():
            continue
        with open(p, encoding='utf-8') as f:
            data = json.load(f)
        
        paras = data.get('paragraphs', [])
        if isinstance(paras, list):
            content = to_simplified('\n'.join(paras))
        else:
            content = to_simplified(str(paras))
        
        if content.strip():
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO guwen (title, author, dynasty, era, content, translation,
                                   background, appreciation, tags, author_bio, paragraphs_json, char_count, collection)
                VALUES (?, ?, ?, ?, ?, '', '', '', '[]', '', '', ?, '四书五经')
            ''', (title, '孔子及弟子', '先秦', 'pre_qin', content, len(content)))
            conn.commit()
            total += 1
            log.info(f"  四书五经·{title}: {len(content)}字")
    
    # 幽梦影
    p = DATA_DIR / '幽梦影' / 'youmengying.json'
    if p.exists():
        with open(p, encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            count = 0
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                c = item.get('content', '')
                if isinstance(c, list):
                    c = '\n'.join(c)
                c = to_simplified(str(c).strip())
                if not c:
                    continue
                
                # 评注作为赏析
                comments = item.get('comment', [])
                appreciation = to_simplified('\n'.join(comments)) if comments else ''
                
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO guwen (title, author, dynasty, era, content, translation,
                                       background, appreciation, tags, author_bio, paragraphs_json, char_count, collection)
                    VALUES (?, ?, ?, ?, ?, '', '', ?, '[]', '', '', ?, '幽梦影')
                ''', (f'幽梦影·其{i+1}', '张潮', '清', 'ming', c, appreciation, len(c)))
                count += 1
            conn.commit()
            log.info(f"  幽梦影: {count} 条")
            total += count
    
    return total


def rebuild_fts(conn):
    """重建FTS索引"""
    log.info("重建FTS索引...")
    conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO guwen_fts(guwen_fts) VALUES('rebuild')")
    conn.commit()
    log.info("完成")


def main():
    log.info("=== 导入缺失合集 ===")
    conn = sqlite3.connect(str(DB_PATH))
    
    # 记录导入前
    max_poem_id = get_max_id(conn, 'poems')
    
    n1 = import_nalan(conn)
    n2 = import_huajianji(conn)
    n3 = import_nantang(conn)
    n4 = import_caocao(conn)
    n5 = import_mengxue(conn)
    n6 = import_sishu(conn)
    
    rebuild_fts(conn)
    
    # 统计
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM poems')
    total = cursor.fetchone()[0]
    log.info(f"\n数据库诗词总数: {total:,} (新增 {total - 344420})")
    
    cursor.execute('SELECT collection, COUNT(*) FROM poems WHERE collection IN (\"纳兰性德\",\"花间集\",\"南唐二主词\",\"曹操诗集\",\"蒙学\") GROUP BY collection')
    log.info("新合集分布:")
    for r in cursor.fetchall():
        log.info(f"  {r[0]}: {r[1]:,}")
    
    cursor.execute('SELECT collection, COUNT(*) FROM guwen WHERE collection IN (\"四书五经\",\"幽梦影\") GROUP BY collection')
    for r in cursor.fetchall():
        log.info(f"  {r[0]}: {r[1]}")
    
    conn.close()
    log.info("完成!")


if __name__ == "__main__":
    main()
