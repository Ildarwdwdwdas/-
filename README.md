# 🔐 Steam Password Changer

Автоматизированная система для смены паролей Steam с настраиваемым интервалом времени. Система работает без использования браузерных драйверов (ChromeDriver и т.д.) и использует прямые API вызовы к Steam.

## ⚠️ Важное предупреждение

**БЕЗОПАСНОСТЬ ПРЕЖДЕ ВСЕГО!**

- Эта система предназначена для повышения безопасности вашего Steam аккаунта
- Используйте только на своих собственных аккаунтах
- Храните конфигурационные файлы в безопасном месте
- Регулярно создавайте резервные копии данных Steam Guard

## 🚀 Возможности

- ✅ **Автоматическая смена паролей** по настраиваемому расписанию
- ✅ **Генерация сильных паролей** с настраиваемыми параметрами
- ✅ **Steam Guard интеграция** без внешних зависимостей
- ✅ **История изменений** с безопасным хранением
- ✅ **Подробное логирование** всех операций
- ✅ **CLI интерфейс** для управления системой
- ✅ **Уведомления** об успешных и неудачных операциях
- ✅ **Защита от спама** (ограничение повторных попыток)
- ✅ **Без браузеров** - только прямые API вызовы

## 📋 Требования

### Системные требования
- Python 3.7+
- Linux/Windows/macOS
- Интернет соединение

### Steam требования
- Steam аккаунт с включенным Steam Guard (мобильный аутентификатор)
- Доступ к Steam Desktop Authenticator или файлам мобильного аутентификатора
- Активный Steam аккаунт

## 🛠️ Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/steam-password-changer.git
cd steam-password-changer
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Первоначальная настройка
```bash
python main.py start
```

При первом запуске система предложит создать конфигурационный файл и проведет вас через процесс настройки.

## 🔧 Настройка Steam Guard

Для работы системы необходимы данные Steam Guard. Вы можете получить их несколькими способами:

### Вариант 1: Steam Desktop Authenticator (SDA)
1. Установите [Steam Desktop Authenticator](https://github.com/Jessecar96/SteamDesktopAuthenticator)
2. Настройте его для вашего аккаунта
3. Найдите файл `.maFile` в папке `maFiles`
4. Откройте файл и найдите значения:
   - `shared_secret`
   - `identity_secret`
   - `device_id`
   - `steamid`

### Вариант 2: Экспорт из мобильного приложения (Root Android)
На устройствах Android с root доступом можно извлечь данные из официального приложения Steam.

### Пример данных Steam Guard:
```json
{
  "shared_secret": "abcdef1234567890abcdef1234567890abcdef12",
  "identity_secret": "1234567890abcdef1234567890abcdef12345678",
  "device_id": "android:12345678-1234-1234-1234-123456789012",
  "steamid": 76561198012345678
}
```

## ⚙️ Конфигурация

Система создает файл `config.json` с настройками:

```json
{
    "steam_account": {
        "login": "ваш_логин",
        "password": "текущий_пароль",
        "shared_secret": "секретный_ключ",
        "identity_secret": "ключ_подтверждения",
        "device_id": "идентификатор_устройства",
        "steamid": 76561198012345678
    },
    "password_change": {
        "change_interval_hours": 24,
        "password_length": 16,
        "use_special_chars": true,
        "use_numbers": true,
        "use_uppercase": true,
        "use_lowercase": true,
        "exclude_ambiguous": true
    },
    "security": {
        "save_password_history": true,
        "max_password_history": 10,
        "require_confirmation": false,
        "backup_old_passwords": true
    },
    "logging": {
        "level": "INFO",
        "log_to_file": true,
        "log_file": "steam_password_changer.log",
        "max_log_size_mb": 10,
        "backup_count": 5
    },
    "notifications": {
        "enable_notifications": true,
        "notify_on_success": true,
        "notify_on_error": true,
        "notification_method": "console"
    }
}
```

## 🎮 Использование

### Основные команды

```bash
# Запустить систему в режиме демона
python main.py start

# Показать статус системы
python main.py status

# Принудительно сменить пароль
python main.py change

# Сгенерировать тестовый пароль
python main.py test-password

# Тестировать подключение к Steam
python main.py test-connection

# Использовать другой конфигурационный файл
python main.py --config custom.json start
```

### Примеры использования

#### Запуск системы
```bash
$ python main.py start
Запуск автоматизированной системы смены паролей Steam...
Система запущена успешно!
Для остановки нажмите Ctrl+C

Текущий статус:
- Планировщик активен: True
- Следующая смена: 2024-01-15 14:30:00
- Последняя успешная смена: 2024-01-14 14:30:00
- Всего смен паролей: 5
```

#### Проверка статуса
```bash
$ python main.py status

=== Статус системы Steam Password Changer ===
Планировщик активен: ✓
Следующая запланированная смена: 2024-01-15 14:30:00
Последняя успешная смена: 2024-01-14 14:30:00
Неудачных попыток сегодня: 0
Всего успешных смен: 5

=== Последние записи истории ===
1. 2024-01-14T14:30:00 - ✓ Успех
2. 2024-01-13T14:30:00 - ✓ Успех
3. 2024-01-12T14:30:00 - ✓ Успех
```

#### Тестирование пароля
```bash
$ python main.py test-password

=== Тестовый пароль ===
Пароль: Kj8#mN2$pQ9!rX5@
Длина: 16
Сила: Очень сильный (баллы: 8/8)
Характеристики:
  - Строчные буквы: ✓
  - Заглавные буквы: ✓
  - Цифры: ✓
  - Специальные символы: ✓
  - Неоднозначные символы: ✗
```

## 📁 Структура проекта

```
steam-password-changer/
├── main.py                 # Главный скрипт CLI
├── scheduler.py            # Планировщик и история паролей
├── steam_client.py         # Steam API клиент
├── password_generator.py   # Генератор безопасных паролей
├── config.json            # Конфигурационный файл
├── requirements.txt       # Python зависимости
├── README.md             # Документация
├── password_history.json # История смены паролей
└── steam_password_changer.log # Лог файл
```

## 🔒 Безопасность

### Рекомендации по безопасности:

1. **Храните конфигурацию в безопасности**
   ```bash
   chmod 600 config.json
   ```

2. **Регулярно создавайте резервные копии**
   ```bash
   cp config.json config_backup_$(date +%Y%m%d).json
   ```

3. **Мониторьте логи**
   ```bash
   tail -f steam_password_changer.log
   ```

4. **Используйте сильные пароли Steam Guard**

5. **Не делитесь данными Steam Guard**

### Что система НЕ сохраняет:
- Пароли в открытом виде (только хэши)
- Полные данные Steam Guard в логах
- Персональную информацию аккаунта

## 🚨 Устранение неполадок

### Ошибка авторизации Steam
```
Ошибка: Не удалось авторизоваться в Steam
```
**Решение:** Проверьте правильность логина, пароля и Steam Guard данных.

### Ошибка Steam Guard
```
Ошибка генерации кода Steam Guard: Неверный формат shared_secret
```
**Решение:** Убедитесь, что `shared_secret` в формате base64.

### Проблемы с сетью
```
Исключение при авторизации: aiohttp.ClientError
```
**Решение:** Проверьте интернет соединение и доступность Steam серверов.

### Слишком много неудачных попыток
```
Слишком много неудачных попыток за последний час, пропускаем смену
```
**Решение:** Подождите час или исправьте конфигурацию и перезапустите.

## 📊 Мониторинг

### Просмотр логов в реальном времени
```bash
tail -f steam_password_changer.log
```

### Системный мониторинг (systemd)
Создайте файл `/etc/systemd/system/steam-password-changer.service`:

```ini
[Unit]
Description=Steam Password Changer
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/steam-password-changer
ExecStart=/usr/bin/python3 main.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск как службы:
```bash
sudo systemctl enable steam-password-changer
sudo systemctl start steam-password-changer
sudo systemctl status steam-password-changer
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл LICENSE для деталей.

## ⚠️ Отказ от ответственности

- Данное программное обеспечение предоставляется "как есть"
- Авторы не несут ответственности за потерю доступа к аккаунтам
- Используйте на свой страх и риск
- Всегда создавайте резервные копии данных Steam Guard
- Тестируйте систему перед использованием на важных аккаунтах

## 🆘 Поддержка

Если у вас возникли проблемы:

1. Проверьте [Issues](https://github.com/your-username/steam-password-changer/issues)
2. Создайте новый Issue с подробным описанием
3. Приложите логи (без конфиденциальных данных)

## 📚 Дополнительные ресурсы

- [Steam Web API Documentation](https://steamcommunity.com/dev)
- [Steam Desktop Authenticator](https://github.com/Jessecar96/SteamDesktopAuthenticator)
- [Steam Guard Mobile Authenticator](https://support.steampowered.com/kb_article.php?ref=4020-ALZM-5519)

---

**⭐ Поставьте звезду, если проект был полезен!**