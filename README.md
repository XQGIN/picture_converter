# 图片批量转换器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

一个功能强大的图片批量转换工具，基于PyQt5和Pillow开发，支持多种图片格式之间的高效转换，并采用现代visionOS风格的液态玻璃效果界面设计。

## 🌟 功能特点

- ✅ 支持多种图片格式转换：JPEG、PNG、WEBP、BMP、TIFF、GIF、HEIC、AVIF、JPEG2000、TGA、JXL等
- ✅ 批量处理多张图片，提高工作效率
- ✅ 灵活的图片质量调整选项
- ✅ 多种图片尺寸调整模式（按宽度、高度或自定义尺寸）
- ✅ 美观的visionOS风格液态玻璃效果界面
- ✅ 支持浅色和深色主题切换
- ✅ 丰富的设置功能，可自定义默认输出目录等选项
- ✅ 支持拖拽文件或文件夹到界面直接添加
- ✅ 实时预览转换进度
- ✅ 支持透明通道处理（如PNG转JPEG时自动处理透明背景）

## 🖼️ 程序截图

![程序图标](resources/icon.png)

## 📋 系统要求

- Windows 7/8/10/11 操作系统
- Python 3.6 或更高版本
- 必要的依赖库（见requirements.txt）

## 🚀 安装与运行

### 方法一：直接运行已编译的程序

1. 前往项目的 `dist\图片批量转换器` 目录
2. 双击运行 `图片批量转换器.exe` 文件即可使用

### 方法二：从源代码运行

1. 确保已安装Python 3.6+环境
2. 克隆或下载本项目到本地
3. 激活虚拟环境（如使用）：
   ```powershell
   .\venv\Scripts\activate
   ```
4. 安装所需依赖：
   ```powershell
   pip install -r requirements.txt
   ```
5. 运行程序：
   ```powershell
   python main.py
   ```

## 📖 使用说明

1. 点击"添加文件"按钮选择要转换的图片文件，或直接拖拽文件/文件夹到界面
2. 在右侧面板设置输出格式、质量等参数
3. 选择输出目录（默认输出到"D:/图片"）
4. 点击"开始转换"按钮开始批量转换
5. 转换进度会在进度条中实时显示
6. 转换完成后，可点击"打开输出目录"查看转换后的文件

## ⚙️ 设置选项

点击"设置"按钮可以打开设置对话框，配置以下选项：

- **默认输出目录**：设置转换后文件的默认保存位置
- **是否覆盖同名文件**：控制是否覆盖已存在的同名文件
- **界面主题**：选择浅色、深色或自动跟随系统主题
- **玻璃透明度**：调整界面的玻璃效果透明度
- **默认输出格式**：设置常用的输出图片格式
- **默认输出质量**：设置图片的默认压缩质量
- **默认图片尺寸调整**：设置常用的图片尺寸调整方式

## 🛠️ 项目结构

```
图片批量转换器/
├── main.py                  # 程序入口文件
├── src/
│   ├── __init__.py          # 包初始化文件
│   └── main_window.py       # 主窗口实现文件
├── resources/               # 资源文件夹
│   └── icon.png             # 应用图标
├── settings.json            # 配置文件
├── requirements.txt         # 依赖库列表
├── picture_converter.spec   # PyInstaller打包配置
├── 图片批量转换器.spec        # PyInstaller中文打包配置
└── README.md                # 项目说明文档
```

## 🚀 打包说明

项目已配置好PyInstaller打包脚本，可以方便地将程序打包成Windows可执行文件：

```powershell
# 使用已有的spec文件打包
pyinstaller picture_converter.spec

# 或使用中文spec文件
pyinstaller 图片批量转换器.spec
```

打包后的可执行文件将位于 `dist\图片批量转换器` 目录下。

## 🤝 贡献指南

欢迎对本项目进行贡献：

1. Fork 本仓库到您的GitHub账号
2. 创建特性分支进行开发
3. 提交代码更改并推送到您的Fork仓库
4. 提交Pull Request，描述您的更改和改进

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 用于构建优雅的GUI界面
- [Pillow](https://python-pillow.org/) - 提供强大的图像处理功能
- [pillow-heif](https://pypi.org/project/pillow-heif/) - 支持HEIC和AVIF格式的处理
- [Pillow-JXL-Plugin](https://pypi.org/project/Pillow-JXL-Plugin/) - 支持JPEG XL格式的处理

## 💡 注意事项

- 转换某些特殊格式（如HEIC、AVIF、JXL）时，需要确保相应的依赖库已正确安装
- 批量转换大量图片时，可能会占用较多系统资源，请耐心等待
- 如遇到程序无法正常启动或功能异常，请尝试以管理员身份运行程序