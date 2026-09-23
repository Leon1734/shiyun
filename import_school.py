#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载并导入中学语文课文（文言文+古诗词）
来源: github.com/lanhin/SchoolChinese (via gh-proxy)
"""

import json
import re
import time
import sqlite3
import urllib.request
import urllib.parse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("school")

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = DATA_DIR / "school_raw"
OUT_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "poetry.db"

PROXY = "https://gh-proxy.com/https://raw.githubusercontent.com/lanhin/SchoolChinese/master/"

GRADE_MAP = {
    '71': '七年级上', '72': '七年级下',
    '81': '八年级上', '82': '八年级下',
    '91': '九年级上', '92': '九年级下',
    '1': '高中必修一', '2': '高中必修二', '3': '高中必修三',
    '4': '高中必修四', '5': '高中必修五',
}


def download_all():
    """下载所有课文"""
    tree_file = Path(__file__).parent / "school_tree.json"
    with open(tree_file, encoding='utf-8') as f:
        tree = json.load(f)
    
    files = [t['path'] for t in tree['tree'] 
             if t['type'] == 'blob' and t['path'].endswith('.md') and (t['path'].startswith('r/') or t['path'].startswith('s/'))]
    
    log.info(f"待下载: {len(files)} 篇")
    
    def dl(rel_path):
        out = OUT_DIR / rel_path.replace('/', '_')
        if out.exists() and out.stat().st_size > 50:
            return 'skip'
        url = PROXY + urllib.parse.quote(rel_path)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                out.write_bytes(resp.read())
            return 'ok'
        except Exception as e:
            return f'fail: {e}'
    
    ok = skip = fail = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(dl, f) for f in files]
        for future in as_completed(futures):
            r = future.result()
            if r == 'ok': ok += 1
            elif r == 'skip': skip += 1
            else: fail += 1
    
    log.info(f"下载完成: ok={ok}, skip={skip}, fail={fail}")
    return len(list(OUT_DIR.glob('*.md')))


def parse_md(text):
    """解析 课程markdown: # 标题 / > 作者 / 正文"""
    lines = text.strip().split('\n')
    title = ''
    author = ''
    content_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            title = line[2:].strip()
        elif line.startswith('> '):
            author = line[2:].strip()
        elif line.startswith('#'):
            continue
        else:
            content_lines.append(line)
    
    content = '\n'.join(content_lines)
    return title, author, content


def is_prose(content):
    """判断是否为文言文（散文）而非诗词"""
    # 文言文特征：包含"之乎者也"等虚词，句子更长，无固定字数
    # 诗词特征：句子整齐，多为5或7字
    
    # 取前几句
    sentences = re.split(r'[，。！？；：]', content[:200])
    sentences = [s for s in sentences if len(s) >= 3][:6]
    
    if not sentences:
        return False
    
    # 如果句子长度差异大 → 散文
    lengths = [len(s) for s in sentences]
    avg = sum(lengths) / len(lengths)
    variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
    
    # 文言文虚词
    prose_markers = ['之', '乎', '者', '也', '矣', '焉', '哉', '耳', '耶', '兮', '曰']
    marker_count = sum(1 for m in prose_markers if m in content)
    
    # 判定：句长差异大 或 虚词多 或 平均句长长
    if variance > 15 or marker_count >= 2 or avg > 9:
        return True
    return False


def import_school():
    """导入课文到数据库"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 确保古文表有 collection 列
    cursor.execute("PRAGMA table_info(guwen)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'collection' not in cols:
        cursor.execute("ALTER TABLE guwen ADD COLUMN collection TEXT DEFAULT '古文观止'")
        cursor.execute("UPDATE guwen SET collection = '古文观止' WHERE collection = '' OR collection IS NULL")
        conn.commit()
    
    files = sorted(OUT_DIR.glob('*.md'))
    log.info(f"处理 {len(files)} 个文件")
    
    prose_count = 0
    poem_count = 0
    poem_new = 0
    
    for f in files:
        # 解析文件名获取年级: r_81_ailianshuo.md
        parts = f.stem.split('_')
        grade = GRADE_MAP.get(parts[1], '中学')
        
        try:
            text = f.read_text(encoding='utf-8')
        except:
            continue
        
        title, author, content = parse_md(text)
        if not title or not content:
            continue
        
        if is_prose(content):
            # 文言文 → guwen表
            cursor.execute('''
                SELECT COUNT(*) FROM guwen WHERE title = ? AND author = ?
            ''', (title, author))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                char_count = len(content.replace('\n', ''))
                cursor.execute('''
                    INSERT INTO guwen (title, author, dynasty, era, content, translation,
                                       background, appreciation, tags, author_bio, paragraphs_json, char_count, collection)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, author, '', grade, content, '', '', '', '[]', '', '', char_count, '中学文言文'))
                prose_count += 1
        else:
            # 诗词 → poems表
            poem_count += 1
            # 检查是否已存在
            cursor.execute('SELECT COUNT(*) FROM poems WHERE title = ? AND author = ?', (title, author))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO poems (title, author, dynasty, content, source, collection)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, author, '', content, 'school', '中学古诗'))
                poem_new += 1
    
    conn.commit()
    
    log.info(f"文言文新增: {prose_count} 篇")
    log.info(f"诗词处理: {poem_count} 篇, 新增: {poem_new} 篇")
    
    # 重建诗词FTS
    if poem_new > 0:
        log.info("更新诗词FTS索引...")
        cursor.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
        conn.commit()
    
    # 重建古文FTS
    log.info("更新古文FTS索引...")
    cursor.execute("INSERT INTO guwen_fts(guwen_fts) VALUES('rebuild')")
    conn.commit()
    
    conn.close()


if __name__ == "__main__":
    log.info("=== 中学语文课文 ===")
    download_all()
    import_school()
    log.info("完成!")
