#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词工具模块
功能：拼音标注、TTS朗读、配图生成
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

try:
    from pypinyin import pinyin, Style
    HAS_PINYIN = True
except ImportError:
    HAS_PINYIN = False

try:
    import edge_tts
    import asyncio
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


def get_pinyin(text):
    """给文字加拼音"""
    if not HAS_PINYIN:
        return text
    
    result = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            py = pinyin(char, style=Style.TONE)
            result.append(f"{char}({py[0][0]})")
        else:
            result.append(char)
    return ''.join(result)


def get_pinyin_lines(text):
    """逐行加拼音"""
    if not HAS_PINYIN:
        return text
    
    lines = text.split('\n')
    result = []
    for line in lines:
        result.append(get_pinyin(line))
        result.append(line)
    return '\n'.join(result)


async def tts_speak(text, voice="zh-CN-XiaoxiaoNeural", rate="+0%"):
    """TTS 朗读"""
    if not HAS_TTS:
        print("edge-tts 未安装，无法朗读")
        return
    
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    output_file = f"tts_{datetime.now().strftime('%H%M%S')}.mp3"
    await communicate.save(output_file)
    return output_file


def generate_poem_card_html(poem, bg_color="#f8f9fa", text_color="#333"):
    """生成诗词卡片 HTML"""
    title = poem.get('title', '')
    author = poem.get('author', '')
    dynasty = poem.get('dynasty', '')
    content = poem.get('content', '')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .card {{
            background: {bg_color};
            color: {text_color};
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            text-align: center;
        }}
        .title {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .author {{
            font-size: 16px;
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        .content {{
            font-size: 20px;
            line-height: 2;
            margin: 20px 0;
            text-align: center;
            color: #34495e;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 12px;
            color: #bdc3c7;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="title">《{title}》</div>
        <div class="author">· {author} ({dynasty})</div>
        <div class="content">{content.replace(chr(10), '<br>')}</div>
        <div class="footer">古诗词桌面小工具 · {datetime.now().strftime('%Y-%m-%d')}</div>
    </div>
</body>
</html>"""
    return html


def generate_poem_card_png(poem, output_path="poem_card.png"):
    """生成诗词卡片 PNG"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow 未安装，无法生成图片")
        return None
    
    # 创建图片
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)
    
    # 尝试加载中文字体
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    
    title_font = None
    content_font = None
    
    for font_path in font_paths:
        try:
            title_font = ImageFont.truetype(font_path, 36)
            content_font = ImageFont.truetype(font_path, 24)
            break
        except:
            continue
    
    if not title_font:
        title_font = ImageFont.load_default()
        content_font = ImageFont.load_default()
    
    # 绘制标题
    title = f"《{poem.get('title', '')}》"
    draw.text((width//2, 80), title, font=title_font, fill=(44, 62, 80), anchor="mm")
    
    # 绘制作者
    author = f"· {poem.get('author', '')} ({poem.get('dynasty', '')})"
    draw.text((width//2, 130), author, font=content_font, fill=(127, 140, 141), anchor="mm")
    
    # 绘制内容
    content = poem.get('content', '')
    y = 200
    for line in content.split('\n'):
        if line.strip():
            draw.text((width//2, y), line, font=content_font, fill=(52, 73, 94), anchor="mm")
            y += 40
    
    # 绘制底部
    footer = f"古诗词桌面小工具 · {datetime.now().strftime('%Y-%m-%d')}"
    draw.text((width//2, height - 50), footer, font=content_font, fill=(189, 195, 199), anchor="mm")
    
    # 保存
    img.save(output_path)
    return output_path


def search_poems_by_mood(poems, mood):
    """按情绪搜索诗句"""
    mood_keywords = {
        '思乡': ['故乡', '乡', '家', '归', '还'],
        '离别': ['离', '别', '送', '去', '远'],
        '欢乐': ['乐', '喜', '笑', '欢', '歌'],
        '忧愁': ['愁', '忧', '悲', '泪', '伤'],
        '豪迈': ['壮', '豪', '雄', '志', '功'],
        '自然': ['山', '水', '花', '月', '风'],
    }
    
    keywords = mood_keywords.get(mood, [mood])
    results = []
    
    for poem in poems:
        content = poem.get('content', '')
        title = poem.get('title', '')
        
        for kw in keywords:
            if kw in content or kw in title:
                results.append(poem)
                break
    
    return results


def get_poem_stats(poems):
    """获取诗词统计"""
    from collections import Counter
    
    # 朝代分布
    dynasty_counts = Counter(p.get('dynasty', '未知') for p in poems)
    
    # 作者分布 (前20)
    author_counts = Counter(p.get('author', '未知') for p in poems)
    
    # 诗名字数分布
    title_lengths = Counter(len(p.get('title', '')) for p in poems)
    
    return {
        'dynasty': dict(dynasty_counts),
        'top_authors': dict(author_counts.most_common(20)),
        'title_lengths': dict(title_lengths)
    }


def export_poems_to_txt(poems, output_path="poems_export.txt"):
    """导出诗句为文本文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"诗词导出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, poem in enumerate(poems, 1):
            f.write(f"{i}. 《{poem.get('title', '')}》\n")
            f.write(f"   · {poem.get('author', '')} ({poem.get('dynasty', '')})\n")
            f.write(f"   {poem.get('content', '')}\n\n")
    
    return output_path


def export_poems_to_csv(poems, output_path="poems_export.csv"):
    """导出诗句为 CSV 文件"""
    import csv
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '标题', '作者', '朝代', '内容', '标签'])
        
        for i, poem in enumerate(poems, 1):
            writer.writerow([
                i,
                poem.get('title', ''),
                poem.get('author', ''),
                poem.get('dynasty', ''),
                poem.get('content', ''),
                ','.join(poem.get('tags', []))
            ])
    
    return output_path


if __name__ == '__main__':
    # 测试拼音
    if HAS_PINYIN:
        test_text = "床前明月光"
        print(f"原文: {test_text}")
        print(f"拼音: {get_pinyin(test_text)}")
        print(f"逐行拼音:\n{get_pinyin_lines(test_text)}")
    else:
        print("pypinyin 未安装")
