#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏界面模块
功能：诗词接龙、飞花令、知识竞赛、排行榜、成就系统
依赖：tkinter, poetry_desktop_v2.THEMES
"""

import json
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 排行榜 / 成就数据文件（优先 data 目录，与 exe 共享；兼容旧位置）
try:
    from app_paths import get_data_dir as _get_data_dir
    SCORE_FILE = _get_data_dir() / "game_scores.json"
    ACHIEVEMENT_FILE = _get_data_dir() / "achievements.json"
except Exception:
    SCORE_FILE = Path(__file__).parent / "game_scores.json"
    ACHIEVEMENT_FILE = Path(__file__).parent / "achievements.json"
_LEGACY_SCORE_FILE = Path(__file__).parent / "game_scores.json"
_LEGACY_ACHIEVEMENT_FILE = Path(__file__).parent / "achievements.json"


# ── 排行榜数据管理 ────────────────────────────────────────────────────────────

class ScoreManager:
    """排行榜数据管理"""

    def __init__(self):
        self.scores = {"chain": [], "feihua": [], "quiz": []}
        self._load()

    def _load(self):
        for fp in (SCORE_FILE, _LEGACY_SCORE_FILE):
            if fp.exists():
                try:
                    with open(fp, encoding="utf-8") as f:
                        self.scores = json.load(f)
                    break
                except Exception:
                    continue

    def save(self):
        try:
            with open(SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_score(self, game, name, score, detail=""):
        entry = {
            "name": name,
            "score": score,
            "detail": detail,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.scores.setdefault(game, [])
        self.scores[game].append(entry)
        self.scores[game].sort(key=lambda x: x["score"], reverse=True)
        self.scores[game] = self.scores[game][:50]  # 保留 top 50
        self.save()

    def get_top(self, game, limit=10):
        return self.scores.get(game, [])[:limit]


# ── 成就系统 ──────────────────────────────────────────────────────────────────

class AchievementManager:
    """成就系统"""

    DEFINITIONS = [
        {"id": "first_game", "name": "🎮 初次体验", "desc": "完成第一局游戏", "condition": "games_played >= 1"},
        {"id": "chain_5", "name": "🔗 接龙新手", "desc": "诗词接龙连续接 5 次", "condition": "chain_best >= 5"},
        {"id": "chain_10", "name": "🔗 接龙达人", "desc": "诗词接龙连续接 10 次", "condition": "chain_best >= 10"},
        {"id": "feihua_5", "name": "🌸 飞花初绽", "desc": "飞花令连续对 5 句", "condition": "feihua_best >= 5"},
        {"id": "feihua_10", "name": "🌸 飞花满天", "desc": "飞花令连续对 10 句", "condition": "feihua_best >= 10"},
        {"id": "quiz_perfect", "name": "🏆 满分学霸", "desc": "知识竞赛获得满分", "condition": "quiz_perfect >= 1"},
        {"id": "quiz_10", "name": "📚 答题高手", "desc": "累计答对 10 题", "condition": "quiz_correct >= 10"},
        {"id": "games_10", "name": "🎯 游戏常客", "desc": "累计游玩 10 次", "condition": "games_played >= 10"},
    ]

    def __init__(self):
        self.unlocked = set()
        self.stats = defaultdict(int)
        self._load()

    def _load(self):
        for fp in (ACHIEVEMENT_FILE, _LEGACY_ACHIEVEMENT_FILE):
            if fp.exists():
                try:
                    with open(fp, encoding="utf-8") as f:
                        data = json.load(f)
                    self.unlocked = set(data.get("unlocked", []))
                    self.stats = defaultdict(int, data.get("stats", {}))
                    break
                except Exception:
                    continue

    def save(self):
        data = {"unlocked": list(self.unlocked), "stats": dict(self.stats)}
        try:
            with open(ACHIEVEMENT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def update_stat(self, key, value):
        self.stats[key] = max(self.stats[key], value)
        self.save()

    def increment_stat(self, key, amount=1):
        self.stats[key] += amount
        self.save()

    def check_unlocks(self):
        """检查是否有新成就解锁，返回新解锁列表"""
        newly = []
        for defn in self.DEFINITIONS:
            if defn["id"] in self.unlocked:
                continue
            if eval(defn["condition"], {"__builtins__": {}}, dict(self.stats)):
                self.unlocked.add(defn["id"])
                newly.append(defn)
        if newly:
            self.save()
        return newly

    def get_all(self):
        """返回所有成就及解锁状态"""
        result = []
        for defn in self.DEFINITIONS:
            d = dict(defn)
            d["achieved"] = defn["id"] in self.unlocked
            result.append(d)
        return result


# ── 诗词接龙界面 ──────────────────────────────────────────────────────────────

class ChainGameUI:
    """诗词接龙：上一句末字 = 下一句首字"""

    def __init__(self, parent, colors, db, score_mgr, ach_mgr):
        self.colors = colors
        self.db = db
        self.score_mgr = score_mgr
        self.ach_mgr = ach_mgr
        self.chain = []           # 接龙链
        self.used_ids = set()     # 已用诗词
        self.game_over = False

        self.win = tk.Toplevel(parent)
        self.win.title("🔗 诗词接龙")
        self.win.geometry("600x580")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors

        # 标题
        tk.Label(self.win, text="🔗 诗词接龙", font=("微软雅黑", 16, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(12, 4))
        tk.Label(self.win, text="规则：下一句的第一个字需与上一句的最后一个字相同",
                 font=("微软雅黑", 9), fg=c["fg_secondary"], bg=c["bg"]).pack()

        # 得分
        self.score_label = tk.Label(self.win, text="当前接龙：0 次",
                                     font=("微软雅黑", 12, "bold"), fg=c["success"], bg=c["bg"])
        self.score_label.pack(pady=6)

        # 接龙显示区
        self.chain_text = tk.Text(self.win, font=("微软雅黑", 11), bg=c["bg_secondary"],
                                   fg=c["fg"], relief="flat", wrap="word", height=12,
                                   padx=12, pady=8, state="disabled",
                                   highlightbackground=c["border"], highlightthickness=1)
        self.chain_text.pack(fill="both", expand=True, padx=16, pady=8)

        # 提示
        self.hint_label = tk.Label(self.win, font=("微软雅黑", 11),
                                    fg=c["warning"], bg=c["bg"])
        self.hint_label.pack(pady=4)

        # 输入区
        input_frame = tk.Frame(self.win, bg=c["bg"])
        input_frame.pack(fill="x", padx=16, pady=(4, 10))

        tk.Button(input_frame, text="🎲 随机开始", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=12, pady=4,
                  command=self._start).pack(side="left", padx=4)

        tk.Button(input_frame, text="🤖 AI 接一句", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=self._ai_play).pack(side="left", padx=4)

        tk.Button(input_frame, text="🏳️ 认输", font=("微软雅黑", 10),
                  bg=c["error"], fg="#ffffff", relief="flat", padx=12, pady=4,
                  command=self._give_up).pack(side="right", padx=4)

    def _append_chain(self, text, tag=None):
        self.chain_text.config(state="normal")
        if tag:
            self.chain_text.insert("end", text + "\n", tag)
            self.chain_text.tag_configure(tag, foreground=self.colors["accent"],
                                           font=("微软雅黑", 11, "bold"))
        else:
            self.chain_text.insert("end", text + "\n")
        self.chain_text.see("end")
        self.chain_text.config(state="disabled")

    def _start(self):
        self.chain.clear()
        self.used_ids.clear()
        self.game_over = False
        self.chain_text.config(state="normal")
        self.chain_text.delete("1.0", "end")
        self.chain_text.config(state="disabled")

        poem = self.db.random_one()
        if not poem:
            return
        self._add_poem(poem, is_player=False)

    def _add_poem(self, poem, is_player=True):
        content = poem.get("content", "")
        if isinstance(content, list):
            content = "\n".join(content)
        title = poem.get("title", "未知")
        author = poem.get("author", "未知")
        first_line = content.split("\n")[0] if content else ""

        self.chain.append({"poem": poem, "first_line": first_line})
        self.used_ids.add(id(poem))

        prefix = "🧑 你：" if is_player else "🤖 起始："
        self._append_chain(f"{prefix}《{title}》 {author}")
        self._append_chain(f"   {first_line}")
        self._append_chain("")

        self.score_label.config(text=f"当前接龙：{len(self.chain)} 次")

        # 更新提示：需要的首字
        last_char = self._get_last_char(first_line)
        if last_char:
            self.hint_label.config(text=f"➡️ 下一句需要以「{last_char}」开头")
        else:
            self.hint_label.config(text="")

    def _get_last_char(self, text):
        """获取一句诗最后一个有效汉字"""
        for ch in reversed(text):
            if "\u4e00" <= ch <= "\u9fff":
                return ch
        return ""

    def _ai_play(self):
        if self.game_over or not self.chain:
            messagebox.showinfo("提示", "请先点击「随机开始」", parent=self.win)
            return

        last_line = self.chain[-1]["first_line"]
        last_char = self._get_last_char(last_line)
        if not last_char:
            return

        # 搜索以该字开头的诗句
        candidates = []
        for poem in self.db.poems:
            if id(poem) in self.used_ids:
                continue
            content = poem.get("content", "")
            if isinstance(content, list):
                content = "\n".join(content)
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped and stripped[0] == last_char:
                    candidates.append((poem, stripped))
                    break

        if not candidates:
            self._append_chain("🤖 找不到接续的诗句，游戏结束！")
            self._end_game()
            return

        poem, line = random.choice(candidates)
        self._add_poem(poem, is_player=False)

    def _give_up(self):
        if not self.chain:
            return
        self._append_chain("🏳️ 你认输了！")
        self._end_game()

    def _end_game(self):
        self.game_over = True
        score = len(self.chain)
        self.score_mgr.add_score("chain", "玩家", score, f"接龙 {score} 次")
        self.ach_mgr.increment_stat("games_played")
        self.ach_mgr.update_stat("chain_best", max(self.ach_mgr.stats.get("chain_best", 0), score))
        newly = self.ach_mgr.check_unlocks()
        if newly:
            names = ", ".join(n["name"] for n in newly)
            messagebox.showinfo("🎉 成就解锁！", f"解锁了：{names}", parent=self.win)
        self.hint_label.config(text=f"🏁 最终成绩：接龙 {score} 次")


# ── 飞花令界面 ────────────────────────────────────────────────────────────────

class FeihuaGameUI:
    """飞花令：轮流说出含指定字的诗句"""

    def __init__(self, parent, colors, db, score_mgr, ach_mgr):
        self.colors = colors
        self.db = db
        self.score_mgr = score_mgr
        self.ach_mgr = ach_mgr
        self.target_char = ""
        self.round_num = 0
        self.used_poems = set()
        self.game_over = False

        self.win = tk.Toplevel(parent)
        self.win.title("🌸 飞花令")
        self.win.geometry("600x560")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors

        tk.Label(self.win, text="🌸 飞花令", font=("微软雅黑", 16, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(12, 4))
        tk.Label(self.win, text="规则：轮流说出含指定字的诗句，接不上者输",
                 font=("微软雅黑", 9), fg=c["fg_secondary"], bg=c["bg"]).pack()

        # 选字区
        char_frame = tk.Frame(self.win, bg=c["bg"])
        char_frame.pack(fill="x", padx=16, pady=8)

        tk.Label(char_frame, text="选择飞花字：", font=("微软雅黑", 11),
                 fg=c["fg"], bg=c["bg"]).pack(side="left")

        common_chars = "春花月风雨山河雪夜秋红青云梦"
        for ch in common_chars:
            tk.Button(char_frame, text=ch, font=("微软雅黑", 11),
                      bg=c["bg_tertiary"], fg=c["fg"], relief="flat",
                      width=2, pady=2,
                      command=lambda cc=ch: self._set_char(cc)).pack(side="left", padx=1)

        # 当前字
        self.char_label = tk.Label(self.win, font=("微软雅黑", 20, "bold"),
                                    fg=c["warning"], bg=c["bg"])
        self.char_label.pack(pady=6)

        self.score_label = tk.Label(self.win, text="回合：0",
                                     font=("微软雅黑", 11), fg=c["success"], bg=c["bg"])
        self.score_label.pack()

        # 对话区
        self.chat_text = tk.Text(self.win, font=("微软雅黑", 11), bg=c["bg_secondary"],
                                  fg=c["fg"], relief="flat", wrap="word", height=10,
                                  padx=12, pady=8, state="disabled",
                                  highlightbackground=c["border"], highlightthickness=1)
        self.chat_text.pack(fill="both", expand=True, padx=16, pady=8)

        # 按钮
        btn_frame = tk.Frame(self.win, bg=c["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(4, 10))

        tk.Button(btn_frame, text="🤖 AI 对一句", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=12, pady=4,
                  command=self._ai_turn).pack(side="left", padx=4)

        tk.Button(btn_frame, text="🏳️ 认输", font=("微软雅黑", 10),
                  bg=c["error"], fg="#ffffff", relief="flat", padx=12, pady=4,
                  command=self._give_up).pack(side="right", padx=4)

    def _set_char(self, ch):
        self.target_char = ch
        self.round_num = 0
        self.used_poems.clear()
        self.game_over = False
        self.char_label.config(text=f"飞花字：「{ch}」")
        self.score_label.config(text="回合：0")
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.insert("end", f"🌸 飞花令开始！目标字：「{ch}」\n\n")
        self.chat_text.config(state="disabled")

    def _append_chat(self, text):
        self.chat_text.config(state="normal")
        self.chat_text.insert("end", text + "\n")
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def _ai_turn(self):
        if not self.target_char:
            messagebox.showinfo("提示", "请先选择一个飞花字", parent=self.win)
            return
        if self.game_over:
            return

        # 搜索含目标字的诗句
        candidates = []
        for poem in self.db.poems:
            if id(poem) in self.used_poems:
                continue
            content = poem.get("content", "")
            if isinstance(content, list):
                content = "\n".join(content)
            if self.target_char in content:
                candidates.append(poem)

        if not candidates:
            self._append_chat("🤖 找不到更多含该字的诗句，AI 认输！你赢了！")
            self._end_game(player_won=True)
            return

        poem = random.choice(candidates)
        self.used_poems.add(id(poem))
        self.round_num += 1
        self.score_label.config(text=f"回合：{self.round_num}")

        content = poem.get("content", "")
        if isinstance(content, list):
            content = "\n".join(content)
        first_line = content.split("\n")[0]
        self._append_chat(f"🤖：《{poem.get('title', '')}》{poem.get('author', '')}")
        self._append_chat(f"   {first_line}\n")

    def _give_up(self):
        if not self.target_char:
            return
        self._append_chat("🏳️ 你认输了！")
        self._end_game(player_won=False)

    def _end_game(self, player_won):
        self.game_over = True
        score = self.round_num
        self.score_mgr.add_score("feihua", "玩家", score, f"飞花「{self.target_char}」{score} 回合")
        self.ach_mgr.increment_stat("games_played")
        self.ach_mgr.update_stat("feihua_best",
                                  max(self.ach_mgr.stats.get("feihua_best", 0), score))
        newly = self.ach_mgr.check_unlocks()
        if newly:
            names = ", ".join(n["name"] for n in newly)
            messagebox.showinfo("🎉 成就解锁！", f"解锁了：{names}", parent=self.win)


# ── 知识竞赛界面 ──────────────────────────────────────────────────────────────

class QuizGameUI:
    """知识竞赛：多轮问答"""

    def __init__(self, parent, colors, db, score_mgr, ach_mgr):
        self.colors = colors
        self.db = db
        self.score_mgr = score_mgr
        self.ach_mgr = ach_mgr
        self.score = 0
        self.total = 0
        self.max_q = 10
        self.answered = False

        self.win = tk.Toplevel(parent)
        self.win.title("🏆 知识竞赛")
        self.win.geometry("540x520")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._next()

    def _next(self):
        c = self.colors
        for w in self.win.winfo_children():
            w.destroy()

        if self.total >= self.max_q:
            self._result()
            return

        self.total += 1
        self.answered = False

        # 随机题型
        qtype = random.choice(["title", "author", "next_line"])
        correct = self.db.random_one()
        if not correct:
            return
        self._correct = correct

        content = correct.get("content", "")
        if isinstance(content, list):
            content = "\n".join(content)
        lines = [l.strip() for l in content.split("\n") if l.strip()]

        if qtype == "title":
            question = f"以下诗句出自哪首诗？\n\n「{lines[0] if lines else ''}」"
            answer = correct.get("title", "")
            options = self._make_options("title", answer)
        elif qtype == "author":
            question = f"「{correct.get('title', '')}」的作者是谁？"
            answer = correct.get("author", "")
            options = self._make_options("author", answer)
        else:
            if len(lines) < 2:
                question = f"这句诗的作者是？\n\n「{lines[0] if lines else ''}」"
                answer = correct.get("author", "")
                options = self._make_options("author", answer)
            else:
                question = f"「{lines[0]}」的下一句是？"
                answer = lines[1]
                opts = [answer]
                random.shuffle(self.db.poems)
                for p in self.db.poems:
                    c2 = p.get("content", "")
                    if isinstance(c2, list):
                        c2 = "\n".join(c2)
                    for l in c2.split("\n"):
                        l = l.strip()
                        if l and l != answer and l not in opts:
                            opts.append(l)
                        if len(opts) >= 4:
                            break
                    if len(opts) >= 4:
                        break
                options = opts[:4]
                random.shuffle(options)

        self._answer_key = answer

        # 题号
        header = tk.Frame(self.win, bg=c["bg"])
        header.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(header, text=f"第 {self.total}/{self.max_q} 题",
                 font=("微软雅黑", 11), fg=c["fg_secondary"], bg=c["bg"]).pack(side="left")
        tk.Label(header, text=f"得分: {self.score}",
                 font=("微软雅黑", 11, "bold"), fg=c["success"], bg=c["bg"]).pack(side="right")

        # 问题
        tk.Label(self.win, text=question, font=("微软雅黑", 12),
                 fg=c["fg"], bg=c["bg"], wraplength=480, justify="center").pack(pady=12)

        # 选项
        opt_frame = tk.Frame(self.win, bg=c["bg"])
        opt_frame.pack(fill="x", padx=24, pady=8)

        self.feedback = tk.Label(self.win, font=("微软雅黑", 11, "bold"),
                                  fg=c["fg"], bg=c["bg"])
        self.feedback.pack(pady=6)

        for opt in options:
            tk.Button(opt_frame, text=opt, font=("微软雅黑", 11),
                      bg=c["button_bg"], fg=c["button_fg"], relief="flat",
                      padx=12, pady=6, anchor="w", wraplength=440,
                      command=lambda o=opt: self._check(o)).pack(fill="x", pady=3)

    def _make_options(self, field, answer):
        opts = [answer]
        random.shuffle(self.db.poems)
        for p in self.db.poems:
            v = p.get(field, "")
            if v and v not in opts:
                opts.append(v)
            if len(opts) >= 4:
                break
        random.shuffle(opts)
        return opts[:4]

    def _check(self, chosen):
        if self.answered:
            return
        self.answered = True
        c = self.colors
        if chosen == self._answer_key:
            self.score += 1
            self.feedback.config(text="✅ 正确！", fg=c["success"])
        else:
            self.feedback.config(text=f"❌ 正确答案：{self._answer_key}", fg=c["error"])
        self.win.after(1000, self._next)

    def _result(self):
        c = self.colors
        pct = int(self.score / self.max_q * 100)
        emoji = "🏆" if pct >= 80 else "👍" if pct >= 60 else "💪"

        self.score_mgr.add_score("quiz", "玩家", self.score, f"{self.score}/{self.max_q}")
        self.ach_mgr.increment_stat("games_played")
        self.ach_mgr.increment_stat("quiz_correct", self.score)
        if self.score == self.max_q:
            self.ach_mgr.increment_stat("quiz_perfect")
        newly = self.ach_mgr.check_unlocks()

        tk.Label(self.win, text=f"{emoji} 竞赛结束！", font=("微软雅黑", 16, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(50, 10))
        tk.Label(self.win, text=f"得分：{self.score}/{self.max_q}（{pct}%）",
                 font=("微软雅黑", 14), fg=c["fg"], bg=c["bg"]).pack(pady=8)

        if newly:
            names = ", ".join(n["name"] for n in newly)
            tk.Label(self.win, text=f"🎉 解锁成就：{names}", font=("微软雅黑", 10),
                     fg=c["warning"], bg=c["bg"]).pack(pady=4)

        tk.Button(self.win, text="🔄 再来一轮", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=20, pady=6,
                  command=self._restart).pack(pady=16)

    def _restart(self):
        self.score = 0
        self.total = 0
        self._next()


# ── 排行榜界面 ────────────────────────────────────────────────────────────────

class LeaderboardUI:
    """排行榜界面"""

    def __init__(self, parent, colors, score_mgr):
        self.colors = colors
        self.score_mgr = score_mgr
        self.win = tk.Toplevel(parent)
        self.win.title("🏅 排行榜")
        self.win.geometry("520x480")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors

        tk.Label(self.win, text="🏅 排行榜", font=("微软雅黑", 14, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(12, 6))

        # Tab 选择
        tab_frame = tk.Frame(self.win, bg=c["bg"])
        tab_frame.pack(fill="x", padx=16, pady=4)

        self.tab_var = tk.StringVar(value="chain")
        games = [("🔗 接龙", "chain"), ("🌸 飞花", "feihua"), ("🏆 竞赛", "quiz")]
        for label, key in games:
            tk.Radiobutton(tab_frame, text=label, variable=self.tab_var, value=key,
                            font=("微软雅黑", 10), bg=c["bg"], fg=c["fg"],
                            selectcolor=c["bg_tertiary"], activebackground=c["bg"],
                            command=self._refresh).pack(side="left", padx=8)

        # 列表
        style = ttk.Style()
        style.configure("LB.Treeview", font=("微软雅黑", 10), rowheight=28,
                        background=c["bg_secondary"], foreground=c["fg"],
                        fieldbackground=c["bg_secondary"])

        cols = ("rank", "name", "score", "detail", "time")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings",
                                  style="LB.Treeview", height=14)
        self.tree.heading("rank", text="#")
        self.tree.heading("name", text="名字")
        self.tree.heading("score", text="得分")
        self.tree.heading("detail", text="详情")
        self.tree.heading("time", text="时间")
        self.tree.column("rank", width=40, anchor="center")
        self.tree.column("name", width=80)
        self.tree.column("score", width=60, anchor="center")
        self.tree.column("detail", width=160)
        self.tree.column("time", width=120)

        scrollbar = ttk.Scrollbar(self.win, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0, 16))

        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        game = self.tab_var.get()
        top = self.score_mgr.get_top(game, 20)
        for i, entry in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
            self.tree.insert("", "end",
                             values=(medal, entry["name"], entry["score"],
                                     entry.get("detail", ""), entry.get("time", "")))


# ── 成就系统界面 ──────────────────────────────────────────────────────────────

class AchievementUI:
    """成就系统界面"""

    def __init__(self, parent, colors, ach_mgr):
        self.colors = colors
        self.ach_mgr = ach_mgr
        self.win = tk.Toplevel(parent)
        self.win.title("🏅 成就系统")
        self.win.geometry("480x460")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors
        achs = self.ach_mgr.get_all()
        unlocked = sum(1 for a in achs if a["achieved"])

        tk.Label(self.win, text=f"🏅 成就系统（{unlocked}/{len(achs)}）",
                 font=("微软雅黑", 14, "bold"), fg=c["accent"], bg=c["bg"]).pack(pady=(12, 8))

        # 进度条
        style = ttk.Style()
        style.configure("Ach.Horizontal.TProgressbar", troughcolor=c["bg_tertiary"],
                        background=c["success"], thickness=12)
        progress = ttk.Progressbar(self.win, maximum=len(achs), value=unlocked,
                                   style="Ach.Horizontal.TProgressbar", length=400)
        progress.pack(fill="x", padx=20, pady=6)

        # 成就列表（可滚动）
        list_frame = tk.Frame(self.win, bg=c["bg"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=8)

        canvas = tk.Canvas(list_frame, bg=c["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=c["bg"])

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for ach in achs:
            card_bg = c["bg_secondary"] if ach["achieved"] else c["bg_tertiary"]
            fg = c["fg"] if ach["achieved"] else c["fg_secondary"]
            card = tk.Frame(inner, bg=card_bg, highlightbackground=c["border"],
                            highlightthickness=1)
            card.pack(fill="x", pady=3, padx=4)

            status = "✅" if ach["achieved"] else "🔒"
            tk.Label(card, text=f"{status} {ach['name']}", font=("微软雅黑", 11, "bold"),
                     fg=fg, bg=card_bg).pack(anchor="w", padx=12, pady=(6, 0))
            tk.Label(card, text=ach["desc"], font=("微软雅黑", 9),
                     fg=c["fg_secondary"], bg=card_bg).pack(anchor="w", padx=24, pady=(0, 6))


# ── 游戏主入口 ────────────────────────────────────────────────────────────────

class GameMainUI:
    """游戏模式主入口"""

    def __init__(self, parent, colors, db):
        self.parent = parent
        self.colors = colors
        self.db = db
        self.score_mgr = ScoreManager()
        self.ach_mgr = AchievementManager()

    def show(self):
        c = self.colors
        win = tk.Toplevel(self.parent)
        win.title("🎮 诗词游戏")
        win.geometry("460x420")
        win.configure(bg=c["bg"])
        win.transient(self.parent)

        tk.Label(win, text="🎮 诗词游戏", font=("微软雅黑", 18, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(20, 6))

        tk.Label(win, text="在游戏中学习诗词，寓教于乐",
                 font=("微软雅黑", 10), fg=c["fg_secondary"], bg=c["bg"]).pack(pady=(0, 16))

        # 游戏入口卡片
        games = [
            ("🔗 诗词接龙", "接龙挑战：上下句首尾相接", lambda: ChainGameUI(self.parent, c, self.db, self.score_mgr, self.ach_mgr)),
            ("🌸 飞花令", "含指定字的诗句对决", lambda: FeihuaGameUI(self.parent, c, self.db, self.score_mgr, self.ach_mgr)),
            ("🏆 知识竞赛", "诗词知识问答挑战", lambda: QuizGameUI(self.parent, c, self.db, self.score_mgr, self.ach_mgr)),
        ]

        for title, desc, cmd in games:
            card = tk.Frame(win, bg=c["bg_secondary"], cursor="hand2",
                            highlightbackground=c["border"], highlightthickness=1)
            card.pack(fill="x", padx=24, pady=4)

            tk.Label(card, text=title, font=("微软雅黑", 13, "bold"),
                     fg=c["accent"], bg=c["bg_secondary"]).pack(anchor="w", padx=16, pady=(10, 0))
            tk.Label(card, text=desc, font=("微软雅黑", 9),
                     fg=c["fg_secondary"], bg=c["bg_secondary"]).pack(anchor="w", padx=16, pady=(0, 10))

            card.bind("<Button-1>", lambda e, c=cmd: c())
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, c=cmd: c())

        # 底部按钮
        bottom = tk.Frame(win, bg=c["bg"])
        bottom.pack(fill="x", padx=24, pady=(12, 16))

        tk.Button(bottom, text="🏅 排行榜", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=lambda: LeaderboardUI(self.parent, c, self.score_mgr)).pack(side="left", padx=4)

        tk.Button(bottom, text="🎖️ 成就", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=12, pady=4,
                  command=lambda: AchievementUI(self.parent, c, self.ach_mgr)).pack(side="left", padx=4)
