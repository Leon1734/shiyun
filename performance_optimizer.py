#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化模块
功能：虚拟滚动、懒加载、内存优化、启动优化
"""

import tkinter as tk
from tkinter import ttk
import logging
import gc

log = logging.getLogger("poetry")


class VirtualList:
    """虚拟列表组件"""
    
    def __init__(self, parent, items, item_height=30, visible_count=20):
        self.parent = parent
        self.items = items
        self.item_height = item_height
        self.visible_count = visible_count
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='both', expand=True)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(self.frame, bg='white')
        self.scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # 创建内部框架
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')
        
        # 绑定事件
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.inner_frame.bind('<Configure>', self._on_inner_frame_configure)
        
        # 初始化显示
        self._update_visible_items()
    
    def _on_canvas_configure(self, event):
        """画布大小改变事件"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _on_inner_frame_configure(self, event):
        """内部框架大小改变事件"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _update_visible_items(self):
        """更新可见项目"""
        # 清空内部框架
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        # 计算可见范围
        canvas_height = self.canvas.winfo_height()
        visible_count = max(1, canvas_height // self.item_height)
        
        # 创建可见项目
        for i in range(min(visible_count, len(self.items))):
            item = self.items[i]
            self._create_item_widget(i, item)
    
    def _create_item_widget(self, index, item):
        """创建项目组件"""
        # 创建项目框架
        item_frame = ttk.Frame(self.inner_frame)
        item_frame.pack(fill='x', padx=5, pady=2)
        
        # 添加内容
        label = ttk.Label(item_frame, text=f"{index + 1}. {item}")
        label.pack(fill='x')
    
    def update_items(self, new_items):
        """更新项目列表"""
        self.items = new_items
        self._update_visible_items()


class LazyLoader:
    """懒加载器"""
    
    def __init__(self, load_func, batch_size=100):
        self.load_func = load_func
        self.batch_size = batch_size
        self.loaded_items = []
        self.current_index = 0
        self.has_more = True
    
    def load_next_batch(self):
        """加载下一批数据"""
        if not self.has_more:
            return []
        
        try:
            batch = self.load_func(self.current_index, self.batch_size)
            
            if len(batch) < self.batch_size:
                self.has_more = False
            
            self.loaded_items.extend(batch)
            self.current_index += len(batch)
            
            return batch
        except Exception as e:
            log.error(f"懒加载失败: {e}")
            return []
    
    def get_loaded_items(self):
        """获取已加载的项目"""
        return self.loaded_items
    
    def reset(self):
        """重置加载器"""
        self.loaded_items = []
        self.current_index = 0
        self.has_more = True


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.cache = {}
        self.max_cache_size = 1000
    
    def get_from_cache(self, key):
        """从缓存获取数据"""
        return self.cache.get(key)
    
    def set_to_cache(self, key, value):
        """设置缓存数据"""
        if len(self.cache) >= self.max_cache_size:
            # 清理旧缓存
            self._cleanup_cache()
        
        self.cache[key] = value
    
    def _cleanup_cache(self):
        """清理缓存"""
        # 删除一半的缓存
        keys_to_delete = list(self.cache.keys())[:len(self.cache) // 2]
        for key in keys_to_delete:
            del self.cache[key]
        
        # 触发垃圾回收
        gc.collect()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        gc.collect()


class StartupOptimizer:
    """启动优化器"""
    
    def __init__(self):
        self.startup_tasks = []
        self.completed_tasks = []
    
    def add_task(self, task_name, task_func, priority=0):
        """添加启动任务"""
        self.startup_tasks.append({
            'name': task_name,
            'func': task_func,
            'priority': priority
        })
    
    def run_tasks(self, callback=None):
        """运行启动任务"""
        # 按优先级排序
        self.startup_tasks.sort(key=lambda x: x['priority'])
        
        def run_next_task(index):
            if index < len(self.startup_tasks):
                task = self.startup_tasks[index]
                try:
                    task['func']()
                    self.completed_tasks.append(task['name'])
                    log.info(f"启动任务完成: {task['name']}")
                except Exception as e:
                    log.error(f"启动任务失败: {task['name']}: {e}")
                
                # 运行下一个任务
                run_next_task(index + 1)
            elif callback:
                callback()
        
        run_next_task(0)
    
    def get_progress(self):
        """获取启动进度"""
        if not self.startup_tasks:
            return 100
        
        return len(self.completed_tasks) / len(self.startup_tasks) * 100


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, name):
        """开始计时"""
        import time
        self.start_times[name] = time.time()
    
    def stop_timer(self, name):
        """停止计时"""
        import time
        if name in self.start_times:
            elapsed = time.time() - self.start_times[name]
            self.metrics[name] = elapsed
            del self.start_times[name]
            return elapsed
        return 0
    
    def get_metric(self, name):
        """获取性能指标"""
        return self.metrics.get(name, 0)
    
    def get_all_metrics(self):
        """获取所有性能指标"""
        return self.metrics.copy()
    
    def clear_metrics(self):
        """清空性能指标"""
        self.metrics.clear()
        self.start_times.clear()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, max_size=1000, ttl=300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self.access_times = {}
    
    def get(self, key):
        """获取缓存数据"""
        import time
        
        if key not in self.cache:
            return None
        
        # 检查是否过期
        if time.time() - self.access_times[key] > self.ttl:
            del self.cache[key]
            del self.access_times[key]
            return None
        
        # 更新访问时间
        self.access_times[key] = time.time()
        
        return self.cache[key]
    
    def set(self, key, value):
        """设置缓存数据"""
        import time
        
        # 如果缓存已满，清理旧数据
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _cleanup(self):
        """清理缓存"""
        import time
        
        current_time = time.time()
        keys_to_delete = []
        
        # 删除过期数据
        for key, access_time in self.access_times.items():
            if current_time - access_time > self.ttl:
                keys_to_delete.append(key)
        
        # 如果还是太多，删除最旧的数据
        if len(self.cache) - len(keys_to_delete) >= self.max_size:
            sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
            for key, _ in sorted_keys[:len(sorted_keys) // 2]:
                if key not in keys_to_delete:
                    keys_to_delete.append(key)
        
        # 删除数据
        for key in keys_to_delete:
            if key in self.cache:
                del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
    
    def size(self):
        """获取缓存大小"""
        return len(self.cache)
