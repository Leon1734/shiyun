#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI 验证测试：启动应用后自动检查界面状态"""
import sys
import tkinter as tk
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.WARNING)

from poetry_desktop import PoetryApp

root = tk.Tk()
app = PoetryApp(root)

results = []

def check_ui():
    """检查 UI 状态"""
    try:
        # 1. 目录树
        items = app.dir_tree.get_children()
        results.append(f"目录树条目数: {len(items)}")
        if items:
            for item in items[:3]:
                vals = app.dir_tree.item(item)['values']
                results.append(f"  条目: {vals}")
        
        # 2. 当前诗词
        if app.current_poem:
            results.append(f"当前诗词: 《{app.current_poem.get('title')}》{app.current_poem.get('author')}")
            content = app.content_text.get('1.0', '200.0').strip()
            results.append(f"正文内容长度: {len(content)}")
            results.append(f"正文前50字: {content[:50]}")
        else:
            results.append("当前诗词: 无")
        
        # 3. 状态栏
        results.append(f"状态栏: {app.status_label.cget('text')}")
        
        # 4. 字体设置
        results.append(f"诗词字体: {app.content_text.cget('font')}")
        results.append(f"标题字体: {app.title_label.cget('font')}")
        
        # 5. 主题色
        results.append(f"主题: {app.current_theme}, bg={app.theme_colors.get('bg')}")
        
        # 6. 分页标签
        results.append(f"分页: {app.page_label.cget('text')}")
        results.append(f"统计: {app.dir_stats_label.cget('text')}")
        
    except Exception as e:
        results.append(f"检查失败: {e}")
    
    # 输出结果
    print("=" * 50)
    print("UI 验证结果")
    print("=" * 50)
    for r in results:
        print(r)
    
    root.destroy()

# 等待数据加载完成后检查（延迟6秒）
root.after(6000, check_ui)
root.mainloop()
print("测试完成")
