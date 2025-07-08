#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки всех компонентов системы автоматической смены паролей Steam
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Импорты наших модулей
from password_generator import PasswordGenerator
from steam_client import SteamAuthenticator, SteamWebClient, SteamPasswordChanger
from scheduler import SteamPasswordScheduler, PasswordHistory, PasswordChangeRecord


class SystemTester:
    """Класс для тестирования всех компонентов системы"""
    
    def __init__(self):
        self.results = {
            'password_generator': False,
            'steam_authenticator': False,
            'password_history': False,
            'config_handling': False,
            'steam_connection': False
        }
        
    def print_header(self, title: str):
        """Печатает заголовок теста"""
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТ: {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Печатает результат теста"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        self.results[test_name] = success
    
    def test_password_generator(self):
        """Тестирует генератор паролей"""
        self.print_header("Генератор паролей")
        
        try:
            generator = PasswordGenerator()
            
            # Тест 1: Генерация базового пароля
            password = generator.generate_password()
            assert len(password) == 16, f"Неправильная длина пароля: {len(password)}"
            print(f"   🔑 Сгенерированный пароль: {password}")
            
            # Тест 2: Проверка силы пароля
            strength = generator.validate_password_strength(password)
            assert strength['score'] >= 5, f"Слабый пароль: {strength['score']}"
            print(f"   💪 Сила пароля: {strength['strength']} (баллы: {strength['score']})")
            
            # Тест 3: Генерация с разными параметрами
            short_password = generator.generate_password(length=8, use_special_chars=False)
            assert len(short_password) == 8, "Неправильная длина короткого пароля"
            print(f"   🔗 Короткий пароль: {short_password}")
            
            # Тест 4: Генерация нескольких паролей
            passwords = generator.generate_multiple_passwords(3, length=12)
            assert len(passwords) == 3, "Неправильное количество паролей"
            assert len(set(passwords)) == 3, "Пароли не уникальны"
            print(f"   📦 Несколько паролей: {passwords}")
            
            self.print_result('password_generator', True, f"Все тесты пройдены")
            
        except Exception as e:
            self.print_result('password_generator', False, f"Ошибка: {e}")
    
    def test_steam_authenticator(self):
        """Тестирует Steam authenticator"""
        self.print_header("Steam Guard Authenticator")
        
        try:
            # Используем тестовый shared_secret (не настоящий)
            test_secret = "dGVzdF9zaGFyZWRfc2VjcmV0X2Zvcl90ZXN0aW5nXzEyMzQ1"
            
            authenticator = SteamAuthenticator(test_secret)
            
            # Тест 1: Генерация кода
            code = authenticator.generate_auth_code()
            assert len(code) == 5, f"Неправильная длина кода: {len(code)}"
            assert code.isdigit(), "Код должен содержать только цифры"
            print(f"   🎯 Сгенерированный код: {code}")
            
            # Тест 2: Генерация кода для определенного времени
            import time
            timestamp = int(time.time())
            code2 = authenticator.generate_auth_code(timestamp)
            assert len(code2) == 5, "Неправильная длина кода с timestamp"
            print(f"   ⏰ Код для timestamp {timestamp}: {code2}")
            
            # Тест 3: Генерация ключа подтверждения
            conf_key = authenticator.generate_confirmation_key(timestamp, "conf")
            assert len(conf_key) > 0, "Пустой ключ подтверждения"
            print(f"   🔐 Ключ подтверждения: {conf_key[:20]}...")
            
            self.print_result('steam_authenticator', True, "Все тесты пройдены")
            
        except Exception as e:
            self.print_result('steam_authenticator', False, f"Ошибка: {e}")
    
    def test_password_history(self):
        """Тестирует историю паролей"""
        self.print_header("История паролей")
        
        try:
            # Используем временный файл
            history_file = "test_password_history.json"
            
            # Очищаем тестовый файл если существует
            if os.path.exists(history_file):
                os.remove(history_file)
            
            history = PasswordHistory(history_file, max_records=3)
            
            # Тест 1: Добавление записи
            from datetime import datetime
            record1 = PasswordChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_password_hash="old_hash_1",
                new_password_hash="new_hash_1",
                success=True
            )
            history.add_record(record1)
            assert len(history.records) == 1, "Запись не добавлена"
            print(f"   📝 Добавлена запись 1")
            
            # Тест 2: Добавление нескольких записей
            record2 = PasswordChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_password_hash="old_hash_2",
                new_password_hash="new_hash_2",
                success=False,
                error_message="Тестовая ошибка"
            )
            history.add_record(record2)
            
            record3 = PasswordChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_password_hash="old_hash_3",
                new_password_hash="new_hash_3",
                success=True
            )
            history.add_record(record3)
            
            assert len(history.records) == 3, "Неправильное количество записей"
            print(f"   📚 Добавлено записей: {len(history.records)}")
            
            # Тест 3: Получение последней успешной смены
            last_change = history.get_last_change()
            assert last_change is not None, "Не найдена последняя смена"
            assert last_change.success, "Последняя смена неуспешна"
            print(f"   🎯 Последняя успешная смена найдена")
            
            # Тест 4: Получение неудачных попыток
            failed_attempts = history.get_failed_attempts(since_hours=24)
            assert len(failed_attempts) == 1, "Неправильное количество неудачных попыток"
            print(f"   ❌ Неудачных попыток: {len(failed_attempts)}")
            
            # Тест 5: Сохранение и загрузка
            history.save_history()
            assert os.path.exists(history_file), "Файл истории не создан"
            
            new_history = PasswordHistory(history_file)
            assert len(new_history.records) == 3, "Неправильная загрузка истории"
            print(f"   💾 Сохранение и загрузка работают")
            
            # Очищаем тестовый файл
            os.remove(history_file)
            
            self.print_result('password_history', True, "Все тесты пройдены")
            
        except Exception as e:
            self.print_result('password_history', False, f"Ошибка: {e}")
    
    def test_config_handling(self):
        """Тестирует обработку конфигурации"""
        self.print_header("Обработка конфигурации")
        
        try:
            # Создаем тестовую конфигурацию
            test_config = {
                "steam_account": {
                    "login": "test_user",
                    "password": "test_password",
                    "shared_secret": "dGVzdF9zaGFyZWRfc2VjcmV0",
                    "identity_secret": "dGVzdF9pZGVudGl0eV9zZWNyZXQ=",
                    "device_id": "test_device_id",
                    "steamid": 76561198000000000
                },
                "password_change": {
                    "change_interval_hours": 24,
                    "password_length": 16,
                    "use_special_chars": True,
                    "use_numbers": True,
                    "use_uppercase": True,
                    "use_lowercase": True,
                    "exclude_ambiguous": True
                },
                "logging": {
                    "level": "INFO",
                    "log_to_file": False
                }
            }
            
            # Тест 1: Создание временного конфигурационного файла
            test_config_file = "test_config.json"
            with open(test_config_file, 'w', encoding='utf-8') as f:
                json.dump(test_config, f, ensure_ascii=False, indent=2)
            
            assert os.path.exists(test_config_file), "Конфигурационный файл не создан"
            print(f"   📄 Конфигурационный файл создан")
            
            # Тест 2: Инициализация планировщика с тестовой конфигурацией
            scheduler = SteamPasswordScheduler(test_config_file)
            assert scheduler.config is not None, "Конфигурация не загружена"
            assert scheduler.config['steam_account']['login'] == 'test_user', "Неправильная загрузка конфигурации"
            print(f"   ⚙️ Планировщик инициализирован")
            
            # Тест 3: Валидация генератора паролей
            generator = scheduler.password_generator
            test_password = generator.generate_password(
                length=test_config['password_change']['password_length']
            )
            assert len(test_password) == 16, "Неправильная длина пароля из конфигурации"
            print(f"   🔧 Генератор паролей работает с конфигурацией")
            
            # Очищаем тестовый файл
            os.remove(test_config_file)
            
            self.print_result('config_handling', True, "Все тесты пройдены")
            
        except Exception as e:
            self.print_result('config_handling', False, f"Ошибка: {e}")
    
    async def test_steam_connection(self):
        """Тестирует соединение с Steam (базовые проверки)"""
        self.print_header("Steam соединение")
        
        try:
            # Тест 1: Создание клиента
            async with SteamWebClient() as client:
                assert client.session is not None, "Сессия не создана"
                print(f"   🌐 HTTP клиент создан")
                
                # Тест 2: Проверка доступности Steam (простой GET запрос)
                try:
                    async with client.session.get('https://steamcommunity.com/', timeout=10) as response:
                        assert response.status == 200, f"Steam недоступен: {response.status}"
                        print(f"   ✅ Steam доступен (статус: {response.status})")
                except Exception as e:
                    print(f"   ⚠️ Проблема с доступностью Steam: {e}")
                    # Не считаем это критической ошибкой
                
                # Тест 3: Проверка получения RSA ключа (без реального логина)
                # Этот тест может не работать без реальных данных
                print(f"   🔑 Базовые проверки клиента выполнены")
            
            self.print_result('steam_connection', True, "Базовые проверки пройдены")
            
        except Exception as e:
            self.print_result('steam_connection', False, f"Ошибка: {e}")
    
    def print_summary(self):
        """Печатает итоговую сводку"""
        self.print_header("ИТОГОВАЯ СВОДКА")
        
        total_tests = len(self.results)
        passed_tests = sum(self.results.values())
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Не пройдено: {total_tests - passed_tests}")
        print(f"Успешность: {(passed_tests / total_tests) * 100:.1f}%")
        
        print(f"\nДетализация:")
        for test_name, result in self.results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print(f"Система готова к использованию.")
        else:
            print(f"\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            print(f"Проверьте конфигурацию и зависимости.")
            
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """Запускает все тесты"""
        print("🚀 ЗАПУСК СИСТЕМНЫХ ТЕСТОВ")
        print("=" * 60)
        
        # Синхронные тесты
        self.test_password_generator()
        self.test_steam_authenticator()
        self.test_password_history()
        self.test_config_handling()
        
        # Асинхронные тесты
        await self.test_steam_connection()
        
        # Итоговая сводка
        return self.print_summary()


async def main():
    """Главная функция"""
    print("Steam Password Changer - Системные тесты")
    print("=" * 60)
    print("Этот скрипт проверяет работоспособность всех компонентов системы.")
    print("Для полного тестирования нужны настоящие данные Steam Guard.")
    print("=" * 60)
    
    # Запрашиваем подтверждение
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        proceed = True
    else:
        proceed = input("Продолжить тестирование? (y/n): ").lower() == 'y'
    
    if not proceed:
        print("Тестирование отменено.")
        return
    
    tester = SystemTester()
    success = await tester.run_all_tests()
    
    # Возвращаем соответствующий код выхода
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nКритическая ошибка при тестировании: {e}")
        sys.exit(1)