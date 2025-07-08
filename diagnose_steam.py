#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт диагностики проблем с конфигурацией Steam
"""

import json
import sys
import base64
import asyncio
import time
from pathlib import Path
from steam_client import SteamAuthenticator, SteamWebClient


def print_step(message, status="INFO"):
    icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def check_config_file():
    """Проверяет существование и базовую структуру config.json"""
    print_step("Проверка конфигурационного файла...")
    
    if not Path("config.json").exists():
        print_step("Файл config.json не найден!", "ERROR")
        return False
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        required_fields = [
            "steam_account.login",
            "steam_account.password", 
            "steam_account.shared_secret",
            "steam_account.identity_secret",
            "steam_account.device_id",
            "steam_account.steamid"
        ]
        
        missing_fields = []
        for field_path in required_fields:
            keys = field_path.split(".")
            current = config
            
            for key in keys:
                if key not in current:
                    missing_fields.append(field_path)
                    break
                current = current[key]
            
            # Проверяем, что поле не пустое
            if field_path not in missing_fields and not str(current).strip():
                missing_fields.append(field_path + " (пустое)")
        
        if missing_fields:
            print_step(f"Отсутствуют или пустые поля: {', '.join(missing_fields)}", "ERROR")
            return False
        
        print_step("Конфигурация найдена и содержит все необходимые поля", "SUCCESS")
        return config
        
    except json.JSONDecodeError as e:
        print_step(f"Ошибка JSON в config.json: {e}", "ERROR")
        return False
    except Exception as e:
        print_step(f"Ошибка чтения config.json: {e}", "ERROR")
        return False


def check_shared_secret(shared_secret):
    """Проверяет формат shared_secret"""
    print_step("Проверка shared_secret...")
    
    try:
        # Проверяем, что это base64
        decoded = base64.b64decode(shared_secret)
        if len(decoded) != 20:  # Steam shared_secret обычно 20 байт
            print_step("shared_secret имеет неправильную длину после декодирования", "WARNING")
        
        print_step(f"shared_secret корректен (длина: {len(decoded)} байт)", "SUCCESS")
        return True
        
    except Exception as e:
        print_step(f"shared_secret имеет неправильный формат base64: {e}", "ERROR")
        print_step("Убедитесь, что вы скопировали shared_secret правильно из .maFile", "WARNING")
        return False


def test_steam_guard_code(shared_secret):
    """Тестирует генерацию Steam Guard кода"""
    print_step("Тестирование генерации Steam Guard кода...")
    
    try:
        authenticator = SteamAuthenticator(shared_secret)
        code = authenticator.generate_auth_code()
        
        print_step(f"Steam Guard код: {code}", "SUCCESS")
        print_step("Проверьте, совпадает ли этот код с кодом в вашем Steam Guard", "INFO")
        return True
        
    except Exception as e:
        print_step(f"Ошибка генерации Steam Guard кода: {e}", "ERROR")
        return False


async def test_steam_connection():
    """Тестирует базовое соединение с Steam"""
    print_step("Тестирование соединения с Steam...")
    
    try:
        async with SteamWebClient() as client:
            # Проверяем доступность Steam
            async with client.session.get("https://steamcommunity.com/", timeout=10) as response:
                if response.status == 200:
                    print_step("Steam доступен", "SUCCESS")
                    return True
                else:
                    print_step(f"Steam недоступен (код: {response.status})", "ERROR")
                    return False
                    
    except Exception as e:
        print_step(f"Ошибка соединения с Steam: {e}", "ERROR")
        print_step("Проверьте интернет соединение", "WARNING")
        return False


async def test_rsa_key_request(username):
    """Тестирует получение RSA ключа для пользователя"""
    print_step(f"Тестирование получения RSA ключа для пользователя '{username}'...")
    
    try:
        async with SteamWebClient() as client:
            rsa_key = await client._get_rsa_key(username)
            
            if rsa_key and rsa_key.get('modulus'):
                print_step("RSA ключ получен успешно", "SUCCESS")
                return True
            else:
                print_step("Не удалось получить RSA ключ", "ERROR")
                print_step("Проверьте правильность логина Steam", "WARNING")
                return False
                
    except Exception as e:
        print_step(f"Ошибка получения RSA ключа: {e}", "ERROR")
        return False


def check_steam_credentials(config):
    """Проверяет учетные данные Steam"""
    print_step("Проверка учетных данных Steam...")
    
    steam_account = config["steam_account"]
    
    # Проверяем формат SteamID
    try:
        steamid = int(steam_account["steamid"])
        if steamid < 76561197960265728:  # Минимальный SteamID64
            print_step("SteamID кажется некорректным", "WARNING")
        else:
            print_step(f"SteamID: {steamid}", "SUCCESS")
    except ValueError:
        print_step("SteamID должен быть числом", "ERROR")
        return False
    
    # Проверяем логин
    login = steam_account["login"]
    if len(login) < 3:
        print_step("Логин слишком короткий", "WARNING")
    else:
        print_step(f"Логин: {login}", "SUCCESS")
    
    # Проверяем пароль
    password = steam_account["password"]
    if len(password) < 5:
        print_step("Пароль слишком короткий", "WARNING")
    else:
        print_step("Пароль установлен", "SUCCESS")
    
    return True


async def full_diagnosis():
    """Полная диагностика системы"""
    print("🔍 Диагностика конфигурации Steam Password Changer")
    print("=" * 60)
    
    # 1. Проверка конфигурации
    config = check_config_file()
    if not config:
        print("\n❌ Критическая ошибка в конфигурации!")
        print("Исправьте config.json и запустите диагностику снова.")
        return False
    
    steam_account = config["steam_account"]
    
    # 2. Проверка учетных данных
    if not check_steam_credentials(config):
        return False
    
    # 3. Проверка shared_secret
    if not check_shared_secret(steam_account["shared_secret"]):
        return False
    
    # 4. Тестирование Steam Guard
    if not test_steam_guard_code(steam_account["shared_secret"]):
        return False
    
    # 5. Проверка соединения с Steam
    if not await test_steam_connection():
        return False
    
    # 6. Тестирование получения RSA ключа
    if not await test_rsa_key_request(steam_account["login"]):
        return False
    
    print("\n" + "=" * 60)
    print("✅ Базовая диагностика пройдена успешно!")
    print("\nРекомендации:")
    print("1. Убедитесь, что Steam Guard код совпадает с кодом в приложении")
    print("2. Проверьте, что аккаунт не заблокирован Steam Guard")
    print("3. Убедитесь, что пароль актуален")
    print("4. Попробуйте войти в Steam вручную для проверки")
    
    return True


def print_troubleshooting_tips():
    """Выводит советы по устранению неполадок"""
    print("\n" + "=" * 60)
    print("🛠️ Советы по устранению неполадок:")
    print("=" * 60)
    
    print("\n1. Проблемы с shared_secret:")
    print("   - Убедитесь, что вы скопировали shared_secret из .maFile файла SDA")
    print("   - Файл находится в папке maFiles Steam Desktop Authenticator")
    print("   - Shared_secret должен быть в формате base64 (например: 'dGVzdF9zZWNyZXQ=')")
    
    print("\n2. Проблемы с авторизацией:")
    print("   - Проверьте правильность логина и пароля Steam")
    print("   - Убедитесь, что аккаунт не заблокирован")
    print("   - Попробуйте войти в Steam клиент вручную")
    
    print("\n3. Проблемы с Steam Guard:")
    print("   - Код должен совпадать с кодом в мобильном приложении")
    print("   - Проверьте время на компьютере (должно быть синхронизировано)")
    print("   - Убедитесь, что device_id и identity_secret также правильные")
    
    print("\n4. Проблемы с сетью:")
    print("   - Проверьте интернет соединение")
    print("   - Убедитесь, что Steam доступен")
    print("   - Отключите VPN если используете")


async def main():
    """Главная функция диагностики"""
    try:
        success = await full_diagnosis()
        
        if not success:
            print_troubleshooting_tips()
            
        print(f"\n{'='*60}")
        print("Диагностика завершена!")
        
        if success:
            print("✅ Система готова к работе")
        else:
            print("❌ Обнаружены проблемы, требующие исправления")
            
    except KeyboardInterrupt:
        print("\nДиагностика прервана пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка диагностики: {e}")


if __name__ == "__main__":
    asyncio.run(main())