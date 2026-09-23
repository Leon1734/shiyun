#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据规范化脚本：修复标题格式 + 异体字
用法:
    python normalize_data.py preview   # 预览（不修改）
    python normalize_data.py apply     # 执行修改
"""
import sqlite3
import re
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("normalize")

DB = Path(__file__).parent / "data" / "poetry.db"

# ── 1. 乐府分类前缀（《乐府诗集》编排类目）──
LE_YUE_PREFIXES = [
    '郊庙歌辞', '燕射歌辞', '鼓吹曲辞', '横吹曲辞', '相和歌辞',
    '清商曲辞', '舞曲歌辞', '琴曲歌辞', '杂曲歌辞', '近代曲辞', '杂歌谣辞',
]

# ── 2. 异体字映射（高频旧字形 → 现代标准字形）──
VARIANT_MAP = {
    '疎': '疏', '迳': '径', '谿': '溪', '廐': '厩', '飬': '养',
    '羇': '羁', '覊': '羁', '鷰': '燕', '邨': '村', '牕': '窗',
    '飜': '翻', '煖': '暖', '猨': '猿', '覩': '睹', '胷': '胸',
    '蘂': '蕊', '劒': '剑', '觧': '解', '荅': '答', '慙': '惭',
    '甆': '瓷', '甎': '砖', '瓈': '璃',
        '鏁': '锁', '狥': '徇', '澘': '潸', '讙': '欢',
        '碁': '棋', '汚': '污', '徧': '遍', '隣': '邻', '槩': '概',
        '粧': '妆', '呌': '叫', '酤': '沽', '麤': '粗', '麄': '粗',
    '筯': '箸', '牀': '床', '挿': '插', '擧': '举', '熈': '熙',
    '甁': '瓶', '塟': '葬', '錬': '炼', '峯': '峰', '畵': '画',
    '綉': '绣',
}

# 特定词组替换（上下文相关，避免误伤专名）
PHRASE_MAP = {
    '衮衮': '滚滚',
}
# 祇/祗 的"只"义用法（避免误伤 祇园/祗候/神祇 等专名或敬语）
ZHI_FOLLOW = ['今', '应', '自', '有', '恐', '为', '是', '如', '缘',
              '在', '因', '得', '见', '闻', '说', '知', '好', '隔', '合', '向']

TITLE_NUM = {
    '一': '一', '二': '二', '三': '三', '四': '四', '五': '五',
    '六': '六', '七': '七', '八': '八', '九': '九', '十': '十',
    '十一': '十一', '十二': '十二', '十三': '十三', '十四': '十四',
    '十五': '十五', '十六': '十六', '十七': '十七', '十八': '十八',
    '十九': '十九', '二十': '二十',
}


def normalize_title(title):
    """标题规范化：剥离乐府前缀 + 编号格式统一 + 空格清理"""
    if not title:
        return title
    original = title
    t = title.strip()

    # 1. 剥离乐府分类前缀
    for p in LE_YUE_PREFIXES:
        if t.startswith(p):
            t = t[len(p):].lstrip()
            break

    # 2. 编号后缀: "  其一" / " 其一" → "·其一"
    t = re.sub(r'\s+其([一二三四五六七八九十]+)\s*$', r'·其\1', t)

    # 3. 编号后缀: " 一" / " 二" → "·其一"（仅单个汉字数字结尾）
    m = re.search(r'\s+([一二三四五六七八九十]+)\s*$', t)
    if m and '·其' not in t:
        t = t[:m.start()] + '·其' + m.group(1)

    # 4. 剩余多空格 → 单空格，去首尾
    t = re.sub(r'\s{2,}', ' ', t).strip()

    return t


def normalize_variants(text):
    """异体字规范化（内容用）"""
    if not text:
        return text
    for old, new in VARIANT_MAP.items():
        if old in text:
            text = text.replace(old, new)
    for old, new in PHRASE_MAP.items():
        if old in text:
            text = text.replace(old, new)
    # 祇/祗 → 只（特定后接字）
    for zhi in ['祇', '祗']:
        for nxt in ZHI_FOLLOW:
            text = text.replace(zhi + nxt, '只' + nxt)
    return text


def preview():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    log.info("=" * 60)
    log.info("【1】标题规范化预览")
    log.info("=" * 60)

    c.execute("SELECT COUNT(*) FROM poems")
    total = c.fetchone()[0]

    # 收集受影响的
    c.execute("SELECT id, title FROM poems WHERE title LIKE '%  %' OR title LIKE '% 一' OR title LIKE '% 二' OR title LIKE '% 三' OR title LIKE '% 四' OR title LIKE '% 五' OR title LIKE '% 六' OR title LIKE '% 七' OR title LIKE '% 八' OR title LIKE '% 九' OR title LIKE '% 十' OR title LIKE '鼓吹曲辞%' OR title LIKE '横吹曲辞%' OR title LIKE '相和歌辞%' OR title LIKE '舞曲歌辞%' OR title LIKE '琴曲歌辞%' OR title LIKE '杂曲歌辞%' OR title LIKE '杂歌谣辞%' OR title LIKE '郊庙歌辞%'")
    rows = c.fetchall()
    changed = []
    for pid, title in rows:
        new_title = normalize_title(title)
        if new_title != title:
            changed.append((pid, title, new_title))

    log.info(f"总诗词: {total:,}")
    log.info(f"标题将修改: {len(changed):,} 首")
    log.info("")
    log.info("--- 样例（前20）---")
    for pid, old, new in changed[:20]:
        log.info(f"  [{pid}] {old!r}")
        log.info(f"        → {new!r}")

    log.info("")
    log.info("=" * 60)
    log.info("【2】异体字规范化预览")
    log.info("=" * 60)

    # 统计每个字的影响
    for ch, new in VARIANT_MAP.items():
        c.execute("SELECT COUNT(*) FROM poems WHERE content LIKE ? OR title LIKE ?", (f'%{ch}%', f'%{ch}%'))
        n = c.fetchone()[0]
        if n:
            log.info(f"  {ch} → {new}: {n:,} 首")

    # 样例
    c.execute("SELECT id, title, substr(content,1,50) FROM poems WHERE content LIKE '%疎%' LIMIT 3")
    log.info("")
    log.info("--- 样例 ---")
    for pid, title, content in c.fetchall():
        log.info(f"  [{pid}] 《{title}》")
        log.info(f"    旧: {content!r}")
        log.info(f"    新: {normalize_variants(content)!r}")

    conn.close()


def apply():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # ── 标题规范化 ──
    log.info("执行标题规范化...")
    c.execute("SELECT id, title FROM poems")
    updates = []
    for pid, title in c.fetchall():
        new_title = normalize_title(title)
        if new_title != title:
            updates.append((new_title, pid))

    c.executemany("UPDATE poems SET title=? WHERE id=?", updates)
    log.info(f"  标题修改: {len(updates):,} 首")

    # ── 异体字（内容）──
    log.info("执行内容异体字规范化...")
    c.execute("SELECT COUNT(*) FROM poems")
    total = c.fetchone()[0]

    content_updates = []
    batch_size = 5000
    offset = 0
    changed_rows = 0
    while offset < total:
        c.execute("SELECT id, content FROM poems ORDER BY id LIMIT ? OFFSET ?", (batch_size, offset))
        rows = c.fetchall()
        if not rows:
            break
        for pid, content in rows:
            new_content = normalize_variants(content)
            if new_content != content:
                content_updates.append((new_content, pid))
                changed_rows += 1
        if len(content_updates) >= 5000:
            c.executemany("UPDATE poems SET content=? WHERE id=?", content_updates)
            content_updates = []
        offset += batch_size
    if content_updates:
        c.executemany("UPDATE poems SET content=? WHERE id=?", content_updates)
    log.info(f"  内容修改: {changed_rows:,} 首")

    # ── 异体字（标题，第二轮：清理残留）──
    c.execute("SELECT id, title FROM poems WHERE title LIKE '%疎%' OR title LIKE '%迳%' OR title LIKE '%谿%' OR title LIKE '%猨%' OR title LIKE '%蘂%' OR title LIKE '%劒%'")
    t_updates = []
    for pid, title in c.fetchall():
        new_title = normalize_variants(title)
        if new_title != title:
            t_updates.append((new_title, pid))
    c.executemany("UPDATE poems SET title=? WHERE id=?", t_updates)
    log.info(f"  标题异体字修改: {len(t_updates):,} 首")

    conn.commit()

    # 重建FTS
    try:
        conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
        conn.commit()
        log.info("  FTS索引已重建")
    except Exception as e:
        log.warning(f"  FTS重建跳过: {e}")

    conn.close()
    log.info("完成!")


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    if mode == 'apply':
        apply()
    else:
        preview()
