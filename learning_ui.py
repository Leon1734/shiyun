#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习模式界面模块
功能：学习主界面、学习计划设置、学习进度显示、错题本界面、学习统计
依赖：tkinter, poetry_desktop_v2.THEMES
"""

import json
import random
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# 数据文件路径（优先 data 目录，与 exe 共享；兼容旧位置）
try:
    from app_paths import get_data_dir as _get_data_dir
    DATA_FILE = _get_data_dir() / "learning_data.json"
except Exception:
    DATA_FILE = Path(__file__).parent / "learning_data.json"
_LEGACY_DATA_FILE = Path(__file__).parent / "learning_data.json"


class LearningData:
    """学习数据持久化管理"""

    def __init__(self):
        self.daily_goal = 5           # 每日学习目标（首）
        self.learned_poems = []       # 已学诗词列表 [{poem_id, title, author, learned_at, quiz_correct, quiz_wrong}]
        self.wrong_book = []          # 错题本 [{poem_id, title, author, content, wrong_count, last_wrong}]
        self.daily_log = {}           # 每日学习记录 {"2026-09-20": count}
        self._load()

    def _load(self):
        for fp in (DATA_FILE, _LEGACY_DATA_FILE):
            if fp.exists():
                try:
                    with open(fp, encoding="utf-8") as f:
                        data = json.load(f)
                    self.daily_goal = data.get("daily_goal", 5)
                    self.learned_poems = data.get("learned_poems", [])
                    self.wrong_book = data.get("wrong_book", [])
                    self.daily_log = data.get("daily_log", {})
                    break
                except Exception:
                    continue

    def save(self):
        data = {
            "daily_goal": self.daily_goal,
            "learned_poems": self.learned_poems,
            "wrong_book": self.wrong_book,
            "daily_log": self.daily_log,
        }
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存学习数据失败: {e}")

    def record_learn(self, poem):
        """记录学习了一首诗"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_log[today] = self.daily_log.get(today, 0) + 1
        pid = id(poem)  # 简易 id
        entry = {
            "poem_id": pid,
            "title": poem.get("title", ""),
            "author": poem.get("author", ""),
            "dynasty": poem.get("dynasty", ""),
            "learned_at": today,
            "quiz_correct": 0,
            "quiz_wrong": 0,
        }
        self.learned_poems.append(entry)
        self.save()

    def record_wrong(self, poem):
        """记录错题"""
        title = poem.get("title", "")
        existing = [w for w in self.wrong_book if w["title"] == title]
        if existing:
            existing[0]["wrong_count"] += 1
            existing[0]["last_wrong"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            content = poem.get("content", "")
            if isinstance(content, list):
                content = "\n".join(content)
            self.wrong_book.append({
                "poem_id": id(poem),
                "title": title,
                "author": poem.get("author", ""),
                "dynasty": poem.get("dynasty", ""),
                "content": content,
                "wrong_count": 1,
                "last_wrong": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        self.save()

    def remove_wrong(self, index):
        """从错题本移除"""
        if 0 <= index < len(self.wrong_book):
            self.wrong_book.pop(index)
            self.save()

    def get_today_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_log.get(today, 0)

    def get_streak(self):
        """计算连续学习天数"""
        streak = 0
        day = datetime.now()
        while True:
            key = day.strftime("%Y-%m-%d")
            if self.daily_log.get(key, 0) > 0:
                streak += 1
                day -= timedelta(days=1)
            else:
                break
        return streak

    def get_total_learned(self):
        return len(self.learned_poems)

    def get_weekly_stats(self):
        """获取最近 7 天的学习数据"""
        stats = []
        for i in range(6, -1, -1):
            day = datetime.now() - timedelta(days=i)
            key = day.strftime("%Y-%m-%d")
            count = self.daily_log.get(key, 0)
            stats.append((day.strftime("%m/%d"), count))
        return stats


# ── 学习主界面 ────────────────────────────────────────────────────────────────

class LearningMainUI:
    """学习模式主界面"""

    def __init__(self, parent, colors, db):
        self.parent = parent
        self.colors = colors
        self.db = db
        self.learn_data = LearningData()
        self.current_poem = None
        self.win = None

    def show(self):
        c = self.colors
        self.win = tk.Toplevel(self.parent)
        self.win.title("📚 学习模式")
        self.win.geometry("700x650")
        self.win.configure(bg=c["bg"])
        self.win.transient(self.parent)

        # ── 顶部状态栏 ──
        status_frame = tk.Frame(self.win, bg=c["bg_secondary"],
                                highlightbackground=c["border"], highlightthickness=1)
        status_frame.pack(fill="x", padx=12, pady=(10, 6))

        today_count = self.learn_data.get_today_count()
        streak = self.learn_data.get_streak()
        total = self.learn_data.get_total_learned()
        goal = self.learn_data.daily_goal

        tk.Label(status_frame, text=f"📅 今日已学 {today_count}/{goal} 首",
                 font=("微软雅黑", 12, "bold"), fg=c["accent"], bg=c["bg_secondary"]
                 ).pack(side="left", padx=16, pady=10)

        tk.Label(status_frame, text=f"🔥 连续 {streak} 天",
                 font=("微软雅黑", 11), fg=c["warning"], bg=c["bg_secondary"]
                 ).pack(side="left", padx=16)

        tk.Label(status_frame, text=f"📊 累计 {total} 首",
                 font=("微软雅黑", 11), fg=c["fg_secondary"], bg=c["bg_secondary"]
                 ).pack(side="left", padx=16)

        # ── 进度条 ──
        progress_frame = tk.Frame(self.win, bg=c["bg"])
        progress_frame.pack(fill="x", padx=12, pady=4)

        style = ttk.Style()
        style.configure("Learn.Horizontal.TProgressbar", troughcolor=c["bg_tertiary"],
                        background=c["accent"], thickness=18)
        progress = ttk.Progressbar(progress_frame, maximum=max(goal, 1), value=today_count,
                                   style="Learn.Horizontal.TProgressbar", length=400)
        progress.pack(fill="x", pady=4)

        # ── 学习区域 ──
        learn_frame = ttk.LabelFrame(self.win, text="📖 今日学习", padding=8)
        learn_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.poem_title = tk.Label(learn_frame, font=("微软雅黑", 15, "bold"),
                                    fg=c["accent"], bg=c["bg"])
        self.poem_title.pack(pady=(8, 2))

        self.poem_author = tk.Label(learn_frame, font=("微软雅黑", 10),
                                     fg=c["fg_secondary"], bg=c["bg"])
        self.poem_author.pack()

        self.poem_content = tk.Text(learn_frame, font=("微软雅黑", 13),
                                     bg=c["bg_secondary"], fg=c["fg"],
                                     relief="flat", wrap="word", spacing1=4, spacing3=4,
                                     padx=20, pady=8, height=8, state="disabled",
                                     selectbackground=c["select_bg"],
                                     highlightbackground=c["border"], highlightthickness=1)
        self.poem_content.pack(fill="both", expand=True, padx=8, pady=8)

        # ── 按钮区 ──
        btn_frame = tk.Frame(self.win, bg=c["bg"])
        btn_frame.pack(fill="x", padx=12, pady=(4, 10))

        tk.Button(btn_frame, text="🎲 随机学习", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=16, pady=6,
                  command=self._random_learn).pack(side="left", padx=4)

        tk.Button(btn_frame, text="✅ 已学会", font=("微软雅黑", 11),
                  bg=c["success"], fg="#ffffff", relief="flat", padx=16, pady=6,
                  command=self._mark_learned).pack(side="left", padx=4)

        tk.Button(btn_frame, text="❌ 未掌握", font=("微软雅黑", 11),
                  bg=c["error"], fg="#ffffff", relief="flat", padx=16, pady=6,
                  command=self._mark_wrong).pack(side="left", padx=4)

        tk.Button(btn_frame, text="📝 测验", font=("微软雅黑", 11),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=16, pady=6,
                  command=self._start_quiz).pack(side="right", padx=4)

        # ── 底部功能入口 ──
        bottom_frame = tk.Frame(self.win, bg=c["bg"])
        bottom_frame.pack(fill="x", padx=12, pady=(0, 10))

        tk.Button(bottom_frame, text="📋 错题本", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=self._open_wrong_book).pack(side="left", padx=4)

        tk.Button(bottom_frame, text="📊 学习统计", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=self._open_stats).pack(side="left", padx=4)

        tk.Button(bottom_frame, text="⚙️ 学习计划", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=self._open_plan).pack(side="left", padx=4)

    def _random_learn(self):
        if not self.db or not self.db.poems:
            messagebox.showinfo("提示", "诗词数据尚未加载", parent=self.win)
            return
        self.current_poem = self.db.random_one()
        self._display(self.current_poem)

    def _display(self, poem):
        c = self.colors
        self.poem_title.config(text=f"《{poem.get('title', '')}》")
        self.poem_author.config(text=f"· {poem.get('author', '')}（{poem.get('dynasty', '')}）")
        content = poem.get("content", "")
        if isinstance(content, list):
            content = "\n".join(content)
        self.poem_content.config(state="normal")
        self.poem_content.delete("1.0", "end")
        self.poem_content.insert("1.0", content)
        self.poem_content.config(state="disabled")

    def _mark_learned(self):
        if not self.current_poem:
            messagebox.showinfo("提示", "请先随机一首诗词", parent=self.win)
            return
        self.learn_data.record_learn(self.current_poem)
        messagebox.showinfo("✅", "已记录为已学会！", parent=self.win)
        self._random_learn()

    def _mark_wrong(self):
        if not self.current_poem:
            messagebox.showinfo("提示", "请先随机一首诗词", parent=self.win)
            return
        self.learn_data.record_wrong(self.current_poem)
        messagebox.showinfo("📝", "已加入错题本", parent=self.win)

    def _start_quiz(self):
        if not self.db or len(self.db.poems) < 4:
            messagebox.showinfo("提示", "诗词数据不足，无法测验", parent=self.win)
            return
        QuizWindow(self.parent, self.colors, self.db, self.learn_data)

    def _open_wrong_book(self):
        WrongBookUI(self.parent, self.colors, self.learn_data)

    def _open_stats(self):
        LearningStatsUI(self.parent, self.colors, self.learn_data)

    def _open_plan(self):
        LearningPlanUI(self.parent, self.colors, self.learn_data)


# ── 学习计划设置 ──────────────────────────────────────────────────────────────

class LearningPlanUI:
    """学习计划设置界面"""

    def __init__(self, parent, colors, learn_data):
        self.colors = colors
        self.learn_data = learn_data
        self.win = tk.Toplevel(parent)
        self.win.title("⚙️ 学习计划设置")
        self.win.geometry("400x320")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors
        ld = self.learn_data

        tk.Label(self.win, text="⚙️ 学习计划", font=("微软雅黑", 14, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(16, 12))

        # 每日目标
        goal_frame = tk.Frame(self.win, bg=c["bg"])
        goal_frame.pack(fill="x", padx=24, pady=8)

        tk.Label(goal_frame, text="🎯 每日学习目标（首）：", font=("微软雅黑", 11),
                 fg=c["fg"], bg=c["bg"]).pack(anchor="w")

        self.goal_var = tk.IntVar(value=ld.daily_goal)
        goal_spin = tk.Spinbox(goal_frame, from_=1, to=50, textvariable=self.goal_var,
                               font=("微软雅黑", 12), width=8,
                               bg=c["entry_bg"], fg=c["entry_fg"],
                               buttonbackground=c["bg_tertiary"])
        goal_spin.pack(anchor="w", pady=4)

        # 提示
        tk.Label(self.win, text="💡 建议每天学习 3~10 首，贵在坚持",
                 font=("微软雅黑", 9), fg=c["fg_secondary"], bg=c["bg"]).pack(pady=4)

        # 学习提醒
        remind_frame = tk.Frame(self.win, bg=c["bg_secondary"],
                                highlightbackground=c["border"], highlightthickness=1)
        remind_frame.pack(fill="x", padx=24, pady=12)

        streak = ld.get_streak()
        today = ld.get_today_count()
        tk.Label(remind_frame, text=f"🔥 当前连续学习 {streak} 天",
                 font=("微软雅黑", 11), fg=c["warning"], bg=c["bg_secondary"]).pack(pady=(10, 2))
        tk.Label(remind_frame, text=f"📅 今日已完成 {today}/{ld.daily_goal} 首",
                 font=("微软雅黑", 10), fg=c["fg"], bg=c["bg_secondary"]).pack(pady=(2, 10))

        # 保存按钮
        def save_plan():
            ld.daily_goal = self.goal_var.get()
            ld.save()
            messagebox.showinfo("✅", "学习计划已更新", parent=self.win)
            self.win.destroy()

        tk.Button(self.win, text="💾 保存设置", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=20, pady=6,
                  command=save_plan).pack(pady=12)


# ── 学习进度 / 统计界面 ──────────────────────────────────────────────────────

class LearningStatsUI:
    """学习统计界面"""

    def __init__(self, parent, colors, learn_data):
        self.colors = colors
        self.learn_data = learn_data
        self.win = tk.Toplevel(parent)
        self.win.title("📊 学习统计")
        self.win.geometry("500x520")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors
        ld = self.learn_data

        tk.Label(self.win, text="📊 学习统计", font=("微软雅黑", 14, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(14, 8))

        # 概览卡片
        overview = tk.Frame(self.win, bg=c["bg_secondary"],
                            highlightbackground=c["border"], highlightthickness=1)
        overview.pack(fill="x", padx=16, pady=6)

        row1 = tk.Frame(overview, bg=c["bg_secondary"])
        row1.pack(fill="x", padx=12, pady=(10, 4))

        stats_items = [
            ("📚 累计学习", f"{ld.get_total_learned()} 首"),
            ("📅 今日学习", f"{ld.get_today_count()} 首"),
            ("🔥 连续天数", f"{ld.get_streak()} 天"),
            ("❌ 错题数量", f"{len(ld.wrong_book)} 首"),
        ]
        for i, (label, value) in enumerate(stats_items):
            card = tk.Frame(row1, bg=c["bg_tertiary"], padx=12, pady=8)
            card.pack(side="left", expand=True, fill="both", padx=3)
            tk.Label(card, text=label, font=("微软雅黑", 9), fg=c["fg_secondary"],
                     bg=c["bg_tertiary"]).pack()
            tk.Label(card, text=value, font=("微软雅黑", 14, "bold"), fg=c["accent"],
                     bg=c["bg_tertiary"]).pack()

        # 最近 7 天柱状图（文本模拟）
        tk.Label(self.win, text="📈 最近 7 天学习量", font=("微软雅黑", 11, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(anchor="w", padx=20, pady=(14, 4))

        chart_frame = tk.Frame(self.win, bg=c["bg_secondary"],
                               highlightbackground=c["border"], highlightthickness=1)
        chart_frame.pack(fill="both", expand=True, padx=16, pady=6)

        weekly = ld.get_weekly_stats()
        max_count = max((cnt for _, cnt in weekly), default=1) or 1

        canvas = tk.Canvas(chart_frame, bg=c["bg_secondary"], highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=12, pady=8)

        def draw_chart(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 50 or h < 50:
                return
            bar_w = max((w - 80) // 7, 30)
            base_y = h - 30
            for i, (day_label, count) in enumerate(weekly):
                x = 40 + i * (bar_w + 8)
                bar_h = int((count / max_count) * (base_y - 40))
                bar_h = max(bar_h, 2) if count > 0 else 2
                color = c["accent"] if count > 0 else c["bg_tertiary"]
                canvas.create_rectangle(x, base_y - bar_h, x + bar_w, base_y, fill=color, outline="")
                canvas.create_text(x + bar_w // 2, base_y + 12, text=day_label,
                                   fill=c["fg_secondary"], font=("微软雅黑", 8))
                if count > 0:
                    canvas.create_text(x + bar_w // 2, base_y - bar_h - 10, text=str(count),
                                       fill=c["fg"], font=("微软雅黑", 8, "bold"))

        canvas.bind("<Configure>", draw_chart)


# ── 错题本界面 ────────────────────────────────────────────────────────────────

class WrongBookUI:
    """错题本界面"""

    def __init__(self, parent, colors, learn_data):
        self.colors = colors
        self.learn_data = learn_data
        self.win = tk.Toplevel(parent)
        self.win.title("📋 错题本")
        self.win.geometry("580x500")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors
        ld = self.learn_data

        # 标题栏
        header = tk.Frame(self.win, bg=c["bg"])
        header.pack(fill="x", padx=12, pady=(10, 4))

        self.count_label = tk.Label(header, text=f"📋 错题本（共 {len(ld.wrong_book)} 首）",
                                     font=("微软雅黑", 12, "bold"), fg=c["accent"], bg=c["bg"])
        self.count_label.pack(side="left")

        # 列表
        style = ttk.Style()
        style.configure("Wrong.Treeview", font=("微软雅黑", 10), rowheight=28,
                        background=c["bg_secondary"], foreground=c["fg"],
                        fieldbackground=c["bg_secondary"])

        cols = ("title", "author", "dynasty", "wrong_count", "last_wrong")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings",
                                  style="Wrong.Treeview", height=12)
        self.tree.heading("title", text="📜 标题")
        self.tree.heading("author", text="👤 作者")
        self.tree.heading("dynasty", text="🏛 朝代")
        self.tree.heading("wrong_count", text="❌ 错误次数")
        self.tree.heading("last_wrong", text="🕐 最近错误")
        self.tree.column("title", width=150)
        self.tree.column("author", width=80)
        self.tree.column("dynasty", width=50)
        self.tree.column("wrong_count", width=80, anchor="center")
        self.tree.column("last_wrong", width=140)

        scrollbar = ttk.Scrollbar(self.win, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=6)
        scrollbar.pack(side="right", fill="y", pady=6, padx=(0, 12))

        self._refresh()

        # 底部按钮
        btn_frame = tk.Frame(self.win, bg=c["bg"])
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        tk.Button(btn_frame, text="📖 查看详情", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=self._view_detail).pack(side="left", padx=4)

        tk.Button(btn_frame, text="✅ 移除（已掌握）", font=("微软雅黑", 10),
                  bg=c["success"], fg="#ffffff", relief="flat", padx=12, pady=4,
                  command=self._remove_selected).pack(side="left", padx=4)

        tk.Button(btn_frame, text="❌ 清空错题本", font=("微软雅黑", 10),
                  bg=c["error"], fg="#ffffff", relief="flat", padx=12, pady=4,
                  command=self._clear_all).pack(side="right", padx=4)

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, w in enumerate(self.learn_data.wrong_book):
            self.tree.insert("", "end", iid=str(i),
                             values=(w["title"], w["author"], w["dynasty"],
                                     w["wrong_count"], w["last_wrong"]))
        self.count_label.config(text=f"📋 错题本（共 {len(self.learn_data.wrong_book)} 首）")

    def _view_detail(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        w = self.learn_data.wrong_book[idx]
        c = self.colors
        detail = tk.Toplevel(self.win)
        detail.title(f"📖 {w['title']}")
        detail.geometry("420x350")
        detail.configure(bg=c["bg"])

        tk.Label(detail, text=f"《{w['title']}》", font=("微软雅黑", 14, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(12, 4))
        tk.Label(detail, text=f"· {w['author']}（{w['dynasty']}）",
                 font=("微软雅黑", 10), fg=c["fg_secondary"], bg=c["bg"]).pack()

        text = tk.Text(detail, font=("微软雅黑", 12), bg=c["bg_secondary"], fg=c["fg"],
                        relief="flat", wrap="word", padx=16, pady=10,
                        highlightbackground=c["border"], highlightthickness=1)
        text.pack(fill="both", expand=True, padx=16, pady=10)
        text.insert("1.0", w["content"])
        text.config(state="disabled")

    def _remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要移除的题目", parent=self.win)
            return
        for s in sorted([int(x) for x in sel], reverse=True):
            self.learn_data.remove_wrong(s)
        self._refresh()

    def _clear_all(self):
        if not self.learn_data.wrong_book:
            return
        if messagebox.askyesno("确认", "确定要清空错题本吗？", parent=self.win):
            self.learn_data.wrong_book.clear()
            self.learn_data.save()
            self._refresh()


# ── 测验窗口 ──────────────────────────────────────────────────────────────────

class QuizWindow:
    """诗词测验窗口 — 根据内容猜标题或作者"""

    def __init__(self, parent, colors, db, learn_data):
        self.colors = colors
        self.db = db
        self.learn_data = learn_data
        self.score = 0
        self.total = 0
        self.max_questions = 10

        self.win = tk.Toplevel(parent)
        self.win.title("📝 诗词测验")
        self.win.geometry("520x480")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._next_question()

    def _next_question(self):
        c = self.colors
        # 清空旧内容
        for w in self.win.winfo_children():
            w.destroy()

        if self.total >= self.max_questions:
            self._show_result()
            return

        # 随机选一首作为正确答案
        correct = self.db.random_one()
        if not correct:
            return
        self._correct_poem = correct
        self.total += 1

        # 生成 4 个选项（标题）
        options = [correct.get("title", "")]
        pool = [p for p in self.db.poems if p.get("title") != options[0]]
        random.shuffle(pool)
        for p in pool[:3]:
            t = p.get("title", "")
            if t not in options:
                options.append(t)
        while len(options) < 4:
            options.append(f"选项{len(options)+1}")
        random.shuffle(options)
        self._options = options

        # 题号 + 得分
        header = tk.Frame(self.win, bg=c["bg"])
        header.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(header, text=f"第 {self.total}/{self.max_questions} 题",
                 font=("微软雅黑", 11), fg=c["fg_secondary"], bg=c["bg"]).pack(side="left")
        tk.Label(header, text=f"得分: {self.score}",
                 font=("微软雅黑", 11, "bold"), fg=c["success"], bg=c["bg"]).pack(side="right")

        # 显示诗句内容
        tk.Label(self.win, text="这首诗的标题是什么？",
                 font=("微软雅黑", 12, "bold"), fg=c["accent"], bg=c["bg"]).pack(pady=(10, 6))

        content = correct.get("content", "")
        if isinstance(content, list):
            content = "\n".join(content)
        # 只显示前 4 句
        lines = content.split("\n")[:4]
        preview = "\n".join(lines)

        poem_frame = tk.Frame(self.win, bg=c["bg_secondary"],
                              highlightbackground=c["border"], highlightthickness=1)
        poem_frame.pack(fill="x", padx=24, pady=8)
        tk.Label(poem_frame, text=preview, font=("微软雅黑", 12),
                 fg=c["fg"], bg=c["bg_secondary"], justify="center", wraplength=440
                 ).pack(padx=16, pady=12)

        tk.Label(self.win, text=f"—— {correct.get('author', '')}（{correct.get('dynasty', '')}）",
                 font=("微软雅黑", 10), fg=c["fg_secondary"], bg=c["bg"]).pack()

        # 选项按钮
        options_frame = tk.Frame(self.win, bg=c["bg"])
        options_frame.pack(fill="x", padx=24, pady=12)

        self.feedback_label = tk.Label(self.win, font=("微软雅黑", 11, "bold"),
                                        fg=c["fg"], bg=c["bg"])
        self.feedback_label.pack(pady=4)

        self._answered = False
        for opt in self._options:
            btn = tk.Button(options_frame, text=opt, font=("微软雅黑", 11),
                            bg=c["button_bg"], fg=c["button_fg"], relief="flat",
                            padx=16, pady=6, anchor="w",
                            command=lambda o=opt: self._answer(o))
            btn.pack(fill="x", pady=3)

    def _answer(self, chosen):
        if self._answered:
            return
        self._answered = True
        c = self.colors
        correct_title = self._correct_poem.get("title", "")
        if chosen == correct_title:
            self.score += 1
            self.feedback_label.config(text="✅ 正确！", fg=c["success"])
        else:
            self.feedback_label.config(text=f"❌ 正确答案：{correct_title}", fg=c["error"])
            self.learn_data.record_wrong(self._correct_poem)

        self.win.after(1200, self._next_question)

    def _show_result(self):
        c = self.colors
        for w in self.win.winfo_children():
            w.destroy()

        pct = int(self.score / self.max_questions * 100)
        emoji = "🏆" if pct >= 80 else "👍" if pct >= 60 else "💪"

        tk.Label(self.win, text=f"{emoji} 测验完成！", font=("微软雅黑", 16, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(40, 10))
        tk.Label(self.win, text=f"得分：{self.score}/{self.max_questions}（{pct}%）",
                 font=("微软雅黑", 14), fg=c["fg"], bg=c["bg"]).pack(pady=8)

        if pct >= 80:
            msg = "非常优秀！继续保持！"
        elif pct >= 60:
            msg = "不错，再接再厉！"
        else:
            msg = "加油，多复习错题本！"
        tk.Label(self.win, text=msg, font=("微软雅黑", 11),
                 fg=c["fg_secondary"], bg=c["bg"]).pack(pady=4)

        tk.Button(self.win, text="🔄 再来一轮", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=20, pady=6,
                  command=lambda: self.__init__(self.win.master, c, self.db, self.learn_data)
                  ).pack(pady=16)

        tk.Button(self.win, text="关闭", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=16, pady=4,
                  command=self.win.destroy).pack()
