#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для генерации безопасных паролей
Поддерживает различные настройки сложности и исключения символов
"""

import secrets
import string
from typing import List, Optional


class PasswordGenerator:
    """Класс для генерации безопасных паролей"""
    
    def __init__(self):
        # Определяем наборы символов
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.numbers = string.digits
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Символы, которые могут быть неоднозначными
        self.ambiguous_chars = "0O1lI"
        
    def generate_password(
        self,
        length: int = 16,
        use_lowercase: bool = True,
        use_uppercase: bool = True,
        use_numbers: bool = True,
        use_special_chars: bool = True,
        exclude_ambiguous: bool = True,
        exclude_chars: Optional[str] = None
    ) -> str:
        """
        Генерирует безопасный пароль
        
        Args:
            length: Длина пароля
            use_lowercase: Использовать строчные буквы
            use_uppercase: Использовать заглавные буквы
            use_numbers: Использовать цифры
            use_special_chars: Использовать специальные символы
            exclude_ambiguous: Исключить неоднозначные символы
            exclude_chars: Дополнительные символы для исключения
            
        Returns:
            Сгенерированный пароль
            
        Raises:
            ValueError: Если параметры не позволяют создать пароль
        """
        if length < 4:
            raise ValueError("Длина пароля должна быть не менее 4 символов")
        
        # Собираем набор символов
        charset = ""
        required_chars = []
        
        if use_lowercase:
            charset += self.lowercase
            required_chars.append(secrets.choice(self.lowercase))
            
        if use_uppercase:
            charset += self.uppercase
            required_chars.append(secrets.choice(self.uppercase))
            
        if use_numbers:
            charset += self.numbers
            required_chars.append(secrets.choice(self.numbers))
            
        if use_special_chars:
            charset += self.special_chars
            required_chars.append(secrets.choice(self.special_chars))
        
        if not charset:
            raise ValueError("Должен быть выбран хотя бы один тип символов")
        
        # Исключаем неоднозначные символы
        if exclude_ambiguous:
            charset = ''.join(c for c in charset if c not in self.ambiguous_chars)
            required_chars = [c for c in required_chars if c not in self.ambiguous_chars]
        
        # Исключаем дополнительные символы
        if exclude_chars:
            charset = ''.join(c for c in charset if c not in exclude_chars)
            required_chars = [c for c in required_chars if c not in exclude_chars]
        
        if len(charset) == 0:
            raise ValueError("После исключений не осталось символов для генерации")
        
        # Генерируем пароль
        if len(required_chars) > length:
            raise ValueError("Длина пароля слишком мала для всех требуемых типов символов")
        
        # Добавляем случайные символы
        remaining_length = length - len(required_chars)
        random_chars = [secrets.choice(charset) for _ in range(remaining_length)]
        
        # Объединяем и перемешиваем
        password_chars = required_chars + random_chars
        password_list = list(password_chars)
        
        # Перемешиваем символы для случайного порядка
        for i in range(len(password_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_list[i], password_list[j] = password_list[j], password_list[i]
        
        return ''.join(password_list)
    
    def validate_password_strength(self, password: str) -> dict:
        """
        Проверяет силу пароля
        
        Args:
            password: Пароль для проверки
            
        Returns:
            Словарь с результатами проверки
        """
        result = {
            'length': len(password),
            'has_lowercase': any(c in self.lowercase for c in password),
            'has_uppercase': any(c in self.uppercase for c in password),
            'has_numbers': any(c in self.numbers for c in password),
            'has_special_chars': any(c in self.special_chars for c in password),
            'has_ambiguous': any(c in self.ambiguous_chars for c in password),
            'score': 0,
            'strength': 'Очень слабый'
        }
        
        # Подсчитываем баллы
        if result['length'] >= 8:
            result['score'] += 1
        if result['length'] >= 12:
            result['score'] += 1
        if result['length'] >= 16:
            result['score'] += 1
            
        if result['has_lowercase']:
            result['score'] += 1
        if result['has_uppercase']:
            result['score'] += 1
        if result['has_numbers']:
            result['score'] += 1
        if result['has_special_chars']:
            result['score'] += 2
            
        # Определяем силу пароля
        if result['score'] >= 7:
            result['strength'] = 'Очень сильный'
        elif result['score'] >= 5:
            result['strength'] = 'Сильный'
        elif result['score'] >= 3:
            result['strength'] = 'Средний'
        elif result['score'] >= 1:
            result['strength'] = 'Слабый'
        
        return result
    
    def generate_multiple_passwords(
        self,
        count: int,
        **kwargs
    ) -> List[str]:
        """
        Генерирует несколько паролей
        
        Args:
            count: Количество паролей
            **kwargs: Параметры для generate_password
            
        Returns:
            Список сгенерированных паролей
        """
        return [self.generate_password(**kwargs) for _ in range(count)]


if __name__ == "__main__":
    # Пример использования
    generator = PasswordGenerator()
    
    # Генерируем пароль с настройками по умолчанию
    password = generator.generate_password()
    print(f"Сгенерированный пароль: {password}")
    
    # Проверяем силу пароля
    strength = generator.validate_password_strength(password)
    print(f"Сила пароля: {strength['strength']} (баллы: {strength['score']})")
    
    # Генерируем несколько паролей
    passwords = generator.generate_multiple_passwords(3, length=20)
    print("\nНесколько паролей:")
    for i, pwd in enumerate(passwords, 1):
        print(f"{i}. {pwd}")