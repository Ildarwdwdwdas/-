#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы со Steam API и автоматизации смены паролей
Использует прямые API вызовы без браузерной автоматизации
"""

import asyncio
import aiohttp
import hashlib
import hmac
import base64
import time
import json
import struct
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging


class SteamAuthenticator:
    """Класс для работы с Steam Guard (двухфакторная аутентификация)"""
    
    def __init__(self, shared_secret: str):
        self.shared_secret = shared_secret
        
    def generate_auth_code(self, timestamp: Optional[int] = None) -> str:
        """
        Генерирует код Steam Guard
        
        Args:
            timestamp: Временная метка (по умолчанию текущее время)
            
        Returns:
            5-значный код аутентификации
        """
        if timestamp is None:
            timestamp = int(time.time())
            
        # Steam использует 30-секундные интервалы
        time_buffer = timestamp // 30
        
        # Преобразуем shared_secret из base64
        try:
            secret_bytes = base64.b64decode(self.shared_secret)
        except Exception as e:
            raise ValueError(f"Неверный формат shared_secret: {e}")
        
        # Создаем HMAC-SHA1
        time_bytes = struct.pack(">Q", time_buffer)
        hmac_digest = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
        
        # Извлекаем динамический код
        offset = hmac_digest[-1] & 0x0F
        code_bytes = hmac_digest[offset:offset + 4]
        code_int = struct.unpack(">I", code_bytes)[0] & 0x7FFFFFFF
        
        # Генерируем 5-значный код
        auth_code = code_int % 1000000
        return f"{auth_code:05d}"
    
    def generate_confirmation_key(self, timestamp: int, tag: str) -> str:
        """
        Генерирует ключ подтверждения для Steam Guard
        
        Args:
            timestamp: Временная метка
            tag: Тег операции (например, 'conf' для подтверждения)
            
        Returns:
            Ключ подтверждения в base64
        """
        try:
            secret_bytes = base64.b64decode(self.shared_secret)
        except Exception as e:
            raise ValueError(f"Неверный формат shared_secret: {e}")
        
        # Создаем данные для подписи
        data = f"{timestamp}{tag}".encode('utf-8')
        
        # Создаем HMAC-SHA1
        hmac_digest = hmac.new(secret_bytes, data, hashlib.sha1).digest()
        
        return base64.b64encode(hmac_digest).decode('utf-8')


class SteamWebClient:
    """Клиент для работы с веб-интерфейсом Steam"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.steam_id: Optional[int] = None
        self.session_id: Optional[str] = None
        self.login_cookies: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self, username: str, password: str, auth_code: str) -> bool:
        """
        Авторизация в Steam
        
        Args:
            username: Имя пользователя Steam
            password: Пароль Steam
            auth_code: Код двухфакторной аутентификации
            
        Returns:
            True если авторизация успешна, False в противном случае
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована")
        
        try:
            # Получаем RSA ключ для шифрования пароля
            rsa_key = await self._get_rsa_key(username)
            if not rsa_key:
                self.logger.error("Не удалось получить RSA ключ")
                return False
            
            # Шифруем пароль
            encrypted_password = self._encrypt_password(password, rsa_key)
            
            # Выполняем вход
            login_data = {
                'username': username,
                'password': encrypted_password,
                'twofactorcode': auth_code,
                'rsatimestamp': rsa_key['timestamp'],
                'remember_login': 'false',
                'donotcache': str(int(time.time() * 1000))
            }
            
            async with self.session.post(
                'https://steamcommunity.com/login/dologin/',
                data=login_data
            ) as response:
                result = await response.json()
                
                if result.get('success') and result.get('login_complete'):
                    # Сохраняем cookie и данные сессии
                    self.login_cookies = {cookie.key: cookie.value 
                                        for cookie in response.cookies}
                    
                    # Извлекаем SteamID и SessionID из ответа
                    if 'transfer_urls' in result:
                        # Парсим данные сессии из URL перенаправления
                        await self._extract_session_data(result['transfer_urls'][0])
                    
                    self.logger.info("Успешная авторизация в Steam")
                    return True
                else:
                    self.logger.error(f"Ошибка авторизации: {result.get('message', 'Неизвестная ошибка')}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Исключение при авторизации: {e}")
            return False
    
    async def change_password(self, current_password: str, new_password: str) -> bool:
        """
        Смена пароля Steam аккаунта
        
        Args:
            current_password: Текущий пароль
            new_password: Новый пароль
            
        Returns:
            True если смена успешна, False в противном случае
        """
        if not self.session or not self.session_id:
            self.logger.error("Необходима авторизация перед сменой пароля")
            return False
        
        try:
            # Получаем токен для смены пароля
            change_password_url = "https://steamcommunity.com/profiles/edit/changepassword"
            
            async with self.session.get(change_password_url) as response:
                if response.status != 200:
                    self.logger.error("Не удалось получить страницу смены пароля")
                    return False
                
                # Извлекаем CSRF токен из страницы
                page_content = await response.text()
                csrf_token = self._extract_csrf_token(page_content)
                
                if not csrf_token:
                    self.logger.error("Не удалось найти CSRF токен")
                    return False
            
            # Отправляем запрос на смену пароля
            change_data = {
                'sessionid': self.session_id,
                'oldpassword': current_password,
                'newpassword': new_password,
                'confirmnewpassword': new_password,
                'csrf_token': csrf_token
            }
            
            async with self.session.post(
                'https://steamcommunity.com/profiles/edit/changepasswordsubmit',
                data=change_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('success'):
                        self.logger.info("Пароль успешно изменен")
                        return True
                    else:
                        self.logger.error(f"Ошибка смены пароля: {result.get('message', 'Неизвестная ошибка')}")
                        return False
                else:
                    self.logger.error(f"HTTP ошибка при смене пароля: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Исключение при смене пароля: {e}")
            return False
    
    async def _get_rsa_key(self, username: str) -> Optional[Dict[str, Any]]:
        """Получает RSA ключ для шифрования пароля"""
        try:
            data = {'username': username}
            async with self.session.post(
                'https://steamcommunity.com/login/getrsakey/',
                data=data
            ) as response:
                result = await response.json()
                
                if result.get('success'):
                    return {
                        'modulus': result.get('publickey_mod'),
                        'exponent': result.get('publickey_exp'),
                        'timestamp': result.get('timestamp')
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка получения RSA ключа: {e}")
            return None
    
    def _encrypt_password(self, password: str, rsa_key: Dict[str, Any]) -> str:
        """Шифрует пароль с использованием RSA ключа"""
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa, padding
            from cryptography.hazmat.primitives import hashes
            
            # Создаем RSA ключ
            modulus = int(rsa_key['modulus'], 16)
            exponent = int(rsa_key['exponent'], 16)
            
            public_key = rsa.RSAPublicNumbers(exponent, modulus).public_key(default_backend())
            
            # Шифруем пароль
            encrypted = public_key.encrypt(
                password.encode('utf-8'),
                padding.PKCS1v15()
            )
            
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Ошибка шифрования пароля: {e}")
            return ""
    
    async def _extract_session_data(self, transfer_url: str):
        """Извлекает данные сессии из URL перенаправления"""
        try:
            async with self.session.get(transfer_url) as response:
                # Извлекаем cookies после перенаправления
                for cookie in response.cookies:
                    self.login_cookies[cookie.key] = cookie.value
                
                # Получаем SteamID и SessionID из cookies или заголовков
                self.session_id = self.login_cookies.get('sessionid')
                
                # SteamID можно извлечь из различных источников
                if 'steamLoginSecure' in self.login_cookies:
                    login_secure = self.login_cookies['steamLoginSecure']
                    if '%7C%7C' in login_secure:
                        self.steam_id = int(login_secure.split('%7C%7C')[0])
                        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения данных сессии: {e}")
    
    def _extract_csrf_token(self, page_content: str) -> Optional[str]:
        """Извлекает CSRF токен из HTML страницы"""
        import re
        
        # Ищем CSRF токен в различных форматах
        patterns = [
            r'name="csrf_token"\s+value="([^"]+)"',
            r'"csrf_token":"([^"]+)"',
            r'g_rgProfileData\s*=\s*{[^}]*"csrf_token"\s*:\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                return match.group(1)
        
        return None


class SteamPasswordChanger:
    """Основной класс для автоматизации смены паролей Steam"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.authenticator = SteamAuthenticator(config['steam_account']['shared_secret'])
        self.logger = logging.getLogger(__name__)
    
    async def change_password(self, new_password: str) -> bool:
        """
        Выполняет смену пароля Steam аккаунта
        
        Args:
            new_password: Новый пароль
            
        Returns:
            True если смена успешна, False в противном случае
        """
        try:
            async with SteamWebClient() as client:
                # Генерируем код аутентификации
                auth_code = self.authenticator.generate_auth_code()
                
                # Авторизуемся
                login_success = await client.login(
                    self.config['steam_account']['login'],
                    self.config['steam_account']['password'],
                    auth_code
                )
                
                if not login_success:
                    self.logger.error("Не удалось авторизоваться в Steam")
                    return False
                
                # Меняем пароль
                change_success = await client.change_password(
                    self.config['steam_account']['password'],
                    new_password
                )
                
                if change_success:
                    # Обновляем конфигурацию
                    self.config['steam_account']['password'] = new_password
                    self.logger.info("Пароль успешно изменен")
                    return True
                else:
                    self.logger.error("Не удалось изменить пароль")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Исключение при смене пароля: {e}")
            return False


if __name__ == "__main__":
    # Пример использования
    async def test_authenticator():
        # Тестируем генерацию кода аутентификации
        # ВНИМАНИЕ: Замените на ваш настоящий shared_secret
        shared_secret = "YOUR_SHARED_SECRET_HERE"
        
        if shared_secret != "YOUR_SHARED_SECRET_HERE":
            authenticator = SteamAuthenticator(shared_secret)
            code = authenticator.generate_auth_code()
            print(f"Сгенерированный код Steam Guard: {code}")
        else:
            print("Установите настоящий shared_secret для тестирования")
    
    # Запускаем тест
    asyncio.run(test_authenticator())