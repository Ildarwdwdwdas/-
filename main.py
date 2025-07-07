#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный скрипт для автоматизированной системы смены паролей Steam
Предоставляет CLI интерфейс для управления и мониторинга
"""

import argparse
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any
import signal

from scheduler import SteamPasswordScheduler
from password_generator import PasswordGenerator
from steam_client import SteamAuthenticator


class SteamPasswordManager:
    """Основной класс для управления системой смены паролей Steam"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.scheduler: SteamPasswordScheduler = None
        
    def ensure_config_exists(self):
        """Проверяет существование конфигурационного файла и создает его при необходимости"""
        if not Path(self.config_file).exists():
            print(f"Конфигурационный файл {self.config_file} не найден.")
            create = input("Создать новый конфигурационный файл? (y/n): ").lower()
            
            if create == 'y':
                self.create_initial_config()
            else:
                print("Отмена операции.")
                sys.exit(1)
    
    def create_initial_config(self):
        """Создает начальную конфигурацию с помощью интерактивного ввода"""
        print("\n=== Создание конфигурации Steam Password Changer ===")
        
        # Собираем данные Steam аккаунта
        print("\n1. Данные Steam аккаунта:")
        steam_login = input("Steam логин: ")
        steam_password = input("Текущий пароль Steam: ")
        shared_secret = input("Shared Secret (из Steam Desktop Authenticator): ")
        identity_secret = input("Identity Secret (из Steam Desktop Authenticator): ")
        device_id = input("Device ID (из Steam Desktop Authenticator): ")
        
        try:
            steamid = int(input("Steam ID (64-bit): "))
        except ValueError:
            steamid = 76561198000000000
            print(f"Используется Steam ID по умолчанию: {steamid}")
        
        # Настройки смены пароля
        print("\n2. Настройки смены пароля:")
        try:
            interval_hours = int(input("Интервал смены пароля в часах (по умолчанию 24): ") or "24")
            password_length = int(input("Длина нового пароля (по умолчанию 16): ") or "16")
        except ValueError:
            interval_hours = 24
            password_length = 16
            print("Используются значения по умолчанию")
        
        # Создаем конфигурацию
        config = {
            "steam_account": {
                "login": steam_login,
                "password": steam_password,
                "shared_secret": shared_secret,
                "identity_secret": identity_secret,
                "device_id": device_id,
                "steamid": steamid
            },
            "password_change": {
                "change_interval_hours": interval_hours,
                "password_length": password_length,
                "use_special_chars": True,
                "use_numbers": True,
                "use_uppercase": True,
                "use_lowercase": True,
                "exclude_ambiguous": True
            },
            "security": {
                "save_password_history": True,
                "max_password_history": 10,
                "require_confirmation": False,
                "backup_old_passwords": True
            },
            "logging": {
                "level": "INFO",
                "log_to_file": True,
                "log_file": "steam_password_changer.log",
                "max_log_size_mb": 10,
                "backup_count": 5
            },
            "notifications": {
                "enable_notifications": True,
                "notify_on_success": True,
                "notify_on_error": True,
                "notification_method": "console"
            }
        }
        
        # Сохраняем конфигурацию
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print(f"\nКонфигурация сохранена в {self.config_file}")
            
            # Проверяем Steam Guard
            if self.test_steam_guard(shared_secret):
                print("✓ Steam Guard работает корректно")
            else:
                print("⚠ Проблема с Steam Guard - проверьте shared_secret")
                
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            sys.exit(1)
    
    def test_steam_guard(self, shared_secret: str) -> bool:
        """Тестирует работу Steam Guard"""
        try:
            authenticator = SteamAuthenticator(shared_secret)
            code = authenticator.generate_auth_code()
            print(f"Тестовый код Steam Guard: {code}")
            return True
        except Exception as e:
            print(f"Ошибка генерации кода Steam Guard: {e}")
            return False
    
    def start_daemon(self):
        """Запускает систему в режиме демона"""
        print("Запуск автоматизированной системы смены паролей Steam...")
        
        try:
            self.scheduler = SteamPasswordScheduler(self.config_file)
            
            # Настраиваем обработчики сигналов для корректного завершения
            def signal_handler(signum, frame):
                print(f"\nПолучен сигнал {signum}. Завершение работы...")
                if self.scheduler:
                    self.scheduler.stop()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Запускаем планировщик
            self.scheduler.start()
            
            print("Система запущена успешно!")
            print("Для остановки нажмите Ctrl+C")
            
            # Показываем статус
            status = self.scheduler.get_status()
            print(f"\nТекущий статус:")
            print(f"- Планировщик активен: {status['is_running']}")
            print(f"- Следующая смена: {status['next_scheduled_change']}")
            print(f"- Последняя успешная смена: {status['last_successful_change']}")
            print(f"- Всего смен паролей: {status['total_password_changes']}")
            
            # Основной цикл
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nЗавершение работы...")
                self.scheduler.stop()
                
        except Exception as e:
            print(f"Ошибка запуска системы: {e}")
            sys.exit(1)
    
    def show_status(self):
        """Показывает текущий статус системы"""
        try:
            self.scheduler = SteamPasswordScheduler(self.config_file)
            status = self.scheduler.get_status()
            
            print("\n=== Статус системы Steam Password Changer ===")
            print(f"Планировщик активен: {'✓' if status['is_running'] else '✗'}")
            print(f"Следующая запланированная смена: {status['next_scheduled_change'] or 'Не запланирована'}")
            print(f"Последняя успешная смена: {status['last_successful_change'] or 'Нет данных'}")
            print(f"Неудачных попыток сегодня: {status['failed_attempts_today']}")
            print(f"Всего успешных смен: {status['total_password_changes']}")
            
            # Показываем историю
            history = self.scheduler.password_history.records[-5:]  # Последние 5 записей
            if history:
                print(f"\n=== Последние записи истории ===")
                for i, record in enumerate(reversed(history), 1):
                    status_icon = "✓" if record.success else "✗"
                    print(f"{i}. {record.timestamp} - {status_icon} {'Успех' if record.success else 'Ошибка'}")
                    if not record.success and record.error_message:
                        print(f"   Ошибка: {record.error_message}")
        
        except Exception as e:
            print(f"Ошибка получения статуса: {e}")
    
    def force_password_change(self):
        """Принудительно запускает смену пароля"""
        print("Принудительная смена пароля Steam...")
        
        try:
            self.scheduler = SteamPasswordScheduler(self.config_file)
            
            # Запрашиваем подтверждение
            confirm = input("Вы уверены, что хотите сменить пароль сейчас? (y/n): ").lower()
            if confirm != 'y':
                print("Отмена операции.")
                return
            
            print("Запускаем смену пароля...")
            self.scheduler.force_password_change()
            
            # Ждем немного и показываем результат
            time.sleep(3)
            
            # Проверяем последнюю запись в истории
            last_record = self.scheduler.password_history.get_last_change()
            if last_record:
                if last_record.success:
                    print("✓ Пароль успешно изменен!")
                else:
                    print("✗ Ошибка при смене пароля")
                    if last_record.error_message:
                        print(f"Детали: {last_record.error_message}")
            else:
                print("⚠ Не удалось получить информацию о результате")
                
        except Exception as e:
            print(f"Ошибка при принудительной смене пароля: {e}")
    
    def generate_test_password(self):
        """Генерирует тестовый пароль для проверки"""
        try:
            generator = PasswordGenerator()
            
            # Загружаем настройки из конфигурации
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            password_config = config.get('password_change', {})
            
            password = generator.generate_password(
                length=password_config.get('password_length', 16),
                use_lowercase=password_config.get('use_lowercase', True),
                use_uppercase=password_config.get('use_uppercase', True),
                use_numbers=password_config.get('use_numbers', True),
                use_special_chars=password_config.get('use_special_chars', True),
                exclude_ambiguous=password_config.get('exclude_ambiguous', True)
            )
            
            strength = generator.validate_password_strength(password)
            
            print(f"\n=== Тестовый пароль ===")
            print(f"Пароль: {password}")
            print(f"Длина: {len(password)}")
            print(f"Сила: {strength['strength']} (баллы: {strength['score']}/8)")
            print(f"Характеристики:")
            print(f"  - Строчные буквы: {'✓' if strength['has_lowercase'] else '✗'}")
            print(f"  - Заглавные буквы: {'✓' if strength['has_uppercase'] else '✗'}")
            print(f"  - Цифры: {'✓' if strength['has_numbers'] else '✗'}")
            print(f"  - Специальные символы: {'✓' if strength['has_special_chars'] else '✗'}")
            print(f"  - Неоднозначные символы: {'✗' if not strength['has_ambiguous'] else '⚠'}")
            
        except Exception as e:
            print(f"Ошибка генерации тестового пароля: {e}")
    
    def test_steam_connection(self):
        """Тестирует подключение к Steam"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("Тестирование подключения к Steam...")
            
            # Тестируем Steam Guard
            shared_secret = config['steam_account']['shared_secret']
            if self.test_steam_guard(shared_secret):
                print("✓ Steam Guard работает")
            else:
                print("✗ Проблема с Steam Guard")
                return
            
            # Здесь можно добавить дополнительные тесты подключения
            print("✓ Базовые проверки пройдены")
            
        except Exception as e:
            print(f"Ошибка тестирования соединения: {e}")


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description="Автоматизированная система смены паролей Steam",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s start                    # Запустить в режиме демона
  %(prog)s status                   # Показать статус системы
  %(prog)s change                   # Принудительно сменить пароль
  %(prog)s test-password            # Сгенерировать тестовый пароль
  %(prog)s test-connection          # Тестировать подключение к Steam
  %(prog)s --config custom.json start  # Использовать custom конфигурацию
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.json',
        help='Путь к файлу конфигурации (по умолчанию: config.json)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Steam Password Changer 1.0.0'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда start
    start_parser = subparsers.add_parser('start', help='Запустить систему в режиме демона')
    
    # Команда status
    status_parser = subparsers.add_parser('status', help='Показать статус системы')
    
    # Команда change
    change_parser = subparsers.add_parser('change', help='Принудительно сменить пароль')
    
    # Команда test-password
    test_pwd_parser = subparsers.add_parser('test-password', help='Сгенерировать тестовый пароль')
    
    # Команда test-connection
    test_conn_parser = subparsers.add_parser('test-connection', help='Тестировать подключение к Steam')
    
    # Парсим аргументы
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Создаем менеджер
    manager = SteamPasswordManager(args.config)
    
    # Проверяем существование конфигурации для команд, которые её требуют
    if args.command in ['start', 'status', 'change', 'test-password', 'test-connection']:
        manager.ensure_config_exists()
    
    # Выполняем команду
    try:
        if args.command == 'start':
            manager.start_daemon()
        elif args.command == 'status':
            manager.show_status()
        elif args.command == 'change':
            manager.force_password_change()
        elif args.command == 'test-password':
            manager.generate_test_password()
        elif args.command == 'test-connection':
            manager.test_steam_connection()
        else:
            print(f"Неизвестная команда: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nОперация прервана пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()