#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件系统模块
功能：插件加载、插件管理、插件API
"""

import json
import importlib
import logging
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

log = logging.getLogger("poetry")

# 插件目录
PLUGINS_DIR = Path(__file__).parent / "plugins"


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins = {}
        self.loaded_plugins = {}
        self.plugin_api = PluginAPI()
        
        # 确保插件目录存在
        PLUGINS_DIR.mkdir(exist_ok=True)
        
        # 扫描插件
        self._scan_plugins()
    
    def _scan_plugins(self):
        """扫描插件"""
        try:
            for plugin_dir in PLUGINS_DIR.iterdir():
                if plugin_dir.is_dir():
                    # 检查是否有 plugin.json
                    plugin_config = plugin_dir / "plugin.json"
                    if plugin_config.exists():
                        try:
                            with open(plugin_config, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            
                            plugin_name = config.get('name', plugin_dir.name)
                            self.plugins[plugin_name] = {
                                'path': plugin_dir,
                                'config': config,
                                'loaded': False
                            }
                            
                            log.info(f"发现插件: {plugin_name}")
                        except Exception as e:
                            log.error(f"加载插件配置失败 {plugin_dir}: {e}")
            
            log.info(f"扫描完成: {len(self.plugins)} 个插件")
        except Exception as e:
            log.error(f"扫描插件失败: {e}")
    
    def load_plugin(self, plugin_name):
        """加载插件"""
        if plugin_name not in self.plugins:
            log.error(f"插件不存在: {plugin_name}")
            return False
        
        plugin_info = self.plugins[plugin_name]
        
        if plugin_info['loaded']:
            log.info(f"插件已加载: {plugin_name}")
            return True
        
        try:
            plugin_path = plugin_info['path']
            config = plugin_info['config']
            
            # 获取入口模块
            entry_point = config.get('entry_point', 'main.py')
            module_path = plugin_path / entry_point
            
            if not module_path.exists():
                log.error(f"插件入口文件不存在: {module_path}")
                return False
            
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(plugin_name, module_path)
            module = importlib.util.module_from_spec(spec)
            
            # 注入API
            module.plugin_api = self.plugin_api
            
            # 执行模块
            spec.loader.exec_module(module)
            
            # 调用初始化函数
            if hasattr(module, 'on_load'):
                module.on_load()
            
            # 记录已加载的插件
            self.loaded_plugins[plugin_name] = {
                'module': module,
                'config': config
            }
            
            plugin_info['loaded'] = True
            
            log.info(f"插件加载成功: {plugin_name}")
            return True
        except Exception as e:
            log.error(f"加载插件失败 {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name):
        """卸载插件"""
        if plugin_name not in self.loaded_plugins:
            log.error(f"插件未加载: {plugin_name}")
            return False
        
        try:
            plugin_info = self.loaded_plugins[plugin_name]
            module = plugin_info['module']
            
            # 调用卸载函数
            if hasattr(module, 'on_unload'):
                module.on_unload()
            
            # 移除已加载的插件
            del self.loaded_plugins[plugin_name]
            
            # 更新插件状态
            if plugin_name in self.plugins:
                self.plugins[plugin_name]['loaded'] = False
            
            log.info(f"插件卸载成功: {plugin_name}")
            return True
        except Exception as e:
            log.error(f"卸载插件失败 {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self):
        """加载所有插件"""
        loaded_count = 0
        
        for plugin_name in self.plugins:
            if self.load_plugin(plugin_name):
                loaded_count += 1
        
        log.info(f"加载完成: {loaded_count}/{len(self.plugins)} 个插件")
        return loaded_count
    
    def unload_all_plugins(self):
        """卸载所有插件"""
        unloaded_count = 0
        
        for plugin_name in list(self.loaded_plugins.keys()):
            if self.unload_plugin(plugin_name):
                unloaded_count += 1
        
        log.info(f"卸载完成: {unloaded_count} 个插件")
        return unloaded_count
    
    def get_plugin_info(self, plugin_name):
        """获取插件信息"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        return None
    
    def get_all_plugins(self):
        """获取所有插件"""
        return self.plugins.copy()
    
    def get_loaded_plugins(self):
        """获取已加载的插件"""
        return self.loaded_plugins.copy()
    
    def reload_plugin(self, plugin_name):
        """重新加载插件"""
        if plugin_name in self.loaded_plugins:
            self.unload_plugin(plugin_name)
        
        return self.load_plugin(plugin_name)


class PluginAPI:
    """插件API"""
    
    def __init__(self):
        self.callbacks = {}
        self.data = {}
    
    def register_callback(self, event, callback):
        """注册回调"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def unregister_callback(self, event, callback):
        """注销回调"""
        if event in self.callbacks:
            if callback in self.callbacks[event]:
                self.callbacks[event].remove(callback)
    
    def trigger_event(self, event, **kwargs):
        """触发事件"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    log.error(f"回调执行失败 {event}: {e}")
    
    def set_data(self, key, value):
        """设置数据"""
        self.data[key] = value
    
    def get_data(self, key, default=None):
        """获取数据"""
        return self.data.get(key, default)
    
    def get_app_info(self):
        """获取应用信息"""
        return {
            'name': '古诗词桌面小工具',
            'version': '6.0',
            'author': 'AI Assistant'
        }
    
    def show_message(self, title, message, type='info'):
        """显示消息"""
        # 这里需要与主程序集成
        log.info(f"[{type}] {title}: {message}")
    
    def add_menu_item(self, menu_name, item_name, callback):
        """添加菜单项"""
        # 这里需要与主程序集成
        log.info(f"添加菜单项: {menu_name} -> {item_name}")
    
    def add_toolbar_button(self, button_name, callback, icon=None):
        """添加工具栏按钮"""
        # 这里需要与主程序集成
        log.info(f"添加工具栏按钮: {button_name}")


class PluginConfigDialog:
    """插件配置对话框"""
    
    def __init__(self, parent, plugin_manager):
        self.parent = parent
        self.plugin_manager = plugin_manager
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("插件管理")
        self.dialog.geometry("500x400")
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔌 插件管理", 
                               font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 插件列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True)
        
        # Treeview
        self.plugin_tree = ttk.Treeview(list_frame, columns=('name', 'version', 'status'),
                                        show='headings', height=10)
        self.plugin_tree.heading('name', text='插件名称')
        self.plugin_tree.heading('version', text='版本')
        self.plugin_tree.heading('status', text='状态')
        self.plugin_tree.column('name', width=200)
        self.plugin_tree.column('version', width=100)
        self.plugin_tree.column('status', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.plugin_tree.yview)
        self.plugin_tree.configure(yscrollcommand=scrollbar.set)
        
        self.plugin_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载插件列表
        self._load_plugins()
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Button(btn_frame, text="加载", command=self._load_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="卸载", command=self._unload_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="重新加载", command=self._reload_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="刷新", command=self._load_plugins).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side='right', padx=5)
    
    def _load_plugins(self):
        """加载插件列表"""
        # 清空列表
        for item in self.plugin_tree.get_children():
            self.plugin_tree.delete(item)
        
        # 获取所有插件
        plugins = self.plugin_manager.get_all_plugins()
        
        # 填充列表
        for name, info in plugins.items():
            config = info['config']
            version = config.get('version', '1.0.0')
            status = '已加载' if info['loaded'] else '未加载'
            
            self.plugin_tree.insert('', 'end', values=(name, version, status))
    
    def _load_selected(self):
        """加载选中的插件"""
        selection = self.plugin_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要加载的插件")
            return
        
        for item in selection:
            values = self.plugin_tree.item(item)['values']
            plugin_name = values[0]
            
            if self.plugin_manager.load_plugin(plugin_name):
                messagebox.showinfo("成功", f"插件 '{plugin_name}' 已加载")
            else:
                messagebox.showerror("错误", f"加载插件 '{plugin_name}' 失败")
        
        self._load_plugins()
    
    def _unload_selected(self):
        """卸载选中的插件"""
        selection = self.plugin_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要卸载的插件")
            return
        
        for item in selection:
            values = self.plugin_tree.item(item)['values']
            plugin_name = values[0]
            
            if self.plugin_manager.unload_plugin(plugin_name):
                messagebox.showinfo("成功", f"插件 '{plugin_name}' 已卸载")
            else:
                messagebox.showerror("错误", f"卸载插件 '{plugin_name}' 失败")
        
        self._load_plugins()
    
    def _reload_selected(self):
        """重新加载选中的插件"""
        selection = self.plugin_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要重新加载的插件")
            return
        
        for item in selection:
            values = self.plugin_tree.item(item)['values']
            plugin_name = values[0]
            
            if self.plugin_manager.reload_plugin(plugin_name):
                messagebox.showinfo("成功", f"插件 '{plugin_name}' 已重新加载")
            else:
                messagebox.showerror("错误", f"重新加载插件 '{plugin_name}' 失败")
        
        self._load_plugins()
