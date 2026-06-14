import tkinter as tk
import tkinter.font as tkfont


class Utils:
    @staticmethod
    def hex_to_rgb(hex_color):
        """
        将十六进制颜色字符串转换为RGB元组，忽略alpha通道
        
        Args:
            hex_color (str): 十六进制颜色字符串，如 "#FF0000" 或 "#FF0000FF"
            
        Returns:
            tuple: (r, g, b) 元组，值范围0-255
        """
        hex_color = hex_color.lstrip('#')[:6]
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb):
        """
        将RGB元组转换为十六进制颜色字符串
        
        Args:
            rgb (tuple): (r, g, b) 元组，值范围0-255
            
        Returns:
            str: 十六进制颜色字符串，如 "#FF0000"
        """
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    @staticmethod
    def hex_to_alpha(hex_color):
        """
        提取十六进制颜色的 alpha 值
        
        Args:
            hex_color (str): 十六进制颜色字符串，如 "#FF0000" 或 "#FF0000FF"
            
        Returns:
            float: alpha 值，0.0-1.0，默认返回 1.0（完全不透明）
        """
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 8:
                return int(hex_color[6:8], 16) / 255.0
            return 1.0
        except Exception:
            return 1.0
    
    @staticmethod
    def blend_color(source, target, alpha):
        """
        混合两个颜色，忽略输入颜色中的alpha通道
        
        Args:
            source (str): 源颜色，十六进制颜色字符串，如 "#FF0000" 或 "#FF0000FF"
            target (str): 目标颜色，十六进制颜色字符串，如 "#00FF00" 或 "#00FF00FF"
            alpha (float): 混合比例，0.0-1.0，0返回source，1返回target
            
        Returns:
            str: 混合后的十六进制颜色字符串，如 "#80FF80"
        """
        source_rgb = Utils.hex_to_rgb(source)
        target_rgb = Utils.hex_to_rgb(target)
        
        r = int(source_rgb[0] * (1 - alpha) + target_rgb[0] * alpha)
        g = int(source_rgb[1] * (1 - alpha) + target_rgb[1] * alpha)
        b = int(source_rgb[2] * (1 - alpha) + target_rgb[2] * alpha)
        
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return Utils.rgb_to_hex((r, g, b))
    
    @staticmethod
    def recolor_image(img, bg_color, fg_color):
        """
        重新着色图片，利用像素的灰度混合前景和背景色
        
        Args:
            img (tk.PhotoImage): 原始图片对象
            bg_color (str): 背景色，十六进制颜色字符串
            fg_color (str): 前景色，十六进制颜色字符串
            
        Returns:
            tk.PhotoImage: 处理后的图片对象（直接修改原始图片）
        """
        try:
            # 获取图片尺寸
            width = img.width()
            height = img.height()
            
            # 转换颜色
            bg_rgb = Utils.hex_to_rgb(bg_color)
            fg_rgb = Utils.hex_to_rgb(fg_color)
            
            # 遍历每个像素
            for x in range(width):
                for y in range(height):
                    try:
                        # 获取原始像素值
                        pixel = img.get(x, y)
                        
                        # 处理像素值格式
                        if isinstance(pixel, str):
                            if pixel.startswith('#'):
                                # 格式为 "#RRGGBB"
                                pixel_rgb = Utils.hex_to_rgb(pixel)
                            else:
                                # 其他字符串格式，跳过
                                continue
                        elif isinstance(pixel, tuple) and len(pixel) >= 3:
                            # 格式为 (r, g, b)
                            pixel_rgb = pixel
                        else:
                            # 其他格式，跳过
                            continue
                        
                        # 计算灰度值（使用亮度公式）
                        gray = int(0.299 * pixel_rgb[0] + 0.587 * pixel_rgb[1] + 0.114 * pixel_rgb[2])
                        
                        # 计算混合比例（灰度值越高，前景色比例越大）
                        ratio = gray / 255.0
                        
                        # 混合颜色
                        r = int(bg_rgb[0] * (1 - ratio) + fg_rgb[0] * ratio)
                        g = int(bg_rgb[1] * (1 - ratio) + fg_rgb[1] * ratio)
                        b = int(bg_rgb[2] * (1 - ratio) + fg_rgb[2] * ratio)
                        
                        # 确保颜色值在0-255范围内
                        r = max(0, min(255, r))
                        g = max(0, min(255, g))
                        b = max(0, min(255, b))
                        
                        # 直接修改原始图片的像素值
                        img.put(Utils.rgb_to_hex((r, g, b)), (x, y))
                    except Exception:
                        # 单个像素处理失败，跳过
                        pass
            
            return img
        except Exception as e:
            # 如果处理失败，返回原始图片
            print(f"图片处理失败: {e}")
            return img
    
    @staticmethod
    def center_rect(parent_width, parent_height, child_width, child_height):
        """
        计算子矩形在父矩形中居中的坐标
        
        Args:
            parent_width (int): 父矩形宽度
            parent_height (int): 父矩形高度
            child_width (int): 子矩形宽度
            child_height (int): 子矩形高度
            
        Returns:
            tuple: (x, y) 子矩形左上角的坐标
        """
        x = max(0, (parent_width - child_width) // 2)
        y = max(0, (parent_height - child_height) // 2)
        return x, y

    @staticmethod
    def is_content_overflow(text: str, available_width: int, available_height: int, min_font_size: int = 8) -> bool:
        """使用最小字号快速预估文本是否会溢出指定容器区域。

        原理：用最小字号（字号越小，同样高度能装的行越多）计算容器高度最多能容纳
        多少个字符。如果待显示的内容字符数超过这个最大容量，说明内容肯定会溢出。
        如果没超过，说明内容量在合理范围内，可以安全走真实布局测量。

        Args:
            text: 要显示的纯文本内容
            available_width: 可用宽度（像素）
            available_height: 可用高度（像素）
            min_font_size: 用于估算的最小字号，默认 8

        Returns:
            True 表示内容大概率溢出，False 表示内容在可接受范围内
        """
        if not text:
            return False

        # 使用最小字号构建临时字体对象进行度量
        temp_font = tkfont.Font(family="TkDefaultFont", size=min_font_size)
        line_height = temp_font.metrics('linespace')

        if line_height <= 0:
            return False

        # 该高度下最多能容纳的行数
        max_lines = available_height // line_height
        if max_lines <= 0:
            return True

        # 用最小字号下单个字符的平均宽度估算每行能放多少字符
        # 使用 "M"（最宽的拉丁字符）和 "中"（代表 CJK 字符）取较小值，让估算更宽松
        char_width_m = temp_font.measure("M")
        char_width_cjk = temp_font.measure("中")
        avg_char_width = min(char_width_m, char_width_cjk)

        if avg_char_width <= 0:
            return False

        # 每行最多字符数
        chars_per_line = available_width // avg_char_width

        if chars_per_line <= 0:
            return True

        # 该区域用最小字号最多能容纳的总字符数
        max_capacity = max_lines * chars_per_line

        # 内容的实际字符数（去除末尾换行）
        content_length = len(text.rstrip('\n'))

        # 换行符会额外占用行，保守估算每个换行浪费半行容量
        newline_count = text.count('\n')
        effective_length = content_length + newline_count * (chars_per_line // 2)

        return effective_length > max_capacity
