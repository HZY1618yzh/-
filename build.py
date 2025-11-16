# build.py
import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'code_style_formatter.py',
    '--onefile',
    '--windowed',
    '--name=CodeStyleFormatter',
    '--icon=icon.ico'  # 可选：添加图标
])
