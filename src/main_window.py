# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
from datetime import datetime
from PIL import Image

# 用于处理资源路径的函数
def resource_path(relative_path):
    """获取资源文件的绝对路径，无论程序是直接运行还是被打包"""
    try:
        # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        # 未打包时，使用当前工作目录
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    return os.path.join(base_path, relative_path)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    # Note: AVIF format uses the same opener as HEIF in current pillow_heif version
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

# 检查JXL格式支持
try:
    # 首先尝试直接导入PIL的JXL插件
    from PIL import JxlImagePlugin
    JXL_SUPPORT = True
except ImportError:
    try:
        # 尝试导入Pillow-JXL-Plugin库
        from pillow_jxl import JpegXLImagePlugin
        JXL_SUPPORT = True
    except ImportError:
        try:
            # 尝试导入pillow-jxl库
            import pillow_jxl
            pillow_jxl.register_jxl_opener()
            JXL_SUPPORT = True
        except ImportError:
            try:
                # 尝试另一种可能的导入方式
                import jpegxl
                jpegxl.register_jxl_opener()
                JXL_SUPPORT = True
            except ImportError:
                JXL_SUPPORT = False
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QRect
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont, QImage, QLinearGradient, QRadialGradient
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QListWidget, QListWidgetItem, QComboBox,
                            QSpinBox, QSlider, QProgressBar, QMessageBox, QGroupBox, QCheckBox,
                            QRadioButton, QButtonGroup, QTabWidget, QScrollArea, QSplitter,
                            QFrame, QStyle, QStyleOption, QDesktopWidget, QSizePolicy, QGridLayout,
                            QLineEdit, QTextEdit, QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox,
                            QGraphicsDropShadowEffect)

class ImageConverterThread(QThread):
    """图片转换线程"""
    progress_updated = pyqtSignal(int)
    conversion_completed = pyqtSignal()
    conversion_failed = pyqtSignal(str)
    
    def __init__(self, input_files, output_dir, output_format, quality, resize_option, resize_width, resize_height, parent=None):
        super().__init__(parent)
        self.input_files = input_files
        self.output_dir = output_dir
        self.output_format = output_format
        self.quality = quality
        self.resize_option = resize_option
        self.resize_width = resize_width
        self.resize_height = resize_height
        self.is_running = True
        self._last_progress_update = 0  # 上次更新进度的时间
        self._progress_update_threshold = 100  # 进度更新阈值（毫秒）
        self._processed_files = 0  # 已处理的文件数
    
    def run(self):
        try:
            total_files = len(self.input_files)
            start_time = datetime.now()
            
            for i, input_file in enumerate(self.input_files):
                if not self.is_running:
                    break
                    
                # 获取文件名（不含扩展名）
                filename = os.path.splitext(os.path.basename(input_file))[0]
                output_file = os.path.join(self.output_dir, f"{filename}.{self.output_format.lower()}")
                
                # 检查输出目录是否存在，不存在则创建
                os.makedirs(self.output_dir, exist_ok=True)
                
                # 打开图片
                with Image.open(input_file) as img:
                    # 处理透明通道（如果是PNG转JPEG）
                    if img.mode in ('RGBA', 'LA') and self.output_format.lower() == 'jpeg':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # 调整大小 - 使用更高效的算法
                    if self.resize_option == "width":
                        width_percent = (self.resize_width / float(img.size[0]))
                        height_size = int((float(img.size[1]) * float(width_percent)))
                        img = img.resize((self.resize_width, height_size), Image.LANCZOS)
                    elif self.resize_option == "height":
                        height_percent = (self.resize_height / float(img.size[1]))
                        width_size = int((float(img.size[0]) * float(height_percent)))
                        img = img.resize((width_size, self.resize_height), Image.LANCZOS)
                    elif self.resize_option == "both":
                        img = img.resize((self.resize_width, self.resize_height), Image.LANCZOS)

                    
                    # 保存图片 - 优化保存参数
                    save_params = {}
                    if self.output_format.lower() == 'jpeg':
                        save_params = {'format': 'JPEG', 'quality': self.quality, 'optimize': True}
                    elif self.output_format.lower() == 'png':
                        save_params = {'format': 'PNG', 'optimize': True}
                        # PNG格式不使用quality参数
                        if 'quality' in save_params:
                            del save_params['quality']
                    elif self.output_format.lower() == 'webp':
                        save_params = {'format': 'WEBP', 'quality': self.quality, 'optimize': True}
                    elif self.output_format.lower() == 'bmp':
                        save_params = {'format': 'BMP'}
                    elif self.output_format.lower() == 'tiff':
                        save_params = {'format': 'TIFF'}
                    elif self.output_format.lower() == 'gif':
                        save_params = {'format': 'GIF'}


                    elif self.output_format.lower() == 'avif':
                        if not HEIF_SUPPORT:
                            raise Exception("AVIF格式需要安装pillow-heif库支持。请运行: pip install pillow-heif")
                        save_params = {'format': 'AVIF', 'quality': self.quality}
                    elif self.output_format.lower() == 'jpeg2000':
                        save_params = {'format': 'JPEG2000', 'quality': self.quality}
                    elif self.output_format.lower() == 'tga':
                        save_params = {'format': 'TGA'}
                    elif self.output_format.lower() == 'jxl':
                        if not JXL_SUPPORT:
                            raise Exception("JXL格式需要安装Pillow-JXL-Plugin库支持。请运行: pip install Pillow-JXL-Plugin")
                        save_params = {'format': 'JXL', 'quality': self.quality}
                    
                    img.save(output_file, **save_params)
                
                # 更新处理文件数
                self._processed_files += 1
                
                # 限制进度更新频率，减少UI刷新
                current_time = datetime.now()
                elapsed_ms = (current_time - start_time).total_seconds() * 1000
                
                # 每处理完一个文件或超过阈值时间才更新进度
                if self._processed_files == total_files or elapsed_ms - self._last_progress_update >= self._progress_update_threshold:
                    progress = int((i + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    self._last_progress_update = elapsed_ms
            
            self.conversion_completed.emit()
        except Exception as e:
            self.conversion_failed.emit(str(e))
    
    def stop(self):
        self.is_running = False

class GlassEffectWidget(QWidget):
    """液态玻璃效果的基础部件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._glass_color = QColor(255, 255, 255, 180)  # 半透明白色
        self._border_color = QColor(255, 255, 255, 100)
        self._border_radius = 20
        self._shadow_blur = 20
        self._shadow_color = QColor(0, 0, 0, 50)
        self._highlight_color = QColor(255, 255, 255, 150)
        self._cached_background = None  # 缓存背景
        self._needs_background_update = True  # 是否需要更新背景
        
    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 如果需要更新背景或窗口大小改变
        if self._needs_background_update or self._cached_background is None or self._cached_background.size() != self.size():
            self._updateBackgroundCache()
            self._needs_background_update = False
        
        # 绘制缓存的背景
        if self._cached_background:
            painter.drawPixmap(0, 0, self._cached_background)
    
    def _updateBackgroundCache(self):
        """更新背景缓存"""
        # 创建与窗口大小相同的缓存图像
        self._cached_background = QPixmap(self.size())
        self._cached_background.fill(Qt.transparent)
        
        painter = QPainter(self._cached_background)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 绘制多层阴影，增加深度感
        shadow_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(Qt.NoPen)
        
        # 外层阴影 - 更模糊，更扩散
        for i in range(self._shadow_blur):
            alpha = int(self._shadow_color.alpha() * (1 - i / self._shadow_blur) * 0.6)
            color = QColor(self._shadow_color.red(), self._shadow_color.green(), 
                          self._shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 内层阴影 - 更锐利，更集中
        inner_shadow_rect = self.rect().adjusted(5, 5, -5, -5)
        for i in range(self._shadow_blur // 2):
            alpha = int(self._shadow_color.alpha() * (1 - i / (self._shadow_blur // 2)) * 0.4)
            color = QColor(self._shadow_color.red(), self._shadow_color.green(), 
                          self._shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(inner_shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 绘制玻璃背景
        painter.setBrush(QBrush(self._glass_color))
        painter.setPen(QPen(self._border_color, 1))
        painter.drawRoundedRect(self.rect().adjusted(5, 5, -5, -5), self._border_radius, self._border_radius)
        
        # 绘制多层次高光效果，增加玻璃质感
        # 主高光 - 从左上到右下的线性渐变
        highlight_rect = QRect(self.rect().left() + 10, self.rect().top() + 10, 
                              self.rect().width() - 20, self.rect().height() // 3)
        main_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        main_gradient.setColorAt(0, QColor(255, 255, 255, self._highlight_color.alpha()))
        main_gradient.setColorAt(0.7, QColor(255, 255, 255, self._highlight_color.alpha() // 2))
        main_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, self._border_radius, self._border_radius)
        
        # 绘制边缘高光，增强玻璃边缘的立体感
        edge_highlight_width = 3
        edge_rect = self.rect().adjusted(5, 5, -5, -5)
        
        # 创建边缘高光的渐变
        edge_gradient = QLinearGradient(edge_rect.topLeft(), edge_rect.topRight())
        edge_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        edge_gradient.setColorAt(0.2, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(0.5, QColor(255, 255, 255, 120))
        edge_gradient.setColorAt(0.8, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(QPen(edge_gradient, edge_highlight_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(edge_rect, self._border_radius, self._border_radius)
        
        painter.end()
    
    def resizeEvent(self, event):
        """窗口大小改变时需要更新缓存"""
        self._needs_background_update = True
        super().resizeEvent(event)
    
    def setGlassColor(self, color):
        self._glass_color = color
        self._needs_background_update = True
        self.update()
    
    def setBorderColor(self, color):
        self._border_color = color
        self._needs_background_update = True
        self.update()
    
    def setBorderRadius(self, radius):
        self._border_radius = radius
        self._needs_background_update = True
        self.update()
    
    def setTransparency(self, transparency):
        """设置玻璃效果透明度"""
        # 更新颜色的透明度
        self._glass_color.setAlpha(transparency)
        self._border_color.setAlpha(max(50, transparency // 2))
        self._shadow_color.setAlpha(max(30, transparency // 3))
        self._highlight_color.setAlpha(min(255, transparency - 30))
        
        # 标记需要更新背景
        self._needs_background_update = True
        self.update()

class HoverableListWidget(QListWidget):
    """列表部件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal_background = QColor(255, 255, 255, 180)
        self._current_background = QColor(self._normal_background)
        self._stylesheet_cache = {}  # 缓存样式表，避免频繁计算
        self._last_theme = None  # 记录上次主题，避免不必要的样式表更新
        self._selection_timer = None  # 选择动画定时器
        self._selection_animation = False  # 是否有选择动画
        self._selection_progress = 0.0  # 选择动画进度
        self._selection_duration = 150  # 选择动画持续时间
        self._selection_start_time = 0  # 选择动画开始时间
        self._selected_item = None  # 当前选中的项
        self._updateStylesheet()  # 初始化样式表
        
        # 启用拖拽功能
        self.setAcceptDrops(True)
        
        # 设置为网格布局以更好地显示图片预览
        self.setViewMode(QListWidget.IconMode)
        self.setMovement(QListWidget.Static)
        self.setResizeMode(QListWidget.Adjust)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        super().mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        """鼠标点击事件 - 点击空白区域触发文件上传"""
        super().mousePressEvent(event)
        
        # 获取点击位置的项
        item = self.itemAt(event.pos())
        
        # 如果点击的是空白区域（没有项）
        if item is None:
            # 改进的MainWindow查找方法
            main_window = None
            current_widget = self
            
            # 向上遍历父级组件，直到找到MainWindow
            while current_widget is not None:
                if hasattr(current_widget, 'addFiles') and callable(getattr(current_widget, 'addFiles')):
                    main_window = current_widget
                    break
                current_widget = current_widget.parent()
            
            # 如果通过父级链没找到，尝试通过顶级窗口查找
            if main_window is None:
                from PyQt5.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    for widget in app.topLevelWidgets():
                        if hasattr(widget, 'addFiles') and callable(getattr(widget, 'addFiles')):
                            main_window = widget
                            break
            
            if main_window:
                main_window.addFiles()
            else:
                # 作为备选方案，直接创建文件选择对话框
                self._showFileDialogDirectly()
    
    def _showFileDialogDirectly(self):
        """直接显示文件选择对话框"""
        from PyQt5.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;所有文件 (*)"
        )
        
        if files:
            # 找到MainWindow实例来处理文件
            main_window = None
            current_widget = self
            while current_widget is not None:
                if hasattr(current_widget, 'addFilesToInput') and callable(getattr(current_widget, 'addFilesToInput')):
                    main_window = current_widget
                    break
                current_widget = current_widget.parent()
            
            if main_window:
                main_window.addFilesToInput(files)
            else:
                print("警告：无法找到处理文件的MainWindow实例")
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = []
            
            # 处理拖拽的文件和文件夹
            for url in urls:
                path = url.toLocalFile()
                if os.path.isfile(path):
                    # 检查文件是否为图片
                    if self.isImageFile(path):
                        files.append(path)
                elif os.path.isdir(path):
                    # 处理文件夹中的图片
                    for root, _, file_names in os.walk(path):
                        for file_name in file_names:
                            file_path = os.path.join(root, file_name)
                            if self.isImageFile(file_path):
                                files.append(file_path)
            
            # 如果有有效的图片文件，添加到列表
            if files:
                # 找到MainWindow实例
                main_window = self
                while main_window and not hasattr(main_window, 'addFilesToInput'):
                    main_window = main_window.parent()
                    
                if main_window:
                    main_window.addFilesToInput(files)
                
    def isImageFile(self, file_path):
        """检查文件是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp', '.avif']
        _, ext = os.path.splitext(file_path.lower())
        return ext in image_extensions
    
    
    
    
    
    
    
    def _updateStylesheet(self):
        """更新样式表"""
        # 获取当前主题
        theme = "light"  # 默认浅色主题
        if hasattr(self.parent(), 'settings'):
            theme_setting = self.parent().settings.get("theme", "浅色")
            if theme_setting == "深色":
                theme = "dark"
        
        # 检查是否需要更新样式表
        if self._last_theme == theme and theme in self._stylesheet_cache:
            # 使用缓存的样式表
            self.setStyleSheet(self._stylesheet_cache[theme])
            return
        
        # 根据主题设置基础样式
        if theme == "dark":
            base_bg = "rgba(45, 45, 48, 180)"
            border_color = "#3F3F46"
            text_color = "#FFFFFF"
            selected_bg = "#007ACC"
            selected_text = "white"
        else:
            base_bg = "rgba(255, 255, 255, 180)"
            border_color = "#CCCCCC"
            text_color = "#333333"
            selected_bg = "#007ACC"
            selected_text = "white"
        
        # 构建样式表
        stylesheet = f"""
            QListWidget {{
                background-color: {base_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                color: {text_color};
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 5px;
                border-radius: 3px;
                margin: 1px;
            }}
            QListWidget::item:selected {{
                background-color: {selected_bg};
                color: {selected_text};
            }}
        """
        
        # 缓存样式表
        self._stylesheet_cache[theme] = stylesheet
        
        # 记录当前主题
        self._last_theme = theme
        
        # 应用样式表
        self.setStyleSheet(stylesheet)
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._selection_timer:
            self._updateSelectionAnimation()
    
    def setTransparency(self, transparency):
        """设置透明度"""
        self._normal_background.setAlpha(transparency)
        self._updateStylesheet()
    
    def _startSelectionAnimation(self, item):
        """启动选择动画"""
        self._selected_item = item
        self._selection_animation = True
        self._selection_progress = 0.0
        self._selection_start_time = 0
        
        # 停止可能正在运行的选择动画
        if self._selection_timer:
            self.killTimer(self._selection_timer)
        
        # 启动新的选择动画
        self._selection_timer = self.startTimer(16)  # 约60fps
    
    def _updateSelectionAnimation(self):
        """更新选择动画进度"""
        if self._selection_start_time == 0:
            self._selection_start_time = self._selection_timer
        
        elapsed = self._selection_timer - self._selection_start_time
        self._selection_progress = min(1.0, elapsed / self._selection_duration)
        
        # 更新选中项的视觉效果
        if self._selected_item:
            # 创建选中项的视觉效果
            font = self._selected_item.font()
            font.setBold(True)
            self._selected_item.setFont(font)
            
            # 可以在这里添加更多视觉效果，如颜色变化、缩放等
        
        # 动画完成
        if self._selection_progress >= 1.0:
            self.killTimer(self._selection_timer)
            self._selection_timer = None
            self._selection_animation = False

class HoverableComboBox(QComboBox):
    """下拉框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal_background = QColor(255, 255, 255, 180)
        self._current_background = QColor(self._normal_background)
        self._updateStylesheet()
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
    
    
    
    
    
    
    
    def _updateStylesheet(self):
        """更新样式表"""
        # 获取当前主题
        theme = "light"  # 默认浅色主题
        if hasattr(self.parent(), 'settings'):
            theme_setting = self.parent().settings.get("theme", "浅色")
            if theme_setting == "深色":
                theme = "dark"
        
        # 根据主题设置基础样式
        if theme == "dark":
            text_color = "#FFFFFF"
            border_color = "#3F3F46"
            dropdown_arrow_color = "#FFFFFF"
            current_bg = "rgba(45, 45, 48, 180)"
        else:
            text_color = "#333333"
            border_color = "#CCCCCC"
            dropdown_arrow_color = "#333333"
            current_bg = "rgba(255, 255, 255, 180)"
        
        # 构建样式表
        stylesheet = f"""
            QComboBox {{
                background-color: {current_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
                color: {text_color};
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {dropdown_arrow_color};
            }}
            QComboBox QAbstractItemView {{
                background-color: {current_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                color: {text_color};
                selection-background-color: #007ACC;
                selection-color: white;
            }}
        """
        
        self.setStyleSheet(stylesheet)
    
    def timerEvent(self, event):
        """定时器事件"""
        pass
    
    def setTransparency(self, transparency):
        """设置透明度"""
        self._normal_background.setAlpha(transparency)
        self._updateStylesheet()

class HoverableLineEdit(QLineEdit):
    """带有悬浮效果的输入框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._normal_background = QColor(255, 255, 255, 180)
        self._hover_background = QColor(255, 255, 255, 220)
        self._focus_background = QColor(255, 255, 255, 240)
        self._current_background = QColor(self._normal_background)
        self._is_hovered = False
        self._is_focused = False
        self._hover_animation_progress = 0.0
        self._hover_animation_timer = None
        self._hover_animation_duration = 150  # 减少动画持续时间，提高响应速度
        self._hover_start_time = 0
        self._last_hover_time = 0  # 上次悬浮时间，用于防止频繁触发动画
        
    def enterEvent(self, event):
        """鼠标进入事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if not self._is_hovered and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_hovered = True
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if self._is_hovered and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_hovered = False
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().leaveEvent(event)
    
    def focusInEvent(self, event):
        """焦点进入事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if not self._is_focused and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_focused = True
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """焦点离开事件 - 优化动画触发"""
        current_time = self._hover_animation_timer if self._hover_animation_timer else 0
        if self._is_focused and current_time - self._last_hover_time > 100:  # 增加阈值到100ms
            self._is_focused = False
            self._last_hover_time = current_time
            self._startHoverAnimation()
        super().focusOutEvent(event)
    
    def _startHoverAnimation(self):
        """开始悬浮动画"""
        self._hover_animation_progress = 0.0
        self._hover_start_time = 0
        
        # 如果已有定时器，先停止
        if self._hover_animation_timer:
            self.killTimer(self._hover_animation_timer)
        
        # 启动新的定时器
        self._hover_animation_timer = self.startTimer(16)  # 约60fps
    
    def _updateHoverAnimation(self):
        """更新悬浮动画进度"""
        if self._hover_start_time == 0:
            self._hover_start_time = self._hover_animation_timer
        
        elapsed = self._hover_animation_timer - self._hover_start_time
        self._hover_animation_progress = min(1.0, elapsed / self._hover_animation_duration)
        
        # 使用三次贝塞尔缓动函数使动画更自然
        eased_progress = self._easeInOutCubic(self._hover_animation_progress)
        
        # 确定目标颜色
        if self._is_focused:
            target_color = self._focus_background
        elif self._is_hovered:
            target_color = self._hover_background
        else:
            target_color = self._normal_background
        
        # 保存之前的颜色值用于比较
        prev_color = self._current_background
        
        # 更新背景颜色
        r = int(self._current_background.red() + 
               (target_color.red() - self._current_background.red()) * 
               eased_progress)
        g = int(self._current_background.green() + 
               (target_color.green() - self._current_background.green()) * 
               eased_progress)
        b = int(self._current_background.blue() + 
               (target_color.blue() - self._current_background.blue()) * 
               eased_progress)
        a = int(self._current_background.alpha() + 
               (target_color.alpha() - self._current_background.alpha()) * 
               eased_progress)
        self._current_background = QColor(r, g, b, a)
        
        # 只有当颜色变化超过阈值时才更新样式，减少不必要的重绘
        color_changed = (abs(prev_color.red() - self._current_background.red()) > 5 or
                        abs(prev_color.green() - self._current_background.green()) > 5 or
                        abs(prev_color.blue() - self._current_background.blue()) > 5 or
                        abs(prev_color.alpha() - self._current_background.alpha()) > 5)
        
        if color_changed or self._hover_animation_progress >= 1.0:
            # 更新样式
            self._updateStylesheet()
        
        # 动画完成
        if self._hover_animation_progress >= 1.0:
            self._current_background = QColor(target_color)
            self.killTimer(self._hover_animation_timer)
            self._hover_animation_timer = None
    
    def _easeInOutQuad(self, t):
        """二次缓动函数"""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
    
    def _updateStylesheet(self):
        """更新样式表"""
        # 获取当前主题
        theme = "light"  # 默认浅色主题
        if hasattr(self.parent(), 'settings'):
            theme_setting = self.parent().settings.get("theme", "浅色")
            if theme_setting == "深色":
                theme = "dark"
        
        # 根据主题设置基础样式
        if theme == "dark":
            text_color = "#FFFFFF"
            border_color = "#3F3F46"
            focus_border_color = "#007ACC"
        else:
            text_color = "#333333"
            border_color = "#CCCCCC"
            focus_border_color = "#007ACC"
        
        # 设置当前背景颜色
        current_bg = f"rgba({self._current_background.red()}, {self._current_background.green()}, {self._current_background.blue()}, {self._current_background.alpha()})"
        
        # 构建样式表
        stylesheet = f"""
            QLineEdit {{
                background-color: {current_bg};
                border: 1px solid {border_color};
                border-radius: 5px;
                padding: 5px;
                color: {text_color};
            }}
            QLineEdit:focus {{
                border: 1px solid {focus_border_color};
            }}
        """
        
        self.setStyleSheet(stylesheet)
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._hover_animation_timer:
            self._updateHoverAnimation()
    
    def setTransparency(self, transparency):
        """设置透明度"""
        self._normal_background.setAlpha(transparency)
        self._hover_background.setAlpha(min(255, transparency + 40))
        self._focus_background.setAlpha(min(255, transparency + 60))
        self._updateStylesheet()

class GlassButton(QPushButton):
    """液态玻璃效果的按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._glass_color = QColor(255, 255, 255, 180)
        self._hover_color = QColor(255, 255, 255, 220)
        self._pressed_color = QColor(255, 255, 255, 150)
        self._text_color = QColor(50, 50, 50)
        self._border_radius = 15
        self._is_hovered = False
        self._is_pressed = False
        self._current_color = self._glass_color  # 当前颜色
        self._target_color = self._glass_color  # 目标颜色
        self._cached_pixmap = None  # 缓存按钮图像
        self._needs_update = True  # 是否需要更新缓存
        self._animation_progress = 0.0  # 动画进度 (0.0 到 1.0)
        self._animation_timer = None  # 动画定时器
        self._animation_duration = 200  # 增加动画持续时间，使效果更流畅
        self._animation_start_time = 0  # 动画开始时间
        self._last_hover_time = 0  # 上次悬浮时间，用于防止频繁触发动画
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        
        # 波纹效果相关
        self._ripple_animation = False  # 是否有波纹动画
        self._ripple_progress = 0.0  # 波纹动画进度
        self._ripple_timer = None  # 波纹动画定时器
        self._ripple_duration = 400  # 增加波纹动画持续时间，使效果更自然
        self._ripple_start_time = 0  # 波纹动画开始时间
        self._ripple_center = QPoint()  # 波纹中心点
        self._ripple_radius = 0  # 波纹半径
        self._ripple_max_radius = 0  # 波纹最大半径
        
        # 光效属性
        self._light_source_pos = QPoint(int(0.3 * 100), int(0.3 * 100))  # 光源位置（相对位置，存储为整数）
        self._ambient_light = 0.6  # 环境光强度
        self._specular_strength = 0.8  # 镜面反射强度
        self._normal_shadow_blur = 15  # 正常状态阴影模糊度
        self._hover_shadow_blur = 20  # 悬浮状态阴影模糊度
        self._normal_shadow_color = QColor(0, 0, 0, 100)  # 正常状态阴影颜色
        self._hover_shadow_color = QColor(0, 0, 0, 150)  # 悬浮状态阴影颜色
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 如果需要更新缓存或大小改变
        if self._needs_update or self._cached_pixmap is None or self._cached_pixmap.size() != self.size():
            self._updateCache()
            self._needs_update = False
        
        # 绘制缓存的按钮
        if self._cached_pixmap:
            painter.drawPixmap(0, 0, self._cached_pixmap)
        
        # 绘制波纹效果
        if self._ripple_animation and self._ripple_progress > 0:
            # 计算当前波纹半径
            current_radius = int(self._ripple_max_radius * self._ripple_progress)
            
            # 计算波纹透明度（随着扩散逐渐消失）
            ripple_alpha = int(150 * (1 - self._ripple_progress))
            
            # 绘制多层波纹，增强视觉效果
            for i in range(3):
                # 每层波纹的半径和透明度略有不同
                layer_radius = current_radius - i * 5
                layer_alpha = ripple_alpha // (i + 1)
                
                if layer_radius > 0:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(255, 255, 255, layer_alpha))
                    painter.drawEllipse(
                        self._ripple_center.x() - layer_radius,
                        self._ripple_center.y() - layer_radius,
                        layer_radius * 2,
                        layer_radius * 2
                    )
        
        # 绘制文本（在波纹效果之后，确保文本在最上层）
        painter.setPen(QPen(self._text_color))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        
        # 添加文本阴影效果，增强可读性
        shadow_offset = 1
        painter.setPen(QPen(QColor(0, 0, 0, 50)))
        painter.drawText(
            self.rect().adjusted(shadow_offset, shadow_offset, shadow_offset, shadow_offset), 
            Qt.AlignCenter, 
            self.text()
        )
        
        # 绘制主文本
        painter.setPen(QPen(self._text_color))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        # 如果有动画在进行，继续更新
        if self._animation_timer and self._animation_progress < 1.0:
            self._updateAnimation()
        
        # 如果有波纹动画在进行，继续更新
        if self._ripple_timer and self._ripple_progress < 1.0:
            self._updateRippleAnimation()
    
    def _updateCache(self):
        """更新按钮缓存"""
        # 创建与按钮大小相同的缓存图像
        self._cached_pixmap = QPixmap(self.size())
        self._cached_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self._cached_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 使用动画进度进行颜色插值
        current_color = self._interpolateColor(self._current_color, self._target_color, self._animation_progress)
        
        # 根据悬浮状态选择阴影参数
        current_shadow_blur = self._normal_shadow_blur
        current_shadow_color = self._normal_shadow_color
        
        if self._is_hovered:
            # 在悬浮状态下，根据动画进度插值阴影参数
            progress = self._easeInOutCubic(self._animation_progress)
            current_shadow_blur = int(
                self._normal_shadow_blur + 
                (self._hover_shadow_blur - self._normal_shadow_blur) * 
                progress
            )
            
            # 插值阴影颜色
            r = int(self._normal_shadow_color.red() + 
                   (self._hover_shadow_color.red() - self._normal_shadow_color.red()) * 
                   progress)
            g = int(self._normal_shadow_color.green() + 
                   (self._hover_shadow_color.green() - self._normal_shadow_color.green()) * 
                   progress)
            b = int(self._normal_shadow_color.blue() + 
                   (self._hover_shadow_color.blue() - self._normal_shadow_color.blue()) * 
                   progress)
            a = int(self._normal_shadow_color.alpha() + 
                   (self._hover_shadow_color.alpha() - self._normal_shadow_color.alpha()) * 
                   progress)
            current_shadow_color = QColor(r, g, b, a)
        
        # 绘制多层阴影，增加深度感
        shadow_rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setPen(Qt.NoPen)
        
        # 外层阴影 - 更模糊，更扩散
        for i in range(current_shadow_blur):
            alpha = int(current_shadow_color.alpha() * (1 - i / current_shadow_blur) * 0.6)
            color = QColor(current_shadow_color.red(), current_shadow_color.green(), 
                          current_shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 内层阴影 - 更锐利，更集中
        inner_shadow_rect = self.rect().adjusted(3, 3, -3, -3)
        for i in range(current_shadow_blur // 2):
            alpha = int(current_shadow_color.alpha() * (1 - i / (current_shadow_blur // 2)) * 0.4)
            color = QColor(current_shadow_color.red(), current_shadow_color.green(), 
                          current_shadow_color.blue(), alpha)
            painter.setBrush(color)
            painter.drawRoundedRect(inner_shadow_rect.adjusted(i, i, -i, -i), self._border_radius, self._border_radius)
        
        # 绘制玻璃背景
        painter.setBrush(QBrush(current_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        
        # 绘制多层次高光效果，增加玻璃质感
        # 主高光 - 从左上到右下的线性渐变
        highlight_rect = QRect(self.rect().left() + 5, self.rect().top() + 5, 
                              self.rect().width() - 10, self.rect().height() // 3)
        main_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.bottomLeft())
        main_gradient.setColorAt(0, QColor(255, 255, 255, 100))
        main_gradient.setColorAt(0.7, QColor(255, 255, 255, 50))
        main_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(main_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight_rect, self._border_radius, self._border_radius)
        
        # 次级高光 - 径向渐变，模拟点光源反射
        highlight_radius = min(self.rect().width(), self.rect().height()) // 4
        highlight_center = QPoint(
            self.rect().left() + int(self.rect().width() * self._light_source_pos.x() / 100),
            self.rect().top() + int(self.rect().height() * self._light_source_pos.y() / 100)
        )
        
        radial_highlight = QRadialGradient(highlight_center, highlight_radius)
        radial_highlight.setColorAt(0, QColor(255, 255, 255, int(100 * self._specular_strength)))
        radial_highlight.setColorAt(0.5, QColor(255, 255, 255, int(50 * self._specular_strength)))
        radial_highlight.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(QBrush(radial_highlight))
        painter.drawEllipse(highlight_center.x() - highlight_radius, 
                           highlight_center.y() - highlight_radius,
                           highlight_radius * 2, highlight_radius * 2)
        
        # 绘制边缘高光，增强玻璃边缘的立体感
        edge_highlight_width = 2
        edge_rect = self.rect().adjusted(2, 2, -2, -2)
        
        # 创建边缘高光的渐变
        edge_gradient = QLinearGradient(edge_rect.topLeft(), edge_rect.topRight())
        edge_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        edge_gradient.setColorAt(0.2, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(0.5, QColor(255, 255, 255, 120))
        edge_gradient.setColorAt(0.8, QColor(255, 255, 255, 80))
        edge_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setPen(QPen(edge_gradient, edge_highlight_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(edge_rect, self._border_radius, self._border_radius)
        
        painter.end()
    
    def _interpolateColor(self, start_color, end_color, progress):
        """在两种颜色之间进行插值，使用改进的缓动函数"""
        # 使用三次贝塞尔缓动函数，使动画更加自然
        eased_progress = self._easeInOutCubic(progress)
        
        r = int(start_color.red() + (end_color.red() - start_color.red()) * eased_progress)
        g = int(start_color.green() + (end_color.green() - start_color.green()) * eased_progress)
        b = int(start_color.blue() + (end_color.blue() - start_color.blue()) * eased_progress)
        a = int(start_color.alpha() + (end_color.alpha() - start_color.alpha()) * eased_progress)
        return QColor(r, g, b, a)
    
    def _easeInOutCubic(self, t):
        """三次贝塞尔缓动函数，使动画更加自然"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _startAnimation(self, target_color):
        """开始颜色过渡动画"""
        self._target_color = target_color
        self._animation_progress = 0.0
        self._animation_start_time = 0
        
        # 如果已有定时器，先停止
        if self._animation_timer:
            self.killTimer(self._animation_timer)
        
        # 启动新的定时器
        self._animation_timer = self.startTimer(16)  # 约60fps
    
    def _updateAnimation(self):
        """更新动画进度"""
        if self._animation_start_time == 0:
            self._animation_start_time = self._animation_timer
        
        elapsed = self._animation_timer - self._animation_start_time
        self._animation_progress = min(1.0, elapsed / self._animation_duration)
        
        # 计算当前颜色
        current_color = self._interpolateColor(self._current_color, self._target_color, self._animation_progress)
        
        # 只有当颜色变化超过阈值时才更新缓存并重绘，减少不必要的重绘
        color_changed = (abs(self._current_color.red() - current_color.red()) > 5 or
                        abs(self._current_color.green() - current_color.green()) > 5 or
                        abs(self._current_color.blue() - current_color.blue()) > 5 or
                        abs(self._current_color.alpha() - current_color.alpha()) > 5)
        
        if color_changed or self._animation_progress >= 1.0:
            # 更新缓存并重绘
            self._needs_update = True
            self.update()
        
        # 动画完成
        if self._animation_progress >= 1.0:
            self._current_color = QColor(self._target_color)
            self.killTimer(self._animation_timer)
            self._animation_timer = None
    
    def timerEvent(self, event):
        """定时器事件"""
        if event.timerId() == self._animation_timer:
            self._updateAnimation()
        elif event.timerId() == self._ripple_timer:
            self._updateRippleAnimation()
    
    def _startRippleAnimation(self, pos):
        """开始波纹动画"""
        self._ripple_animation = True
        self._ripple_progress = 0.0
        self._ripple_start_time = 0
        self._ripple_center = pos
        
        # 计算最大波纹半径（从点击点到按钮最远角的距离）
        dx = max(pos.x(), self.width() - pos.x())
        dy = max(pos.y(), self.height() - pos.y())
        self._ripple_max_radius = int((dx * dx + dy * dy) ** 0.5)
        
        # 如果已有定时器，先停止
        if self._ripple_timer:
            self.killTimer(self._ripple_timer)
        
        # 启动新的定时器
        self._ripple_timer = self.startTimer(16)  # 约60fps
    
    def _updateRippleAnimation(self):
        """更新波纹动画进度"""
        if self._ripple_start_time == 0:
            self._ripple_start_time = self._ripple_timer
        
        elapsed = self._ripple_timer - self._ripple_start_time
        self._ripple_progress = min(1.0, elapsed / self._ripple_duration)
        
        # 使用缓出函数使波纹扩散更自然
        eased_progress = self._easeOutQuad(self._ripple_progress)
        self._ripple_progress = eased_progress
        
        # 重绘
        self.update()
        
        # 动画完成
        if self._ripple_progress >= 1.0:
            self._ripple_animation = False
            self.killTimer(self._ripple_timer)
            self._ripple_timer = None
    
    def _easeOutQuad(self, t):
        """二次缓出函数"""
        return 1 - (1 - t) * (1 - t)
    
    def enterEvent(self, event):
        """鼠标进入事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if not self._is_hovered and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_hovered = True
            self._last_hover_time = current_time
            if not self._is_pressed:
                self._startAnimation(self._hover_color)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if self._is_hovered and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_hovered = False
            self._last_hover_time = current_time
            if not self._is_pressed:
                self._startAnimation(self._glass_color)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if not self._is_pressed and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_pressed = True
            self._last_hover_time = current_time
            self._startAnimation(self._pressed_color)
            
            # 开始波纹动画
            self._startRippleAnimation(event.pos())
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 优化动画触发"""
        current_time = self._animation_timer if self._animation_timer else 0
        if self._is_pressed and current_time - getattr(self, '_last_hover_time', 0) > 100:  # 增加阈值到100ms
            self._is_pressed = False
            self._last_hover_time = current_time
            if self._is_hovered:
                self._startAnimation(self._hover_color)
            else:
                self._startAnimation(self._glass_color)
        super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        """按钮大小改变时需要更新缓存"""
        self._needs_update = True
        super().resizeEvent(event)
    
    def setTransparency(self, transparency):
        """设置按钮透明度"""
        # 更新所有颜色的透明度
        self._glass_color.setAlpha(transparency)
        self._hover_color.setAlpha(min(255, transparency + 40))  # 悬停时稍微增加透明度
        self._pressed_color.setAlpha(max(100, transparency - 30))  # 按下时稍微降低透明度
        
        # 如果当前没有动画，更新当前颜色
        if not self._animation_timer:
            if self._is_pressed:
                self._current_color = QColor(self._pressed_color)
            elif self._is_hovered:
                self._current_color = QColor(self._hover_color)
            else:
                self._current_color = QColor(self._glass_color)
        
        # 标记需要更新缓存
        self._needs_update = True
        self.update()

class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self.initUI()
        self.loadSettings()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # 创建玻璃效果容器
        glass_container = GlassEffectWidget(self)
        glass_layout = QVBoxLayout(glass_container)
        glass_layout.setContentsMargins(20, 20, 20, 20)
        glass_layout.setSpacing(15)
        
        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout()
        
        self.overwrite_checkbox = QCheckBox("覆盖同名文件")
        output_layout.addRow(self.overwrite_checkbox)
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_label = QLabel("输出格式:")
        format_layout.addWidget(format_label)
        
        self.output_format_combo = HoverableComboBox()
        self.output_format_combo.addItems(["JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "AVIF", "JPEG2000", "TGA", "JXL"])
        format_layout.addWidget(self.output_format_combo)
        output_layout.addRow(format_layout)
        
        # 质量设置
        quality_layout = QHBoxLayout()
        quality_label = QLabel("图片质量:")
        quality_layout.addWidget(quality_label)
        
        self.output_quality_slider = QSlider(Qt.Horizontal)
        self.output_quality_slider.setRange(1, 100)
        self.output_quality_slider.setValue(90)
        self.output_quality_label = QLabel("90")
        
        self.output_quality_slider.valueChanged.connect(lambda v: self.output_quality_label.setText(str(v)))
        quality_layout.addWidget(self.output_quality_slider)
        quality_layout.addWidget(self.output_quality_label)
        output_layout.addRow(quality_layout)
        
        output_group.setLayout(output_layout)
        glass_layout.addWidget(output_group)
        
        # 尺寸调整组
        resize_group = QGroupBox("尺寸调整")
        resize_layout = QVBoxLayout()
        
        # 尺寸调整选项
        resize_options_layout = QHBoxLayout()
        
        self.no_resize_radio = QRadioButton("不调整")
        self.no_resize_radio.setChecked(True)
        resize_options_layout.addWidget(self.no_resize_radio)
        
        self.resize_width_radio = QRadioButton("按宽度")
        resize_options_layout.addWidget(self.resize_width_radio)
        
        self.resize_height_radio = QRadioButton("按高度")
        resize_options_layout.addWidget(self.resize_height_radio)
        
        self.resize_both_radio = QRadioButton("自定义")
        resize_options_layout.addWidget(self.resize_both_radio)
        
        resize_layout.addLayout(resize_options_layout)
        
        # 尺寸设置
        size_layout = QHBoxLayout()
        
        width_label = QLabel("宽度:")
        size_layout.addWidget(width_label)
        
        self.output_width_spin = QSpinBox()
        self.output_width_spin.setRange(1, 5000)
        self.output_width_spin.setValue(800)
        self.output_width_spin.setEnabled(False)
        size_layout.addWidget(self.output_width_spin)
        
        height_label = QLabel("高度:")
        size_layout.addWidget(height_label)
        
        self.output_height_spin = QSpinBox()
        self.output_height_spin.setRange(1, 5000)
        self.output_height_spin.setValue(600)
        self.output_height_spin.setEnabled(False)
        size_layout.addWidget(self.output_height_spin)
        
        resize_layout.addLayout(size_layout)
        
        # 连接单选按钮信号
        self.no_resize_radio.toggled.connect(lambda: self.updateResizeOptions())
        self.resize_width_radio.toggled.connect(lambda: self.updateResizeOptions())
        self.resize_height_radio.toggled.connect(lambda: self.updateResizeOptions())
        self.resize_both_radio.toggled.connect(lambda: self.updateResizeOptions())
        
        resize_group.setLayout(resize_layout)
        glass_layout.addWidget(resize_group)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "自动"])
        ui_layout.addRow("主题:", self.theme_combo)
        
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(100, 255)
        self.transparency_slider.setValue(200)
        self.transparency_label = QLabel("200")
        
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(self.transparency_slider)
        transparency_layout.addWidget(self.transparency_label)
        
        self.transparency_slider.valueChanged.connect(lambda v: self.transparency_label.setText(str(v)))
        ui_layout.addRow("玻璃透明度:", transparency_layout)
        
        ui_group.setLayout(ui_layout)
        glass_layout.addWidget(ui_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        ok_btn = GlassButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = GlassButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        glass_layout.addLayout(button_layout)
        layout.addWidget(glass_container)
        self.setLayout(layout)
    
    def updateResizeOptions(self):
        # 更新尺寸调整选项的可用状态
        self.output_width_spin.setEnabled(self.resize_width_radio.isChecked() or self.resize_both_radio.isChecked())
        self.output_height_spin.setEnabled(self.resize_height_radio.isChecked() or self.resize_both_radio.isChecked())
    
    def loadSettings(self):
        # 加载设置
        self.overwrite_checkbox.setChecked(self.settings.get("overwrite_files", False))
        self.theme_combo.setCurrentText(self.settings.get("theme", "浅色"))
        self.transparency_slider.setValue(self.settings.get("glass_transparency", 200))
        
        # 加载输出设置
        self.output_format_combo.setCurrentText(self.settings.get("output_format", "JPEG"))
        self.output_quality_slider.setValue(self.settings.get("output_quality", 90))
        
        # 加载尺寸调整设置
        resize_option = self.settings.get("resize_option", "none")
        if resize_option == "none":
            self.no_resize_radio.setChecked(True)
        elif resize_option == "width":
            self.resize_width_radio.setChecked(True)
        elif resize_option == "height":
            self.resize_height_radio.setChecked(True)
        else:  # both
            self.resize_both_radio.setChecked(True)
            
        self.output_width_spin.setValue(self.settings.get("output_width", 800))
        self.output_height_spin.setValue(self.settings.get("output_height", 600))
    
    def getSettings(self):
        # 返回设置
        settings = {
            "overwrite_files": self.overwrite_checkbox.isChecked(),
            "theme": self.theme_combo.currentText(),
            "glass_transparency": self.transparency_slider.value(),
            # 输出设置
            "output_format": self.output_format_combo.currentText(),
            "output_quality": self.output_quality_slider.value(),
            # 尺寸调整设置
            "output_width": self.output_width_spin.value(),
            "output_height": self.output_height_spin.value()
        }
        
        # 添加尺寸调整选项
        if self.no_resize_radio.isChecked():
            settings["resize_option"] = "none"
        elif self.resize_width_radio.isChecked():
            settings["resize_option"] = "width"
        elif self.resize_height_radio.isChecked():
            settings["resize_option"] = "height"
        else:  # both
            settings["resize_option"] = "both"
            
        return settings

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        print("正在初始化主窗口...")
        super().__init__()
        print("设置窗口标题和大小...")
        self.setWindowTitle("图片批量转换器")
        self.setMinimumSize(900, 600)
        
        # 设置窗口图标
        print("设置窗口图标...")
        self.setWindowIcon(QIcon(resource_path("resources/icon.png")))
        
        # 初始化设置
        print("加载设置...")
        self.settings = self.loadSettings()
        
        # 初始化UI
        print("初始化UI...")
        self.initUI()
        
        # 初始化变量
        print("初始化变量...")
        self.input_files = []
        self.conversion_thread = None
        
        # 应用主题
        print("应用主题...")
        self.applyTheme()
        
        # 启用拖拽功能
        self.setAcceptDrops(True)
        
        print("主窗口初始化完成")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = []
            
            # 处理拖拽的文件和文件夹
            for url in urls:
                path = url.toLocalFile()
                if os.path.isfile(path):
                    # 检查文件是否为图片
                    if self.isImageFile(path):
                        files.append(path)
                elif os.path.isdir(path):
                    # 处理文件夹中的图片
                    for root, _, file_names in os.walk(path):
                        for file_name in file_names:
                            file_path = os.path.join(root, file_name)
                            if self.isImageFile(file_path):
                                files.append(file_path)
            
            # 如果有有效的图片文件，添加到列表
            if files:
                self.addFilesToInput(files)
    
    def isImageFile(self, file_path):
        """检查文件是否为图片文件"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp', '.avif']
        _, ext = os.path.splitext(file_path.lower())
        return ext in image_extensions
    
    def initUI(self):
        print("开始初始化UI...")
        # 创建中央部件
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 创建主内容区域
        print("创建主内容区域...")
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # 左侧面板 - 文件列表
        print("创建左侧面板...")
        left_panel = GlassEffectWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)
        
        # 文件列表标题
        files_title = QLabel("图片列表")
        files_title.setFont(QFont("", 12, QFont.Bold))
        left_layout.addWidget(files_title)
        
        # 文件列表
        print("创建文件列表...")
        self.file_list = HoverableListWidget()
        self.file_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.file_list)
        
        # 文件操作按钮
        print("创建文件操作按钮...")
        file_buttons_layout = QHBoxLayout()
        
        # 清空列表按钮（占据原来添加文件按钮的位置）
        self.clear_files_btn = GlassButton("清空列表")
        self.clear_files_btn.clicked.connect(self.clearFiles)
        self.clear_files_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        file_buttons_layout.addWidget(self.clear_files_btn)
        
        left_layout.addLayout(file_buttons_layout)
        
        # 设置文件列表支持拖拽
        self.file_list.setAcceptDrops(True)
        self.file_list.setIconSize(QSize(100, 100))  # 设置图标大小
        
        # 右侧面板 - 转换设置
        print("创建右侧面板...")
        right_panel = GlassEffectWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)
        
        # 转换设置标题
        settings_title = QLabel("转换设置")
        settings_title.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(settings_title)
        
        # 输出目录
        print("创建输出目录...")
        output_layout = QHBoxLayout()
        output_label = QLabel("输出目录:")
        output_layout.addWidget(output_label)
        
        self.output_dir_edit = HoverableLineEdit()
        self.output_dir_edit.setText(self.settings.get("default_output_dir", os.path.expanduser("~/Pictures")))
        output_layout.addWidget(self.output_dir_edit)
        
        browse_btn = GlassButton("浏览")
        browse_btn.clicked.connect(self.browseOutputDir)
        output_layout.addWidget(browse_btn)
        
        right_layout.addLayout(output_layout)
        
        # 预览区域
        print("创建预览区域...")
        preview_group = QGroupBox("预览效果")
        preview_layout = QVBoxLayout()
        
        # 预览图片
        self.preview_label = QLabel("暂无预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setStyleSheet("border: 2px solid #007ACC; border-radius: 8px; background-color: rgba(240, 240, 240, 180); padding: 10px;")
        self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        preview_layout.addWidget(self.preview_label)
        
        # 预览控制按钮
        preview_controls_layout = QHBoxLayout()
        
        self.clear_preview_btn = GlassButton("清除预览")
        self.clear_preview_btn.clicked.connect(self.clearPreview)
        preview_controls_layout.addWidget(self.clear_preview_btn)
        
        preview_layout.addLayout(preview_controls_layout)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # 转换按钮
        print("创建转换按钮...")
        convert_btn = GlassButton("开始转换")
        convert_btn.setMinimumHeight(50)
        convert_btn.clicked.connect(self.startConversion)
        right_layout.addWidget(convert_btn)
        
        # 进度条
        print("创建进度条...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 添加左右面板到主布局
        print("添加左右面板到主布局...")
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel, 1)
        
        main_layout.addWidget(content_widget)
        
        # 底部按钮栏
        print("创建底部按钮栏...")
        bottom_layout = QHBoxLayout()
        
        settings_btn = GlassButton("设置")
        settings_btn.clicked.connect(self.openSettings)
        bottom_layout.addWidget(settings_btn)
        
        about_btn = GlassButton("关于")
        about_btn.clicked.connect(self.showAbout)
        bottom_layout.addWidget(about_btn)
        
        bottom_layout.addStretch()
        
        exit_btn = GlassButton("退出")
        exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(exit_btn)
        
        main_layout.addLayout(bottom_layout)
        
        print("设置中央部件...")
        self.setCentralWidget(central_widget)
        print("UI初始化完成")
    
    def updateResizeOptions(self):
        # 更新设置中的尺寸调整选项
        resize_option = self.settings.get("resize_option", "none")
        
        # 保存设置
        self.saveSettings()
    
    def previewConversion(self):
        """预览转换效果"""
        if not self.input_files:
            QMessageBox.warning(self, "警告", "请先添加要转换的图片文件！")
            return
        
        # 获取当前选中的图片
        current_item = self.file_list.currentItem()
        if not current_item:
            # 如果没有选中项，使用第一张图片
            if self.file_list.count() > 0:
                current_item = self.file_list.item(0)
            else:
                QMessageBox.warning(self, "警告", "请先添加要转换的图片文件！")
                return
        
        # 获取图片文件路径
        index = self.file_list.row(current_item)
        if index < len(self.input_files):
            input_file = self.input_files[index]
            
            try:
                # 打开原始图片
                with Image.open(input_file) as img:
                    # 创建预览图片的副本
                    preview_img = img.copy()
                    
                    # 应用转换设置
                    output_format = self.settings.get("output_format", "JPEG")
                    quality = self.settings.get("output_quality", 90)
                    resize_option = self.settings.get("resize_option", "none")
                    output_width = self.settings.get("output_width", 800)
                    output_height = self.settings.get("output_height", 600)
                    
                    # 处理透明通道（如果是PNG转JPEG）
                    if preview_img.mode in ('RGBA', 'LA') and output_format.lower() == 'jpeg':
                        background = Image.new('RGB', preview_img.size, (255, 255, 255))
                        background.paste(preview_img, mask=preview_img.split()[-1] if preview_img.mode == 'RGBA' else None)
                        preview_img = background
                    
                    # 调整大小
                    if resize_option == "width":
                        width_percent = (output_width / float(preview_img.size[0]))
                        height_size = int((float(preview_img.size[1]) * float(width_percent)))
                        preview_img = preview_img.resize((output_width, height_size), Image.LANCZOS)
                    elif resize_option == "height":
                        height_percent = (output_height / float(preview_img.size[1]))
                        width_size = int((float(preview_img.size[0]) * float(height_percent)))
                        preview_img = preview_img.resize((width_size, output_height), Image.LANCZOS)
                    elif resize_option == "both":
                        preview_img = preview_img.resize((output_width, output_height), Image.LANCZOS)
                    
                    # 将PIL图像转换为QPixmap并显示
                    # 首先将PIL图像转换为QImage
                    if preview_img.mode == 'RGBA':
                        qimage = QImage(preview_img.tobytes(), preview_img.size[0], preview_img.size[1], QImage.Format_RGBA8888)
                    elif preview_img.mode == 'RGB':
                        qimage = QImage(preview_img.tobytes(), preview_img.size[0], preview_img.size[1], QImage.Format_RGB888)
                    else:
                        # 其他模式转换为RGB
                        preview_img = preview_img.convert('RGB')
                        qimage = QImage(preview_img.tobytes(), preview_img.size[0], preview_img.size[1], QImage.Format_RGB888)
                    
                    # 将QImage转换为QPixmap
                    pixmap = QPixmap.fromImage(qimage)
                    
                    # 创建一个带阴影和圆角的QPixmap
                    shadow_pixmap = QPixmap(pixmap.size() + QSize(20, 20))
                    shadow_pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(shadow_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setRenderHint(QPainter.SmoothPixmapTransform)
                    
                    # 绘制阴影
                    shadow_effect = QGraphicsDropShadowEffect()
                    shadow_effect.setBlurRadius(10)
                    shadow_effect.setColor(QColor(0, 0, 0, 100))
                    shadow_effect.setOffset(5, 5)
                    
                    # 绘制带圆角的图片
                    rounded_rect = QRect(10, 10, pixmap.width(), pixmap.height())
                    painter.setBrush(QBrush(pixmap))
                    painter.drawRoundedRect(rounded_rect, 10, 10)
                    painter.end()
                    
                    # 缩放预览图以适应预览区域，保持高画质
                    preview_size = self.preview_label.size()
                    scaled_pixmap = shadow_pixmap.scaled(preview_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # 显示预览图
                    self.preview_label.setPixmap(scaled_pixmap)
                    
                    # 显示预览信息
                    info_text = f"预览: {output_format} 格式, 质量: {quality}"
                    if resize_option != "none":
                        info_text += f", 尺寸: {preview_img.size[0]}x{preview_img.size[1]}"
                    self.preview_label.setToolTip(info_text)
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"预览过程中发生错误：{str(e)}")
    
    def clearPreview(self):
        """清除预览"""
        self.preview_label.clear()
        self.preview_label.setText("暂无预览")
        self.preview_label.setToolTip("")
    
    def addFiles(self):
        """添加文件到输入列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;所有文件 (*)"
        )
        
        if files:
            self.addFilesToInput(files)
            # 自动预览第一张图片已在addFilesToInput方法中处理
            
    def addFilesToInput(self, files):
        # 批量添加文件，减少UI更新次数
        current_count = len(self.input_files)
        self.input_files.extend(files)
        
        # 如果添加了大量文件，只更新一次列表
        if len(files) > 10:
            self.updateFileList()
        else:
            # 少量文件，逐个添加到列表
            self.file_list.setUpdatesEnabled(False)  # 临时禁用更新
            for file_path in files:
                self.addFileToList(file_path)
            self.file_list.setUpdatesEnabled(True)  # 重新启用更新
        
        # 自动预览第一张添加的图片
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(current_count)  # 选中新添加的第一张图片
            # 预览会自动触发，因为已经连接了currentItemChanged信号
            
    def addFileToList(self, file_path):
        # 创建列表项
        item = QListWidgetItem()
        
        # 创建预览图
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # 缩放预览图以适应图标大小
            scaled_pixmap = pixmap.scaled(
                self.file_list.iconSize(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            item.setIcon(QIcon(scaled_pixmap))
        
        # 设置项的大小
        item.setSizeHint(QSize(self.file_list.iconSize().width() + 10, self.file_list.iconSize().height() + 10))
        
        # 添加到列表
        self.file_list.addItem(item)
        
        # 连接选择变化信号（只需连接一次）
        if not hasattr(self, '_selection_connected'):
            self.file_list.currentItemChanged.connect(self.onFileSelectionChanged)
            self._selection_connected = True
    
    def onFileSelectionChanged(self, current, previous):
        """当文件列表选择变化时更新预览"""
        if current and self.input_files:
            row = self.file_list.row(current)
            if row < len(self.input_files):
                # 立即预览选中的图片
                self.previewConversion()
    
    def clearFiles(self):
        # 优化清空文件列表操作
        if self.input_files:  # 只有在有文件时才执行操作
            self.input_files = []
            self.file_list.clear()  # 直接清空列表，避免调用updateFileList
    
    def updateFileList(self):
        # 优化文件列表更新，减少UI刷新
        self.file_list.setUpdatesEnabled(False)  # 临时禁用更新
        self.file_list.clear()
        
        for file_path in self.input_files:
            self.addFileToList(file_path)
            
        self.file_list.setUpdatesEnabled(True)  # 重新启用更新
    
    def browseOutputDir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            # 立即保存设置，确保输出目录保存到用户上次修改的路径
            self.saveSettings()
    
    def startConversion(self):
        if not self.input_files:
            QMessageBox.warning(self, "警告", "请先添加要转换的图片文件！")
            return
        
        output_dir = self.output_dir_edit.text()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(self, "警告", "请选择有效的输出目录！")
            return
        
        # 确定尺寸调整选项 - 从设置中获取，而不是直接访问UI元素
        resize_option = self.settings.get("resize_option", "none")
        output_width = self.settings.get("output_width", 800)
        output_height = self.settings.get("output_height", 600)
        
        # 创建并启动转换线程
        self.conversion_thread = ImageConverterThread(
            self.input_files,
            output_dir,
            self.settings.get("output_format", "JPEG"),
            self.settings.get("output_quality", 90),
            resize_option,
            output_width,
            output_height
        )
        
        self.conversion_thread.progress_updated.connect(self.updateProgress)
        self.conversion_thread.conversion_completed.connect(self.conversionCompleted)
        self.conversion_thread.conversion_failed.connect(self.conversionFailed)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.conversion_thread.start()
    
    def updateProgress(self, value):
        # 只在进度值变化时更新UI，减少不必要的重绘
        if self.progress_bar.value() != value:
            self.progress_bar.setValue(value)
    
    def conversionCompleted(self):
        self.progress_bar.setVisible(False)
        
        # 显示转换完成提示
        QMessageBox.information(self, "完成", "图片转换已完成！")
    
    def conversionFailed(self, error_msg):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", f"转换过程中发生错误：{error_msg}")
    
    def openSettings(self):
        # 获取当前输出设置
        current_settings = self.settings.copy()
        
        dialog = SettingsDialog(current_settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.getSettings()
            self.saveSettings()
            self.applyTheme()
            # 更新输出目录为系统设置中的默认输出目录
            self.output_dir_edit.setText(self.settings.get("default_output_dir", os.path.expanduser("~/Pictures")))
    

    
    def showAbout(self):
        dialog = AboutDialog(self)
        dialog.exec_()
        
    def applyTheme(self):
        """应用主题"""
        # 从设置中获取主题
        theme = self.settings.get('theme', '浅色')
        
        # 应用对应的样式表
        if theme == '深色':
            self.setStyleSheet(self._getDarkThemeStylesheet())
        else:
            self.setStyleSheet(self._getLightThemeStylesheet())
        
        # 更新玻璃效果透明度
        transparency = self.settings.get('glass_transparency', 200)
        self._updateGlassTransparency(transparency)
        
    def _getDarkThemeStylesheet(self):
        """获取深色主题样式表"""
        return """
            QMainWindow {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget {
                background-color: rgba(45, 45, 48, 180);
                border: 1px solid #3F3F46;
                border-radius: 5px;
                color: #FFFFFF;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
            }
            QComboBox, QLineEdit, QSpinBox {
                background-color: rgba(45, 45, 48, 180);
                border: 1px solid #3F3F46;
                border-radius: 5px;
                padding: 5px;
                color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #FFFFFF;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3F3F46;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007ACC;
                border: 1px solid #007ACC;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QProgressBar {
                border: 1px solid #3F3F46;
                border-radius: 5px;
                text-align: center;
                background-color: rgba(45, 45, 48, 180);
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #007ACC;
                border-radius: 4px;
            }
            QRadioButton {
                color: #FFFFFF;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #3F3F46;
                border-radius: 7px;
            }
            QRadioButton::indicator:checked {
                background-color: #007ACC;
                border: 1px solid #007ACC;
            }
        """
        
    def _getLightThemeStylesheet(self):
        """获取浅色主题样式表"""
        return """
            QMainWindow {
                background-color: #F0F0F0;
                color: #333333;
            }
            QLabel {
                color: #333333;
            }
            QGroupBox {
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                color: #333333;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
            QComboBox, QLineEdit, QSpinBox {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px;
                color: #333333;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #333333;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #CCCCCC;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007ACC;
                border: 1px solid #007ACC;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                text-align: center;
                background-color: rgba(255, 255, 255, 180);
                color: #333333;
            }
            QProgressBar::chunk {
                background-color: #007ACC;
                border-radius: 4px;
            }
            QRadioButton {
                color: #333333;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
                border: 1px solid #CCCCCC;
                border-radius: 7px;
            }
            QRadioButton::indicator:checked {
                background-color: #007ACC;
                border: 1px solid #007ACC;
            }
        """
        
    def _updateGlassTransparency(self, transparency):
        """更新玻璃效果透明度"""
        # 更新所有玻璃效果小部件的透明度
        for widget in self.findChildren(GlassEffectWidget):
            widget.setTransparency(transparency)
        
        # 更新所有玻璃按钮的透明度
        for widget in self.findChildren(GlassButton):
            widget.setTransparency(transparency)
            
        # 更新新的悬浮效果组件的透明度
        for list_widget in self.findChildren(HoverableListWidget):
            list_widget.setTransparency(transparency)
            
        for combo_box in self.findChildren(HoverableComboBox):
            combo_box.setTransparency(transparency)
            
        for line_edit in self.findChildren(HoverableLineEdit):
            line_edit.setTransparency(transparency)
            
    def loadSettings(self):
        settings_file = "settings.json"
        default_settings = {
            "default_output_dir": os.path.expanduser("~/Pictures"),
            "overwrite_files": False,
            "theme": "浅色",
            "glass_transparency": 200,
            # 输出设置
            "output_format": "JPEG",
            "output_quality": 90,
            # 尺寸调整设置
            "resize_option": "none",
            "output_width": 800,
            "output_height": 600
        }
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                    # 合并默认设置和加载的设置，确保所有设置项都存在
                    return {**default_settings, **loaded_settings}
            except:
                return default_settings
        else:
            return default_settings
            
    def saveSettings(self):
        settings_file = "settings.json"
        
        # 获取当前输出设置
        output_format = self.settings.get("output_format", "JPEG")
        output_quality = self.settings.get("output_quality", 90)
        
        # 获取尺寸调整选项
        resize_option = self.settings.get("resize_option", "none")
        
        output_width = self.settings.get("output_width", 800)
        output_height = self.settings.get("output_height", 600)
        
        # 更新设置字典
        self.settings.update({
            "default_output_dir": self.output_dir_edit.text(),
            "output_format": output_format,
            "output_quality": output_quality,
            "resize_option": resize_option,
            "output_width": output_width,
            "output_height": output_height,
            "overwrite_files": self.settings.get("overwrite_files", False),
            "theme": self.settings.get("theme", "浅色"),
            "glass_transparency": self.settings.get("glass_transparency", 200)
        })
        
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存设置失败: {e}")

class AboutDialog(QDialog):
    """关于对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)
        self.setWindowIcon(QIcon(resource_path("resources/icon.png")))
        self.initUI()
        
    def initUI(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 创建玻璃效果容器
        glass_container = GlassEffectWidget(self)
        glass_layout = QVBoxLayout(glass_container)
        glass_layout.setContentsMargins(20, 20, 20, 20)
        glass_layout.setSpacing(20)
        
        # 应用透明度设置
        if hasattr(self.parent(), 'settings'):
            transparency = self.parent().settings.get("glass_transparency", 200)
            glass_container.setTransparency(transparency)
        
        # 应用主题
        if hasattr(self.parent(), 'settings'):
            theme = self.parent().settings.get("theme", "浅色")
            if theme == "深色":
                text_color = "#FFFFFF"
            else:
                text_color = "#333333"
        else:
            text_color = "#333333"
        
        # 图标区域
        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # 创建图标
        icon_label = QLabel()
        icon_pixmap = QPixmap(resource_path("resources/icon.png")).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 文本区域（居中显示，无图标）
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignCenter)
        text_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题 - 优化字体显示效果
        title_label = QLabel("图片批量转换器 v1.0")
        title_font = QFont()
        title_font.setFamily("Microsoft YaHei UI")
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {text_color}; padding: 5px 0;")
        text_layout.addWidget(title_label)
        
        # 描述文本 - 优化字体显示效果
        description = (
            "一个基于PyQt5的图片批量转换工具，\n"
            "支持多种图片格式之间的转换。"
        )
        
        description_label = QLabel(description)
        description_font = QFont()
        description_font.setFamily("Microsoft YaHei UI")
        description_font.setPointSize(11)
        description_label.setFont(description_font)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet(f"color: {text_color}; padding: 5px 0;")
        text_layout.addWidget(description_label)
        
        # 版权信息 - 优化字体显示效果
        copyright_label = QLabel("© 2025 PictureConverter")
        copyright_font = QFont()
        copyright_font.setFamily("Microsoft YaHei UI")
        copyright_font.setPointSize(10)
        copyright_font.setItalic(True)
        copyright_label.setFont(copyright_font)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet(f"color: {text_color}; padding: 5px 0;")
        text_layout.addWidget(copyright_label)
        
        glass_layout.addLayout(text_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        
        ok_button = GlassButton("确定")
        ok_button.setMinimumWidth(100)
        ok_button.clicked.connect(self.accept)
        
        # 应用透明度设置到按钮
        if hasattr(self.parent(), 'settings'):
            ok_button.setTransparency(transparency)
            
        button_layout.addWidget(ok_button)
        glass_layout.addLayout(button_layout)
        
        main_layout.addWidget(glass_container)
        self.setLayout(main_layout)
        
        # 居中显示
        self.center()
        
    def center(self):
        """居中显示窗口"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def showAbout(self):
        dialog = AboutDialog(self)
        dialog.exec_()
    def closeEvent(self, event):
        # 如果有转换线程在运行，先停止它
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.conversion_thread.stop()
            self.conversion_thread.wait()
        
        # 保存设置
        self.saveSettings()
        
        event.accept()