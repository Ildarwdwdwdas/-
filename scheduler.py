#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль планировщика для автоматической смены паролей Steam по расписанию
Поддерживает различные интервалы и настройки планирования
"""

import asyncio
import schedule
import time
import threading
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional, List
import logging
from dataclasses import dataclass, asdict
from password_generator import PasswordGenerator
from steam_client import SteamPasswordChanger


@dataclass
class PasswordChangeRecord:
    """Запись о смене пароля"""
    timestamp: str
    old_password_hash: str  # Хэш старого пароля для безопасности
    new_password_hash: str  # Хэш нового пароля
    success: bool
    error_message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordChangeRecord':
        """Создает объект из словаря"""
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь"""
        return asdict(self)


class PasswordHistory:
    """Класс для управления историей смены паролей"""
    
    def __init__(self, history_file: str = "password_history.json", max_records: int = 10):
        self.history_file = history_file
        self.max_records = max_records
        self.records: List[PasswordChangeRecord] = []
        self.load_history()
    
    def load_history(self):
        """Загружает историю из файла"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [PasswordChangeRecord.from_dict(record) for record in data]
        except Exception as e:
            logging.error(f"Ошибка загрузки истории паролей: {e}")
            self.records = []
    
    def save_history(self):
        """Сохраняет историю в файл"""
        try:
            # Ограничиваем количество записей
            if len(self.records) > self.max_records:
                self.records = self.records[-self.max_records:]
            
            data = [record.to_dict() for record in self.records]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Ошибка сохранения истории паролей: {e}")
    
    def add_record(self, record: PasswordChangeRecord):
        """Добавляет запись о смене пароля"""
        self.records.append(record)
        self.save_history()
    
    def get_last_change(self) -> Optional[PasswordChangeRecord]:
        """Возвращает последнюю успешную смену пароля"""
        for record in reversed(self.records):
            if record.success:
                return record
        return None
    
    def get_failed_attempts(self, since_hours: int = 24) -> List[PasswordChangeRecord]:
        """Возвращает неудачные попытки за указанный период"""
        cutoff_time = datetime.now() - timedelta(hours=since_hours)
        failed_attempts = []
        
        for record in self.records:
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                if record_time > cutoff_time and not record.success:
                    failed_attempts.append(record)
            except ValueError:
                continue
        
        return failed_attempts


class SteamPasswordScheduler:
    """Планировщик автоматической смены паролей Steam"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.password_generator = PasswordGenerator()
        self.password_changer = SteamPasswordChanger(self.config)
        self.password_history = PasswordHistory(
            max_records=self.config.get('security', {}).get('max_password_history', 10)
        )
        self.logger = self.setup_logging()
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Файл конфигурации {self.config_file} не найден")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка в формате JSON: {e}")
            raise
    
    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.logger.info("Конфигурация сохранена")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def setup_logging(self) -> logging.Logger:
        """Настраивает систему логирования"""
        logger = logging.getLogger('SteamPasswordScheduler')
        
        # Удаляем существующие обработчики
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        logger.setLevel(level)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный вывод
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Файловый вывод
        if log_config.get('log_to_file', True):
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_config.get('log_file', 'steam_password_changer.log'),
                    maxBytes=log_config.get('max_log_size_mb', 10) * 1024 * 1024,
                    backupCount=log_config.get('backup_count', 5),
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.error(f"Не удалось настроить файловое логирование: {e}")
        
        return logger
    
    def hash_password(self, password: str) -> str:
        """Создает хэш пароля для безопасного хранения"""
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest()[:16]  # Первые 16 символов
    
    async def change_password_job(self):
        """Основная задача смены пароля"""
        self.logger.info("Начинаем процедуру смены пароля")
        
        try:
            # Проверяем, не было ли недавних неудачных попыток
            failed_attempts = self.password_history.get_failed_attempts(since_hours=1)
            if len(failed_attempts) >= 3:
                self.logger.warning("Слишком много неудачных попыток за последний час, пропускаем смену")
                return
            
            # Генерируем новый пароль
            password_config = self.config.get('password_change', {})
            new_password = self.password_generator.generate_password(
                length=password_config.get('password_length', 16),
                use_lowercase=password_config.get('use_lowercase', True),
                use_uppercase=password_config.get('use_uppercase', True),
                use_numbers=password_config.get('use_numbers', True),
                use_special_chars=password_config.get('use_special_chars', True),
                exclude_ambiguous=password_config.get('exclude_ambiguous', True)
            )
            
            # Проверяем силу пароля
            password_strength = self.password_generator.validate_password_strength(new_password)
            self.logger.info(f"Сгенерирован пароль силой: {password_strength['strength']}")
            
            # Сохраняем старый пароль для записи в историю
            old_password = self.config['steam_account']['password']
            
            # Меняем пароль
            success = await self.password_changer.change_password(new_password)
            
            # Создаем запись в истории
            record = PasswordChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_password_hash=self.hash_password(old_password),
                new_password_hash=self.hash_password(new_password),
                success=success,
                error_message=None if success else "Неизвестная ошибка"
            )
            
            self.password_history.add_record(record)
            
            if success:
                # Сохраняем новый пароль в конфигурации
                self.config['steam_account']['password'] = new_password
                self.save_config()
                
                self.logger.info("Пароль успешно изменен и сохранен")
                
                # Отправляем уведомление
                if self.config.get('notifications', {}).get('notify_on_success', True):
                    self.send_notification(f"Пароль Steam успешно изменен на новый (сила: {password_strength['strength']})")
            else:
                self.logger.error("Не удалось изменить пароль Steam")
                
                # Отправляем уведомление об ошибке
                if self.config.get('notifications', {}).get('notify_on_error', True):
                    self.send_notification("ОШИБКА: Не удалось изменить пароль Steam")
                
        except Exception as e:
            self.logger.error(f"Исключение при смене пароля: {e}")
            
            # Записываем ошибку в историю
            record = PasswordChangeRecord(
                timestamp=datetime.now().isoformat(),
                old_password_hash="",
                new_password_hash="",
                success=False,
                error_message=str(e)
            )
            self.password_history.add_record(record)
            
            # Отправляем уведомление об ошибке
            if self.config.get('notifications', {}).get('notify_on_error', True):
                self.send_notification(f"КРИТИЧЕСКАЯ ОШИБКА при смене пароля: {e}")
    
    def send_notification(self, message: str):
        """Отправляет уведомление"""
        notifications_config = self.config.get('notifications', {})
        
        if not notifications_config.get('enable_notifications', True):
            return
        
        method = notifications_config.get('notification_method', 'console')
        
        if method == 'console':
            self.logger.info(f"УВЕДОМЛЕНИЕ: {message}")
        # Здесь можно добавить другие методы уведомлений (email, telegram, etc.)
    
    def run_async_job(self, job_func):
        """Запускает асинхронную задачу в отдельном потоке"""
        def wrapper():
            if self.loop is None:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            
            try:
                self.loop.run_until_complete(job_func())
            except Exception as e:
                self.logger.error(f"Ошибка выполнения асинхронной задачи: {e}")
        
        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
    
    def schedule_password_changes(self):
        """Настраивает расписание смены паролей"""
        # Очищаем предыдущие задачи
        schedule.clear()
        
        change_interval = self.config.get('password_change', {}).get('change_interval_hours', 24)
        
        # Планируем регулярную смену паролей
        schedule.every(change_interval).hours.do(
            lambda: self.run_async_job(self.change_password_job)
        )
        
        self.logger.info(f"Запланирована смена пароля каждые {change_interval} часов")
        
        # Можно добавить дополнительные расписания
        # Например, ежедневно в определенное время:
        # schedule.every().day.at("02:00").do(lambda: self.run_async_job(self.change_password_job))
    
    def scheduler_worker(self):
        """Основной рабочий цикл планировщика"""
        self.logger.info("Планировщик запущен")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(5)
        
        self.logger.info("Планировщик остановлен")
    
    def start(self):
        """Запускает планировщик"""
        if self.is_running:
            self.logger.warning("Планировщик уже запущен")
            return
        
        self.logger.info("Запускаем планировщик смены паролей Steam")
        
        # Настраиваем расписание
        self.schedule_password_changes()
        
        # Запускаем планировщик в отдельном потоке
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self.scheduler_worker)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        self.logger.info("Планировщик успешно запущен")
    
    def stop(self):
        """Останавливает планировщик"""
        if not self.is_running:
            self.logger.warning("Планировщик не запущен")
            return
        
        self.logger.info("Останавливаем планировщик")
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # Закрываем event loop
        if self.loop and not self.loop.is_closed():
            self.loop.close()
        
        self.logger.info("Планировщик остановлен")
    
    def force_password_change(self):
        """Принудительно запускает смену пароля"""
        self.logger.info("Принудительный запуск смены пароля")
        self.run_async_job(self.change_password_job)
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус планировщика"""
        last_change = self.password_history.get_last_change()
        failed_attempts = self.password_history.get_failed_attempts()
        
        return {
            'is_running': self.is_running,
            'next_scheduled_change': str(schedule.next_run()) if schedule.jobs else None,
            'last_successful_change': last_change.timestamp if last_change else None,
            'failed_attempts_today': len(failed_attempts),
            'total_password_changes': len([r for r in self.password_history.records if r.success])
        }


if __name__ == "__main__":
    # Пример использования
    try:
        scheduler = SteamPasswordScheduler()
        
        print("Статус планировщика:", scheduler.get_status())
        
        # Запускаем планировщик
        scheduler.start()
        
        print("Планировщик запущен. Нажмите Ctrl+C для остановки...")
        
        # Ожидаем прерывания
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nОстанавливаем планировщик...")
            scheduler.stop()
            
    except Exception as e:
        print(f"Ошибка: {e}")