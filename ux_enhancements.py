#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户体验增强模块
功能：右键菜单、拖放支持、工具栏自定义、状态栏增强
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

log = logging.getLogger("poetry")


class ContextMenu:
    """右键菜单"""
    
    def __init__(self, parent):
        self.parent = parent
        self.menu = None
        self.commands = {}
    
    def create_menu(self, items):
        """创建右键菜单"""
        self.menu = tk.Menu(self.parent, tearoff=0)
        
        for item in items:
            if item == '-':
                self.menu.add_separator()
            else:
                label = item.get('label', '')
                command = item.get('command', None)
                accelerator = item.get('accelerator', '')
                
                if command:
                    self.commands[label] = command
                    self.menu.add_command(label=label, command=command, 
                                        accelerator=accelerator)
        
        # 绑定右键事件
        self.parent.bind('<Button-3>', self._show_menu)
    
    def _show_menu(self, event):
        """显示右键菜单"""
        if self.menu:
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()


class DragDropSupport:
    """拖放支持"""
    
    def __init__(self, parent):
        self.parent = parent
        self.drag_data = {'x': 0, 'y': 0, 'item': None}
        self.drop_targets = []
    
    def enable_drag(self, widget, data=None):
        """启用拖动"""
        widget.bind('<Button-1>', lambda e: self._start_drag(e, widget, data))
        widget.bind('<B1-Motion>', self._drag)
        widget.bind('<ButtonRelease-1>', self._stop_drag)
    
    def add_drop_target(self, widget, callback):
        """添加放置目标"""
        self.drop_targets.append({
            'widget': widget,
            'callback': callback
        })
        
        widget.bind('<ButtonRelease-1>', lambda e: self._drop(e, widget))
    
    def _start_drag(self, event, widget, data):
        """开始拖动"""
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.drag_data['item'] = data
        
        # 改变鼠标样式
        widget.config(cursor='hand2')
    
    def _drag(self, event):
        """拖动中"""
        # 计算移动距离
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        
        # 移动组件
        widget = event.widget
        widget.place(x=widget.winfo_x() + dx, y=widget.winfo_y() + dy)
        
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
    
    def _stop_drag(self, event):
        """停止拖动"""
        # 恢复鼠标样式
        event.widget.config(cursor='')
        
        # 检查是否放置在目标上
        for target in self.drop_targets:
            widget = target['widget']
            callback = target['callback']
            
            # 检查位置
            x = event.x_root
            y = event.y_root
            
            widget_x = widget.winfo_rootx()
            widget_y = widget.winfo_rooty()
            widget_width = widget.winfo_width()
            widget_height = widget.winfo_height()
            
            if (widget_x <= x <= widget_x + widget_width and
                widget_y <= y <= widget_y + widget_height):
                # 放置在目标上
                callback(self.drag_data['item'])
                break
        
        self.drag_data = {'x': 0, 'y': 0, 'item': None}
    
    def _drop(self, event, widget):
        """放置"""
        # 检查是否有拖动数据
        if self.drag_data['item']:
            # 找到对应的回调
            for target in self.drop_targets:
                if target['widget'] == widget:
                    target['callback'](self.drag_data['item'])
                    break


class ToolbarCustomizer:
    """工具栏自定义"""
    
    def __init__(self, parent, toolbar):
        self.parent = parent
        self.toolbar = toolbar
        self.buttons = []
        self.visible_buttons = []
    
    def add_button(self, button, visible=True):
        """添加按钮"""
        self.buttons.append({
            'button': button,
            'visible': visible
        })
        
        if visible:
            self.visible_buttons.append(button)
    
    def remove_button(self, button):
        """移除按钮"""
        for btn_info in self.buttons:
            if btn_info['button'] == button:
                self.buttons.remove(btn_info)
                if button in self.visible_buttons:
                    self.visible_buttons.remove(button)
                break
    
    def show_button(self, button):
        """显示按钮"""
        for btn_info in self.buttons:
            if btn_info['button'] == button:
                btn_info['visible'] = True
                if button not in self.visible_buttons:
                    self.visible_buttons.append(button)
                break
        
        self._update_toolbar()
    
    def hide_button(self, button):
        """隐藏按钮"""
        for btn_info in self.buttons:
            if btn_info['button'] == button:
                btn_info['visible'] = False
                if button in self.visible_buttons:
                    self.visible_buttons.remove(button)
                break
        
        self._update_toolbar()
    
    def _update_toolbar(self):
        """更新工具栏"""
        # 隐藏所有按钮
        for btn_info in self.buttons:
            btn_info['button'].pack_forget()
        
        # 显示可见按钮
        for button in self.visible_buttons:
            button.pack(side='left', padx=2)
    
    def show_customization_dialog(self):
        """显示自定义对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("自定义工具栏")
        dialog.geometry("300x400")
        
        # 按钮列表
        listbox = tk.Listbox(dialog, selectmode='multiple')
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 添加按钮选项
        for btn_info in self.buttons:
            button = btn_info['button']
            visible = btn_info['visible']
            label = button.cget('text')
            
            listbox.insert(tk.END, label)
            
            if visible:
                listbox.selection_set(tk.END)
        
        # 按钮框架
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        def apply_changes():
            """应用更改"""
            selected_indices = listbox.curselection()
            
            # 更新可见性
            for i, btn_info in enumerate(self.buttons):
                if i in selected_indices:
                    btn_info['visible'] = True
                else:
                    btn_info['visible'] = False
            
            # 更新可见按钮列表
            self.visible_buttons = [
                btn_info['button'] for btn_info in self.buttons 
                if btn_info['visible']
            ]
            
            # 更新工具栏
            self._update_toolbar()
            
            dialog.destroy()
        
        ttk.Button(btn_frame, text="应用", command=apply_changes).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='left', padx=5)


class StatusBarEnhancer:
    """状态栏增强"""
    
    def __init__(self, parent):
        self.parent = parent
        self.status_bar = None
        self.progress_bar = None
        self.labels = {}
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.parent)
        self.status_bar.pack(fill='x', side='bottom')
        
        # 主状态标签
        self.labels['main'] = ttk.Label(self.status_bar, text="就绪")
        self.labels['main'].pack(side='left', padx=5)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(self.status_bar, length=100, mode='determinate')
        self.progress_bar.pack(side='right', padx=5)
        
        # 其他标签
        self.labels['count'] = ttk.Label(self.status_bar, text="")
        self.labels['count'].pack(side='right', padx=5)
        
        return self.status_bar
    
    def set_status(self, text):
        """设置状态文本"""
        if 'main' in self.labels:
            self.labels['main'].config(text=text)
    
    def set_count(self, text):
        """设置计数文本"""
        if 'count' in self.labels:
            self.labels['count'].config(text=text)
    
    def set_progress(self, value):
        """设置进度"""
        if self.progress_bar:
            self.progress_bar['value'] = value
    
    def start_progress(self, maximum=100):
        """开始进度"""
        if self.progress_bar:
            self.progress_bar['maximum'] = maximum
            self.progress_bar['value'] = 0
    
    def update_progress(self, value):
        """更新进度"""
        if self.progress_bar:
            self.progress_bar['value'] = value
    
    def stop_progress(self):
        """停止进度"""
        if self.progress_bar:
            self.progress_bar['value'] = 0


class KeyboardShortcuts:
    """键盘快捷键"""
    
    def __init__(self, parent):
        self.parent = parent
        self.shortcuts = {}
    
    def add_shortcut(self, key, command, description=""):
        """添加快捷键"""
        self.shortcuts[key] = {
            'command': command,
            'description': description
        }
        
        # 绑定快捷键
        self.parent.bind(key, lambda e: command())
    
    def remove_shortcut(self, key):
        """移除快捷键"""
        if key in self.shortcuts:
            del self.shortcuts[key]
            self.parent.unbind(key)
    
    def get_shortcuts(self):
        """获取所有快捷键"""
        return self.shortcuts.copy()
    
    def show_shortcuts_dialog(self):
        """显示快捷键对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("键盘快捷键")
        dialog.geometry("400x300")
        
        # 快捷键列表
        tree = ttk.Treeview(dialog, columns=('key', 'description'), show='headings')
        tree.heading('key', text='快捷键')
        tree.heading('description', text='功能')
        tree.column('key', width=150)
        tree.column('description', width=250)
        
        # 添加快捷键
        for key, info in self.shortcuts.items():
            tree.insert('', 'end', values=(key, info['description']))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 关闭按钮
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)


class ThemeManager:
    """主题管理器"""
    
    def __init__(self, parent):
        self.parent = parent
        self.themes = {}
        self.current_theme = None
    
    def add_theme(self, name, colors):
        """添加主题"""
        self.themes[name] = colors
    
    def set_theme(self, name):
        """设置主题"""
        if name in self.themes:
            self.current_theme = name
            colors = self.themes[name]
            self._apply_theme(colors)
    
    def _apply_theme(self, colors):
        """应用主题"""
        # 更新样式
        style = ttk.Style()
        
        # 配置各种组件样式
        style.configure('TFrame', background=colors.get('bg', '#ffffff'))
        style.configure('TLabel', background=colors.get('bg', '#ffffff'), 
                       foreground=colors.get('fg', '#000000'))
        style.configure('TButton', 
                       background=colors.get('button_bg', '#e1e1e1'),
                       foreground=colors.get('button_fg', '#000000'))
        
        # 更新根窗口背景
        self.parent.configure(background=colors.get('bg', '#ffffff'))
    
    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme
    
    def get_theme_colors(self):
        """获取当前主题颜色"""
        if self.current_theme:
            return self.themes[self.current_theme]
        return {}
