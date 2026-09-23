#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
界面美化模块
功能：动画效果、响应式布局、自定义主题
"""

import tkinter as tk
from tkinter import ttk
import logging

log = logging.getLogger("poetry")


class AnimationManager:
    """动画管理器"""
    
    def __init__(self, root):
        self.root = root
        self.animations = {}
    
    def fade_in(self, widget, duration=300, callback=None):
        """淡入动画"""
        try:
            # 获取初始透明度
            alpha = 0.0
            widget.attributes('-alpha', alpha)
            
            # 动画步数
            steps = 20
            step_time = duration // steps
            
            def animate(step):
                if step <= steps:
                    alpha = step / steps
                    try:
                        widget.attributes('-alpha', alpha)
                    except:
                        pass
                    self.root.after(step_time, animate, step + 1)
                elif callback:
                    callback()
            
            animate(0)
        except Exception as e:
            log.error(f"淡入动画失败: {e}")
    
    def fade_out(self, widget, duration=300, callback=None):
        """淡出动画"""
        try:
            # 获取初始透明度
            alpha = 1.0
            
            # 动画步数
            steps = 20
            step_time = duration // steps
            
            def animate(step):
                if step <= steps:
                    alpha = 1.0 - (step / steps)
                    try:
                        widget.attributes('-alpha', alpha)
                    except:
                        pass
                    self.root.after(step_time, animate, step + 1)
                elif callback:
                    callback()
            
            animate(0)
        except Exception as e:
            log.error(f"淡出动画失败: {e}")
    
    def slide_in(self, widget, direction='left', duration=300, callback=None):
        """滑入动画"""
        try:
            # 获取初始位置
            x = widget.winfo_x()
            y = widget.winfo_y()
            width = widget.winfo_width()
            
            # 动画步数
            steps = 20
            step_time = duration // steps
            
            if direction == 'left':
                start_x = x - width
                end_x = x
            elif direction == 'right':
                start_x = x + width
                end_x = x
            elif direction == 'top':
                start_y = y - widget.winfo_height()
                end_y = y
            else:
                start_y = y + widget.winfo_height()
                end_y = y
            
            def animate(step):
                if step <= steps:
                    progress = step / steps
                    if direction in ['left', 'right']:
                        current_x = start_x + (end_x - start_x) * progress
                        widget.place(x=current_x, y=y)
                    else:
                        current_y = start_y + (end_y - start_y) * progress
                        widget.place(x=x, y=current_y)
                    self.root.after(step_time, animate, step + 1)
                elif callback:
                    callback()
            
            animate(0)
        except Exception as e:
            log.error(f"滑入动画失败: {e}")
    
    def pulse(self, widget, duration=500, callback=None):
        """脉冲动画"""
        try:
            # 动画步数
            steps = 10
            step_time = duration // steps
            
            def animate(step):
                if step <= steps:
                    # 计算缩放比例
                    if step <= steps // 2:
                        scale = 1.0 + (step / (steps // 2)) * 0.1
                    else:
                        scale = 1.1 - ((step - steps // 2) / (steps // 2)) * 0.1
                    
                    # 应用缩放（通过改变字体大小）
                    try:
                        current_font = widget.cget('font')
                        if isinstance(current_font, str):
                            font_parts = current_font.split()
                            if len(font_parts) >= 2:
                                size = int(font_parts[1])
                                new_size = int(size * scale)
                                widget.config(font=(font_parts[0], new_size))
                    except:
                        pass
                    
                    self.root.after(step_time, animate, step + 1)
                elif callback:
                    # 恢复原始字体
                    try:
                        widget.config(font=('微软雅黑', 12))
                    except:
                        pass
                    callback()
            
            animate(0)
        except Exception as e:
            log.error(f"脉冲动画失败: {e}")


class UIEnhancer:
    """UI增强器"""
    
    def __init__(self, root, theme_colors):
        self.root = root
        self.theme_colors = theme_colors
        self.animation_manager = AnimationManager(root)
    
    def apply_hover_effect(self, widget, hover_color=None):
        """应用悬停效果"""
        if hover_color is None:
            hover_color = self.theme_colors['accent']
        
        original_color = widget.cget('background')
        
        def on_enter(e):
            widget.config(background=hover_color)
        
        def on_leave(e):
            widget.config(background=original_color)
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def apply_click_effect(self, widget, click_color=None):
        """应用点击效果"""
        if click_color is None:
            click_color = self.theme_colors['accent_hover']
        
        original_color = widget.cget('background')
        
        def on_press(e):
            widget.config(background=click_color)
        
        def on_release(e):
            widget.config(background=original_color)
        
        widget.bind('<ButtonPress-1>', on_press)
        widget.bind('<ButtonRelease-1>', on_release)
    
    def create_tooltip(self, widget, text):
        """创建工具提示"""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(tooltip, text=text, 
                           background=self.theme_colors['tooltip_bg'],
                           foreground=self.theme_colors['fg'],
                           font=('微软雅黑', 9),
                           padx=5, pady=3)
            label.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def create_responsive_layout(self, container, min_width=800, min_height=600):
        """创建响应式布局"""
        def on_resize(event):
            # 获取窗口大小
            width = event.width
            height = event.height
            
            # 根据大小调整布局
            if width < min_width or height < min_height:
                # 紧凑模式
                self._apply_compact_layout(container)
            else:
                # 正常模式
                self._apply_normal_layout(container)
        
        container.bind('<Configure>', on_resize)
    
    def _apply_compact_layout(self, container):
        """应用紧凑布局"""
        # 隐藏非必要组件
        for widget in container.winfo_children():
            if isinstance(widget, ttk.Frame):
                # 检查是否是工具栏
                if widget.winfo_name() == 'toolbar':
                    # 隐藏部分按钮
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button):
                            if '统计' in child.cget('text') or '导出' in child.cget('text'):
                                child.pack_forget()
    
    def _apply_normal_layout(self, container):
        """应用正常布局"""
        # 显示所有组件
        for widget in container.winfo_children():
            if isinstance(widget, ttk.Frame):
                if widget.winfo_name() == 'toolbar':
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button):
                            child.pack(side='left', padx=2)
