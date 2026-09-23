#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入经典选本三件套（结构化数据源）：
1. 千家诗 219首（含组诗拆分）
2. 唐诗三百首 366首（含tags→题材/诗体映射）
3. 宋词三百首 280首（词牌·首句 标题格式）
替换蒙学里的两个blob记录
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from normalize_data import normalize_title, normalize_variants

from opencc import OpenCC

DB = Path(__file__).parent / "data" / "poetry.db"
CC = OpenCC('t2s')


def to_simp(s):
    return CC.convert(s)


def parse_author(raw):
    """解析（唐）孟浩然 → (孟浩然, 唐)"""
    raw = raw.strip()
    m = re.match(r'[（(]([^）)]+)[）)]\s*(.+)', raw)
    if m:
        dynasty = m.group(1).strip()
        author = m.group(2).strip()
        # 处理 "南宋"/"北宋" → "宋"
        if dynasty in ('南宋', '北宋'):
            dynasty = '宋'
        elif dynasty in ('五代', '南唐'):
            dynasty = dynasty
        elif '唐' in dynasty:
            dynasty = '唐'
        return to_simp(author), dynasty
    return to_simp(raw), ''


def clean_para(p):
    """paragraphs 可能嵌套dict"""
    if isinstance(p, str):
        return p
    return ''


# 题材映射（从tags）
THEME_MAP = {
    '写景': '山水田园', '山水': '山水田园', '田园': '山水田园',
    '思乡': '羁旅思乡', '思念': '羁旅思乡', '怀人': '羁旅思乡', '羁旅': '羁旅思乡',
    '送别': '送别怀人', '友情': '送别怀人', '赠别': '送别怀人',
    '咏物': '咏物言志', '咏物诗': '咏物言志', '言志': '咏物言志',
    '咏史': '咏史怀古', '怀古': '咏史怀古', '咏史怀古诗': '咏史怀古',
    '边塞': '边塞征战', '战争': '边塞征战', '从军': '边塞征战',
    '爱情': '爱情闺怨', '闺怨': '爱情闺怨', '女子': '爱情闺怨', '宫怨': '爱情闺怨',
    '悼亡': '悼亡哀伤', '哀伤': '悼亡哀伤', '伤怀': '悼亡哀伤',
    '哲理': '哲理人生', '人生': '哲理人生', '励志': '哲理人生',
    '节日': '节令民俗', '节气': '节令民俗', '民俗': '节令民俗',
}

# 诗体映射
FORM_MAP = {
    '五言律诗': '五言律诗', '七言律诗': '七言律诗',
    '五言绝句': '五言绝句', '七言绝句': '七言绝句',
    '五言古诗': '五言古诗', '七言古诗': '七言古诗',
    '乐府': '乐府', '五言': '五言', '七言': '七言',
}


def map_theme(tags):
    for t in tags:
        if t in THEME_MAP:
            return THEME_MAP[t]
    return ''


def map_form(tags):
    for t in tags:
        if t in FORM_MAP:
            return FORM_MAP[t]
    return ''


def insert_poem(c, title, author, dynasty, content, collection, theme='', form='', chars=0):
    title = normalize_title(normalize_variants(to_simp(title)))
    author = to_simp(author)
    content = normalize_variants(to_simp(content))
    word_count = len(content.replace('\n', ''))
    line_count = content.count('\n') + 1
    c.execute('''
        INSERT INTO poems (title, author, dynasty, content, source, theme, poem_form,
                           chars_per_line, line_count, word_count, collection)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, author, dynasty, content, collection, theme, form, chars, line_count, word_count, collection))


def import_qianjiashi(conn):
    """千家诗"""
    c = conn.cursor()
    with open('data/蒙学/qianjiashi.json', encoding='utf-8') as f:
        qjs = json.load(f)

    # 先删除旧blob
    c.execute("DELETE FROM poems WHERE collection='蒙学' AND (title LIKE '%千家诗%' OR source='qianjiashi')")

    count = 0
    form_abbr = {'五言絕句': ('五言绝句', 5), '五言律詩': ('五言律诗', 5),
                 '七言絕句': ('七言绝句', 7), '七言律詩': ('七言律诗', 7)}

    for section in qjs['content']:
        stype = section.get('type', '')
        form, chars = form_abbr.get(stype, ('', 0))
        for item in section['content']:
            chapter = item.get('chapter', '')
            author_raw = item.get('author', '')
            paras = item.get('paragraphs', [])
            author, dynasty = parse_author(author_raw)

            # 普通条目：paragraphs 全是字符串
            str_paras = [p for p in paras if isinstance(p, str)]
            dict_paras = [p for p in paras if isinstance(p, dict)]

            if str_paras and not dict_paras:
                content = '\n'.join(str_paras)
                insert_poem(c, chapter, author, dynasty, content, '千家诗', '', form, chars)
                count += 1
            else:
                # 组诗：拆分为 其一/其二...
                for sub in dict_paras:
                    sub_title = f"{chapter}·{sub.get('subchapter', '')}"
                    sub_content = '\n'.join([p for p in sub.get('paragraphs', []) if isinstance(p, str)])
                    if sub_content:
                        insert_poem(c, sub_title, author, dynasty, sub_content, '千家诗', '', form, chars)
                        count += 1

    print(f"千家诗导入: {count}首")
    return count


def import_tssbs(conn):
    """唐诗三百首（366首）"""
    c = conn.cursor()
    with open('data/全唐诗/唐诗三百首.json', encoding='utf-8') as f:
        ts = json.load(f)

    # 删除旧数据（含蒙学blob）
    c.execute("DELETE FROM poems WHERE collection='唐诗三百首'")
    c.execute("DELETE FROM poems WHERE collection='蒙学' AND (title LIKE '%唐诗三百首%' OR source='tangshisanbaishou')")

    count = 0
    for item in ts:
        title = item['title']
        author = item['author']
        paras = item.get('paragraphs', [])
        tags = item.get('tags', [])
        content = '\n'.join(paras)
        theme = map_theme(tags)
        form = map_form(tags)
        chars = 5 if '五言' in form else (7 if '七言' in form else 0)
        insert_poem(c, title, author, '唐', content, '唐诗三百首', theme, form, chars)
        count += 1

    print(f"唐诗三百首导入: {count}首")
    return count


def import_scsbs(conn):
    """宋词三百首（280首）"""
    c = conn.cursor()
    with open('data/宋词/宋词三百首.json', encoding='utf-8') as f:
        sc = json.load(f)

    # 删除旧数据（如果有）
    c.execute("DELETE FROM poems WHERE collection='宋词三百首'")

    count = 0
    for item in sc:
        author = item['author']
        rhythmic = item.get('rhythmic', '')
        paras = item.get('paragraphs', [])
        tags = item.get('tags', [])

        # 标题 = 词牌·首句（首句取前7字去标点）
        first = re.sub(r'[，。！？、；：]', '', paras[0]) if paras else ''
        first = first[:9]
        title = f"{rhythmic}·{first}" if rhythmic else first

        content = '\n'.join(paras)
        insert_poem(c, title, author, '宋', content, '宋词三百首')
        count += 1

    print(f"宋词三百首导入: {count}首")
    return count


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'preview'

    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    if action == 'preview':
        # 只读预览
        print("=== 预览模式 ===")
        with open('data/蒙学/qianjiashi.json', encoding='utf-8') as f:
            qjs = json.load(f)
        n1 = sum(len(s['content']) for s in qjs['content'])
        print(f"  千家诗: {n1}条（含组诗）")

        with open('data/全唐诗/唐诗三百首.json', encoding='utf-8') as f:
            ts = json.load(f)
        print(f"  唐诗三百首: {len(ts)}条")

        with open('data/宋词/宋词三百首.json', encoding='utf-8') as f:
            sc = json.load(f)
        print(f"  宋词三百首: {len(sc)}条")

        # 示例转换
        print()
        print("=== 示例转换 ===")
        item = qjs['content'][0]['content'][0]
        print(f"  千家诗[0]: chapter={item['chapter']!r} author={item['author']!r}")
        print(f"    → 标题《{normalize_title(to_simp(item['chapter']))}》 作者={parse_author(item['author'])}")
        print(f"    内容: {to_simp(''.join(item['paragraphs']))[:40]!r}")

        item = ts[0]
        print(f"  唐诗[0]: {item['title']!r} {item['author']!r}")
        print(f"    → 标题《{normalize_title(to_simp(item['title']))}》 作者={to_simp(item['author'])} 题材={map_theme(item['tags'])} 诗体={map_form(item['tags'])}")

        item = sc[0]
        print(f"  宋词[0]: {item['rhythmic']!r} {item['author']!r}")
        first = re.sub(r'[，。！？、；：]', '', item['paragraphs'][0])[:9]
        print(f"    → 标题《{item['rhythmic']}·{first}》")

    elif action == 'apply':
        print("=== 正式导入 ===")
        n1 = import_qianjiashi(conn)
        n2 = import_tssbs(conn)
        n3 = import_scsbs(conn)
        conn.commit()
        print(f"总计: {n1 + n2 + n3}首")

        # 重建FTS
        conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
        conn.commit()
        print("FTS已重建")

    conn.close()
