#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序集成模块
功能：将学习模式、游戏模式、创作辅助集成到主菜单
使用方法：
    1. 在 poetry_desktop_v2.py 末尾的 PoetryApp 类中导入并调用
    2. 或者直接运行本文件，它会同时启动主程序和新功能
依赖：learning_ui, game_ui, creation_ui, poetry_desktop_v2
"""

import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# 确保当前目录在 path 中
sys.path.insert(0, str(Path(__file__).parent))

# 导入新模块
try:
    from learning_ui import LearningMainUI
    HAS_LEARNING = True
except ImportError as e:
    HAS_LEARNING = False
    print(f"⚠️ learning_ui 模块未找到: {e}")

try:
    from game_ui import GameMainUI
    HAS_GAME = True
except ImportError as e:
    HAS_GAME = False
    print(f"⚠️ game_ui 模块未找到: {e}")

try:
    from creation_ui import CreationEditor
    HAS_CREATION = True
except ImportError as e:
    HAS_CREATION = False
    print(f"⚠️ creation_ui 模块未找到: {e}")


def integrate(app):
    """
    将新功能集成到 PoetryApp 实例中。
    调用方式：在 PoetryApp.__init__ 末尾调用 integrate(self)
    """
    c = app.colors

    # ── 在底部操作栏添加新功能按钮 ──
    if hasattr(app, "footer_frame"):
        # 分隔符
        sep = ttk.Separator(app.footer_frame, orient="vertical")
        sep.pack(side="left", fill="y", padx=8, pady=2)

        if HAS_LEARNING:
            tk.Button(app.footer_frame, text="📚 学习",
                      font=("微软雅黑", 10), bg=c["accent"], fg="#ffffff",
                      relief="flat", padx=10, pady=3,
                      command=lambda: LearningMainUI(app.root, c, app.db).show()
                      ).pack(side="left", padx=3)

        if HAS_GAME:
            tk.Button(app.footer_frame, text="🎮 游戏",
                      font=("微软雅黑", 10), bg=c["warning"], fg="#000000",
                      relief="flat", padx=10, pady=3,
                      command=lambda: GameMainUI(app.root, c, app.db).show()
                      ).pack(side="left", padx=3)

        if HAS_CREATION:
            tk.Button(app.footer_frame, text="✍️ 创作",
                      font=("微软雅黑", 10), bg=c["success"], fg="#ffffff",
                      relief="flat", padx=10, pady=3,
                      command=lambda: CreationEditor(app.root, c, app.db).show()
                      ).pack(side="left", padx=3)

    # ── 添加菜单栏（如果还没有） ──
    _add_menubar(app)


def _add_menubar(app):
    """添加菜单栏，包含所有功能入口"""
    c = app.colors

    # 检查是否已有菜单栏
    existing_menu = app.root.nametowidget(app.root["menu"]) if app.root["menu"] else None
    if existing_menu:
        return

    menubar = tk.Menu(app.root, bg=c["bg_secondary"], fg=c["fg"],
                       activebackground=c["accent"], activeforeground="#ffffff",
                       relief="flat")

    # 文件菜单
    file_menu = tk.Menu(menubar, tearoff=0, bg=c["bg_secondary"], fg=c["fg"],
                         activebackground=c["accent"], activeforeground="#ffffff")
    file_menu.add_command(label="📤 导出收藏", command=app._export_favorites)
    file_menu.add_separator()
    file_menu.add_command(label="❌ 退出", command=app.root.quit)
    menubar.add_cascade(label="📁 文件", menu=file_menu)

    # 查看菜单
    view_menu = tk.Menu(menubar, tearoff=0, bg=c["bg_secondary"], fg=c["fg"],
                         activebackground=c["accent"], activeforeground="#ffffff")
    view_menu.add_command(label="⭐ 收藏夹", command=app._show_favorites)
    view_menu.add_command(label="🕐 历史记录", command=app._show_history)
    view_menu.add_command(label="📊 诗词统计", command=app._show_stats)
    view_menu.add_separator()
    view_menu.add_command(label="🌙/☀️ 切换主题", command=app._toggle_theme)
    menubar.add_cascade(label="👁️ 查看", menu=view_menu)

    # 学习菜单
    if HAS_LEARNING:
        learn_menu = tk.Menu(menubar, tearoff=0, bg=c["bg_secondary"], fg=c["fg"],
                              activebackground=c["accent"], activeforeground="#ffffff")
        learn_menu.add_command(label="📚 学习模式",
                               command=lambda: LearningMainUI(app.root, c, app.db).show())
        menubar.add_cascade(label="📚 学习", menu=learn_menu)

    # 游戏菜单
    if HAS_GAME:
        game_menu = tk.Menu(menubar, tearoff=0, bg=c["bg_secondary"], fg=c["fg"],
                             activebackground=c["accent"], activeforeground="#ffffff")
        game_menu.add_command(label="🎮 游戏中心",
                              command=lambda: GameMainUI(app.root, c, app.db).show())
        menubar.add_cascade(label="🎮 游戏", menu=game_menu)

    # 创作菜单
    if HAS_CREATION:
        create_menu = tk.Menu(menubar, tearoff=0, bg=c["bg_secondary"], fg=c["fg"],
                               activebackground=c["accent"], activeforeground="#ffffff")
        create_menu.add_command(label="✍️ 创作编辑器",
                                command=lambda: CreationEditor(app.root, c, app.db).show())
        menubar.add_cascade(label="✍️ 创作", menu=create_menu)

    # 帮助菜单
    help_menu = tk.Menu(menubar, tearoff=0, bg=c["bg_secondary"], fg=c["fg"],
                         activebackground=c["accent"], activeforeground="#ffffff")
    help_menu.add_command(label="ℹ️ 关于", command=lambda: _show_about(app))
    menubar.add_cascade(label="❓ 帮助", menu=help_menu)

    app.root.config(menu=menubar)


def _show_about(app):
    """显示关于对话框"""
    from tkinter import messagebox
    messagebox.showinfo(
        "关于",
        "📜 古诗词桌面小工具 v3.0\n\n"
        "功能：\n"
        "  • 随机诗词 / 搜索 / 收藏 / 历史\n"
        "  • 📚 学习模式（计划 / 进度 / 错题本 / 测验）\n"
        "  • 🎮 游戏模式（接龙 / 飞花令 / 知识竞赛）\n"
        "  • ✍️ 创作辅助（编辑器 / 格律检查 / 模板）\n\n"
        "基于 chinese-poetry 开源数据",
        parent=app.root
    )


# ── 独立运行入口 ──────────────────────────────────────────────────────────────

def main():
    """
    独立运行入口：先启动原版主程序，再自动注入新功能。
    用法：python integration.py
    """
    try:
        from poetry_desktop_v2 import PoetryApp
    except ImportError:
        print("❌ 无法导入 poetry_desktop_v2，请确保在同一目录下运行")
        sys.exit(1)

    root = tk.Tk()
    app = PoetryApp(root)

    # 等待主窗口初始化完成后再注入
    root.after(500, lambda: integrate(app))

    root.mainloop()


if __name__ == "__main__":
    main()
