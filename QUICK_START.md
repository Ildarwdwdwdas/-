# 🚀 Быстрый старт Steam Password Changer

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
