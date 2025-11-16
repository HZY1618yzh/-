# 码风修改器
这是我用`python`写的码风修改器。目前仅支持 windows 系统
# 编译方式：
有两种方式，一种直接下载：[链接](https://pan.baidu.com/s/1tfIAAepJ13sfOcqkx9l2ug?pwd=hzy6),一种自己编译。

先确保电脑安装了`python`的解释器。复制好两个`.py`文件的代码，保存在同一目录下，文件名要对应好。

按`win+r`，输入`cmd`，打开终端。  
在终端输入
```bash
pip install pillow pystray keyboard pywin32 requests
```
等待安装完毕，运行`code_style_formatter_fixed.py`就可以了。

如果想要打包成`exe`文件，就再输入
```bash
pip install pyinstaller
```
安装完毕后，接着打开`build.py`，在代码里把`'--icon=icon.ico'  # 可选：添加图标`删掉。或者把自己喜欢的图标放在同一目录下。

运行`build.py`，等待大概一分钟。它会在同级目录下创建`build`和`dist`文件，`build`文件可以删掉，`dist`文件里会出现一个`exe`格式文件。

# 用法
运行后，在右下角找到一个`^`形符号，点击就会看见在后台运行的程序，你会看到第一个是我的头像（或者是深蓝色方框）。

右键它，让后在弹出的方框里选择打开设置，会弹出一个窗口。你可以在里面设置码风。选中代码，按下`ctrl+q`即可修改码风。
