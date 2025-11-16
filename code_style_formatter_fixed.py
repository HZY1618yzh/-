# code_style_formatter_fixed.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import keyboard
import threading
import json
import os
import sys
import platform
import time
import winreg
import getpass
import re

class CodeStyleFormatter:
    def __init__(self):
        # 创建主Tk窗口但不显示
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        
        self.settings = self.load_settings()
        self.settings_window = None
        self.setup_tray_icon()
        self.setup_hotkey()
        self.sync_auto_start_status()
        
    def load_settings(self):
        """加载设置"""
        default_settings = {
            'style': 'standard',
            'use_indentation': True,
            'indent_size': 4,
            'space_before_parentheses': True,
            'space_around_operators': True,
            'space_after_comma': True,
            'auto_start': False
        }
        
        settings_file = self.get_settings_path()
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                    for key in default_settings:
                        if key in loaded_settings:
                            default_settings[key] = loaded_settings[key]
                    
                    return default_settings
            else:
                return default_settings
                
        except Exception as e:
            return default_settings
    
    def get_settings_path(self):
        """获取设置文件路径"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            return os.path.join(exe_dir, 'code_style_formatter_settings.json')
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(script_dir, 'code_style_formatter_settings.json')
    
    def save_settings(self):
        """保存设置"""
        try:
            settings_file = self.get_settings_path()
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def get_current_exe_path(self):
        """获取当前可执行文件路径"""
        if getattr(sys, 'frozen', False):
            return os.path.abspath(sys.executable)
        else:
            return os.path.abspath(sys.argv[0])
    
    def set_auto_start(self, enable):
        """设置开机自启动"""
        try:
            if platform.system() != "Windows":
                return False
            
            exe_path = self.get_current_exe_path()
            app_name = "CodeStyleFormatter"
            
            if enable:
                success = self._set_auto_start_windows(app_name, exe_path)
                return success
            else:
                success = self._remove_auto_start_windows(app_name)
                return success
                
        except Exception as e:
            return False
    
    def _set_auto_start_windows(self, app_name, exe_path):
        """Windows平台设置开机自启动"""
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                quoted_path = f'"{exe_path}"'
                winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, quoted_path)
                return True
        except PermissionError:
            return False
        except Exception as e:
            return False
    
    def _remove_auto_start_windows(self, app_name):
        """Windows平台移除开机自启动"""
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                try:
                    winreg.DeleteValue(reg_key, app_name)
                    return True
                except FileNotFoundError:
                    return True
        except Exception as e:
            return False
    
    def check_auto_start_status(self):
        """检查当前自启动状态"""
        try:
            if platform.system() != "Windows":
                return False
            
            app_name = "CodeStyleFormatter"
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as reg_key:
                try:
                    value, _ = winreg.QueryValueEx(reg_key, app_name)
                    return bool(value)
                except FileNotFoundError:
                    return False
        except Exception as e:
            return False
    
    def sync_auto_start_status(self):
        """同步自启动状态"""
        try:
            current_registry_status = self.check_auto_start_status()
            current_settings_status = self.settings.get('auto_start', False)
            if current_registry_status != current_settings_status:
                self.settings['auto_start'] = current_registry_status
        except Exception as e:
            pass
    
    def create_tray_image(self):
        """从网络加载托盘图标"""
        try:
            import requests
            from io import BytesIO
            icon_url = "https://cdn.luogu.com.cn/upload/usericon/1394471.png"
            
            # 下载图片
            response = requests.get(icon_url)
            response.raise_for_status()  # 检查请求是否成功
            
            # 从内存中打开图片
            image = Image.open(BytesIO(response.content))
            # 调整大小
            return image.resize((64, 64), Image.LANCZOS)
        except Exception as e:
            # 加载失败时使用默认图标
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color='blue')
            dc = ImageDraw.Draw(image)
            dc.text((width//2-10, height//2-10), "C", fill='white')
            return image
    
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        menu = (
            item('打开设置', self.show_settings),
            item('退出', self.quit_app)
        )
        
        image = self.create_tray_image()
        
        self.icon = pystray.Icon(
            "code_style_formatter",
            image,
            "代码风格修改器 - Ctrl+q格式化代码",
            menu
        )
    
    def setup_hotkey(self):
        """设置全局快捷键"""
        try:
            keyboard.add_hotkey('ctrl+q', self.format_selected_code)
        except Exception as e:
            pass
    
    def format_selected_code(self):
        """格式化选中的代码 - 增加重试和错误处理"""
        try:
            # 先保存当前剪贴板内容
            original_clipboard = self.get_clipboard_text()
            
            # 清空剪贴板，确保能检测到新的选中内容
            self.set_clipboard_text("")
            time.sleep(0.05)
            
            # 模拟 Ctrl+C 复制选中的文本
            keyboard.send('ctrl+c')
            time.sleep(0.2)  # 增加等待时间
            
            # 获取复制后的剪贴板内容
            new_clipboard = self.get_clipboard_text()
            
            # 检查是否有选中的文本
            if not new_clipboard or new_clipboard.strip() == "":
                # 如果没有选中文本，恢复原始剪贴板内容
                if original_clipboard:
                    self.set_clipboard_text(original_clipboard)
                return
            
            # 检查复制的内容是否与原始剪贴板内容相同
            if new_clipboard == original_clipboard:
                return
            
            # 有选中的文本，进行格式化
            selected_code = new_clipboard
            
            if selected_code and selected_code.strip():
                formatted_code = self.apply_code_style(selected_code)
                
                # 将格式化后的代码放回剪贴板
                self.set_clipboard_text(formatted_code)
                time.sleep(0.1)
                
                # 粘贴格式化后的代码
                keyboard.send('ctrl+v')
                time.sleep(0.1)
                
                # 恢复原始剪贴板内容
                if original_clipboard:
                    self.set_clipboard_text(original_clipboard)
                    
        except Exception as e:
            # 如果出现异常，尽量恢复原始剪贴板内容
            try:
                if original_clipboard:
                    self.set_clipboard_text(original_clipboard)
            except:
                pass
    
    def get_clipboard_text(self):
        """获取剪贴板文本"""
        try:
            if platform.system() == "Windows":
                import win32clipboard
                win32clipboard.OpenClipboard()
                try:
                    data = win32clipboard.GetClipboardData()
                except:
                    data = None
                win32clipboard.CloseClipboard()
                return data
            else:
                import subprocess
                result = subprocess.run(['pbpaste'], capture_output=True, text=True)
                return result.stdout if result.returncode == 0 else None
        except Exception as e:
            return None
    
    def set_clipboard_text(self, text):
        """设置剪贴板文本"""
        try:
            if platform.system() == "Windows":
                import win32clipboard
                import win32con
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
            else:
                import subprocess
                subprocess.run(['pbcopy'], input=text, text=True)
        except Exception as e:
            pass

    def apply_code_style(self, code):
        """应用代码风格"""
        if self.settings['style'] == 'standard':
            return self.apply_standard_style(code)
        elif self.settings['style'] == 'concise':
            return self.apply_concise_style(code)
        elif self.settings['style'] == 'custom':
            return self.apply_custom_style(code)
        else:
            return code

    def apply_standard_style(self, code):
        """应用标准风格 - 全新的简单实现"""
        import re
        
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 跳过空行
            if not line.strip():
                formatted_lines.append(line)
                continue
                
            # 保留缩进
            indent_match = re.match(r'^(\s*)', line)
            indent = indent_match.group(1) if indent_match else ''
            content = line[len(indent):]
            
            # 跳过注释和预处理指令
            if re.match(r'\s*(//|#|/\*)', content):
                formatted_lines.append(indent + content)
                continue
            
            # 保护字符串内容
            protected_content, string_map = self.protect_strings_simple(content)
            
            # 处理运算符周围的空格
            protected_content = self.add_spaces_simple(protected_content)
            
            # 处理逗号和分号
            protected_content = re.sub(r',(?!\s)', ', ', protected_content)
            protected_content = re.sub(r';(?!\s|$)', '; ', protected_content)
            
            # 处理括号
            if self.settings.get('space_before_parentheses', True):
                protected_content = re.sub(r'(\w)\(', r'\1 (', protected_content)
            
            # 处理大括号
            protected_content = re.sub(r'\s*\{\s*', ' { ', protected_content)
            protected_content = re.sub(r'\s*\}\s*', ' } ', protected_content)
            
            # 恢复字符串内容
            content = self.restore_strings_simple(protected_content, string_map)
            
            # 清理多余空格
            content = re.sub(r'\s+', ' ', content).strip()
            
            formatted_lines.append(indent + content)
        
        return '\n'.join(formatted_lines)

    def protect_strings_simple(self, content):
        """保护字符串内容 - 简单版本"""
        import re
        
        string_map = {}
        counter = 0
        
        # 保护双引号字符串
        def protect_double(match):
            nonlocal counter
            placeholder = f'__STR_D{counter}__'
            string_map[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        # 保护单引号字符串
        def protect_single(match):
            nonlocal counter
            placeholder = f'__STR_S{counter}__'
            string_map[placeholder] = match.group(0)
            counter += 1
            return placeholder
        
        # 先保护双引号字符串
        protected_content = re.sub(r'"(?:\\.|[^"\\])*"', protect_double, content)
        # 再保护单引号字符串
        protected_content = re.sub(r"'(?:\\.|[^'\\])*'", protect_single, protected_content)
        
        return protected_content, string_map

    def restore_strings_simple(self, content, string_map):
        """恢复字符串内容 - 简单版本"""
        for placeholder, original in string_map.items():
            content = content.replace(placeholder, original)
        return content

    def add_spaces_simple(self, content):
        """在运算符周围添加空格 - 简单版本"""
        import re
        
        # 定义复合运算符（这些不应该被拆分）
        compound_operators = [
            '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=',
            '==', '!=', '<=', '>=', '&&', '||', '<<', '>>', '++', '--', '->', '::'
        ]
        
        # 先处理复合运算符 - 确保它们周围有空格
        for op in compound_operators:
            # 使用单词边界确保精确匹配
            content = re.sub(rf'\b{re.escape(op)}\b', f' {op} ', content)
        
        # 为单个运算符添加空格
        single_operators = ['=', '+', '-', '*', '/', '%', '<', '>', '!', '&', '|', '^', '~']
        
        for op in single_operators:
            # 简单的空格添加，使用负向断言避免影响复合运算符
            pattern = rf'(?<![+\-*/%<>&|^~=!])\s*{re.escape(op)}\s*(?![+\-*/%<>&|^~=!])'
            content = re.sub(pattern, f' {op} ', content)
        
        return content

    def apply_concise_style(self, code):
        """应用简洁风格 - 全新的简单实现"""
        import re
        
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 跳过空行
            if not line.strip():
                formatted_lines.append(line)
                continue
                
            # 保留缩进
            indent_match = re.match(r'^(\s*)', line)
            indent = indent_match.group(1) if indent_match else ''
            content = line[len(indent):]
            
            # 跳过注释和预处理指令
            if re.match(r'\s*(//|#|/\*)', content):
                formatted_lines.append(indent + content)
                continue
            
            # 保护字符串内容
            protected_content, string_map = self.protect_strings_simple(content)
            
            # 移除运算符周围的空格
            protected_content = self.remove_spaces_simple(protected_content)
            
            # 恢复字符串内容
            content = self.restore_strings_simple(protected_content, string_map)
            
            formatted_lines.append(indent + content)
        
        return '\n'.join(formatted_lines)

    def remove_spaces_simple(self, content):
        """移除运算符周围的空格 - 简单版本"""
        import re
        
        # 移除所有运算符周围的空格
        operators = ['=', '+', '-', '*', '/', '%', '<', '>', '!', '&', '|', '^', '~', ',', ';']
        
        for op in operators:
            content = re.sub(rf'\s*{re.escape(op)}\s*', op, content)
        
        # 处理括号和大括号
        content = re.sub(r'\s*\(\s*', '(', content)
        content = re.sub(r'\s*\)\s*', ')', content)
        content = re.sub(r'\s*\{\s*', '{', content)
        content = re.sub(r'\s*\}\s*', '}', content)
        
        return content

    def apply_custom_style(self, code):
        """应用自定义风格"""
        import re
        
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 跳过空行
            if not line.strip():
                formatted_lines.append(line)
                continue
                
            # 保留缩进
            indent_match = re.match(r'^(\s*)', line)
            indent = indent_match.group(1) if indent_match else ''
            content = line[len(indent):]
            
            # 跳过注释和预处理指令
            if re.match(r'\s*(//|#|/\*)', content):
                formatted_lines.append(indent + content)
                continue
            
            # 保护字符串内容
            protected_content, string_map = self.protect_strings_simple(content)
            
            # 根据自定义设置处理
            if self.settings.get('space_around_operators', True):
                protected_content = self.add_spaces_simple(protected_content)
            else:
                protected_content = self.remove_spaces_simple(protected_content)
                
            if self.settings.get('space_after_comma', True):
                protected_content = re.sub(r',(?!\s)', ', ', protected_content)
            else:
                protected_content = re.sub(r',\s+', ',', protected_content)
                
            if self.settings.get('space_before_parentheses', True):
                protected_content = re.sub(r'(\w)\(', r'\1 (', protected_content)
            else:
                protected_content = re.sub(r'\s+\(', '(', protected_content)
            
            # 恢复字符串内容
            content = self.restore_strings_simple(protected_content, string_map)
            
            formatted_lines.append(indent + content)
        
        return '\n'.join(formatted_lines)

    def show_settings(self, icon=None, item=None):
        """显示设置窗口 - 简化版本"""
        # 直接在主线程创建窗口，不经过after
        self._create_settings_window()
    
    def _create_settings_window(self):
        """创建设置窗口 - 简化版本"""
        # 如果窗口已存在，则激活它
        if self.settings_window and self.is_window_alive(self.settings_window):
            try:
                self.settings_window.deiconify()
                self.settings_window.lift()
                self.settings_window.focus_force()
                return
            except Exception as e:
                self.settings_window = None
        
        # 创建新的设置窗口
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("代码风格修改器 - 设置")
        self.settings_window.geometry("600x650")
        self.settings_window.resizable(True, True)
        self.settings_window.configure(bg='white')
        
        self.settings_window.attributes('-topmost', True)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.on_settings_close)
        
        # 创建主容器
        outer_frame = ttk.Frame(self.settings_window, padding="0")
        outer_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # 创建滚动框架
        scroll_frame = ScrolledFrame(outer_frame)
        scroll_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建控件
        self.create_settings_widgets(scroll_frame.inner_frame)
        
        # 居中显示
        #self.center_window(self.settings_window)
    
    def on_settings_close(self):
        """处理设置窗口关闭事件"""
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
    
    def center_window(self, window):
        """窗口居中显示"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_settings_widgets(self, parent):
        """创建设置界面控件"""
        # 开机自启动设置
        autostart_frame = ttk.LabelFrame(parent, text="🚀 开机自启动设置", padding="10")
        autostart_frame.pack(fill='x', pady=5)
        
        self.auto_start_var = tk.BooleanVar(value=self.settings.get('auto_start', False))
        
        current_status = self.check_auto_start_status()
        status_text = "已启用" if current_status else "已禁用"
        status_color = "green" if current_status else "red"
        
        ttk.Checkbutton(autostart_frame, text="开机自动启动", 
                       variable=self.auto_start_var).pack(anchor='w', pady=2)
        
        status_label = ttk.Label(autostart_frame, text=f"当前状态: {status_text}", 
                               foreground=status_color)
        status_label.pack(anchor='w', pady=2)
        
        ttk.Label(autostart_frame, text="注意: 启用后每次开机都会自动运行本程序", 
                 foreground="gray", wraplength=500).pack(anchor='w', pady=2)
        
        # 代码风格选择
        style_frame = ttk.LabelFrame(parent, text="📝 代码风格设置", padding="10")
        style_frame.pack(fill='x', pady=5)
        
        self.style_var = tk.StringVar(value=self.settings['style'])
        
        ttk.Radiobutton(style_frame, text="标准风格（空格繁多）", 
                       variable=self.style_var, value='standard').pack(anchor='w', pady=2)
        ttk.Radiobutton(style_frame, text="简洁风格（尽量无空格）", 
                       variable=self.style_var, value='concise').pack(anchor='w', pady=2)
        ttk.Radiobutton(style_frame, text="自定义风格", 
                       variable=self.style_var, value='custom').pack(anchor='w', pady=2)
        
        # 自定义设置
        custom_frame = ttk.LabelFrame(parent, text="⚙️ 自定义设置", padding="10")
        custom_frame.pack(fill='x', pady=5)
        
        self.space_operators_var = tk.BooleanVar(value=self.settings['space_around_operators'])
        ttk.Checkbutton(custom_frame, text="操作符周围添加空格 (单个运算符)", 
                       variable=self.space_operators_var).pack(anchor='w', pady=2)
        
        self.space_comma_var = tk.BooleanVar(value=self.settings['space_after_comma'])
        ttk.Checkbutton(custom_frame, text="逗号后添加空格", 
                       variable=self.space_comma_var).pack(anchor='w', pady=2)
        
        self.space_parentheses_var = tk.BooleanVar(value=self.settings['space_before_parentheses'])
        ttk.Checkbutton(custom_frame, text="括号前添加空格", 
                       variable=self.space_parentheses_var).pack(anchor='w', pady=2)
        
        # 缩进设置
        indent_frame = ttk.LabelFrame(parent, text="📐 缩进设置", padding="10")
        indent_frame.pack(fill='x', pady=5)
        
        indent_subframe = ttk.Frame(indent_frame)
        indent_subframe.pack(fill='x')
        
        self.indent_var = tk.BooleanVar(value=self.settings['use_indentation'])
        ttk.Checkbutton(indent_subframe, text="保留原始缩进", 
                       variable=self.indent_var).pack(side='left')
        
        ttk.Label(indent_subframe, text="缩进大小:").pack(side='left', padx=(20, 5))
        self.indent_size_var = tk.IntVar(value=self.settings['indent_size'])
        indent_spinbox = ttk.Spinbox(indent_subframe, from_=2, to=8, 
                                   width=5, textvariable=self.indent_size_var)
        indent_spinbox.pack(side='left')
        ttk.Label(indent_subframe, text="空格").pack(side='left', padx=(5, 0))
        
        # 测试区域
        test_frame = ttk.LabelFrame(parent, text="🧪 实时测试", padding="10")
        test_frame.pack(fill='x', pady=5)
        
        ttk.Label(test_frame, text="测试代码 (包含复合运算符、字符串和注释):").pack(anchor='w')
        
        test_input_frame = ttk.Frame(test_frame)
        test_input_frame.pack(fill='x', pady=5)
        
        ttk.Label(test_input_frame, text="输入:").pack(anchor='w')
        self.test_input = scrolledtext.ScrolledText(test_input_frame, height=8, width=60)
        self.test_input.pack(fill='x', pady=2)
        
        # 包含各种复合运算符、字符串和注释的测试代码
        test_code = '''#include <iostream>
using namespace std;

// 这是一个测试函数
int main() {
    string message = "Hello, World! <= 这个字符串不应该被修改";
    char ch = 'a'; // 字符常量
    char ch2='b';
    int x=1,y=2;
    /* 多行注释
       这里的内容应该被保护 */
    if(x<=y&&y>=x){  // 复合运算符测试
        x+=y;
        y-=x;
        x*=2;
        y/=2;
        x%=3;
        cout<<x<<" <= 输出x"<<endl;
        cout<<y<<" != 输出y"<<endl;
    }
    return 0;
}'''
        self.test_input.insert('1.0', test_code)
        
        ttk.Button(test_frame, text="测试格式化", 
                  command=self.test_formatting).pack(anchor='w', pady=5)
        
        test_output_frame = ttk.Frame(test_frame)
        test_output_frame.pack(fill='x', pady=5)
        
        ttk.Label(test_output_frame, text="输出:").pack(anchor='w')
        self.test_output = scrolledtext.ScrolledText(test_output_frame, height=8, width=60, 
                                                   background='#f0f0f0')
        self.test_output.pack(fill='x', pady=2)
        
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="💾 保存设置", 
                  command=self.save_settings_from_ui).pack(side='right', padx=5)
        ttk.Button(button_frame, text="🔄 检查状态", 
                  command=lambda: self.refresh_status(status_label)).pack(side='right', padx=5)
        ttk.Button(button_frame, text="❌ 关闭", 
                  command=self.on_settings_close).pack(side='right', padx=5)
        
        # 状态信息
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=5)
        ttk.Label(status_frame, text="❗️ 注意：此插件仅用于教学目的，请勿用于商业用途，软件编写者：HZY1618yzh", foreground="red").pack(anchor='w')
        ttk.Label(status_frame, text="✅ 状态: 程序运行中", foreground="green").pack(anchor='w')
        ttk.Label(status_frame, text="🎯 快捷键: Ctrl+q 格式化选中的代码", foreground="blue").pack(anchor='w')
        ttk.Label(status_frame, text="💡 提示: 字符串、注释和头文件会被正确保护", 
                 foreground="gray", wraplength=500).pack(anchor='w')
    
    def refresh_status(self, status_label):
        """刷新自启动状态显示"""
        current_status = self.check_auto_start_status()
        status_text = "已启用" if current_status else "已禁用"
        status_color = "green" if current_status else "red"
        
        status_label.config(text=f"当前状态: {status_text}", foreground=status_color)
    
    def test_formatting(self):
        """测试格式化功能"""
        test_code = self.test_input.get('1.0', 'end-1c')
        formatted = self.apply_code_style(test_code)
        
        self.test_output.delete('1.0', 'end')
        self.test_output.insert('1.0', formatted)
    
    def save_settings_from_ui(self):
        """从UI保存设置"""
        self.settings.update({
            'style': self.style_var.get(),
            'use_indentation': self.indent_var.get(),
            'indent_size': self.indent_size_var.get(),
            'space_before_parentheses': self.space_parentheses_var.get(),
            'space_around_operators': self.space_operators_var.get(),
            'space_after_comma': self.space_comma_var.get(),
            'auto_start': self.auto_start_var.get(),
        })
        
        self.save_settings()
        success = self.set_auto_start(self.settings['auto_start'])
    
    def run(self):
        """运行程序"""
        # 在单独的线程中运行系统托盘图标
        def run_tray():
            try:
                self.icon.run()
            except Exception as e:
                # 如果托盘图标失败，显示设置窗口
                self._create_settings_window()
        
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
        
        # 在主线程中运行Tkinter主循环
        try:
            self.root.mainloop()
        except Exception as e:
            pass
    
    def quit_app(self, icon=None, item=None):
        """退出程序"""
        # 直接退出程序
        self._quit_app()
    
    def _quit_app(self):
        """安全退出程序"""
        try:
            if self.settings_window and self.is_window_alive(self.settings_window):
                self.settings_window.destroy()
        except:
            pass
        
        try:
            self.icon.stop()
        except:
            pass
        
        try:
            keyboard.unhook_all()
        except:
            pass
        
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        
        os._exit(0)
    
    def is_window_alive(self, window):
        """检查窗口是否还存在"""
        try:
            window.winfo_exists()
            return True
        except:
            return False


class ScrolledFrame(tk.Frame):
    """可滚动的Frame组件"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 绑定内部Frame的大小变化事件
        self.inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 在Canvas中创建窗口
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # 绑定Canvas大小变化事件
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # 绑定鼠标滚轮事件
        self._bind_mousewheel()
        
        # 布局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
    
    def _on_canvas_configure(self, event):
        """当Canvas大小变化时，调整内部Frame的宽度"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _bind_mousewheel(self):
        """绑定鼠标滚轮事件"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 绑定到Canvas和内部Frame
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.inner_frame.bind("<MouseWheel>", _on_mousewheel)


def main():
    """主函数"""
    try:
        formatter = CodeStyleFormatter()
        formatter.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("按任意键退出...")


if __name__ == "__main__":
    main()
