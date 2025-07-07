#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт установки и быстрого старта для автоматизированной системы смены паролей Steam
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(title: str):
    """Печатает заголовок"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")


def print_step(step: str, status: str = "INFO"):
    """Печатает шаг установки"""
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    print(f"{icons.get(status, 'ℹ️')} {step}")


def check_python_version():
    """Проверяет версию Python"""
    print_step("Проверка версии Python...")
    
    version = sys.version_info
    if version < (3, 7):
        print_step(f"Ошибка: Требуется Python 3.7+, найден Python {version.major}.{version.minor}", "ERROR")
        return False
    
    print_step(f"Python {version.major}.{version.minor}.{version.micro} - OK", "SUCCESS")
    return True


def install_dependencies():
    """Устанавливает зависимости"""
    print_step("Установка зависимостей...")
    
    requirements_file = "requirements.txt"
    if not Path(requirements_file).exists():
        print_step(f"Файл {requirements_file} не найден", "ERROR")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print_step("Зависимости установлены успешно", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_step(f"Ошибка установки зависимостей: {e}", "ERROR")
        return False


def run_system_tests():
    """Запускает системные тесты"""
    print_step("Запуск системных тестов...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_system.py", "--auto"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_step("Системные тесты пройдены успешно", "SUCCESS")
            return True
        else:
            print_step("Некоторые системные тесты не пройдены", "WARNING")
            print(result.stdout)
            return False
    except Exception as e:
        print_step(f"Ошибка запуска тестов: {e}", "ERROR")
        return False


def create_example_config():
    """Создает пример конфигурации"""
    print_step("Создание примера конфигурации...")
    
    example_config = {
        "steam_account": {
            "login": "YOUR_STEAM_LOGIN",
            "password": "YOUR_CURRENT_PASSWORD",
            "shared_secret": "YOUR_SHARED_SECRET_FROM_SDA",
            "identity_secret": "YOUR_IDENTITY_SECRET_FROM_SDA", 
            "device_id": "YOUR_DEVICE_ID_FROM_SDA",
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
    
    try:
        import json
        with open("config.example.json", "w", encoding="utf-8") as f:
            json.dump(example_config, f, ensure_ascii=False, indent=4)
        
        print_step("Пример конфигурации создан: config.example.json", "SUCCESS")
        return True
    except Exception as e:
        print_step(f"Ошибка создания примера конфигурации: {e}", "ERROR")
        return False


def create_systemd_service():
    """Создает systemd service файл для Linux"""
    if platform.system() != "Linux":
        return
    
    print_step("Создание systemd service файла...")
    
    current_dir = Path.cwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Steam Password Changer
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'steam')}
WorkingDirectory={current_dir}
ExecStart={python_path} main.py start
Restart=always
RestartSec=10
Environment=PYTHONPATH={current_dir}

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open("steam-password-changer.service", "w", encoding="utf-8") as f:
            f.write(service_content)
        
        print_step("Systemd service файл создан: steam-password-changer.service", "SUCCESS")
        print_step("Для установки службы выполните:", "INFO")
        print_step("  sudo cp steam-password-changer.service /etc/systemd/system/", "INFO")
        print_step("  sudo systemctl enable steam-password-changer", "INFO")
        print_step("  sudo systemctl start steam-password-changer", "INFO")
        
    except Exception as e:
        print_step(f"Ошибка создания systemd service: {e}", "ERROR")


def create_quick_start_guide():
    """Создает руководство быстрого старта"""
    print_step("Создание руководства быстрого старта...")
    
    guide = """# 🚀 Быстрый старт Steam Password Changer

## 1. Получение данных Steam Guard

Для работы системы нужны данные Steam Guard. Получите их одним из способов:

### Вариант A: Steam Desktop Authenticator (SDA)
1. Скачайте SDA: https://github.com/Jessecar96/SteamDesktopAuthenticator
2. Настройте для вашего аккаунта
3. Найдите файл .maFile в папке maFiles
4. Откройте файл и скопируйте значения

### Вариант B: Экспорт из мобильного приложения (Root Android)
Требуется root доступ для извлечения данных из официального приложения Steam.

## 2. Настройка конфигурации

```bash
# Скопируйте пример конфигурации
cp config.example.json config.json

# Отредактируйте config.json с вашими данными
nano config.json
```

## 3. Запуск системы

```bash
# Тестирование конфигурации
python main.py test-connection

# Генерация тестового пароля
python main.py test-password

# Запуск системы
python main.py start
```

## 4. Полезные команды

```bash
# Проверка статуса
python main.py status

# Принудительная смена пароля
python main.py change

# Просмотр логов
tail -f steam_password_changer.log
```

## 5. Безопасность

```bash
# Установите права доступа к конфигурации
chmod 600 config.json

# Создайте резервную копию
cp config.json config_backup_$(date +%Y%m%d).json
```

## 6. Автозапуск (Linux)

```bash
# Установите как системную службу
sudo cp steam-password-changer.service /etc/systemd/system/
sudo systemctl enable steam-password-changer
sudo systemctl start steam-password-changer

# Проверка статуса службы
sudo systemctl status steam-password-changer
```

## 🆘 Помощь

Если возникли проблемы:
1. Проверьте config.json на корректность данных
2. Убедитесь, что Steam Guard работает
3. Посмотрите логи: tail -f steam_password_changer.log
4. Запустите тесты: python test_system.py

Удачи! 🎮
"""
    
    try:
        with open("QUICK_START.md", "w", encoding="utf-8") as f:
            f.write(guide)
        
        print_step("Руководство быстрого старта создано: QUICK_START.md", "SUCCESS")
        return True
    except Exception as e:
        print_step(f"Ошибка создания руководства: {e}", "ERROR")
        return False


def main():
    """Главная функция установки"""
    print("🔐 Steam Password Changer - Установка")
    print("=" * 60)
    print("Автоматизированная система смены паролей Steam")
    print("Без использования ChromeDriver и браузерной автоматизации")
    print("=" * 60)
    
    # Проверка Python
    print_header("Проверка системы")
    if not check_python_version():
        sys.exit(1)
    
    # Установка зависимостей  
    print_header("Установка зависимостей")
    if "--skip-deps" not in sys.argv:
        if not install_dependencies():
            print_step("Установка зависимостей не удалась. Продолжить? (y/n)", "WARNING")
            if input().lower() != 'y':
                sys.exit(1)
    else:
        print_step("Пропуск установки зависимостей", "INFO")
    
    # Системные тесты
    print_header("Системные тесты")
    if "--skip-tests" not in sys.argv:
        run_system_tests()
    else:
        print_step("Пропуск системных тестов", "INFO")
    
    # Создание файлов
    print_header("Создание конфигурационных файлов")
    create_example_config()
    create_systemd_service()
    create_quick_start_guide()
    
    # Финальные инструкции
    print_header("Установка завершена!")
    print_step("Система готова к настройке и использованию", "SUCCESS")
    print()
    print("📋 Следующие шаги:")
    print("1. Получите данные Steam Guard (см. QUICK_START.md)")
    print("2. Скопируйте config.example.json в config.json")
    print("3. Отредактируйте config.json с вашими данными")
    print("4. Протестируйте: python main.py test-connection") 
    print("5. Запустите: python main.py start")
    print()
    print("📚 Документация:")
    print("- README.md - полная документация")
    print("- QUICK_START.md - быстрый старт")
    print("- config.example.json - пример конфигурации")
    print()
    print("🔒 Важно:")
    print("- Защитите config.json: chmod 600 config.json")
    print("- Создавайте резервные копии Steam Guard данных")
    print("- Тестируйте на тестовом аккаунте перед использованием")
    print()
    print("🎮 Удачи с автоматизацией безопасности Steam!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nУстановка прервана пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nКритическая ошибка установки: {e}")
        sys.exit(1)