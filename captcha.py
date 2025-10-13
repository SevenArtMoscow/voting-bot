# Модуль для генерации и проверки CAPTCHA
from PIL import Image, ImageDraw, ImageFont
import random
import string
import os
from config import CAPTCHA_LENGTH, CAPTCHA_WIDTH, CAPTCHA_HEIGHT, CAPTCHA_FOLDER

class CaptchaGenerator:
    def __init__(self):
        self.length = CAPTCHA_LENGTH
        self.width = CAPTCHA_WIDTH
        self.height = CAPTCHA_HEIGHT
        self.folder = CAPTCHA_FOLDER
    
    def generate_captcha(self, telegram_id):
        """Генерация CAPTCHA изображения"""
        # Генерируем случайный код
        code = ''.join(random.choices(string.digits, k=self.length))
        
        # Создаем изображение
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Пытаемся использовать системный шрифт
        try:
            # Для Windows
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            try:
                # Альтернативный шрифт
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
            except:
                # Используем стандартный шрифт
                font = ImageFont.load_default()
        
        # Рисуем фон с шумом
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Рисуем линии-помехи
        for _ in range(5):
            start_x = random.randint(0, self.width)
            start_y = random.randint(0, self.height)
            end_x = random.randint(0, self.width)
            end_y = random.randint(0, self.height)
            draw.line([(start_x, start_y), (end_x, end_y)], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)
        
        # Рисуем текст
        text_width = len(code) * 25
        text_height = 40
        start_x = (self.width - text_width) // 2
        start_y = (self.height - text_height) // 2
        
        for i, char in enumerate(code):
            # Случайный цвет для каждого символа
            color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
            
            # Случайное смещение для каждого символа
            char_x = start_x + i * 25 + random.randint(-5, 5)
            char_y = start_y + random.randint(-5, 5)
            
            # Рисуем символ
            draw.text((char_x, char_y), char, font=font, fill=color)
        
        # Сохраняем изображение
        filename = f"{self.folder}/captcha_{telegram_id}.png"
        image.save(filename)
        
        return code, filename
    
    def cleanup_captcha(self, filename):
        """Удаление файла CAPTCHA"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
