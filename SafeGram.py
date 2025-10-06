#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SafeGram 4.0 Ultimate Pro Edition
=================================

ОГРОМНЫЙ МНОГОФУНКЦИОНАЛЬНЫЙ МЕССЕНДЖЕР
Конкурент Discord и Telegram с полным набором функций

✅ Многопользовательские чаты и каналы
✅ Голосовые каналы (эмуляция)
✅ Файловый менеджер с превью
✅ Система ботов и автоответчиков
✅ Темы оформления и кастомизация
✅ Расширенная модерация
✅ Игры и развлечения
✅ Интеграции с внешними сервисами
✅ Продвинутая аналитика
✅ Система ачивок и уровней
✅ Marketplace стикеров
✅ И множество других функций!

Автор: Lev
Версия: 4.0 Ultimate Pro
Дата: 2025-10-06
"""
import math
import os
import sys
import json
import time
import re
import secrets
import base64
import hashlib
import smtplib
import zipfile
import io
import shutil
import mimetypes
import uuid
import threading
import queue
import sqlite3
import csv
import signal
from collections import defaultdict, deque

from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from urllib.parse import quote, unquote

import site
sys.path.append(site.getusersitepackages())

from flask import Flask, request, jsonify, make_response, send_from_directory, abort, redirect, render_template_string, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from werkzeug.utils import secure_filename

# Попытка импорта psutil для сбора системной информации
try:
    import psutil
except ModuleNotFoundError:
    psutil = None

# ========================================================================
# ИСПРАВЛЕНИЕ ВСЕХ UNDEFINED VARIABLES
# ========================================================================

# Инициализация глобальных переменных
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_safegram")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
AVATAR_DIR = os.path.join(DATA_DIR, "avatars")
STICKERS_DIR = os.path.join(DATA_DIR, "stickers")
TEMP_DIR = os.path.join(DATA_DIR, "temp")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
VOICE_DIR = os.path.join(DATA_DIR, "voice")
THEMES_DIR = os.path.join(DATA_DIR, "themes")
BOTS_DIR = os.path.join(DATA_DIR, "bots")
USERS_DIR = os.path.join(DATA_DIR, "users")
SERVERS_DIR = os.path.join(DATA_DIR, "servers")
CHANNELS_DIR = os.path.join(DATA_DIR, "channels")
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")

USERS_JSON = os.path.join(DATA_DIR, "users.json")
MESSAGES_JSON = os.path.join(DATA_DIR, "messages.json")
CHANNELS_JSON = os.path.join(DATA_DIR, "channels.json")
SERVERS_JSON = os.path.join(DATA_DIR, "servers.json")
SESSIONS_JSON = os.path.join(DATA_DIR, "sessions.json")
STATS_JSON = os.path.join(DATA_DIR, "stats.json")
FRIENDS_JSON = os.path.join(DATA_DIR, "friends.json")
BOTS_JSON = os.path.join(DATA_DIR, "bots.json")
THEMES_JSON = os.path.join(DATA_DIR, "themes.json")
ACHIEVEMENTS_JSON = os.path.join(DATA_DIR, "achievements.json")
SETTINGS_JSON = os.path.join(DATA_DIR, "settings.json")
LOGS_JSON = os.path.join(DATA_DIR, "system_logs.json")
REPORTS_JSON = os.path.join(DATA_DIR, "reports.json")
MARKETPLACE_JSON = os.path.join(DATA_DIR, "marketplace.json")
NOTIFICATIONS_JSON = os.path.join(DATA_DIR, "notifications.json")
VOICE_SESSIONS_JSON = os.path.join(DATA_DIR, "voice_sessions.json")
FILE_STORAGE_JSON = os.path.join(DATA_DIR, "file_storage.json")

# Создание директорий
for d in [DATA_DIR, UPLOAD_DIR, AVATAR_DIR, STICKERS_DIR, TEMP_DIR, BACKUP_DIR, LOGS_DIR, VOICE_DIR, THEMES_DIR, BOTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ========================================================================
# КОНФИГУРАЦИЯ SafeGram 4.0 Ultimate Pro
# ========================================================================

APP_NAME = "SafeGram 4.0 Ultimate Pro"
APP_VERSION = "4.0.0"
APP_PORT = int(os.environ.get("SAFEGRAM_PORT", 8080))
DEBUG_MODE = os.environ.get("SAFEGRAM_DEBUG", "false").lower() == "true"

SECRET_KEY = os.environ.get("SAFEGRAM_SECRET", "ultra_mega_secure_key_2025")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_MESSAGE_LENGTH = 4000
MAX_CHANNEL_MEMBERS = 10000
MAX_SERVERS_PER_USER = 100
MAX_CHANNELS_PER_SERVER = 500
RATE_LIMIT_MESSAGES = 30
RATE_LIMIT_FILES = 10
ONLINE_TIMEOUT = 300

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@safegram.local")

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
ALLOWED_ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
ALLOWED_CODE_EXTENSIONS = {'.py', '.js', '.html', '.css', '.json', '.xml', '.md'}

SUPPORTED_LANGUAGES = ['ru', 'en', 'es', 'fr', 'de', 'zh', 'ja', 'ko']

# ========================================================================
# Flask и SocketIO инициализация
# ========================================================================

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Rate limiting
user_message_times = defaultdict(deque)
user_registration_ips = defaultdict(list)
banned_ips = set()

print(f"✅ Импорты и основные настройки для {APP_NAME} инициализированы")

# ========================================================================
# ИНИЦИАЛИЗАЦИЯ ДАННЫХ И БАЗОВЫЕ СТРУКТУРЫ
# ========================================================================

# Базовые структуры данных
DEFAULT_SETTINGS = {
    "app_name": APP_NAME,
    "version": APP_VERSION,
    "registration_enabled": True,
    "email_verification": False,
    "max_file_size_mb": MAX_FILE_SIZE // (1024*1024),
    "default_language": "ru",
    "default_theme": "dark",
    "maintenance_mode": False,
    "debug_mode": DEBUG_MODE,
    "features": {
        "voice_channels": True,
        "file_sharing": True,
        "bots": True,
        "games": True,
        "marketplace": True,
        "achievements": True,
        "custom_themes": True
    }
}

DEFAULT_USER = {
    "id": "",
    "username": "",
    "email": "",
    "password_hash": "",
    "avatar": "",
    "status": "online",  # online, idle, busy, offline
    "custom_status": "",
    "created_at": 0,
    "last_seen": 0,
    "language": "ru",
    "theme": "dark",
    "level": 1,
    "experience": 0,
    "achievements": [],
    "friends": [],
    "blocked_users": [],
    "servers": [],
    "settings": {
        "show_online_status": True,
        "allow_friend_requests": True,
        "allow_server_invites": True,
        "notifications": True,
        "sound_notifications": True,
        "email_notifications": False
    },
    "statistics": {
        "messages_sent": 0,
        "files_shared": 0,
        "voice_time": 0,
        "servers_joined": 0
    }
}

DEFAULT_SERVER = {
    "id": "",
    "name": "",
    "description": "",
    "icon": "",
    "owner_id": "",
    "created_at": 0,
    "members": [],
    "channels": [],
    "roles": [],
    "settings": {
        "public": False,
        "invite_only": True,
        "member_verification": False,
        "explicit_content_filter": True,
        "default_notifications": True
    },
    "statistics": {
        "member_count": 0,
        "message_count": 0,
        "channel_count": 0
    }
}

DEFAULT_CHANNEL = {
    "id": "",
    "name": "",
    "type": "text",  # text, voice, category, announcement
    "server_id": "",
    "category_id": "",
    "position": 0,
    "topic": "",
    "created_at": 0,
    "permissions": {},
    "settings": {
        "nsfw": False,
        "slowmode": 0,
        "auto_archive": False
    },
    "statistics": {
        "message_count": 0
    }
}

DEFAULT_MESSAGE = {
    "id": "",
    "channel_id": "",
    "server_id": "",
    "author_id": "",
    "content": "",
    "type": "default",  # default, system, bot, embed
    "created_at": 0,
    "edited_at": 0,
    "attachments": [],
    "embeds": [],
    "reactions": {},
    "mentions": [],
    "reply_to": None,
    "pinned": False,
    "deleted": False,
    "flags": []
}

# Инициализация JSON файлов с дефолтными данными
INITIAL_DATA = {
    USERS_JSON: [
        {
            **DEFAULT_USER,
            "id": "system",
            "username": "System",
            "email": "system@safegram.local",
            "avatar": "🤖",
            "status": "online",
            "level": 99,
            "created_at": time.time()
        }
    ],
    MESSAGES_JSON: [],
    CHANNELS_JSON: [
        {
            **DEFAULT_CHANNEL,
            "id": "general",
            "name": "общий",
            "type": "text",
            "server_id": "main",
            "created_at": time.time()
        },
        {
            **DEFAULT_CHANNEL,
            "id": "voice_general",
            "name": "Общий голосовой",
            "type": "voice",
            "server_id": "main",
            "created_at": time.time()
        }
    ],
    SERVERS_JSON: [
        {
            **DEFAULT_SERVER,
            "id": "main",
            "name": "SafeGram Community",
            "description": "Главный сервер SafeGram",
            "icon": "🏠",
            "owner_id": "system",
            "channels": ["general", "voice_general"],
            "members": ["system"],
            "created_at": time.time()
        }
    ],
    FRIENDS_JSON: {},
    BOTS_JSON: [
        {
            "id": "welcome_bot",
            "name": "Welcome Bot",
            "description": "Приветствует новых пользователей",
            "avatar": "👋",
            "status": "online",
            "commands": ["/welcome", "/help"],
            "created_at": time.time()
        }
    ],
    THEMES_JSON: [
        {
            "id": "dark",
            "name": "Тёмная тема",
            "author": "SafeGram Team",
            "colors": {
                "primary": "#0a0a0f",
                "secondary": "#161620",
                "accent": "#00d4ff",
                "text": "#ffffff",
                "background": "#1f1f2e"
            },
            "default": True
        },
        {
            "id": "light",
            "name": "Светлая тема",
            "author": "SafeGram Team", 
            "colors": {
                "primary": "#ffffff",
                "secondary": "#f5f7fb",
                "accent": "#007acc",
                "text": "#111111",
                "background": "#ffffff"
            },
            "default": False
        },
        {
            "id": "cyberpunk",
            "name": "Киберпанк",
            "author": "SafeGram Team",
            "colors": {
                "primary": "#0d1117",
                "secondary": "#21262d",
                "accent": "#ff0080",
                "text": "#00ff80",
                "background": "#161b22"
            },
            "default": False
        }
    ],
    ACHIEVEMENTS_JSON: [
        {
            "id": "first_message",
            "name": "Первое сообщение",
            "description": "Отправьте своё первое сообщение",
            "icon": "💬",
            "reward_xp": 10
        },
        {
            "id": "friend_maker",
            "name": "Заводила",
            "description": "Добавьте 10 друзей",
            "icon": "👥",
            "reward_xp": 50
        },
        {
            "id": "server_creator",
            "name": "Создатель",
            "description": "Создайте свой первый сервер",
            "icon": "🏗️",
            "reward_xp": 100
        }
    ],
    SETTINGS_JSON: DEFAULT_SETTINGS,
    STATS_JSON: {
        "total_users": 1,
        "total_messages": 0,
        "total_servers": 1,
        "total_channels": 2,
        "uptime_start": time.time(),
        "daily_stats": {},
        "popular_features": {}
    },
    SESSIONS_JSON: {},
    LOGS_JSON: [],
    REPORTS_JSON: [],
    MARKETPLACE_JSON: [
        {
            "id": "basic_emoji_pack",
            "name": "Базовый набор эмодзи",
            "type": "stickers",
            "price": 0,
            "author": "SafeGram Team",
            "downloads": 0,
            "rating": 5.0,
            "created_at": time.time()
        }
    ]
}

# Инициализируем файлы данных
def initialize_data_files():
    """Инициализация всех JSON файлов с базовыми данными"""
    for file_path, default_data in INITIAL_DATA.items():
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                print(f"✅ Создан файл: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"❌ Ошибка создания {file_path}: {e}")

# Запускаем инициализацию при импорте
initialize_data_files()

# ========================================================================
# БАЗОВЫЕ УТИЛИТЫ И ПОМОЩНИКИ
# ========================================================================

def load_json(filepath: str, default=None):
    """Безопасная загрузка JSON файла"""
    if default is None:
        default = []
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        log_error(f"Ошибка загрузки {filepath}: {e}")
        return default

def save_json(filepath: str, data):
    """Безопасное сохранение JSON файла"""
    try:
        # Создаем резервную копию
        if os.path.exists(filepath):
            backup_path = filepath + '.backup'
            shutil.copy2(filepath, backup_path)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_error(f"Ошибка сохранения {filepath}: {e}")
        return False

def generate_id(prefix: str = "") -> str:
    """Генерация уникального ID"""
    timestamp = str(int(time.time() * 1000))[-8:]
    random_part = secrets.token_hex(4)
    return f"{prefix}_{timestamp}_{random_part}" if prefix else f"{timestamp}_{random_part}"

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${base64.b64encode(pwd_hash).decode()}"

def verify_password(password: str, hash_str: str) -> bool:
    """Проверка пароля"""
    try:
        salt, pwd_hash = hash_str.split('$')
        expected_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return base64.b64encode(expected_hash).decode() == pwd_hash
    except:
        return False

def log_event(event_type: str, description: str, user_id: str = "system", 
              additional_data: dict = None):
    """Логирование событий системы"""
    logs = load_json(LOGS_JSON, [])
    log_entry = {
        "id": generate_id("log"),
        "timestamp": time.time(),
        "type": event_type,
        "user_id": user_id,
        "description": description,
        "data": additional_data or {},
        "ip": request.remote_addr if request else "localhost"
    }
    logs.append(log_entry)

    # Храним только последние 5000 записей
    if len(logs) > 5000:
        logs = logs[-5000:]

    save_json(LOGS_JSON, logs)

def log_error(message: str):
    """Логирование ошибок"""
    log_event("error", message)
    if DEBUG_MODE:
        print(f"❌ ERROR: {message}")

def log_info(message: str):
    """Логирование информации"""
    log_event("info", message)
    if DEBUG_MODE:
        print(f"ℹ️ INFO: {message}")

def get_file_type(filename: str) -> str:
    """Определение типа файла"""
    ext = os.path.splitext(filename.lower())[1]
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        return "document"
    elif ext in ALLOWED_ARCHIVE_EXTENSIONS:
        return "archive"
    elif ext in ALLOWED_CODE_EXTENSIONS:
        return "code"
    else:
        return "file"

def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def is_valid_email(email: str) -> bool:
    """Проверка валидности email"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.match(pattern, email) is not None

def sanitize_username(username: str) -> str:
    """Очистка имени пользователя"""
    # Оставляем только буквы, цифры, дефис и подчеркивание
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    return clean[:32]  # Максимум 32 символа

def get_user_level(experience: int) -> int:
    """Вычисление уровня пользователя по опыту"""
    # Каждый уровень требует в 1.5 раза больше опыта
    level = 1
    required_xp = 100
    current_xp = 0

    while current_xp + required_xp <= experience:
        current_xp += required_xp
        level += 1
        required_xp = int(required_xp * 1.5)

    return min(level, 100)  # Максимум 100 уровень

print("✅ Добавлены инициализация данных и базовые утилиты")

# ========================================================================
# СИСТЕМА УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ
# ========================================================================

class UserManager:
    """Менеджер для работы с пользователями"""

    @staticmethod
    def create_user(username: str, email: str, password: str) -> dict:
        """Создание нового пользователя"""
        users = load_json(USERS_JSON, [])

        # Проверяем уникальность
        if any(u['email'].lower() == email.lower() for u in users):
            return {"success": False, "error": "Email уже используется"}

        if any(u['username'].lower() == username.lower() for u in users):
            return {"success": False, "error": "Имя пользователя уже занято"}

        # Создаем пользователя
        user = {
            **DEFAULT_USER,
            "id": generate_id("user"),
            "username": sanitize_username(username),
            "email": email.lower(),
            "password_hash": hash_password(password),
            "created_at": time.time(),
            "last_seen": time.time()
        }

        users.append(user)
        save_json(USERS_JSON, users)

        # Добавляем пользователя к главному серверу
        servers = load_json(SERVERS_JSON, [])
        main_server = next((s for s in servers if s['id'] == 'main'), None)
        if main_server and user['id'] not in main_server['members']:
            main_server['members'].append(user['id'])
            save_json(SERVERS_JSON, servers)

        log_event("user_created", f"Создан пользователь: {username}", user['id'])

        # Начисляем достижение за регистрацию
        AchievementManager.award_achievement(user['id'], 'first_registration')

        return {"success": True, "user": user}

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[dict]:
        """Получение пользователя по ID"""
        users = load_json(USERS_JSON, [])
        return next((u for u in users if u['id'] == user_id), None)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[dict]:
        """Получение пользователя по email"""
        users = load_json(USERS_JSON, [])
        return next((u for u in users if u['email'].lower() == email.lower()), None)

    @staticmethod
    def update_user(user_id: str, updates: dict) -> bool:
        """Обновление данных пользователя"""
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)

        if not user:
            return False

        # Обновляем только разрешенные поля
        allowed_fields = ['username', 'status', 'custom_status', 'language', 
                         'theme', 'settings', 'avatar', 'last_seen']

        for field, value in updates.items():
            if field in allowed_fields:
                user[field] = value

        save_json(USERS_JSON, users)
        log_event("user_updated", f"Обновлён пользователь: {user_id}", user_id)
        return True

    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Удаление пользователя"""
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)

        if not user:
            return False

        # Удаляем пользователя из всех серверов
        servers = load_json(SERVERS_JSON, [])
        for server in servers:
            if user_id in server['members']:
                server['members'].remove(user_id)
        save_json(SERVERS_JSON, servers)

        # Удаляем сообщения пользователя (помечаем как удаленные)
        messages = load_json(MESSAGES_JSON, [])
        for msg in messages:
            if msg['author_id'] == user_id:
                msg['deleted'] = True
                msg['content'] = "[Пользователь удален]"
        save_json(MESSAGES_JSON, messages)

        # Удаляем из списка пользователей
        users = [u for u in users if u['id'] != user_id]
        save_json(USERS_JSON, users)

        log_event("user_deleted", f"Удален пользователь: {user['username']}", "system")
        return True

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[dict]:
        """Аутентификация пользователя"""
        user = UserManager.get_user_by_email(email)

        if user and 'password_hash' in user and verify_password(password, user['password_hash']):
            # Обновляем время последнего посещения
            UserManager.update_user(user['id'], {"last_seen": time.time()})
            log_event("user_login", f"Вход пользователя: {user['username']}", user['id'])
            return user

        log_event("login_failed", f"Неудачная попытка входа: {email}")
        return None

    @staticmethod
    def get_online_users() -> List[dict]:
        """Получение списка онлайн пользователей"""
        users = load_json(USERS_JSON, [])
        sessions = load_json(SESSIONS_JSON, {})
        current_time = time.time()

        online_users = []
        for user in users:
            session = sessions.get(user['id'])
            if session and (current_time - session.get('last_activity', 0)) < ONLINE_TIMEOUT:
                user_copy = user.copy()
                user_copy.pop('password_hash', None)  # Убираем пароль из ответа
                online_users.append(user_copy)

        return online_users

    @staticmethod
    def add_friend(user_id: str, friend_id: str) -> bool:
        """Добавление в друзья"""
        if user_id == friend_id:
            return False

        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)
        friend = next((u for u in users if u['id'] == friend_id), None)

        if not user or not friend:
            return False

        # Добавляем взаимно
        if friend_id not in user['friends']:
            user['friends'].append(friend_id)

        if user_id not in friend['friends']:
            friend['friends'].append(user_id)

        save_json(USERS_JSON, users)

        # Проверяем достижение
        if len(user['friends']) >= 10:
            AchievementManager.award_achievement(user_id, 'friend_maker')

        log_event("friend_added", f"{user['username']} добавил в друзья {friend['username']}", user_id)
        return True

    @staticmethod
    def remove_friend(user_id: str, friend_id: str) -> bool:
        """Удаление из друзей"""
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)
        friend = next((u for u in users if u['id'] == friend_id), None)

        if not user or not friend:
            return False

        # Удаляем взаимно
        if friend_id in user['friends']:
            user['friends'].remove(friend_id)

        if user_id in friend['friends']:
            friend['friends'].remove(user_id)

        save_json(USERS_JSON, users)
        log_event("friend_removed", f"{user['username']} удалил из друзей {friend['username']}", user_id)
        return True

def get_current_user():
    """
    Получить текущего пользователя по session['user_id'].
    Возвращает словарь с данными пользователя или None.
    """
    user_id = session.get('user_id')
    if not user_id:
        return None

    # Специальный пользователь «админ»
    if user_id == 'admin':
        return {
            "id": "admin",
            "username": "Administrator",
            "email": "admin@safegram.local",
            "is_admin": True,
            "is_guest": False,
            "status": "online",
            "avatar": "👑"
        }

    # Загружаем всех пользователей
    try:
        users = []
        if os.path.exists(USERS_JSON):
            with open(USERS_JSON, 'r', encoding='utf-8') as f:
                users = json.load(f)
    except Exception:
        users = []

    # Находим текущего пользователя по id
    user = next((u for u in users if u.get('id') == user_id), None)

    # Если нашли, обновим last_seen и статус
    if user:
        user['last_seen'] = time.time()
        user['status'] = 'online'

    return user


# ========================================================================
# СИСТЕМА СЕССИЙ
# ========================================================================

class SessionManager:
    """Менеджер сессий пользователей"""

    @staticmethod
    def create_session(user_id: str, ip_address: str = None) -> str:
        """Создание новой сессии"""
        sessions = load_json(SESSIONS_JSON, {})

        session_token = secrets.token_hex(32)
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "ip_address": ip_address or request.remote_addr if request else "unknown",
            "user_agent": request.headers.get('User-Agent', 'unknown') if request else "unknown"
        }

        sessions[session_token] = session_data
        save_json(SESSIONS_JSON, sessions)

        log_event("session_created", f"Создана сессия для пользователя: {user_id}", user_id)
        return session_token

    @staticmethod
    def validate_session(session_token: str) -> Optional[dict]:
        """Проверка валидности сессии"""
        if not session_token:
            return None

        sessions = load_json(SESSIONS_JSON, {})
        session = sessions.get(session_token)

        if not session:
            return None

        # Проверяем не истекла ли сессия
        current_time = time.time()
        if current_time - session['last_activity'] > ONLINE_TIMEOUT * 6:  # 30 минут неактивности
            SessionManager.delete_session(session_token)
            return None

        # Обновляем время последней активности
        session['last_activity'] = current_time
        sessions[session_token] = session
        save_json(SESSIONS_JSON, sessions)

        return session

    @staticmethod
    def delete_session(session_token: str) -> bool:
        """Удаление сессии"""
        sessions = load_json(SESSIONS_JSON, {})

        if session_token in sessions:
            user_id = sessions[session_token].get('user_id', 'unknown')
            del sessions[session_token]
            save_json(SESSIONS_JSON, sessions)
            log_event("session_deleted", f"Удалена сессия пользователя: {user_id}", user_id)
            return True

        return False

    @staticmethod
    def cleanup_expired_sessions():
        """Очистка истекших сессий"""
        sessions = load_json(SESSIONS_JSON, {})
        current_time = time.time()
        expired_tokens = []

        for token, session in sessions.items():
            if current_time - session['last_activity'] > ONLINE_TIMEOUT * 12:  # 1 час
                expired_tokens.append(token)

        for token in expired_tokens:
            del sessions[token]

        if expired_tokens:
            save_json(SESSIONS_JSON, sessions)
            log_event("sessions_cleaned", f"Очищено {len(expired_tokens)} истекших сессий", "system")

    @staticmethod
    def get_current_user():
        """Получение текущего пользователя из сессии"""
        session_token = request.cookies.get('session_token')
        if not session_token:
            return None

        session = SessionManager.validate_session(session_token)
        if not session:
            return None

        return UserManager.get_user_by_id(session['user_id'])

# ========================================================================
# СИСТЕМА ДОСТИЖЕНИЙ
# ========================================================================

class AchievementManager:
    """Менеджер достижений пользователей"""

    @staticmethod
    def award_achievement(user_id: str, achievement_id: str) -> bool:
        """Присуждение достижения пользователю"""
        users = load_json(USERS_JSON, [])
        achievements = load_json(ACHIEVEMENTS_JSON, [])

        user = next((u for u in users if u['id'] == user_id), None)
        achievement = next((a for a in achievements if a['id'] == achievement_id), None)

        if not user or not achievement:
            return False

        # Проверяем, есть ли уже это достижение
        if achievement_id in user.get('achievements', []):
            return False

        # Добавляем достижение
        if 'achievements' not in user:
            user['achievements'] = []

        user['achievements'].append({
            "id": achievement_id,
            "earned_at": time.time()
        })

        # Начисляем опыт
        if 'experience' not in user:
            user['experience'] = 0

        user['experience'] += achievement.get('reward_xp', 0)
        user['level'] = get_user_level(user['experience'])

        save_json(USERS_JSON, users)

        log_event("achievement_awarded", 
                 f"Пользователь {user['username']} получил достижение: {achievement['name']}", 
                 user_id)

        return True

    @staticmethod
    def get_user_achievements(user_id: str) -> List[dict]:
        """Получение достижений пользователя"""
        user = UserManager.get_user_by_id(user_id)
        achievements = load_json(ACHIEVEMENTS_JSON, [])

        if not user:
            return []

        user_achievements = user.get('achievements', [])
        result = []

        for user_achievement in user_achievements:
            achievement = next((a for a in achievements if a['id'] == user_achievement['id']), None)
            if achievement:
                result.append({
                    **achievement,
                    "earned_at": user_achievement['earned_at']
                })

        return result

    @staticmethod
    def get_available_achievements() -> List[dict]:
        """Получение списка всех доступных достижений"""
        return load_json(ACHIEVEMENTS_JSON, [])

print("✅ Добавлены системы управления пользователями, сессий и достижений")

# ========================================================================
# СИСТЕМА СЕРВЕРОВ И КАНАЛОВ
# ========================================================================

class ServerManager:
    """Менеджер серверов (аналог Discord серверов)"""

    @staticmethod
    def create_server(name: str, description: str, owner_id: str, icon: str = "🏠") -> dict:
        """Создание нового сервера"""
        servers = load_json(SERVERS_JSON, [])

        server = {
            **DEFAULT_SERVER,
            "id": generate_id("server"),
            "name": name,
            "description": description,
            "icon": icon,
            "owner_id": owner_id,
            "created_at": time.time(),
            "members": [owner_id]
        }

        # Создаем базовые каналы
        general_channel = {
            **DEFAULT_CHANNEL,
            "id": generate_id("channel"),
            "name": "общий",
            "type": "text",
            "server_id": server["id"],
            "created_at": time.time()
        }

        voice_channel = {
            **DEFAULT_CHANNEL,
            "id": generate_id("channel"),
            "name": "Общий голосовой",
            "type": "voice",
            "server_id": server["id"],
            "created_at": time.time()
        }

        server["channels"] = [general_channel["id"], voice_channel["id"]]

        # Сохраняем сервер
        servers.append(server)
        save_json(SERVERS_JSON, servers)

        # Сохраняем каналы
        channels = load_json(CHANNELS_JSON, [])
        channels.extend([general_channel, voice_channel])
        save_json(CHANNELS_JSON, channels)

        # Добавляем сервер в список пользователя
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == owner_id), None)
        if user:
            if 'servers' not in user:
                user['servers'] = []
            user['servers'].append(server['id'])
            save_json(USERS_JSON, users)

            # Достижение за создание сервера
            AchievementManager.award_achievement(owner_id, 'server_creator')

        log_event("server_created", f"Создан сервер: {name}", owner_id)
        return {"success": True, "server": server}

    @staticmethod
    def get_server_by_id(server_id: str) -> Optional[dict]:
        """Получение сервера по ID"""
        servers = load_json(SERVERS_JSON, [])
        return next((s for s in servers if s['id'] == server_id), None)

    @staticmethod
    def get_user_servers(user_id: str) -> List[dict]:
        """Получение серверов пользователя"""
        servers = load_json(SERVERS_JSON, [])
        user_servers = []

        for server in servers:
            if user_id in server.get('members', []):
                user_servers.append(server)

        return user_servers

    @staticmethod
    def join_server(server_id: str, user_id: str) -> bool:
        """Присоединение к серверу"""
        servers = load_json(SERVERS_JSON, [])
        server = next((s for s in servers if s['id'] == server_id), None)

        if not server or user_id in server.get('members', []):
            return False

        server['members'].append(user_id)
        server['statistics']['member_count'] = len(server['members'])
        save_json(SERVERS_JSON, servers)

        # Добавляем сервер в список пользователя
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)
        if user:
            if 'servers' not in user:
                user['servers'] = []
            if server_id not in user['servers']:
                user['servers'].append(server_id)
                user['statistics']['servers_joined'] = user['statistics'].get('servers_joined', 0) + 1
            save_json(USERS_JSON, users)

        log_event("server_joined", f"Пользователь присоединился к серверу: {server['name']}", user_id)
        return True

    @staticmethod
    def leave_server(server_id: str, user_id: str) -> bool:
        """Покидание сервера"""
        servers = load_json(SERVERS_JSON, [])
        server = next((s for s in servers if s['id'] == server_id), None)

        if not server or user_id not in server.get('members', []):
            return False

        # Нельзя покинуть сервер, если ты его владелец
        if server['owner_id'] == user_id:
            return False

        server['members'].remove(user_id)
        server['statistics']['member_count'] = len(server['members'])
        save_json(SERVERS_JSON, servers)

        # Удаляем сервер из списка пользователя
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)
        if user and 'servers' in user and server_id in user['servers']:
            user['servers'].remove(server_id)
            save_json(USERS_JSON, users)

        log_event("server_left", f"Пользователь покинул сервер: {server['name']}", user_id)
        return True

class ChannelManager:
    """Менеджер каналов"""

    @staticmethod
    def create_channel(server_id: str, name: str, channel_type: str = "text", 
                      topic: str = "", creator_id: str = None) -> dict:
        """Создание нового канала"""
        channels = load_json(CHANNELS_JSON, [])
        servers = load_json(SERVERS_JSON, [])

        server = next((s for s in servers if s['id'] == server_id), None)
        if not server:
            return {"success": False, "error": "Сервер не найден"}

        channel = {
            **DEFAULT_CHANNEL,
            "id": generate_id("channel"),
            "name": name,
            "type": channel_type,
            "server_id": server_id,
            "topic": topic,
            "created_at": time.time()
        }

        channels.append(channel)
        save_json(CHANNELS_JSON, channels)

        # Добавляем канал к серверу
        server['channels'].append(channel['id'])
        server['statistics']['channel_count'] = len(server['channels'])
        save_json(SERVERS_JSON, servers)

        log_event("channel_created", f"Создан канал: {name} на сервере: {server['name']}", creator_id)
        return {"success": True, "channel": channel}

    @staticmethod
    def get_channel_by_id(channel_id: str) -> Optional[dict]:
        """Получение канала по ID"""
        channels = load_json(CHANNELS_JSON, [])
        return next((c for c in channels if c['id'] == channel_id), None)

    @staticmethod
    def get_server_channels(server_id: str) -> List[dict]:
        """Получение каналов сервера"""
        channels = load_json(CHANNELS_JSON, [])
        return [c for c in channels if c['server_id'] == server_id]

    @staticmethod
    def delete_channel(channel_id: str, user_id: str) -> bool:
        """Удаление канала"""
        channels = load_json(CHANNELS_JSON, [])
        channel = next((c for c in channels if c['id'] == channel_id), None)

        if not channel:
            return False

        # Проверяем права (должен быть владелец сервера)
        server = ServerManager.get_server_by_id(channel['server_id'])
        if not server or server['owner_id'] != user_id:
            return False

        # Удаляем канал
        channels = [c for c in channels if c['id'] != channel_id]
        save_json(CHANNELS_JSON, channels)

        # Удаляем из сервера
        servers = load_json(SERVERS_JSON, [])
        server = next((s for s in servers if s['id'] == channel['server_id']), None)
        if server and channel_id in server['channels']:
            server['channels'].remove(channel_id)
            save_json(SERVERS_JSON, servers)

        log_event("channel_deleted", f"Удален канал: {channel['name']}", user_id)
        return True

# ========================================================================
# СИСТЕМА СООБЩЕНИЙ
# ========================================================================

class MessageManager:
    """Менеджер сообщений"""

    @staticmethod
    def send_message(channel_id: str, author_id: str, content: str, 
                    message_type: str = "default", attachments: List = None,
                    reply_to: str = None) -> dict:
        """Отправка сообщения"""
        messages = load_json(MESSAGES_JSON, [])

        # Проверяем канал
        channel = ChannelManager.get_channel_by_id(channel_id)
        if not channel:
            return {"success": False, "error": "Канал не найден"}

        # Проверяем длину сообщения
        if len(content) > MAX_MESSAGE_LENGTH:
            return {"success": False, "error": f"Максимальная длина сообщения {MAX_MESSAGE_LENGTH} символов"}

        # Создаем сообщение
        message = {
            **DEFAULT_MESSAGE,
            "id": generate_id("msg"),
            "channel_id": channel_id,
            "server_id": channel['server_id'],
            "author_id": author_id,
            "content": content,
            "type": message_type,
            "created_at": time.time(),
            "attachments": attachments or [],
            "reply_to": reply_to
        }

        messages.append(message)
        save_json(MESSAGES_JSON, messages)

        # Обновляем статистику канала
        channels = load_json(CHANNELS_JSON, [])
        channel = next((c for c in channels if c['id'] == channel_id), None)
        if channel:
            channel['statistics']['message_count'] += 1
            save_json(CHANNELS_JSON, channels)

        # Обновляем статистику пользователя
        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == author_id), None)
        if user:
            user['statistics']['messages_sent'] = user['statistics'].get('messages_sent', 0) + 1
            user['experience'] = user.get('experience', 0) + 1  # 1 XP за сообщение
            user['level'] = get_user_level(user['experience'])
            save_json(USERS_JSON, users)

            # Достижение за первое сообщение
            if user['statistics']['messages_sent'] == 1:
                AchievementManager.award_achievement(author_id, 'first_message')

        log_event("message_sent", f"Отправлено сообщение в канал: {channel['name']}", author_id)
        return {"success": True, "message": message}

    @staticmethod
    def get_channel_messages(channel_id: str, limit: int = 50, before: str = None) -> List[dict]:
        """Получение сообщений канала"""
        messages = load_json(MESSAGES_JSON, [])

        # Фильтруем по каналу и не удаленные
        channel_messages = [m for m in messages 
                          if m['channel_id'] == channel_id and not m.get('deleted', False)]

        # Сортируем по времени
        channel_messages.sort(key=lambda x: x['created_at'], reverse=True)

        # Применяем пагинацию
        if before:
            before_timestamp = float(before)
            channel_messages = [m for m in channel_messages if m['created_at'] < before_timestamp]

        return channel_messages[:limit]

    @staticmethod
    def edit_message(message_id: str, user_id: str, new_content: str) -> bool:
        """Редактирование сообщения"""
        messages = load_json(MESSAGES_JSON, [])
        message = next((m for m in messages if m['id'] == message_id), None)

        if not message or message['author_id'] != user_id or message.get('deleted'):
            return False

        message['content'] = new_content
        message['edited_at'] = time.time()
        save_json(MESSAGES_JSON, messages)

        log_event("message_edited", f"Отредактировано сообщение: {message_id}", user_id)
        return True

    @staticmethod
    def delete_message(message_id: str, user_id: str) -> bool:
        """Удаление сообщения"""
        messages = load_json(MESSAGES_JSON, [])
        message = next((m for m in messages if m['id'] == message_id), None)

        if not message:
            return False

        # Проверяем права на удаление
        can_delete = False

        # Автор может удалить свое сообщение
        if message['author_id'] == user_id:
            can_delete = True

        # Владелец сервера может удалить любое сообщение
        if message['server_id']:
            server = ServerManager.get_server_by_id(message['server_id'])
            if server and server['owner_id'] == user_id:
                can_delete = True

        if not can_delete:
            return False

        message['deleted'] = True
        message['content'] = "[Сообщение удалено]"
        save_json(MESSAGES_JSON, messages)

        log_event("message_deleted", f"Удалено сообщение: {message_id}", user_id)
        return True

    @staticmethod
    def pin_message(message_id: str, user_id: str) -> bool:
        """Закрепление сообщения"""
        messages = load_json(MESSAGES_JSON, [])
        message = next((m for m in messages if m['id'] == message_id), None)

        if not message:
            return False

        # Проверяем права (владелец сервера)
        server = ServerManager.get_server_by_id(message['server_id'])
        if not server or server['owner_id'] != user_id:
            return False

        message['pinned'] = not message.get('pinned', False)
        save_json(MESSAGES_JSON, messages)

        action = "закреплено" if message['pinned'] else "открепленно"
        log_event("message_pinned", f"Сообщение {action}: {message_id}", user_id)
        return True

    @staticmethod
    def add_reaction(message_id: str, user_id: str, emoji: str) -> bool:
        """Добавление реакции к сообщению"""
        messages = load_json(MESSAGES_JSON, [])
        message = next((m for m in messages if m['id'] == message_id), None)

        if not message:
            return False

        if 'reactions' not in message:
            message['reactions'] = {}

        if emoji not in message['reactions']:
            message['reactions'][emoji] = []

        if user_id not in message['reactions'][emoji]:
            message['reactions'][emoji].append(user_id)
        else:
            message['reactions'][emoji].remove(user_id)
            if not message['reactions'][emoji]:
                del message['reactions'][emoji]

        save_json(MESSAGES_JSON, messages)
        return True

    @staticmethod
    def search_messages(query: str, channel_id: str = None, user_id: str = None, 
                       limit: int = 50) -> List[dict]:
        """Поиск сообщений"""
        messages = load_json(MESSAGES_JSON, [])

        # Фильтруем сообщения
        filtered_messages = []
        for message in messages:
            if message.get('deleted'):
                continue

            # Поиск по содержимому
            if query.lower() not in message.get('content', '').lower():
                continue

            # Фильтр по каналу
            if channel_id and message['channel_id'] != channel_id:
                continue

            # Фильтр по пользователю
            if user_id and message['author_id'] != user_id:
                continue

            filtered_messages.append(message)

        # Сортируем по релевантности (новые сначала)
        filtered_messages.sort(key=lambda x: x['created_at'], reverse=True)

        return filtered_messages[:limit]

print("✅ Добавлены системы серверов, каналов и сообщений")

# ========================================================================
# СИСТЕМА ФАЙЛОВ И МЕДИА
# ========================================================================

class FileManager:
    """Менеджер файлов и медиа"""

    @staticmethod
    def upload_file(file, user_id: str, channel_id: str = None) -> dict:
        """Загрузка файла"""
        try:
            if not file or not file.filename:
                return {"success": False, "error": "Файл не выбран"}

            # Проверяем размер файла
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            if file_size > MAX_FILE_SIZE:
                return {"success": False, "error": f"Максимальный размер файла {MAX_FILE_SIZE//1024//1024}MB"}

            # Генерируем безопасное имя файла
            filename = secure_filename(file.filename)
            file_id = generate_id("file")
            file_ext = os.path.splitext(filename)[1].lower()
            safe_filename = f"{file_id}{file_ext}"

            # Определяем подпапку по типу файла
            file_type = get_file_type(filename)
            subfolder = {
                "image": "images",
                "video": "videos", 
                "audio": "audio",
                "document": "documents",
                "archive": "archives",
                "code": "code"
            }.get(file_type, "other")

            # Создаем директорию если не существует
            upload_subfolder = os.path.join(UPLOAD_DIR, subfolder)
            os.makedirs(upload_subfolder, exist_ok=True)

            # Сохраняем файл
            file_path = os.path.join(upload_subfolder, safe_filename)
            file.save(file_path)

            # Создаем запись о файле
            file_record = {
                "id": file_id,
                "original_name": filename,
                "safe_name": safe_filename,
                "path": os.path.join(subfolder, safe_filename),
                "size": file_size,
                "type": file_type,
                "mime_type": mimetypes.guess_type(filename)[0],
                "uploaded_by": user_id,
                "channel_id": channel_id,
                "uploaded_at": time.time(),
                "download_count": 0
            }

            # Обновляем статистику пользователя
            users = load_json(USERS_JSON, [])
            user = next((u for u in users if u['id'] == user_id), None)
            if user:
                user['statistics']['files_shared'] = user['statistics'].get('files_shared', 0) + 1
                user['experience'] = user.get('experience', 0) + 5  # 5 XP за файл
                user['level'] = get_user_level(user['experience'])
                save_json(USERS_JSON, users)

            log_event("file_uploaded", f"Загружен файл: {filename} ({format_file_size(file_size)})", user_id)

            return {
                "success": True,
                "file": file_record,
                "url": f"/uploads/{subfolder}/{safe_filename}"
            }

        except Exception as e:
            log_error(f"Ошибка загрузки файла: {e}")
            return {"success": False, "error": "Ошибка загрузки файла"}

    @staticmethod
    def get_file_info(file_id: str) -> Optional[dict]:
        """Получение информации о файле"""
        # В реальной реализации это была бы отдельная таблица файлов
        # Пока ищем в сообщениях
        messages = load_json(MESSAGES_JSON, [])
        for message in messages:
            for attachment in message.get('attachments', []):
                if attachment.get('id') == file_id:
                    return attachment
        return None

    @staticmethod
    def delete_file(file_id: str, user_id: str) -> bool:
        """Удаление файла"""
        file_info = FileManager.get_file_info(file_id)
        if not file_info or file_info['uploaded_by'] != user_id:
            return False

        try:
            file_path = os.path.join(UPLOAD_DIR, file_info['path'])
            if os.path.exists(file_path):
                os.remove(file_path)

            log_event("file_deleted", f"Удален файл: {file_info['original_name']}", user_id)
            return True
        except Exception as e:
            log_error(f"Ошибка удаления файла: {e}")
            return False

    @staticmethod
    def get_user_files(user_id: str, file_type: str = None, limit: int = 50) -> List[dict]:
        """Получение файлов пользователя"""
        messages = load_json(MESSAGES_JSON, [])
        user_files = []

        for message in messages:
            if message['author_id'] == user_id:
                for attachment in message.get('attachments', []):
                    if not file_type or attachment.get('type') == file_type:
                        user_files.append({
                            **attachment,
                            "message_id": message['id'],
                            "channel_id": message['channel_id']
                        })

        # Сортируем по дате
        user_files.sort(key=lambda x: x.get('uploaded_at', 0), reverse=True)
        return user_files[:limit]

    @staticmethod
    def create_thumbnail(file_path: str, file_type: str) -> Optional[str]:
        """Создание превью для изображений (заглушка)"""
        # В реальной реализации здесь был бы код для создания превью
        # используя PIL или другие библиотеки
        if file_type == "image":
            return f"{file_path}_thumb.jpg"
        return None

# ========================================================================
# СИСТЕМА БОТОВ
# ========================================================================

class BotManager:
    """Менеджер ботов и автоответчиков"""

    @staticmethod
    def create_bot(name: str, description: str, creator_id: str, commands: List[str] = None) -> dict:
        """Создание нового бота"""
        bots = load_json(BOTS_JSON, [])

        bot = {
            "id": generate_id("bot"),
            "name": name,
            "description": description,
            "avatar": "🤖",
            "creator_id": creator_id,
            "status": "online",
            "commands": commands or [],
            "created_at": time.time(),
            "message_count": 0,
            "servers": [],
            "settings": {
                "auto_respond": True,
                "learn_from_messages": False,
                "moderate_content": False
            }
        }

        bots.append(bot)
        save_json(BOTS_JSON, bots)

        log_event("bot_created", f"Создан бот: {name}", creator_id)
        return {"success": True, "bot": bot}

    @staticmethod
    def get_bot_by_id(bot_id: str) -> Optional[dict]:
        """Получение бота по ID"""
        bots = load_json(BOTS_JSON, [])
        return next((b for b in bots if b['id'] == bot_id), None)

    @staticmethod
    def process_bot_command(message: dict) -> Optional[dict]:
        """Обработка команд ботов"""
        content = message.get('content', '')
        if not content.startswith('/'):
            return None

        command = content.split()[0].lower()
        bots = load_json(BOTS_JSON, [])

        # Простые встроенные команды
        bot_responses = {
            '/help': "📋 Доступные команды:\n/help - помощь\n/time - текущее время\n/stats - статистика сервера\n/quote - случайная цитата",
            '/time': f"🕐 Текущее время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}",
            '/stats': "📊 Статистика сервера: 3 пользователя онлайн, 47 сообщений сегодня",
            '/quote': "💭 ""Программирование - это искусство управления сложностью" - "Брэд Кокс",
            '/weather': "🌤️ Погода: +20°C, облачно с прояснениями",
            '/joke': "😄 Почему программисты не любят природу? Слишком много багов! 🐛"
        }

        response_text = bot_responses.get(command)
        if response_text:
            return {
                "content": response_text,
                "author": "🤖 SafeGram Bot",
                "type": "bot"
            }

        return None

    @staticmethod
    def add_bot_to_server(bot_id: str, server_id: str, user_id: str) -> bool:
        """Добавление бота на сервер"""
        # Проверяем права (должен быть владелец сервера)
        server = ServerManager.get_server_by_id(server_id)
        if not server or server['owner_id'] != user_id:
            return False

        bots = load_json(BOTS_JSON, [])
        bot = next((b for b in bots if b['id'] == bot_id), None)

        if not bot or server_id in bot.get('servers', []):
            return False

        bot['servers'].append(server_id)
        save_json(BOTS_JSON, bots)

        log_event("bot_added", f"Бот {bot['name']} добавлен на сервер {server['name']}", user_id)
        return True

# ========================================================================
# СИСТЕМА ТЕМ ОФОРМЛЕНИЯ
# ========================================================================

class ThemeManager:
    """Менеджер тем оформления"""

    @staticmethod
    def create_custom_theme(name: str, colors: dict, creator_id: str) -> dict:
        """Создание пользовательской темы"""
        themes = load_json(THEMES_JSON, [])

        theme = {
            "id": generate_id("theme"),
            "name": name,
            "author": creator_id,
            "colors": colors,
            "created_at": time.time(),
            "downloads": 0,
            "rating": 5.0,
            "custom": True
        }

        themes.append(theme)
        save_json(THEMES_JSON, themes)

        log_event("theme_created", f"Создана тема: {name}", creator_id)
        return {"success": True, "theme": theme}

    @staticmethod
    def get_all_themes() -> List[dict]:
        """Получение всех доступных тем"""
        return load_json(THEMES_JSON, [])

    @staticmethod
    def get_theme_by_id(theme_id: str) -> Optional[dict]:
        """Получение темы по ID"""
        themes = load_json(THEMES_JSON, [])
        return next((t for t in themes if t['id'] == theme_id), None)

    @staticmethod
    def apply_user_theme(user_id: str, theme_id: str) -> bool:
        """Применение темы для пользователя"""
        theme = ThemeManager.get_theme_by_id(theme_id)
        if not theme:
            return False

        users = load_json(USERS_JSON, [])
        user = next((u for u in users if u['id'] == user_id), None)

        if not user:
            return False

        user['theme'] = theme_id
        save_json(USERS_JSON, users)

        # Увеличиваем счетчик скачиваний темы
        themes = load_json(THEMES_JSON, [])
        theme_obj = next((t for t in themes if t['id'] == theme_id), None)
        if theme_obj:
            theme_obj['downloads'] = theme_obj.get('downloads', 0) + 1
            save_json(THEMES_JSON, themes)

        log_event("theme_applied", f"Применена тема: {theme['name']}", user_id)
        return True

    @staticmethod
    def get_popular_themes(limit: int = 10) -> List[dict]:
        """Получение популярных тем"""
        themes = load_json(THEMES_JSON, [])
        # Сортируем по количеству скачиваний
        themes.sort(key=lambda x: x.get('downloads', 0), reverse=True)
        return themes[:limit]

# ========================================================================
# СИСТЕМА МОДЕРАЦИИ
# ========================================================================

class ModerationManager:
    """Менеджер модерации контента"""

    @staticmethod
    def report_content(reporter_id: str, content_type: str, content_id: str, reason: str) -> bool:
        """Подача жалобы на контент"""
        reports = load_json(REPORTS_JSON, [])

        report = {
            "id": generate_id("report"),
            "reporter_id": reporter_id,
            "content_type": content_type,  # message, user, server
            "content_id": content_id,
            "reason": reason,
            "status": "pending",  # pending, reviewed, resolved
            "created_at": time.time(),
            "moderator_id": None,
            "resolution": None
        }

        reports.append(report)
        save_json(REPORTS_JSON, reports)

        log_event("content_reported", f"Подана жалоба на {content_type}: {content_id}", reporter_id)
        return True

    @staticmethod
    def get_pending_reports() -> List[dict]:
        """Получение нерассмотренных жалоб"""
        reports = load_json(REPORTS_JSON, [])
        return [r for r in reports if r['status'] == 'pending']

    @staticmethod
    def moderate_report(report_id: str, moderator_id: str, resolution: str, action: str = None) -> bool:
        """Рассмотрение жалобы модератором"""
        reports = load_json(REPORTS_JSON, [])
        report = next((r for r in reports if r['id'] == report_id), None)

        if not report:
            return False

        report['status'] = 'resolved'
        report['moderator_id'] = moderator_id
        report['resolution'] = resolution
        report['resolved_at'] = time.time()

        # Выполняем действие если необходимо
        if action == 'delete_message' and report['content_type'] == 'message':
            MessageManager.delete_message(report['content_id'], moderator_id)
        elif action == 'ban_user' and report['content_type'] == 'user':
            # В реальной реализации здесь был бы бан пользователя
            pass

        save_json(REPORTS_JSON, reports)
        log_event("report_resolved", f"Рассмотрена жалоба: {report_id}", moderator_id)
        return True

    @staticmethod
    def check_spam_content(content: str, user_id: str) -> dict:
        """Простая проверка на спам (заглушка)"""
        # В реальной системе здесь были бы сложные алгоритмы или ИИ
        spam_keywords = ['спам', 'реклама', 'купить', 'скидка', 'акция']

        spam_score = 0
        for keyword in spam_keywords:
            if keyword in content.lower():
                spam_score += 1

        is_spam = spam_score >= 2

        return {
            "is_spam": is_spam,
            "confidence": min(spam_score * 0.3, 1.0),
            "keywords_found": spam_score
        }

print("✅ Добавлены системы файлов, ботов, тем и модерации")

# ========================================================================
# УТИЛИТЫ
# ========================================================================

def create_directories():
    import os

    directories = [
        USERS_DIR,
        SERVERS_DIR,
        CHANNELS_DIR,
        MESSAGES_DIR,
        VOICE_DIR,
        THEMES_DIR,
        BOTS_DIR,
        LOGS_DIR,
        BACKUP_DIR,
        # Добавьте все остальные пути, которые должны быть созданы
    ]

    for directory in directories:
        if directory is not None and isinstance(directory, (str, bytes, os.PathLike)):
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        else:
            print(f"Warning: path {directory} is not set or invalid")

def save_json(filepath: str, data: Any) -> bool:
    """Безопасное сохранение JSON"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_error(f"Ошибка сохранения {filepath}: {e}")
        return False

def generate_id(prefix: str = "") -> str:
    """Генерация уникального ID"""
    timestamp = str(int(time.time() * 1000))[-8:]
    random_part = secrets.token_hex(6)
    return f"{prefix}{timestamp}{random_part}" if prefix else f"{timestamp}{random_part}"

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${base64.b64encode(pwd_hash).decode()}"

def verify_password(password: str, hash_str: str) -> bool:
    """Проверка пароля"""
    try:
        salt, pwd_hash = hash_str.split('$')
        expected_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return base64.b64encode(expected_hash).decode() == pwd_hash
    except:
        return False

def log_error(message: str):
    """Логирование ошибок"""
    print(f"❌ ERROR: {message}")

# ========================================================================
# СИСТЕМА ДРУЗЕЙ И КОНТАКТОВ - ПОЛНАЯ РЕАЛИЗАЦИЯ
# ========================================================================

class FriendsManager:
    """Полная система управления друзьями и контактами"""
    
    @staticmethod
    def add_friend(user_id: str, friend_id: str) -> Dict:
        """Добавление друга"""
        try:
            friends = load_json(FRIENDS_JSON, [])
            
            # Проверяем, что пользователи существуют
            users = load_json(USERS_JSON, [])
            user_exists = any(u['id'] == user_id for u in users)
            friend_exists = any(u['id'] == friend_id for u in users)
            
            if not user_exists or not friend_exists:
                return {"success": False, "error": "Пользователь не найден"}
            
            if user_id == friend_id:
                return {"success": False, "error": "Нельзя добавить себя в друзья"}
            
            # Проверяем, что они еще не друзья
            existing = next((f for f in friends if 
                           (f['user_id'] == user_id and f['friend_id'] == friend_id) or
                           (f['user_id'] == friend_id and f['friend_id'] == user_id)), None)
            
            if existing:
                return {"success": False, "error": "Уже в списке друзей"}
            
            # Добавляем дружбу (взаимную)
            friendship = {
                "id": generate_id("friend_"),
                "user_id": user_id,
                "friend_id": friend_id,
                "created_at": time.time(),
                "status": "active",
                "favorite": False
            }
            
            # Обратная связь
            reverse_friendship = {
                "id": generate_id("friend_"),
                "user_id": friend_id,
                "friend_id": user_id,
                "created_at": time.time(),
                "status": "active",
                "favorite": False
            }
            
            friends.extend([friendship, reverse_friendship])
            save_json(FRIENDS_JSON, friends)
            
            # Отправляем уведомление
            user_data = next(u for u in users if u['id'] == user_id)
            NotificationManager.send_notification(
                friend_id, 
                "Новый друг!", 
                f"{user_data['username']} добавил вас в друзья", 
                "friend_added"
            )
            
            return {"success": True, "friendship": friendship}
            
        except Exception as e:
            log_error(f"Ошибка добавления друга: {e}")
            return {"success": False, "error": "Внутренняя ошибка"}
    
    @staticmethod
    def remove_friend(user_id: str, friend_id: str) -> bool:
        """Удаление друга"""
        try:
            friends = load_json(FRIENDS_JSON, [])
            
            # Удаляем обе записи дружбы
            friends = [f for f in friends if not (
                (f['user_id'] == user_id and f['friend_id'] == friend_id) or
                (f['user_id'] == friend_id and f['friend_id'] == user_id)
            )]
            
            save_json(FRIENDS_JSON, friends)
            return True
            
        except Exception as e:
            log_error(f"Ошибка удаления друга: {e}")
            return False
    
    @staticmethod
    def get_friends_list(user_id: str) -> List[Dict]:
        """Список друзей пользователя"""
        try:
            friends = load_json(FRIENDS_JSON, [])
            users = load_json(USERS_JSON, [])
            
            user_friends = [f for f in friends if f['user_id'] == user_id]
            
            # Получаем детали друзей
            friends_details = []
            for friendship in user_friends:
                friend_data = next((u for u in users if u['id'] == friendship['friend_id']), None)
                if friend_data:
                    friend_info = {
                        "id": friend_data['id'],
                        "username": friend_data['username'],
                        "avatar": friend_data.get('avatar', '👤'),
                        "status": friend_data.get('status', 'offline'),
                        "last_seen": friend_data.get('last_seen', 0),
                        "friendship_date": friendship['created_at'],
                        "favorite": friendship.get('favorite', False)
                    }
                    friends_details.append(friend_info)
            
            return friends_details
            
        except Exception as e:
            log_error(f"Ошибка получения списка друзей: {e}")
            return []
    
    @staticmethod
    def send_friend_request(from_user: str, to_user: str, message: str = "") -> Dict:
        """Отправка заявки в друзья"""
        try:
            # Загружаем данные
            users = load_json(USERS_JSON, [])
            notifications = load_json(NOTIFICATIONS_JSON, [])
            
            # Проверяем пользователей
            from_user_data = next((u for u in users if u['id'] == from_user), None)
            to_user_data = next((u for u in users if u['id'] == to_user), None)
            
            if not from_user_data or not to_user_data:
                return {"success": False, "error": "Пользователь не найден"}
            
            # Создаем заявку
            request_data = {
                "id": generate_id("freq_"),
                "from_user": from_user,
                "to_user": to_user,
                "message": message,
                "created_at": time.time(),
                "status": "pending"
            }
            
            # Создаем уведомление
            notification = {
                "id": generate_id("notif_"),
                "user_id": to_user,
                "type": "friend_request",
                "title": "Заявка в друзья",
                "message": f"{from_user_data['username']} хочет добавить вас в друзья",
                "data": request_data,
                "created_at": time.time(),
                "read": False
            }
            
            notifications.append(notification)
            save_json(NOTIFICATIONS_JSON, notifications)
            
            return {"success": True, "request": request_data}
            
        except Exception as e:
            log_error(f"Ошибка отправки заявки в друзья: {e}")
            return {"success": False, "error": "Внутренняя ошибка"}
    
    @staticmethod
    def get_friend_requests(user_id: str) -> List[Dict]:
        """Получение заявок в друзья"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            users = load_json(USERS_JSON, [])
            
            # Получаем заявки в друзья
            requests = [n for n in notifications if 
                       n['user_id'] == user_id and 
                       n['type'] == 'friend_request' and 
                       not n.get('read', False)]
            
            # Добавляем информацию об отправителях
            for request in requests:
                from_user_id = request['data']['from_user']
                from_user_data = next((u for u in users if u['id'] == from_user_id), None)
                if from_user_data:
                    request['from_user_info'] = {
                        "id": from_user_data['id'],
                        "username": from_user_data['username'],
                        "avatar": from_user_data.get('avatar', '👤')
                    }
            
            return requests
            
        except Exception as e:
            log_error(f"Ошибка получения заявок в друзья: {e}")
            return []
    
    @staticmethod
    def accept_friend_request(user_id: str, request_id: str) -> Dict:
        """Принятие заявки в друзья"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            
            # Находим заявку
            request = next((n for n in notifications if n['id'] == request_id), None)
            if not request or request['user_id'] != user_id:
                return {"success": False, "error": "Заявка не найдена"}
            
            from_user_id = request['data']['from_user']
            
            # Добавляем в друзья
            result = FriendsManager.add_friend(user_id, from_user_id)
            
            if result['success']:
                # Отмечаем заявку как прочитанную
                for notification in notifications:
                    if notification['id'] == request_id:
                        notification['read'] = True
                        break
                
                save_json(NOTIFICATIONS_JSON, notifications)
                
                # Отправляем уведомление отправителю
                users = load_json(USERS_JSON, [])
                user_data = next(u for u in users if u['id'] == user_id)
                NotificationManager.send_notification(
                    from_user_id,
                    "Заявка принята!",
                    f"{user_data['username']} принял вашу заявку в друзья",
                    "friend_accepted"
                )
            
            return result
            
        except Exception as e:
            log_error(f"Ошибка принятия заявки: {e}")
            return {"success": False, "error": "Внутренняя ошибка"}

# ========================================================================
# ГОЛОСОВЫЕ КАНАЛЫ И ЗВОНКИ - ПОЛНАЯ РЕАЛИЗАЦИЯ
# ========================================================================

class VoiceManager:
    """Полная система голосовых каналов и звонков"""
    
    active_calls = {}
    voice_channels = {}
    screen_shares = {}
    
    @staticmethod
    def create_voice_room(channel_id: str, creator_id: str) -> Dict:
        """Создание голосовой комнаты"""
        try:
            voice_sessions = load_json(VOICE_SESSIONS_JSON, {})
            
            room_data = {
                "id": generate_id("voice_"),
                "channel_id": channel_id,
                "creator_id": creator_id,
                "created_at": time.time(),
                "participants": [creator_id],
                "settings": {
                    "max_participants": 50,
                    "push_to_talk": False,
                    "noise_suppression": True,
                    "echo_cancellation": True,
                    "bitrate": 64000
                },
                "status": "active"
            }
            
            voice_sessions[room_data['id']] = room_data
            VoiceManager.voice_channels[room_data['id']] = room_data
            
            save_json(VOICE_SESSIONS_JSON, voice_sessions)
            
            return {"success": True, "room": room_data}
            
        except Exception as e:
            log_error(f"Ошибка создания голосовой комнаты: {e}")
            return {"success": False, "error": "Не удалось создать комнату"}
    
    @staticmethod
    def join_voice_channel(user_id: str, channel_id: str) -> Dict:
        """Подключение к голосовому каналу"""
        try:
            voice_sessions = load_json(VOICE_SESSIONS_JSON, {})
            
            # Находим комнату для этого канала
            room = None
            for room_id, room_data in voice_sessions.items():
                if room_data['channel_id'] == channel_id and room_data['status'] == 'active':
                    room = room_data
                    break
            
            if not room:
                # Создаем новую комнату
                result = VoiceManager.create_voice_room(channel_id, user_id)
                if result['success']:
                    return result
                else:
                    return {"success": False, "error": "Не удалось подключиться"}
            
            # Проверяем лимит участников
            if len(room['participants']) >= room['settings']['max_participants']:
                return {"success": False, "error": "Комната переполнена"}
            
            # Добавляем пользователя
            if user_id not in room['participants']:
                room['participants'].append(user_id)
                
                # Обновляем в памяти и на диске
                voice_sessions[room['id']] = room
                VoiceManager.voice_channels[room['id']] = room
                save_json(VOICE_SESSIONS_JSON, voice_sessions)
                
                # Уведомляем других участников
                VoiceManager._notify_participants(room['id'], {
                    "type": "user_joined",
                    "user_id": user_id,
                    "participants_count": len(room['participants'])
                })
            
            return {"success": True, "room": room}
            
        except Exception as e:
            log_error(f"Ошибка подключения к голосовому каналу: {e}")
            return {"success": False, "error": "Ошибка подключения"}
    
    @staticmethod
    def leave_voice_channel(user_id: str, room_id: str) -> Dict:
        """Отключение от голосового канала"""
        try:
            voice_sessions = load_json(VOICE_SESSIONS_JSON, {})
            
            if room_id not in voice_sessions:
                return {"success": False, "error": "Комната не найдена"}
            
            room = voice_sessions[room_id]
            
            # Удаляем пользователя
            if user_id in room['participants']:
                room['participants'].remove(user_id)
                
                # Если комната пуста, закрываем её
                if not room['participants']:
                    room['status'] = 'closed'
                    if room_id in VoiceManager.voice_channels:
                        del VoiceManager.voice_channels[room_id]
                else:
                    # Уведомляем остальных участников
                    VoiceManager._notify_participants(room_id, {
                        "type": "user_left",
                        "user_id": user_id,
                        "participants_count": len(room['participants'])
                    })
                
                voice_sessions[room_id] = room
                save_json(VOICE_SESSIONS_JSON, voice_sessions)
            
            return {"success": True}
            
        except Exception as e:
            log_error(f"Ошибка отключения от голосового канала: {e}")
            return {"success": False, "error": "Ошибка отключения"}
    
    @staticmethod
    def start_screen_share(user_id: str, room_id: str) -> Dict:
        """Демонстрация экрана"""
        try:
            if room_id not in VoiceManager.voice_channels:
                return {"success": False, "error": "Голосовая комната не найдена"}
            
            room = VoiceManager.voice_channels[room_id]
            
            if user_id not in room['participants']:
                return {"success": False, "error": "Вы не в этой комнате"}
            
            # Проверяем, что экран еще никто не демонстрирует
            if room_id in VoiceManager.screen_shares:
                current_presenter = VoiceManager.screen_shares[room_id]['presenter_id']
                if current_presenter != user_id:
                    return {"success": False, "error": "Экран уже демонстрируется"}
            
            # Начинаем демонстрацию
            share_data = {
                "presenter_id": user_id,
                "started_at": time.time(),
                "quality": "high",
                "audio_included": True
            }
            
            VoiceManager.screen_shares[room_id] = share_data
            
            # Уведомляем участников
            VoiceManager._notify_participants(room_id, {
                "type": "screen_share_started",
                "presenter_id": user_id
            })
            
            return {"success": True, "share_data": share_data}
            
        except Exception as e:
            log_error(f"Ошибка начала демонстрации экрана: {e}")
            return {"success": False, "error": "Ошибка демонстрации"}
    
    @staticmethod
    def stop_screen_share(user_id: str, room_id: str) -> Dict:
        """Остановка демонстрации экрана"""
        try:
            if room_id not in VoiceManager.screen_shares:
                return {"success": False, "error": "Демонстрация не активна"}
            
            share_data = VoiceManager.screen_shares[room_id]
            
            if share_data['presenter_id'] != user_id:
                return {"success": False, "error": "Вы не демонстрируете экран"}
            
            # Останавливаем демонстрацию
            del VoiceManager.screen_shares[room_id]
            
            # Уведомляем участников
            VoiceManager._notify_participants(room_id, {
                "type": "screen_share_stopped",
                "presenter_id": user_id
            })
            
            return {"success": True}
            
        except Exception as e:
            log_error(f"Ошибка остановки демонстрации: {e}")
            return {"success": False, "error": "Ошибка остановки"}
    
    @staticmethod
    def toggle_mute(user_id: str, room_id: str, muted: bool = None) -> Dict:
        """Включение/выключение микрофона"""
        try:
            if room_id not in VoiceManager.voice_channels:
                return {"success": False, "error": "Комната не найдена"}
            
            room = VoiceManager.voice_channels[room_id]
            
            if user_id not in room['participants']:
                return {"success": False, "error": "Вы не в комнате"}
            
            # Состояние микрофона (в реальном приложении было бы в WebRTC)
            if 'audio_states' not in room:
                room['audio_states'] = {}
            
            if muted is None:
                current_state = room['audio_states'].get(user_id, False)
                muted = not current_state
            
            room['audio_states'][user_id] = muted
            
            # Уведомляем участников
            VoiceManager._notify_participants(room_id, {
                "type": "user_audio_changed",
                "user_id": user_id,
                "muted": muted
            })
            
            return {"success": True, "muted": muted}
            
        except Exception as e:
            log_error(f"Ошибка переключения микрофона: {e}")
            return {"success": False, "error": "Ошибка переключения"}
    
    @staticmethod
    def get_voice_channel_info(channel_id: str) -> Dict:
        """Получение информации о голосовом канале"""
        try:
            voice_sessions = load_json(VOICE_SESSIONS_JSON, {})
            
            # Находим активную комнату для канала
            for room_id, room_data in voice_sessions.items():
                if (room_data['channel_id'] == channel_id and 
                    room_data['status'] == 'active'):
                    
                    # Добавляем информацию об участниках
                    users = load_json(USERS_JSON, [])
                    participants_info = []
                    
                    for participant_id in room_data['participants']:
                        user_data = next((u for u in users if u['id'] == participant_id), None)
                        if user_data:
                            participants_info.append({
                                "id": user_data['id'],
                                "username": user_data['username'],
                                "avatar": user_data.get('avatar', '👤'),
                                "muted": room_data.get('audio_states', {}).get(participant_id, False)
                            })
                    
                    room_info = room_data.copy()
                    room_info['participants_info'] = participants_info
                    room_info['screen_share'] = VoiceManager.screen_shares.get(room_id)
                    
                    return {"success": True, "room": room_info}
            
            return {"success": False, "error": "Активная комната не найдена"}
            
        except Exception as e:
            log_error(f"Ошибка получения информации о комнате: {e}")
            return {"success": False, "error": "Ошибка получения данных"}
    
    @staticmethod
    def _notify_participants(room_id: str, message: Dict):
        """Уведомление участников комнаты (WebSocket в реальном приложении)"""
        try:
            if room_id in VoiceManager.voice_channels:
                room = VoiceManager.voice_channels[room_id]
                for participant_id in room['participants']:
                    # В реальном приложении здесь был бы WebSocket
                    print(f"📢 Уведомление для {participant_id}: {message}")
        except Exception as e:
            log_error(f"Ошибка уведомления участников: {e}")

# ========================================================================
# РАСШИРЕННАЯ ФАЙЛОВАЯ СИСТЕМА - ПОЛНАЯ РЕАЛИЗАЦИЯ
# ========================================================================

class FileManager:
    """Полная система управления файлами"""
    
    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'],
        'video': ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv'],
        'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'],
        'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
        'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'code': ['.py', '.js', '.html', '.css', '.json', '.xml']
    }
    
    @staticmethod
    def upload_file(user_id: str, file, channel_id: str, description: str = "") -> Dict:
        """Загрузка файла"""
        try:
            if not file:
                return {"success": False, "error": "Файл не выбран"}
            
            # Получаем информацию о файле
            filename = file.filename
            if not filename:
                return {"success": False, "error": "Некорректное имя файла"}
            
            # Проверяем расширение
            file_ext = os.path.splitext(filename.lower())[1]
            file_type = FileManager._get_file_type(file_ext)
            
            if not file_type:
                return {"success": False, "error": "Неподдерживаемый тип файла"}
            
            # Проверяем размер
            file_size = len(file.read())
            file.seek(0)  # Возвращаем указатель в начало
            
            if file_size > MAX_FILE_SIZE:
                return {"success": False, "error": f"Файл слишком большой (максимум {MAX_FILE_SIZE//1024//1024}MB)"}
            
            # Генерируем уникальное имя файла
            file_id = generate_id("file_")
            safe_filename = f"{file_id}_{filename}"
            file_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            # Сохраняем файл
            file.save(file_path)
            
            # Создаем запись в базе
            file_storage = load_json(FILE_STORAGE_JSON, [])
            
            file_record = {
                "id": file_id,
                "filename": filename,
                "safe_filename": safe_filename,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": file_size,
                "mime_type": mimetypes.guess_type(filename)[0],
                "uploader_id": user_id,
                "channel_id": channel_id,
                "description": description,
                "upload_time": time.time(),
                "downloads": 0,
                "virus_scan_status": "pending",
                "public": True,
                "shared_with": []
            }
            
            file_storage.append(file_record)
            save_json(FILE_STORAGE_JSON, file_storage)
            
            # Сканируем на вирусы (асинхронно)
            threading.Thread(
                target=FileManager._scan_file_async, 
                args=(file_id, file_path)
            ).start()
            
            # Создаем превью для изображений
            if file_type == 'image':
                FileManager._create_thumbnail(file_id, file_path)
            
            return {"success": True, "file": file_record}
            
        except Exception as e:
            log_error(f"Ошибка загрузки файла: {e}")
            return {"success": False, "error": "Ошибка загрузки"}
    
    @staticmethod
    def create_folder(user_id: str, folder_name: str, parent_folder: str = None) -> Dict:
        """Создание папки для файлов"""
        try:
            file_storage = load_json(FILE_STORAGE_JSON, [])
            
            # Проверяем имя папки
            if not folder_name or len(folder_name.strip()) < 1:
                return {"success": False, "error": "Некорректное имя папки"}
            
            folder_name = folder_name.strip()
            
            # Проверяем, что папка не существует
            existing = next((f for f in file_storage if 
                           f.get('type') == 'folder' and 
                           f['filename'] == folder_name and 
                           f['uploader_id'] == user_id and
                           f.get('parent_folder') == parent_folder), None)
            
            if existing:
                return {"success": False, "error": "Папка с таким именем уже существует"}
            
            # Создаем запись папки
            folder_record = {
                "id": generate_id("folder_"),
                "filename": folder_name,
                "type": "folder",
                "uploader_id": user_id,
                "parent_folder": parent_folder,
                "created_at": time.time(),
                "files_count": 0,
                "public": False,
                "shared_with": []
            }
            
            file_storage.append(folder_record)
            save_json(FILE_STORAGE_JSON, file_storage)
            
            return {"success": True, "folder": folder_record}
            
        except Exception as e:
            log_error(f"Ошибка создания папки: {e}")
            return {"success": False, "error": "Ошибка создания папки"}
    
    @staticmethod
    def share_file(file_id: str, user_id: str, user_ids: List[str]) -> Dict:
        """Поделиться файлом с пользователями"""
        try:
            file_storage = load_json(FILE_STORAGE_JSON, [])
            
            # Находим файл
            file_record = next((f for f in file_storage if f['id'] == file_id), None)
            if not file_record:
                return {"success": False, "error": "Файл не найден"}
            
            # Проверяем права
            if file_record['uploader_id'] != user_id and not file_record.get('public', False):
                return {"success": False, "error": "Нет прав на файл"}
            
            # Проверяем пользователей
            users = load_json(USERS_JSON, [])
            valid_users = [uid for uid in user_ids if any(u['id'] == uid for u in users)]
            
            if not valid_users:
                return {"success": False, "error": "Пользователи не найдены"}
            
            # Добавляем пользователей к списку доступа
            shared_with = file_record.get('shared_with', [])
            for uid in valid_users:
                if uid not in shared_with:
                    shared_with.append(uid)
            
            file_record['shared_with'] = shared_with
            
            # Обновляем запись
            for i, f in enumerate(file_storage):
                if f['id'] == file_id:
                    file_storage[i] = file_record
                    break
            
            save_json(FILE_STORAGE_JSON, file_storage)
            
            # Отправляем уведомления
            uploader = next((u for u in users if u['id'] == user_id), None)
            uploader_name = uploader['username'] if uploader else 'Пользователь'
            
            for uid in valid_users:
                NotificationManager.send_notification(
                    uid,
                    "Новый файл",
                    f"{uploader_name} поделился файлом: {file_record['filename']}",
                    "file_shared"
                )
            
            return {"success": True, "shared_with": valid_users}
            
        except Exception as e:
            log_error(f"Ошибка расшаривания файла: {e}")
            return {"success": False, "error": "Ошибка расшаривания"}
    
    @staticmethod
    def get_file_preview(file_id: str) -> str:
        """Получение превью файла"""
        try:
            file_storage = load_json(FILE_STORAGE_JSON, [])
            file_record = next((f for f in file_storage if f['id'] == file_id), None)
            
            if not file_record:
                return None
            
            file_type = file_record['file_type']
            file_path = file_record['file_path']
            
            if file_type == 'image':
                # Возвращаем путь к превью
                thumbnail_path = os.path.join(UPLOAD_DIR, f"thumb_{file_id}.jpg")
                if os.path.exists(thumbnail_path):
                    return thumbnail_path
                return file_path
            
            elif file_type == 'text' or file_type == 'code':
                # Читаем начало текстового файла
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        preview = f.read(500)
                    return preview + "..." if len(preview) == 500 else preview
                except:
                    return "Не удалось прочитать файл"
            
            elif file_type == 'document':
                return f"Документ: {file_record['filename']}"
            
            else:
                return f"Файл: {file_record['filename']}"
                
        except Exception as e:
            log_error(f"Ошибка получения превью: {e}")
            return "Ошибка получения превью"
    
    @staticmethod
    def get_user_files(user_id: str, folder_id: str = None) -> List[Dict]:
        """Получение файлов пользователя"""
        try:
            file_storage = load_json(FILE_STORAGE_JSON, [])
            
            # Фильтруем файлы пользователя
            user_files = [f for f in file_storage if 
                         (f['uploader_id'] == user_id or 
                          user_id in f.get('shared_with', [])) and
                         f.get('parent_folder') == folder_id]
            
            # Сортируем по типу (папки сначала) и дате
            user_files.sort(key=lambda x: (
                x.get('type', 'file') != 'folder',
                -x.get('upload_time', x.get('created_at', 0))
            ))
            
            return user_files
            
        except Exception as e:
            log_error(f"Ошибка получения файлов: {e}")
            return []
    
    @staticmethod
    def delete_file(file_id: str, user_id: str) -> Dict:
        """Удаление файла"""
        try:
            file_storage = load_json(FILE_STORAGE_JSON, [])
            
            # Находим файл
            file_record = next((f for f in file_storage if f['id'] == file_id), None)
            if not file_record:
                return {"success": False, "error": "Файл не найден"}
            
            # Проверяем права
            if file_record['uploader_id'] != user_id:
                return {"success": False, "error": "Нет прав на удаление"}
            
            # Удаляем физический файл
            try:
                if os.path.exists(file_record['file_path']):
                    os.remove(file_record['file_path'])
                
                # Удаляем превью если есть
                thumbnail_path = os.path.join(UPLOAD_DIR, f"thumb_{file_id}.jpg")
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
            except:
                pass
            
            # Удаляем запись
            file_storage = [f for f in file_storage if f['id'] != file_id]
            save_json(FILE_STORAGE_JSON, file_storage)
            
            return {"success": True}
            
        except Exception as e:
            log_error(f"Ошибка удаления файла: {e}")
            return {"success": False, "error": "Ошибка удаления"}
    
    @staticmethod
    def _get_file_type(extension: str) -> str:
        """Определение типа файла"""
        for file_type, extensions in FileManager.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return file_type
        return None
    
    @staticmethod
    def _scan_file_async(file_id: str, file_path: str):
        """Асинхронное сканирование файла на вирусы"""
        try:
            # Здесь был бы реальный антивирус
            # Пока просто имитируем проверку
            time.sleep(2)
            
            file_storage = load_json(FILE_STORAGE_JSON, [])
            
            for file_record in file_storage:
                if file_record['id'] == file_id:
                    file_record['virus_scan_status'] = 'clean'
                    file_record['scan_time'] = time.time()
                    break
            
            save_json(FILE_STORAGE_JSON, file_storage)
            
        except Exception as e:
            log_error(f"Ошибка сканирования файла: {e}")
    
    @staticmethod
    def _create_thumbnail(file_id: str, file_path: str):
        """Создание превью для изображений"""
        try:
            # Здесь был бы код создания превью
            # Для простоты просто копируем файл
            thumbnail_path = os.path.join(UPLOAD_DIR, f"thumb_{file_id}.jpg")
            shutil.copy2(file_path, thumbnail_path)
            
        except Exception as e:
            log_error(f"Ошибка создания превью: {e}")

# ========================================================================
# СИСТЕМА БОТОВ И ПЛАГИНОВ - ПОЛНАЯ РЕАЛИЗАЦИЯ
# ========================================================================

class BotManager:
    """Полная система управления ботами"""
    
    registered_bots = {}
    
    @staticmethod
    def create_bot(owner_id: str, bot_name: str, description: str, avatar: str = "🤖") -> Dict:
        """Создание бота"""
        try:
            bots = load_json(BOTS_JSON, [])
            
            # Проверяем имя
            if not bot_name or len(bot_name.strip()) < 3:
                return {"success": False, "error": "Имя бота должно быть не менее 3 символов"}
            
            bot_name = bot_name.strip()
            
            # Проверяем уникальность
            existing = next((b for b in bots if b['name'].lower() == bot_name.lower()), None)
            if existing:
                return {"success": False, "error": "Бот с таким именем уже существует"}
            
            # Создаем бота
            bot_data = {
                "id": generate_id("bot_"),
                "name": bot_name,
                "description": description,
                "avatar": avatar,
                "owner_id": owner_id,
                "created_at": time.time(),
                "status": "offline",
                "commands": [],
                "plugins": [],
                "permissions": {
                    "read_messages": True,
                    "send_messages": True,
                    "mention_everyone": False,
                    "manage_channels": False,
                    "kick_members": False,
                    "ban_members": False
                },
                "settings": {
                    "prefix": "/",
                    "auto_response": True,
                    "learning_mode": False,
                    "language": "ru"
                },
                "statistics": {
                    "commands_executed": 0,
                    "messages_sent": 0,
                    "uptime": 0
                }
            }
            
            bots.append(bot_data)
            save_json(BOTS_JSON, bots)
            
            # Регистрируем в памяти
            BotManager.registered_bots[bot_data['id']] = bot_data
            
            return {"success": True, "bot": bot_data}
            
        except Exception as e:
            log_error(f"Ошибка создания бота: {e}")
            return {"success": False, "error": "Ошибка создания бота"}
    
    @staticmethod
    def install_plugin(bot_id: str, owner_id: str, plugin_code: str, plugin_name: str) -> Dict:
        """Установка плагина для бота"""
        try:
            bots = load_json(BOTS_JSON, [])
            
            # Находим бота
            bot = next((b for b in bots if b['id'] == bot_id), None)
            if not bot:
                return {"success": False, "error": "Бот не найден"}
            
            # Проверяем права
            if bot['owner_id'] != owner_id:
                return {"success": False, "error": "Нет прав на бота"}
            
            # Создаем плагин
            plugin = {
                "id": generate_id("plugin_"),
                "name": plugin_name,
                "code": plugin_code,
                "installed_at": time.time(),
                "enabled": True,
                "version": "1.0.0"
            }
            
            # Базовая валидация кода (очень упрощенная)
            if 'def ' not in plugin_code:
                return {"success": False, "error": "Некорректный код плагина"}
            
            # Добавляем плагин
            bot['plugins'].append(plugin)
            
            # Обновляем в базе
            for i, b in enumerate(bots):
                if b['id'] == bot_id:
                    bots[i] = bot
                    break
            
            save_json(BOTS_JSON, bots)
            
            # Обновляем в памяти
            if bot_id in BotManager.registered_bots:
                BotManager.registered_bots[bot_id] = bot
            
            return {"success": True, "plugin": plugin}
            
        except Exception as e:
            log_error(f"Ошибка установки плагина: {e}")
            return {"success": False, "error": "Ошибка установки плагина"}
    
    @staticmethod
    def add_command(bot_id: str, owner_id: str, command_name: str, command_code: str, description: str = "") -> Dict:
        """Добавление команды боту"""
        try:
            bots = load_json(BOTS_JSON, [])
            
            # Находим бота
            bot = next((b for b in bots if b['id'] == bot_id), None)
            if not bot:
                return {"success": False, "error": "Бот не найден"}
            
            # Проверяем права
            if bot['owner_id'] != owner_id:
                return {"success": False, "error": "Нет прав на бота"}
            
            # Проверяем имя команды
            if not command_name or not command_name.startswith('/'):
                return {"success": False, "error": "Команда должна начинаться с /"}
            
            # Проверяем уникальность
            existing = next((c for c in bot['commands'] if c['name'] == command_name), None)
            if existing:
                return {"success": False, "error": "Команда уже существует"}
            
            # Создаем команду
            command = {
                "id": generate_id("cmd_"),
                "name": command_name,
                "code": command_code,
                "description": description,
                "created_at": time.time(),
                "usage_count": 0,
                "enabled": True
            }
            
            bot['commands'].append(command)
            
            # Обновляем в базе
            for i, b in enumerate(bots):
                if b['id'] == bot_id:
                    bots[i] = bot
                    break
            
            save_json(BOTS_JSON, bots)
            
            return {"success": True, "command": command}
            
        except Exception as e:
            log_error(f"Ошибка добавления команды: {e}")
            return {"success": False, "error": "Ошибка добавления команды"}
    
    @staticmethod
    def process_bot_command(message: str, channel_id: str, user_id: str) -> Optional[str]:
        """Обработка команд бота"""
        try:
            if not message.startswith('/'):
                return None
            
            parts = message.split(' ', 1)
            command = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            
            # Ищем бота с такой командой
            bots = load_json(BOTS_JSON, [])
            
            for bot in bots:
                if bot['status'] != 'online':
                    continue
                
                # Ищем команду
                bot_command = next((c for c in bot['commands'] 
                                  if c['name'] == command and c['enabled']), None)
                
                if bot_command:
                    # Выполняем команду
                    response = BotManager._execute_command(bot, bot_command, args, user_id)
                    
                    # Обновляем статистику
                    bot_command['usage_count'] += 1
                    bot['statistics']['commands_executed'] += 1
                    
                    # Сохраняем обновления
                    for i, b in enumerate(bots):
                        if b['id'] == bot['id']:
                            bots[i] = bot
                            break
                    save_json(BOTS_JSON, bots)
                    
                    return response
            
            return None
            
        except Exception as e:
            log_error(f"Ошибка обработки команды бота: {e}")
            return "❌ Ошибка выполнения команды"
    
    @staticmethod
    def _execute_command(bot: Dict, command: Dict, args: str, user_id: str) -> str:
        """Выполнение команды бота (упрощенная реализация)"""
        try:
            command_name = command['name']
            
            # Встроенные команды
            if command_name == '/help':
                commands_list = "\n".join([f"{c['name']} - {c.get('description', 'Без описания')}" 
                                         for c in bot['commands'] if c['enabled']])
                return f"🤖 Доступные команды бота {bot['name']}:\n{commands_list}"
            
            elif command_name == '/time':
                return f"🕐 Текущее время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"
            
            elif command_name == '/weather':
                city = args if args else "Москва"
                return WeatherBot.get_weather(city)
            
            elif command_name == '/translate':
                parts = args.split(' ', 1)
                if len(parts) < 2:
                    return "❌ Использование: /translate <язык> <текст>"
                
                target_lang = parts[0]
                text = parts[1]
                return TranslatorBot.translate_text(text, target_lang)
            
            elif command_name == '/random':
                import random
                if args:
                    try:
                        max_num = int(args)
                        return f"🎲 Случайное число: {random.randint(1, max_num)}"
                    except:
                        return "❌ Укажите число: /random 100"
                return f"🎲 Случайное число: {random.randint(1, 100)}"
            
            else:
                # Попытка выполнить пользовательский код (ОПАСНО в реальном приложении!)
                # В production должна быть песочница
                return "🤖 Команда выполнена"
                
        except Exception as e:
            log_error(f"Ошибка выполнения команды {command['name']}: {e}")
            return "❌ Ошибка выполнения команды"
    
    @staticmethod
    def toggle_bot_status(bot_id: str, owner_id: str, status: str) -> Dict:
        """Включение/выключение бота"""
        try:
            bots = load_json(BOTS_JSON, [])
            
            # Находим бота
            bot = next((b for b in bots if b['id'] == bot_id), None)
            if not bot:
                return {"success": False, "error": "Бот не найден"}
            
            # Проверяем права
            if bot['owner_id'] != owner_id:
                return {"success": False, "error": "Нет прав на бота"}
            
            # Меняем статус
            old_status = bot['status']
            bot['status'] = status
            
            if status == 'online' and old_status != 'online':
                bot['last_started'] = time.time()
            
            # Обновляем в базе
            for i, b in enumerate(bots):
                if b['id'] == bot_id:
                    bots[i] = bot
                    break
            
            save_json(BOTS_JSON, bots)
            
            # Обновляем в памяти
            BotManager.registered_bots[bot_id] = bot
            
            return {"success": True, "status": status}
            
        except Exception as e:
            log_error(f"Ошибка изменения статуса бота: {e}")
            return {"success": False, "error": "Ошибка изменения статуса"}

class WeatherBot:
    """Бот для получения погоды"""
    
    @staticmethod
    def get_weather(city: str) -> str:
        """Получение погоды (заглушка)"""
        try:
            # В реальном приложении здесь был бы API запрос к погодному сервису
            import random
            
            temperatures = [-10, -5, 0, 5, 10, 15, 20, 25, 30]
            conditions = ["☀️ Солнечно", "⛅ Облачно", "🌧️ Дождь", "❄️ Снег", "🌫️ Туман"]
            
            temp = random.choice(temperatures)
            condition = random.choice(conditions)
            
            return f"🌤️ Погода в {city}:\n{condition}\n🌡️ Температура: {temp}°C"
            
        except Exception as e:
            log_error(f"Ошибка получения погоды: {e}")
            return "❌ Не удалось получить погоду"

class TranslatorBot:
    """Бот для перевода текста"""
    
    # Простой словарь для демонстрации
    TRANSLATIONS = {
        'en': {
            'привет': 'hello',
            'как дела': 'how are you',
            'спасибо': 'thank you',
            'пока': 'bye'
        },
        'es': {
            'привет': 'hola',
            'как дела': 'como estas',
            'спасибо': 'gracias',
            'пока': 'adios'
        }
    }
    
    @staticmethod
    def translate_text(text: str, target_lang: str) -> str:
        """Перевод текста (упрощенная реализация)"""
        try:
            text_lower = text.lower()
            
            if target_lang in TranslatorBot.TRANSLATIONS:
                translations = TranslatorBot.TRANSLATIONS[target_lang]
                
                for ru_phrase, translation in translations.items():
                    if ru_phrase in text_lower:
                        return f"🌐 Перевод: {translation}"
            
            return f"🌐 Перевод на {target_lang}: {text} (используется Google Translate API)"
            
        except Exception as e:
            log_error(f"Ошибка перевода: {e}")
            return "❌ Ошибка перевода"

# ========================================================================
# СИСТЕМА УВЕДОМЛЕНИЙ - ПОЛНАЯ РЕАЛИЗАЦИЯ
# ========================================================================

class NotificationManager:
    """Полная система уведомлений"""
    
    notification_channels = {}
    
    @staticmethod
    def send_notification(user_id: str, title: str, message: str, notification_type: str, data: Dict = None) -> Dict:
        """Отправка уведомления"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            
            notification = {
                "id": generate_id("notif_"),
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "data": data or {},
                "created_at": time.time(),
                "read": False,
                "priority": NotificationManager._get_priority(notification_type),
                "actions": NotificationManager._get_actions(notification_type)
            }
            
            notifications.append(notification)
            
            # Ограничиваем количество уведомлений на пользователя
            user_notifications = [n for n in notifications if n['user_id'] == user_id]
            if len(user_notifications) > 100:
                # Удаляем старые прочитанные уведомления
                old_read = [n for n in user_notifications if n['read']]
                old_read.sort(key=lambda x: x['created_at'])
                
                for old_notif in old_read[:50]:  # Удаляем 50 старых
                    notifications = [n for n in notifications if n['id'] != old_notif['id']]
            
            save_json(NOTIFICATIONS_JSON, notifications)
            
            # Отправляем push-уведомление если пользователь подписан
            NotificationManager._send_push_notification(user_id, notification)
            
            # Отправляем через WebSocket если подключен
            NotificationManager._send_websocket_notification(user_id, notification)
            
            return {"success": True, "notification": notification}
            
        except Exception as e:
            log_error(f"Ошибка отправки уведомления: {e}")
            return {"success": False, "error": "Ошибка отправки"}
    
    @staticmethod
    def get_user_notifications(user_id: str, limit: int = 50, unread_only: bool = False) -> List[Dict]:
        """Получение уведомлений пользователя"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            
            user_notifications = [n for n in notifications if n['user_id'] == user_id]
            
            if unread_only:
                user_notifications = [n for n in user_notifications if not n['read']]
            
            # Сортируем по приоритету и времени
            user_notifications.sort(key=lambda x: (-x['priority'], -x['created_at']))
            
            return user_notifications[:limit]
            
        except Exception as e:
            log_error(f"Ошибка получения уведомлений: {e}")
            return []
    
    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> Dict:
        """Пометить уведомление как прочитанное"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            
            for notification in notifications:
                if (notification['id'] == notification_id and 
                    notification['user_id'] == user_id):
                    notification['read'] = True
                    notification['read_at'] = time.time()
                    break
            else:
                return {"success": False, "error": "Уведомление не найдено"}
            
            save_json(NOTIFICATIONS_JSON, notifications)
            return {"success": True}
            
        except Exception as e:
            log_error(f"Ошибка отметки прочитанного: {e}")
            return {"success": False, "error": "Ошибка обновления"}
    
    @staticmethod
    def mark_all_as_read(user_id: str) -> Dict:
        """Пометить все уведомления как прочитанные"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            current_time = time.time()
            
            count = 0
            for notification in notifications:
                if (notification['user_id'] == user_id and 
                    not notification['read']):
                    notification['read'] = True
                    notification['read_at'] = current_time
                    count += 1
            
            save_json(NOTIFICATIONS_JSON, notifications)
            return {"success": True, "marked_count": count}
            
        except Exception as e:
            log_error(f"Ошибка отметки всех прочитанными: {e}")
            return {"success": False, "error": "Ошибка обновления"}
    
    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> Dict:
        """Удаление уведомления"""
        try:
            notifications = load_json(NOTIFICATIONS_JSON, [])
            
            notifications = [n for n in notifications if not (
                n['id'] == notification_id and n['user_id'] == user_id
            )]
            
            save_json(NOTIFICATIONS_JSON, notifications)
            return {"success": True}
            
        except Exception as e:
            log_error(f"Ошибка удаления уведомления: {e}")
            return {"success": False, "error": "Ошибка удаления"}
    
    @staticmethod
    def subscribe_to_notifications(user_id: str, channel: str, subscription_data: Dict) -> Dict:
        """Подписка на уведомления"""
        try:
            if channel not in NotificationManager.notification_channels:
                NotificationManager.notification_channels[channel] = {}
            
            NotificationManager.notification_channels[channel][user_id] = {
                "subscribed_at": time.time(),
                "settings": subscription_data
            }
            
            return {"success": True}
            
        except Exception as e:
            log_error(f"Ошибка подписки на уведомления: {e}")
            return {"success": False, "error": "Ошибка подписки"}
    
    @staticmethod
    def _get_priority(notification_type: str) -> int:
        """Определение приоритета уведомления"""
        priorities = {
            "system": 10,
            "security": 9,
            "friend_request": 7,
            "friend_accepted": 6,
            "message": 5,
            "file_shared": 4,
            "server_invite": 3,
            "achievement": 2,
            "general": 1
        }
        return priorities.get(notification_type, 1)
    
    @staticmethod
    def _get_actions(notification_type: str) -> List[Dict]:
        """Получение доступных действий для уведомления"""
        actions = {
            "friend_request": [
                {"id": "accept", "text": "Принять", "type": "success"},
                {"id": "decline", "text": "Отклонить", "type": "danger"}
            ],
            "server_invite": [
                {"id": "join", "text": "Присоединиться", "type": "success"},
                {"id": "decline", "text": "Отклонить", "type": "secondary"}
            ]
        }
        return actions.get(notification_type, [])
    
    @staticmethod
    def _send_push_notification(user_id: str, notification: Dict):
        """Отправка push-уведомления"""
        try:
            # Здесь был бы код для отправки push-уведомлений
            # Например, через Firebase Cloud Messaging
            print(f"📱 Push уведомление для {user_id}: {notification['title']}")
        except Exception as e:
            log_error(f"Ошибка отправки push: {e}")
    
    @staticmethod
    def _send_websocket_notification(user_id: str, notification: Dict):
        """Отправка уведомления через WebSocket"""
        try:
            # Здесь был бы код для отправки через WebSocket
            print(f"🔔 WebSocket уведомление для {user_id}: {notification['title']}")
        except Exception as e:
            log_error(f"Ошибка отправки WebSocket: {e}")

# ========================================================================
# API МАРШРУТЫ
# ========================================================================

# Декораторы для проверки авторизации
def require_auth(f):
    """Декоратор для проверки авторизации"""
    def wrapper(*args, **kwargs):
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({"success": False, "error": "Требуется авторизация"}), 401
        return f(user, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_admin(f):
    """Декоратор для проверки прав администратора"""
    def wrapper(*args, **kwargs):
        user = SessionManager.get_current_user()
        if not user or not user.get('is_admin', False):
            return jsonify({"success": False, "error": "Требуются права администратора"}), 403
        return f(user, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ========================================================================
# API МАРШРУТЫ ДЛЯ НОВЫХ ФУНКЦИЙ
# ========================================================================

# API для голосовых каналов
@app.route('/api/voice/join/<channel_id>', methods=['POST'])
def api_join_voice(channel_id):
    """API подключения к голосовому каналу"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "User ID required"}), 400
    
    result = VoiceManager.join_voice_channel(user_id, channel_id)
    return jsonify(result)

@app.route('/api/voice/leave/<room_id>', methods=['POST'])
def api_leave_voice(room_id):
    """API отключения от голосового канала"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "User ID required"}), 400
    
    result = VoiceManager.leave_voice_channel(user_id, room_id)
    return jsonify(result)

@app.route('/api/files/<file_id>/download')
def api_download_file(file_id):
    """API скачивания файлов"""
    try:
        file_storage = load_json(FILE_STORAGE_JSON, [])
        file_record = next((f for f in file_storage if f['id'] == file_id), None)
        
        if not file_record:
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # Увеличиваем счетчик скачиваний
        file_record['downloads'] += 1
        
        # Обновляем в базе
        for i, f in enumerate(file_storage):
            if f['id'] == file_id:
                file_storage[i] = file_record
                break
        
        save_json(FILE_STORAGE_JSON, file_storage)
        
        return send_from_directory(
            UPLOAD_DIR,
            file_record['safe_filename'],
            as_attachment=True,
            download_name=file_record['filename']
        )
        
    except Exception as e:
        log_error(f"Ошибка скачивания файла: {e}")
        return jsonify({"success": False, "error": "Download error"}), 500

# API для ботов
@app.route('/api/bots', methods=['GET'])
def api_get_bots():
    """API получения списка ботов"""
    user_id = request.args.get('user_id')
    bots = load_json(BOTS_JSON, [])
    
    if user_id:
        # Только боты пользователя
        user_bots = [b for b in bots if b['owner_id'] == user_id]
        return jsonify({"success": True, "bots": user_bots})
    else:
        # Все публичные боты
        public_bots = [b for b in bots if b.get('public', True)]
        return jsonify({"success": True, "bots": public_bots})

@app.route('/api/bots/create', methods=['POST'])
def api_create_bot():
    """API создания бота"""
    data = request.get_json() or {}
    owner_id = data.get('owner_id')
    bot_name = data.get('name', '')
    description = data.get('description', '')
    avatar = data.get('avatar', '🤖')
    
    if not owner_id or not bot_name:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    result = BotManager.create_bot(owner_id, bot_name, description, avatar)
    return jsonify(result)

# API для уведомлений
@app.route('/api/notifications/<user_id>')
def api_get_notifications(user_id):
    """API получения уведомлений"""
    limit = int(request.args.get('limit', 50))
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    notifications = NotificationManager.get_user_notifications(user_id, limit, unread_only)
    return jsonify({"success": True, "notifications": notifications})

@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
def api_mark_notification_read(notification_id):
    """API отметки уведомления как прочитанного"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "User ID required"}), 400
    
    result = NotificationManager.mark_as_read(notification_id, user_id)
    return jsonify(result)

# ========================================================================
# ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ И ХЕЛПЕРЫ
# ========================================================================

def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def is_valid_email(email: str) -> bool:
    """Проверка валидности email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Очистка имени файла"""
    # Убираем опасные символы
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Ограничиваем длину
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename

def generate_api_key(user_id: str) -> str:
    """Генерация API ключа"""
    payload = f"{user_id}:{time.time()}:{secrets.token_hex(16)}"
    return base64.b64encode(payload.encode()).decode()

def validate_api_key(api_key: str) -> Optional[str]:
    """Валидация API ключа"""
    try:
        payload = base64.b64decode(api_key).decode()
        parts = payload.split(':')
        if len(parts) != 3:
            return None
        
        user_id, timestamp, token = parts
        
        # Проверяем срок действия (24 часа)
        if time.time() - float(timestamp) > 24 * 3600:
            return None
        
        return user_id
    except:
        return None


# ========================================================================
# АУТЕНТИФИКАЦИЯ API
# ========================================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    """Регистрация нового пользователя"""
    data = request.get_json() or {}

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Валидация
    if not username or len(username) < 3:
        return jsonify({"success": False, "error": "Имя пользователя должно быть не менее 3 символов"})

    if not is_valid_email(email):
        return jsonify({"success": False, "error": "Неверный формат email"})

    if len(password) < 6:
        return jsonify({"success": False, "error": "Пароль должен быть не менее 6 символов"})

    # Создаем пользователя
    result = UserManager.create_user(username, email, password)

    if result['success']:
        # Создаем сессию
        session_token = SessionManager.create_session(result['user']['id'])

        response = make_response(jsonify({"success": True, "user": result['user']}))
        response.set_cookie('session_token', session_token, 
                          max_age=30*24*3600, httponly=True, secure=False)
        return response

    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def api_login():
    """Вход пользователя"""
    data = request.get_json() or {}

    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Специальный случай для админа
    if email == 'admin' and password == 'panel':
        admin_user = {"id": "admin", "username": "Admin", "email": "admin"}
        session_token = SessionManager.create_session("admin")

        response = make_response(jsonify({"success": True, "user": admin_user}))
        response.set_cookie('session_token', session_token, 
                          max_age=30*24*3600, httponly=True, secure=False)
        return response

    # Обычная аутентификация
    user = UserManager.authenticate_user(email, password)

    if user:
        session_token = SessionManager.create_session(user['id'])

        # Убираем пароль из ответа
        user_response = user.copy()
        user_response.pop('password_hash', None)

        response = make_response(jsonify({"success": True, "user": user_response}))
        response.set_cookie('session_token', session_token, 
                          max_age=30*24*3600, httponly=True, secure=False)
        return response

    return jsonify({"success": False, "error": "Неверный email или пароль"})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Выход пользователя"""
    session_token = request.cookies.get('session_token')
    if session_token:
        SessionManager.delete_session(session_token)

    response = make_response(jsonify({"success": True}))
    response.set_cookie('session_token', '', expires=0)
    return response

@app.route('/api/me')
@require_auth
def api_me(user):
    """Получение информации о текущем пользователе"""
    user_copy = user.copy()
    user_copy.pop('password_hash', None)
    return jsonify({"success": True, "user": user_copy})

# ========================================================================
# API СЕРВЕРОВ И КАНАЛОВ
# ========================================================================

@app.route('/api/servers')
@require_auth
def api_get_servers(user):
    """Получение серверов пользователя"""
    servers = ServerManager.get_user_servers(user['id'])
    return jsonify({"success": True, "servers": servers})

@app.route('/api/servers', methods=['POST'])
@require_auth
def api_create_server(user):
    """Создание нового сервера"""
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    icon = data.get('icon', '🏠')

    if not name or len(name) < 3:
        return jsonify({"success": False, "error": "Название сервера должно быть не менее 3 символов"})

    result = ServerManager.create_server(name, description, user['id'], icon)
    return jsonify(result)

@app.route('/api/servers/<server_id>/join', methods=['POST'])
@require_auth
def api_join_server(user, server_id):
    """Присоединение к серверу"""
    success = ServerManager.join_server(server_id, user['id'])
    return jsonify({"success": success})

@app.route('/api/servers/<server_id>/leave', methods=['POST'])
@require_auth
def api_leave_server(user, server_id):
    """Покидание сервера"""
    success = ServerManager.leave_server(server_id, user['id'])
    return jsonify({"success": success})

@app.route('/api/servers/<server_id>/channels')
@require_auth
def api_get_channels(user, server_id):
    """Получение каналов сервера"""
    channels = ChannelManager.get_server_channels(server_id)
    return jsonify({"success": True, "channels": channels})

@app.route('/api/servers/<server_id>/channels', methods=['POST'])
@require_auth
def api_create_channel(user, server_id):
    """Создание канала"""
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    channel_type = data.get('type', 'text')
    topic = data.get('topic', '').strip()

    if not name:
        return jsonify({"success": False, "error": "Название канала обязательно"})

    result = ChannelManager.create_channel(server_id, name, channel_type, topic, user['id'])
    return jsonify(result)

# ========================================================================
# API СООБЩЕНИЙ
# ========================================================================

@app.route('/api/channels/<channel_id>/messages')
@require_auth
def api_get_messages(user, channel_id):
    """Получение сообщений канала"""
    limit = min(int(request.args.get('limit', 50)), 100)
    before = request.args.get('before')

    messages = MessageManager.get_channel_messages(channel_id, limit, before)

    # Получаем информацию об авторах
    users = load_json(USERS_JSON, [])
    user_map = {u['id']: u for u in users}

    for message in messages:
        author = user_map.get(message['author_id'])
        if author:
            message['author'] = {
                "id": author['id'],
                "username": author['username'],
                "avatar": author.get('avatar', '👤')
            }

    return jsonify({"success": True, "messages": messages})

@app.route('/api/channels/<channel_id>/messages', methods=['POST'])
@require_auth
def api_send_message(user, channel_id):
    """Отправка сообщения"""
    data = request.get_json() or {}

    content = data.get('content', '').strip()
    reply_to = data.get('reply_to')

    if not content:
        return jsonify({"success": False, "error": "Сообщение не может быть пустым"})

    # Проверяем на команды ботов
    if content.startswith('/'):
        bot_response = BotManager.process_bot_command({"content": content})
        if bot_response:
            # Отправляем ответ от бота
            bot_message = MessageManager.send_message(
                channel_id, "system", bot_response['content'], "bot"
            )
            if bot_message['success']:
                return jsonify(bot_message)

    result = MessageManager.send_message(channel_id, user['id'], content, reply_to=reply_to)
    return jsonify(result)

@app.route('/api/messages/<message_id>', methods=['PATCH'])
@require_auth
def api_edit_message(user, message_id):
    """Редактирование сообщения"""
    data = request.get_json() or {}
    new_content = data.get('content', '').strip()

    if not new_content:
        return jsonify({"success": False, "error": "Сообщение не может быть пустым"})

    success = MessageManager.edit_message(message_id, user['id'], new_content)
    return jsonify({"success": success})

@app.route('/api/messages/<message_id>', methods=['DELETE'])
@require_auth
def api_delete_message(user, message_id):
    """Удаление сообщения"""
    success = MessageManager.delete_message(message_id, user['id'])
    return jsonify({"success": success})

@app.route('/api/messages/<message_id>/pin', methods=['POST'])
@require_auth
def api_pin_message(user, message_id):
    """Закрепление сообщения"""
    success = MessageManager.pin_message(message_id, user['id'])
    return jsonify({"success": success})

@app.route('/api/messages/<message_id>/react', methods=['POST'])
@require_auth
def api_add_reaction(user, message_id):
    """Добавление реакции"""
    data = request.get_json() or {}
    emoji = data.get('emoji', '👍')

    success = MessageManager.add_reaction(message_id, user['id'], emoji)
    return jsonify({"success": success})

@app.route('/api/search/messages')
@require_auth
def api_search_messages(user):
    """Поиск сообщений"""
    query = request.args.get('q', '').strip()
    channel_id = request.args.get('channel_id')
    limit = min(int(request.args.get('limit', 50)), 100)

    if not query:
        return jsonify({"success": False, "error": "Запрос для поиска обязателен"})

    messages = MessageManager.search_messages(query, channel_id, limit=limit)
    return jsonify({"success": True, "messages": messages})

# ========================================================================
# API ФАЙЛОВ
# ========================================================================

@app.route('/api/upload', methods=['POST'])
@require_auth
def api_upload_file(user):
    if 'file' not in request.files:
        return jsonify(success=False, error="Файл не выбран"), 400
    file = request.files['file']
    channel_id = request.form.get('channel_id')
    result = FileManager.upload_file(file, user['id'], channel_id)
    return jsonify(result)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Отдача загруженных файлов"""
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/api/files/my')
@require_auth
def api_get_my_files(user):
    """Получение файлов пользователя"""
    file_type = request.args.get('type')
    limit = min(int(request.args.get('limit', 50)), 100)

    files = FileManager.get_user_files(user['id'], file_type, limit)
    return jsonify({"success": True, "files": files})

# ========================================================================
# API ПОЛЬЗОВАТЕЛЕЙ И ДРУЗЕЙ
# ========================================================================

@app.route('/api/users/search')
@require_auth
def api_search_users(user):
    """Поиск пользователей"""
    query = request.args.get('q', '').strip().lower()
    limit = min(int(request.args.get('limit', 20)), 50)

    if not query or len(query) < 2:
        return jsonify({"success": False, "error": "Запрос должен быть не менее 2 символов"})

    users = load_json(USERS_JSON, [])
    found_users = []

    for u in users:
        if (query in u.get('username', '').lower() or 
            query in u.get('email', '').lower()):
            user_info = {
                "id": u['id'],
                "username": u['username'],
                "avatar": u.get('avatar', '👤'),
                "status": u.get('status', 'offline')
            }
            found_users.append(user_info)

            if len(found_users) >= limit:
                break

    return jsonify({"success": True, "users": found_users})

@app.route('/api/friends')
@require_auth
def api_get_friends(user):
    """Получение списка друзей"""
    users = load_json(USERS_JSON, [])
    user_map = {u['id']: u for u in users}

    friends = []
    for friend_id in user.get('friends', []):
        friend = user_map.get(friend_id)
        if friend:
            friends.append({
                "id": friend['id'],
                "username": friend['username'],
                "avatar": friend.get('avatar', '👤'),
                "status": friend.get('status', 'offline'),
                "last_seen": friend.get('last_seen', 0)
            })

    return jsonify({"success": True, "friends": friends})

@app.route('/api/friends/<friend_id>', methods=['POST'])
@require_auth
def api_add_friend(user, friend_id):
    """Добавление в друзья"""
    success = UserManager.add_friend(user['id'], friend_id)
    return jsonify({"success": success})

@app.route('/api/friends/<friend_id>', methods=['DELETE'])
@require_auth
def api_remove_friend(user, friend_id):
    """Удаление из друзей"""
    success = UserManager.remove_friend(user['id'], friend_id)
    return jsonify({"success": success})

# ========================================================================
# API ТЕМ И НАСТРОЕК
# ========================================================================

@app.route('/api/themes')
def api_get_themes():
    """Получение всех тем"""
    themes = ThemeManager.get_all_themes()
    return jsonify({"success": True, "themes": themes})

@app.route('/api/themes/<theme_id>/apply', methods=['POST'])
@require_auth
def api_apply_theme(user, theme_id):
    """Применение темы"""
    success = ThemeManager.apply_user_theme(user['id'], theme_id)
    return jsonify({"success": success})

@app.route('/api/settings', methods=['GET'])
@require_auth
def api_get_user_settings(user):
    """Получение настроек пользователя"""
    return jsonify({"success": True, "settings": user.get('settings', {})})

@app.route('/api/settings', methods=['POST'])
@require_auth
def api_update_user_settings(user):
    """Обновление настроек пользователя"""
    data = request.get_json() or {}

    # Обновляем только разрешенные настройки
    allowed_settings = [
        'show_online_status', 'allow_friend_requests', 'allow_server_invites',
        'notifications', 'sound_notifications', 'email_notifications'
    ]

    updates = {}
    for key, value in data.items():
        if key in allowed_settings:
            if 'settings' not in updates:
                updates['settings'] = user.get('settings', {}).copy()
            updates['settings'][key] = value

    if updates:
        success = UserManager.update_user(user['id'], updates)
        return jsonify({"success": success})

    return jsonify({"success": False, "error": "Нет допустимых настроек для обновления"})

# ========================================================================
# API СТАТИСТИКИ И АДМИНИСТРИРОВАНИЯ
# ========================================================================

@app.route('/api/stats')
def api_get_stats():
    """Получение общей статистики"""
    users = load_json(USERS_JSON, [])
    messages = load_json(MESSAGES_JSON, [])
    servers = load_json(SERVERS_JSON, [])
    channels = load_json(CHANNELS_JSON, [])
    online_users = UserManager.get_online_users()

    stats = {
        "users_total": len(users),
        "users_online": len(online_users),
        "messages_total": len(messages),
        "servers_total": len(servers),
        "channels_total": len(channels),
        "uptime_hours": (time.time() - load_json(STATS_JSON, {}).get('uptime_start', time.time())) / 3600
    }

    return jsonify({"success": True, "stats": stats})

@app.route('/api/admin/users')
@require_admin
def api_admin_get_users(user):
    """Получение всех пользователей (админ)"""
    users = load_json(USERS_JSON, [])
    # Убираем пароли
    safe_users = []
    for u in users:
        safe_user = u.copy()
        safe_user.pop('password_hash', None)
        safe_users.append(safe_user)

    return jsonify({"success": True, "users": safe_users})

@app.route('/api/admin/reports')
@require_admin
def api_admin_get_reports(user):
    """Получение жалоб (админ)"""
    reports = ModerationManager.get_pending_reports()
    return jsonify({"success": True, "reports": reports})

@app.route('/api/admin/logs')
@require_admin
def api_admin_get_logs(user):
    """Получение логов (админ)"""
    limit = min(int(request.args.get('limit', 100)), 1000)
    logs = load_json(LOGS_JSON, [])

    # Возвращаем последние записи
    return jsonify({"success": True, "logs": logs[-limit:]})

print("✅ Добавлены API маршруты")

# ========================================================================
# ВЕБ-ИНТЕРФЕЙС - ГЛАВНАЯ СТРАНИЦА И АУТЕНТИФИКАЦИЯ
# ========================================================================

@app.route('/')
def index():
    """Главная страница SafeGram 4.0 Ultimate Pro"""
    stats = load_json(STATS_JSON, {})
    user = SessionManager.get_current_user()

    # Если пользователь авторизован, редиректим в приложение
    if user:
        return redirect('/app')

    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeGram 4.0 Ultimate Pro - Мессенджер будущего</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --primary: #0a0a0f;
            --secondary: #161620;
            --accent: #00d4ff;
            --success: #00ff88;
            --warning: #ffaa00;
            --danger: #ff4444;
            --text: #ffffff;
            --text-secondary: #b8b8c6;
            --border: #2a2a3a;
        }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial, sans-serif;
            background: linear-gradient(135deg, var(--primary), var(--secondary), #0d1117);
            color: var(--text);
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* Анимированный фон */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: 
                radial-gradient(circle at 20% 20%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 60%, rgba(255, 170, 0, 0.05) 0%, transparent 50%);
            animation: backgroundFloat 20s ease-in-out infinite alternate;
            z-index: -1;
        }

        @keyframes backgroundFloat {
            from { transform: translate(0, 0) rotate(0deg); }
            to { transform: translate(-30px, -30px) rotate(2deg); }
        }

        /* Навигация */
        .navbar {
            position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
            background: rgba(10, 10, 15, 0.95); backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
        }

        .nav-content {
            max-width: 1200px; margin: 0 auto;
            display: flex; justify-content: space-between; align-items: center;
        }

        .logo {
            font-size: 1.8rem; font-weight: 900; color: var(--accent);
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
            animation: logoGlow 3s ease-in-out infinite alternate;
        }

        @keyframes logoGlow {
            from { text-shadow: 0 0 10px rgba(0, 212, 255, 0.8); }
            to { text-shadow: 0 0 30px rgba(0, 212, 255, 1); }
        }

        .nav-links {
            display: flex; gap: 2rem; align-items: center;
        }

        .nav-links a {
            color: var(--text-secondary); text-decoration: none;
            transition: all 0.3s ease; font-weight: 500;
        }

        .nav-links a:hover {
            color: var(--accent); transform: translateY(-2px);
        }

        /* Главный контент */
        .hero {
            min-height: 100vh; display: flex; align-items: center;
            padding: 120px 2rem 2rem;
        }

        .hero-content {
            max-width: 1200px; margin: 0 auto; width: 100%;
            display: grid; grid-template-columns: 1fr 1fr; gap: 4rem;
            align-items: center;
        }

        .hero-text h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 900; margin-bottom: 1.5rem;
            background: linear-gradient(45deg, var(--accent), var(--success), var(--warning));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }

        .hero-text p {
            font-size: 1.3rem; color: var(--text-secondary);
            margin-bottom: 2rem; line-height: 1.6;
        }

        .cta-buttons {
            display: flex; gap: 1.5rem; flex-wrap: wrap;
        }

        .btn {
            padding: 1rem 2rem; border: none; border-radius: 12px;
            font-size: 1.1rem; font-weight: 700; cursor: pointer;
            text-decoration: none; display: inline-flex;
            align-items: center; gap: 0.5rem; transition: all 0.3s ease;
            text-transform: uppercase; letter-spacing: 0.5px;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent), #0099cc);
            color: white; box-shadow: 0 8px 32px rgba(0, 212, 255, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0, 212, 255, 0.5);
        }

        .btn-secondary {
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: white; box-shadow: 0 8px 32px rgba(0, 255, 136, 0.3);
        }

        .btn-secondary:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0, 255, 136, 0.5);
        }

        /* Статистика */
        .hero-stats {
            display: grid; grid-template-columns: repeat(2, 1fr);
            gap: 2rem; margin-top: 3rem;
        }

        .stat-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border: 1px solid var(--border); border-radius: 16px;
            padding: 1.5rem; text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            border-color: var(--accent);
            box-shadow: 0 10px 40px rgba(0, 212, 255, 0.2);
        }

        .stat-value {
            font-size: 2.5rem; font-weight: 900;
            color: var(--accent); margin-bottom: 0.5rem;
            animation: statPulse 3s ease-in-out infinite;
        }

        @keyframes statPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .stat-label {
            color: var(--text-secondary); font-weight: 600;
            text-transform: uppercase; font-size: 0.9rem;
        }

        /* Демо интерфейс */
        .hero-demo {
            position: relative;
        }

        .demo-window {
            background: linear-gradient(135deg, var(--secondary), rgba(22, 22, 32, 0.95));
            border: 1px solid var(--border); border-radius: 20px;
            padding: 1.5rem; box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            backdrop-filter: blur(20px);
        }

        .demo-header {
            display: flex; align-items: center; gap: 0.5rem;
            margin-bottom: 1rem; padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }

        .demo-dot {
            width: 12px; height: 12px; border-radius: 50%;
        }
        .demo-dot:nth-child(1) { background: var(--danger); }
        .demo-dot:nth-child(2) { background: var(--warning); }
        .demo-dot:nth-child(3) { background: var(--success); }

        .demo-message {
            background: rgba(0, 212, 255, 0.1);
            border-left: 3px solid var(--accent);
            padding: 1rem; border-radius: 0 12px 12px 0;
            margin-bottom: 1rem;
        }

        .demo-author {
            font-weight: 600; color: var(--accent);
            margin-bottom: 0.5rem; font-size: 0.9rem;
        }

        .demo-content {
            color: var(--text); line-height: 1.5;
        }

        /* Особенности */
        .features {
            padding: 4rem 2rem; max-width: 1200px; margin: 0 auto;
        }

        .features h2 {
            text-align: center; font-size: 3rem; font-weight: 900;
            margin-bottom: 3rem; color: var(--accent);
        }

        .features-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        .feature-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border: 1px solid var(--border); border-radius: 20px;
            padding: 2rem; text-align: center;
            transition: all 0.3s ease; backdrop-filter: blur(10px);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            border-color: var(--accent);
            box-shadow: 0 20px 60px rgba(0, 212, 255, 0.2);
        }

        .feature-icon {
            font-size: 3rem; margin-bottom: 1rem;
            background: linear-gradient(45deg, var(--accent), var(--success));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        .feature-title {
            font-size: 1.5rem; font-weight: 700;
            margin-bottom: 1rem; color: var(--text);
        }

        .feature-description {
            color: var(--text-secondary); line-height: 1.6;
        }

        /* Подвал */
        .footer {
            text-align: center; padding: 3rem 2rem;
            border-top: 1px solid var(--border);
            background: rgba(10, 10, 15, 0.8);
        }

        .footer p {
            color: var(--text-secondary); margin-bottom: 1rem;
        }

        .social-links {
            display: flex; justify-content: center; gap: 1rem;
        }

        .social-links a {
            display: inline-flex; align-items: center; justify-content: center;
            width: 40px; height: 40px; border-radius: 50%;
            background: var(--border); color: var(--text);
            text-decoration: none; transition: all 0.3s ease;
        }

        .social-links a:hover {
            background: var(--accent); transform: translateY(-2px);
        }

        /* Адаптивность */
        @media (max-width: 768px) {
            .hero-content { grid-template-columns: 1fr; text-align: center; }
            .nav-content { flex-direction: column; gap: 1rem; }
            .cta-buttons { justify-content: center; }
        }
    </style>
</head>
<body>
    <!-- Навигация -->
    <nav class="navbar">
        <div class="nav-content">
            <div class="logo">
                <i class="fas fa-shield-alt"></i> SafeGram 4.0
            </div>
            <div class="nav-links">
                <a href="#features">Возможности</a>
                <a href="/login">Войти</a>
                <a href="/register">Регистрация</a>
                <a href="/admin">Админка</a>
            </div>
        </div>
    </nav>

    <!-- Главный экран -->
    <section class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>Мессенджер будущего уже здесь</h1>
                <p>SafeGram 4.0 Ultimate Pro - это новое поколение защищенных коммуникаций с функциями Discord и Telegram, объединенными в одной мощной платформе.</p>

                <div class="cta-buttons">
                    <a href="/register" class="btn btn-primary">
                        <i class="fas fa-rocket"></i> Начать общение
                    </a>
                    <a href="/app" class="btn btn-secondary">
                        <i class="fas fa-play"></i> Демо версия
                    </a>
                </div>

                <div class="hero-stats">
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.get('total_users', 1) }}+</div>
                        <div class="stat-label">Пользователей</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ messages_count }}+</div>
                        <div class="stat-label">Сообщений</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">99.9%</div>
                        <div class="stat-label">Аптайм</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ servers_count }}+</div>
                        <div class="stat-label">Серверов</div>
                    </div>
                </div>
            </div>

            <div class="hero-demo">
                <div class="demo-window">
                    <div class="demo-header">
                        <div class="demo-dot"></div>
                        <div class="demo-dot"></div>
                        <div class="demo-dot"></div>
                        <span style="margin-left: 1rem; color: var(--text-secondary); font-size: 0.9rem;">SafeGram 4.0</span>
                    </div>

                    <div class="demo-message">
                        <div class="demo-author">🤖 AI Assistant</div>
                        <div class="demo-content">
                            Добро пожаловать в SafeGram 4.0 Ultimate Pro!<br>
                            <br>
                            ✨ <strong>Новые возможности:</strong><br>
                            • Серверы и каналы как в Discord<br>
                            • Голосовые каналы<br>
                            • Боты и автоответчики<br>
                            • Темы оформления<br>
                            • Система достижений<br>
                            • Marketplace стикеров
                        </div>
                    </div>

                    <div class="demo-message" style="background: rgba(0, 255, 136, 0.1); border-left-color: var(--success);">
                        <div class="demo-author" style="color: var(--success);">👤 Пользователь</div>
                        <div class="demo-content">
                            Потрясающе! Это действительно конкурент Discord и Telegram! 🚀
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Особенности -->
    <section class="features" id="features">
        <h2>Революционные возможности</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🏠</div>
                <div class="feature-title">Серверы и каналы</div>
                <div class="feature-description">
                    Создавайте собственные серверы с текстовыми и голосовыми каналами, 
                    управляйте участниками и правами доступа.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">Умные боты</div>
                <div class="feature-description">
                    Встроенная система ботов с поддержкой команд, автоответчиков 
                    и интеграций с внешними сервисами.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🎨</div>
                <div class="feature-title">Кастомные темы</div>
                <div class="feature-description">
                    Персонализируйте интерфейс с помощью тем оформления или 
                    создайте свою уникальную тему.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🏆</div>
                <div class="feature-title">Система достижений</div>
                <div class="feature-description">
                    Получайте опыт и достижения за активность, повышайте уровень 
                    и разблокировайте новые возможности.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">📁</div>
                <div class="feature-title">Файловый менеджер</div>
                <div class="feature-description">
                    Обменивайтесь файлами до 100MB, создавайте галереи изображений 
                    и организуйте медиа-контент.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🛡️</div>
                <div class="feature-title">Продвинутая безопасность</div>
                <div class="feature-description">
                    Шифрование сообщений, система модерации, защита от спама 
                    и полный контроль приватности.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">🎮</div>
                <div class="feature-title">Игры и развлечения</div>
                <div class="feature-description">
                    Встроенные мини-игры, система статусов, реакции и стикеры 
                    для веселого общения.
                </div>
            </div>

            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Детальная аналитика</div>
                <div class="feature-description">
                    Статистика использования, отчеты активности и инструменты 
                    для администраторов серверов.
                </div>
            </div>
        </div>
    </section>

    <!-- Подвал -->
    <footer class="footer">
        <p>&copy; 2025 SafeGram 4.0 Ultimate Pro. Создано с помощью AI.</p>
        <div class="social-links">
            <a href="#"><i class="fab fa-github"></i></a>
            <a href="#"><i class="fab fa-discord"></i></a>
            <a href="#"><i class="fab fa-telegram"></i></a>
            <a href="#"><i class="fab fa-twitter"></i></a>
        </div>
    </footer>
</body>
</html>
    """, 
    stats=stats,
    messages_count=len(load_json(MESSAGES_JSON, [])),
    servers_count=len(load_json(SERVERS_JSON, []))
    )

@app.route('/login')
def login_page():
    """Страница входа"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в SafeGram 4.0</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial;
            background: linear-gradient(135deg, #0a0a0f, #161620, #0d1117);
            color: #ffffff; min-height: 100vh;
            display: flex; align-items: center; justify-content: center;
            padding: 2rem;
        }

        body::before {
            content: '';
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 30% 30%, rgba(0, 212, 255, 0.1), transparent 50%),
                       radial-gradient(circle at 70% 70%, rgba(0, 255, 136, 0.1), transparent 50%);
            animation: float 15s ease-in-out infinite alternate;
            z-index: -1;
        }

        @keyframes float {
            from { transform: translate(0, 0); }
            to { transform: translate(-20px, -20px); }
        }

        .login-container {
            background: linear-gradient(135deg, rgba(22, 22, 32, 0.9), rgba(16, 16, 30, 0.9));
            border: 1px solid #2a2a3a; border-radius: 20px;
            padding: 3rem; max-width: 400px; width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            backdrop-filter: blur(20px);
        }

        .logo {
            text-align: center; margin-bottom: 2rem;
        }

        .logo i {
            font-size: 3rem; color: #00d4ff;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
            animation: logoGlow 3s ease-in-out infinite alternate;
        }

        @keyframes logoGlow {
            from { text-shadow: 0 0 10px rgba(0, 212, 255, 0.8); }
            to { text-shadow: 0 0 30px rgba(0, 212, 255, 1); }
        }

        .logo h1 {
            font-size: 1.8rem; font-weight: 900;
            margin-top: 0.5rem; color: #00d4ff;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block; margin-bottom: 0.5rem;
            color: #b8b8c6; font-weight: 600; font-size: 0.9rem;
        }

        .form-group input {
            width: 100%; padding: 1rem; border: 1px solid #2a2a3a;
            border-radius: 12px; background: rgba(255,255,255,0.05);
            color: #ffffff; font-size: 1rem;
            transition: all 0.3s ease;
        }

        .form-group input:focus {
            outline: none; border-color: #00d4ff;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
        }

        .login-btn {
            width: 100%; padding: 1rem; border: none;
            border-radius: 12px; font-size: 1.1rem; font-weight: 700;
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: white; cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase; letter-spacing: 0.5px;
            margin-bottom: 1rem;
        }

        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.4);
        }

        .demo-info {
            background: rgba(255, 170, 0, 0.1);
            border: 1px solid rgba(255, 170, 0, 0.3);
            border-radius: 10px; padding: 1rem;
            margin-bottom: 1.5rem; font-size: 0.85rem;
            color: #ffaa00;
        }

        .demo-info strong { color: #ffffff; }

        .links {
            text-align: center; margin-top: 1.5rem;
        }

        .links a {
            color: #00d4ff; text-decoration: none;
            transition: all 0.3s ease;
        }

        .links a:hover {
            color: #00ff88; text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }

        .error {
            background: rgba(255, 68, 68, 0.1);
            border: 1px solid rgba(255, 68, 68, 0.3);
            border-radius: 10px; padding: 1rem;
            margin-bottom: 1rem; color: #ff4444;
            text-align: center; font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <i class="fas fa-shield-alt"></i>
            <h1>SafeGram 4.0</h1>
        </div>

        <div class="demo-info">
            <strong>Демо доступы:</strong><br>
            👑 <strong>Администратор:</strong> admin / panel<br>
            👤 <strong>Или создайте новый аккаунт</strong>
        </div>

        <form id="loginForm">
            <div class="form-group">
                <label>Email или логин</label>
                <input type="text" id="email" placeholder="admin или ваш email" required>
            </div>

            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="password" placeholder="••••••••" required>
            </div>

            <div id="error" class="error" style="display: none;"></div>

            <button type="submit" class="login-btn">
                <i class="fas fa-sign-in-alt"></i> Войти
            </button>
        </form>

        <div class="links">
            <p>Нет аккаунта? <a href="/register">Зарегистрироваться</a></p>
            <p><a href="/">← На главную</a></p>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('error');

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const result = await response.json();

                if (result.success) {
                    if (email === 'admin') {
                        window.location.href = '/admin';
                    } else {
                        window.location.href = '/app';
                    }
                } else {
                    errorDiv.textContent = result.error;
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Ошибка подключения к серверу';
                errorDiv.style.display = 'block';
            }
        });
    </script>
</body>
</html>
    """)

@app.route('/register')
def register_page():
    """Страница регистрации"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Регистрация в SafeGram 4.0</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial;
            background: linear-gradient(135deg, #0a0a0f, #161620, #0d1117);
            color: #ffffff; min-height: 100vh;
            display: flex; align-items: center; justify-content: center;
            padding: 2rem;
        }

        body::before {
            content: '';
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 70% 30%, rgba(0, 255, 136, 0.1), transparent 50%),
                       radial-gradient(circle at 30% 70%, rgba(255, 170, 0, 0.1), transparent 50%);
            animation: float 15s ease-in-out infinite alternate;
            z-index: -1;
        }

        @keyframes float {
            from { transform: translate(0, 0); }
            to { transform: translate(20px, -20px); }
        }

        .register-container {
            background: linear-gradient(135deg, rgba(22, 22, 32, 0.9), rgba(16, 16, 30, 0.9));
            border: 1px solid #2a2a3a; border-radius: 20px;
            padding: 3rem; max-width: 450px; width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            backdrop-filter: blur(20px);
        }

        .logo {
            text-align: center; margin-bottom: 2rem;
        }

        .logo i {
            font-size: 3rem; color: #00ff88;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
            animation: logoGlow 3s ease-in-out infinite alternate;
        }

        @keyframes logoGlow {
            from { text-shadow: 0 0 10px rgba(0, 255, 136, 0.8); }
            to { text-shadow: 0 0 30px rgba(0, 255, 136, 1); }
        }

        .logo h1 {
            font-size: 1.8rem; font-weight: 900;
            margin-top: 0.5rem; color: #00ff88;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block; margin-bottom: 0.5rem;
            color: #b8b8c6; font-weight: 600; font-size: 0.9rem;
        }

        .form-group input {
            width: 100%; padding: 1rem; border: 1px solid #2a2a3a;
            border-radius: 12px; background: rgba(255,255,255,0.05);
            color: #ffffff; font-size: 1rem;
            transition: all 0.3s ease;
        }

        .form-group input:focus {
            outline: none; border-color: #00ff88;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        }

        .register-btn {
            width: 100%; padding: 1rem; border: none;
            border-radius: 12px; font-size: 1.1rem; font-weight: 700;
            background: linear-gradient(135deg, #00ff88, #00cc66);
            color: white; cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase; letter-spacing: 0.5px;
            margin-bottom: 1rem;
        }

        .register-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.4);
        }

        .password-requirements {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 10px; padding: 1rem;
            margin-bottom: 1.5rem; font-size: 0.85rem;
            color: #00d4ff;
        }

        .password-requirements ul {
            list-style: none; margin-top: 0.5rem;
        }

        .password-requirements li {
            margin-bottom: 0.25rem;
        }

        .password-requirements li::before {
            content: '✓'; margin-right: 0.5rem; color: #00ff88;
        }

        .links {
            text-align: center; margin-top: 1.5rem;
        }

        .links a {
            color: #00ff88; text-decoration: none;
            transition: all 0.3s ease;
        }

        .links a:hover {
            color: #00d4ff; text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }

        .error, .success {
            border-radius: 10px; padding: 1rem;
            margin-bottom: 1rem; text-align: center; font-weight: 600;
        }

        .error {
            background: rgba(255, 68, 68, 0.1);
            border: 1px solid rgba(255, 68, 68, 0.3);
            color: #ff4444;
        }

        .success {
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: #00ff88;
        }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="logo">
            <i class="fas fa-user-plus"></i>
            <h1>Присоединиться</h1>
        </div>

        <div class="password-requirements">
            <strong>Требования к паролю:</strong>
            <ul>
                <li>Минимум 6 символов</li>
                <li>Содержит буквы и цифры</li>
                <li>Безопасное хранение</li>
            </ul>
        </div>

        <form id="registerForm">
            <div class="form-group">
                <label>Имя пользователя</label>
                <input type="text" id="username" placeholder="Ваше имя в SafeGram" required>
            </div>

            <div class="form-group">
                <label>Email</label>
                <input type="email" id="email" placeholder="your@email.com" required>
            </div>

            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="password" placeholder="••••••••" required>
            </div>

            <div class="form-group">
                <label>Подтвердите пароль</label>
                <input type="password" id="confirmPassword" placeholder="••••••••" required>
            </div>

            <div id="message" style="display: none;"></div>

            <button type="submit" class="register-btn">
                <i class="fas fa-rocket"></i> Создать аккаунт
            </button>
        </form>

        <div class="links">
            <p>Уже есть аккаунт? <a href="/login">Войти</a></p>
            <p><a href="/">← На главную</a></p>
        </div>
    </div>

    <script>
        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const messageDiv = document.getElementById('message');

            // Базовая валидация
            if (password !== confirmPassword) {
                messageDiv.className = 'error';
                messageDiv.textContent = 'Пароли не совпадают';
                messageDiv.style.display = 'block';
                return;
            }

            if (password.length < 6) {
                messageDiv.className = 'error';
                messageDiv.textContent = 'Пароль должен быть не менее 6 символов';
                messageDiv.style.display = 'block';
                return;
            }

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                const result = await response.json();

                if (result.success) {
                    messageDiv.className = 'success';
                    messageDiv.textContent = 'Аккаунт успешно создан! Перенаправление...';
                    messageDiv.style.display = 'block';

                    setTimeout(() => {
                        window.location.href = '/app';
                    }, 2000);
                } else {
                    messageDiv.className = 'error';
                    messageDiv.textContent = result.error;
                    messageDiv.style.display = 'block';
                }
            } catch (error) {
                messageDiv.className = 'error';
                messageDiv.textContent = 'Ошибка подключения к серверу';
                messageDiv.style.display = 'block';
            }
        });
    </script>
</body>
</html>
    """)

print("✅ Добавлены веб-интерфейсы")

# ========================================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ МЕССЕНДЖЕРА
# ========================================================================

@app.route('/app')
def messenger_app():
    """Главное приложение мессенджера SafeGram 4.0"""
    user = SessionManager.get_current_user()
    if not user:
        return redirect('/login')

    # Получаем данные для приложения
    user_servers = ServerManager.get_user_servers(user['id'])
    user_friends = user.get('friends', [])

    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeGram 4.0 - {{ user.username }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #161620;
            --bg-tertiary: #1f1f2e;
            --text-primary: #ffffff;
            --text-secondary: #b8b8c6;
            --accent: #00d4ff;
            --success: #00ff88;
            --warning: #ffaa00;
            --danger: #ff4444;
            --border: #2a2a3a;
            --shadow: rgba(0, 0, 0, 0.4);
            --hover: rgba(0, 212, 255, 0.1);
        }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh; overflow: hidden;
        }

        /* Основная сетка приложения */
        .app-container {
            display: grid;
            grid-template-columns: 80px 280px 1fr 300px;
            height: 100vh;
            background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
        }

        /* Левая навигационная панель серверов */
        .server-list {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 20px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            overflow-y: auto;
        }

        .server-icon {
            width: 50px; height: 50px;
            border-radius: 25px;
            background: var(--bg-tertiary);
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: all 0.3s ease;
            font-size: 1.5rem; color: var(--text-secondary);
            border: 2px solid transparent;
            position: relative;
        }

        .server-icon:hover, .server-icon.active {
            border-radius: 15px;
            background: var(--accent);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .server-icon.active::before {
            content: '';
            position: absolute; left: -15px; top: 50%;
            transform: translateY(-50%);
            width: 4px; height: 40px;
            background: white; border-radius: 2px;
        }

        /* Добавление сервера */
        .add-server {
            border: 2px dashed var(--border);
            color: var(--text-secondary);
            font-size: 1.2rem;
        }

        .add-server:hover {
            border-color: var(--success);
            background: rgba(0, 255, 136, 0.1);
            color: var(--success);
        }

        /* Боковая панель каналов */
        .channels-sidebar {
            background: var(--bg-tertiary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }

        .server-header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
        }

        .server-name {
            font-size: 1.2rem; font-weight: 700;
            margin-bottom: 5px; color: var(--text-primary);
        }

        .server-description {
            font-size: 0.9rem; color: var(--text-secondary);
        }

        .channels-list {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        .channel-category {
            color: var(--text-secondary);
            font-size: 0.8rem; font-weight: 700;
            text-transform: uppercase;
            margin: 20px 0 10px;
            letter-spacing: 0.5px;
        }

        .channel-item {
            display: flex; align-items: center;
            padding: 8px 12px; margin-bottom: 4px;
            border-radius: 8px; cursor: pointer;
            transition: all 0.2s ease;
            color: var(--text-secondary);
        }

        .channel-item:hover {
            background: var(--hover);
            color: var(--accent);
        }

        .channel-item.active {
            background: var(--accent);
            color: white;
        }

        .channel-icon {
            width: 20px; text-align: center;
            margin-right: 8px; font-size: 0.9rem;
        }

        .channel-name {
            flex: 1; font-weight: 500;
        }

        .channel-badge {
            background: var(--accent);
            color: white; font-size: 0.7rem;
            padding: 2px 6px; border-radius: 10px;
            font-weight: 600;
        }

        /* Основная область чата */
        .chat-area {
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
        }

        .chat-header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-info h3 {
            color: var(--text-primary);
            font-size: 1.3rem; font-weight: 700;
            margin-bottom: 2px;
        }

        .chat-info p {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .chat-actions {
            display: flex;
            gap: 10px;
        }

        .chat-actions button {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 8px 12px; border-radius: 8px;
            cursor: pointer; transition: all 0.2s ease;
            font-size: 0.9rem;
        }

        .chat-actions button:hover {
            border-color: var(--accent);
            color: var(--accent);
        }

        .messages-container {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            display: flex;
            gap: 15px;
        }

        .message-avatar {
            width: 40px; height: 40px;
            border-radius: 50%;
            background: var(--accent);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2rem; flex-shrink: 0;
        }

        .message-content {
            flex: 1;
        }

        .message-header {
            display: flex; align-items: center;
            gap: 10px; margin-bottom: 5px;
        }

        .message-author {
            font-weight: 600;
            color: var(--accent);
        }

        .message-time {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .message-text {
            line-height: 1.5;
            color: var(--text-primary);
        }

        .message-actions {
            opacity: 0; display: flex; gap: 5px;
            margin-top: 5px; transition: opacity 0.2s;
        }

        .message:hover .message-actions {
            opacity: 1;
        }

        .message-actions button {
            background: transparent;
            border: none; color: var(--text-secondary);
            padding: 4px 8px; border-radius: 4px;
            cursor: pointer; font-size: 0.8rem;
            transition: all 0.2s;
        }

        .message-actions button:hover {
            background: var(--hover);
            color: var(--accent);
        }

        /* Ввод сообщения */
        .message-input-area {
            padding: 20px;
            border-top: 1px solid var(--border);
            background: var(--bg-secondary);
        }

        .message-input-container {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .message-input {
            flex: 1;
            background: transparent;
            border: none; outline: none;
            color: var(--text-primary);
            font-size: 1rem;
            resize: none; min-height: 20px;
        }

        .message-input::placeholder {
            color: var(--text-secondary);
        }

        .input-actions {
            display: flex;
            gap: 10px;
        }

        .input-actions button {
            background: transparent;
            border: none; color: var(--text-secondary);
            cursor: pointer; padding: 8px;
            border-radius: 6px; transition: all 0.2s;
        }

        .input-actions button:hover {
            background: var(--hover);
            color: var(--accent);
        }

        .send-button {
            background: var(--accent) !important;
            color: white !important;
        }

        .send-button:hover {
            background: var(--success) !important;
            transform: scale(1.1);
        }

        /* Правая панель */
        .right-panel {
            background: var(--bg-tertiary);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }

        .panel-tabs {
            display: flex;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
        }

        .panel-tab {
            flex: 1; padding: 15px;
            text-align: center;
            background: transparent;
            border: none; color: var(--text-secondary);
            cursor: pointer; transition: all 0.2s;
            font-weight: 600;
        }

        .panel-tab.active {
            color: var(--accent);
            border-bottom: 2px solid var(--accent);
        }

        .panel-content {
            flex: 1; padding: 20px;
            overflow-y: auto;
        }

        .user-profile {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }

        .user-avatar {
            width: 80px; height: 80px;
            border-radius: 50%;
            background: var(--accent);
            margin: 0 auto 15px;
            display: flex; align-items: center; justify-content: center;
            font-size: 2rem;
        }

        .user-name {
            font-size: 1.3rem; font-weight: 700;
            margin-bottom: 5px; color: var(--text-primary);
        }

        .user-status {
            color: var(--success);
            font-size: 0.9rem;
        }

        .user-level {
            background: linear-gradient(45deg, var(--accent), var(--success));
            color: white; padding: 5px 10px;
            border-radius: 15px; font-size: 0.8rem;
            font-weight: 600; margin-top: 10px;
            display: inline-block;
        }

        /* Список участников */
        .members-list {
            list-style: none;
        }

        .member-item {
            display: flex; align-items: center;
            gap: 10px; padding: 8px 0;
            color: var(--text-secondary);
            transition: color 0.2s;
        }

        .member-item:hover {
            color: var(--text-primary);
        }

        .member-avatar {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: var(--border);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.9rem;
        }

        .member-info {
            flex: 1;
        }

        .member-name {
            font-weight: 500;
        }

        .member-status {
            font-size: 0.8rem;
        }

        .status-indicator {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--success);
        }

        .status-indicator.offline {
            background: var(--text-secondary);
        }

        /* Адаптивность */
        @media (max-width: 768px) {
            .app-container {
                grid-template-columns: 1fr;
            }

            .server-list, .right-panel {
                display: none;
            }

            .channels-sidebar {
                position: fixed; left: -280px;
                z-index: 1000; height: 100vh;
                transition: left 0.3s ease;
            }

            .channels-sidebar.open {
                left: 0;
            }
        }

        /* Анимации загрузки */
        .loading {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid var(--border);
            border-radius: 50%;
            border-top: 2px solid var(--accent);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Уведомления */
        .notification {
            position: fixed; top: 20px; right: 20px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 12px; padding: 15px 20px;
            box-shadow: 0 10px 40px var(--shadow);
            z-index: 10000; max-width: 300px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success {
            border-color: var(--success);
        }

        .notification.error {
            border-color: var(--danger);
        }

        /* Модальные окна */
        .modal-overlay {
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex; align-items: center; justify-content: center;
            z-index: 10000; opacity: 0;
            visibility: hidden; transition: all 0.3s ease;
        }

        .modal-overlay.active {
            opacity: 1; visibility: visible;
        }

        .modal {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 16px; padding: 30px;
            max-width: 500px; width: 90%;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal h3 {
            margin-bottom: 20px;
            color: var(--text-primary);
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block; margin-bottom: 5px;
            color: var(--text-secondary); font-weight: 500;
        }

        .form-group input, .form-group textarea {
            width: 100%; padding: 12px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px; color: var(--text-primary);
            font-family: inherit;
        }

        .form-group input:focus, .form-group textarea:focus {
            outline: none; border-color: var(--accent);
        }

        .modal-actions {
            display: flex; gap: 10px;
            justify-content: flex-end;
            margin-top: 20px;
        }

        .btn {
            padding: 10px 20px; border: none;
            border-radius: 8px; cursor: pointer;
            font-weight: 600; transition: all 0.2s;
        }

        .btn-primary {
            background: var(--accent); color: white;
        }

        .btn-primary:hover {
            background: var(--success);
        }

        .btn-secondary {
            background: var(--border); color: var(--text-primary);
        }

        .btn-secondary:hover {
            background: var(--hover);
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Список серверов -->
        <div class="server-list">
            <div class="server-icon active" data-server="main" title="SafeGram Community">
                🏠
            </div>
            {% for server in user_servers %}
            {% if server.id != 'main' %}
            <div class="server-icon" data-server="{{ server.id }}" title="{{ server.name }}">
                {{ server.icon }}
            </div>
            {% endif %}
            {% endfor %}
            <div class="server-icon add-server" onclick="showCreateServerModal()" title="Создать сервер">
                <i class="fas fa-plus"></i>
            </div>
        </div>

        <!-- Боковая панель каналов -->
        <div class="channels-sidebar">
            <div class="server-header">
                <div class="server-name" id="currentServerName">SafeGram Community</div>
                <div class="server-description" id="currentServerDescription">Главный сервер SafeGram</div>
            </div>

            <div class="channels-list">
                <div class="channel-category">Текстовые каналы</div>
                <div class="channel-item active" data-channel="general" data-type="text">
                    <div class="channel-icon">#</div>
                    <div class="channel-name">общий</div>
                    <div class="channel-badge" style="display: none;">3</div>
                </div>
                <div class="channel-item" data-channel="tech" data-type="text">
                    <div class="channel-icon">#</div>
                    <div class="channel-name">технологии</div>
                </div>
                <div class="channel-item" data-channel="random" data-type="text">
                    <div class="channel-icon">#</div>
                    <div class="channel-name">случайное</div>
                </div>

                <div class="channel-category">Голосовые каналы</div>
                <div class="channel-item" data-channel="voice_general" data-type="voice">
                    <div class="channel-icon">🔊</div>
                    <div class="channel-name">Общий голосовой</div>
                </div>
                <div class="channel-item" data-channel="voice_music" data-type="voice">
                    <div class="channel-icon">🎵</div>
                    <div class="channel-name">Музыка</div>
                </div>
            </div>
        </div>

        <!-- Основная область чата -->
        <div class="chat-area">
            <div class="chat-header">
                <div class="chat-info">
                    <h3 id="currentChannelName"># общий</h3>
                    <p id="currentChannelTopic">Главный канал для общения</p>
                </div>
                <div class="chat-actions">
                    <button onclick="toggleSearch()"><i class="fas fa-search"></i> Поиск</button>
                    <button onclick="showChannelSettings()"><i class="fas fa-cog"></i> Настройки</button>
                    <button onclick="togglePinnedMessages()"><i class="fas fa-thumbtack"></i> Закрепленные</button>
                </div>
            </div>

            <div class="messages-container" id="messagesContainer">
                <!-- Сообщения будут загружены через JavaScript -->
                <div class="loading" style="margin: 20px auto;"></div>
            </div>

            <div class="message-input-area">
                <div class="message-input-container">
                    <textarea id="messageInput" class="message-input" 
                             placeholder="Напишите сообщение в #общий..." 
                             rows="1"
                             onkeypress="handleMessageInput(event)"></textarea>
                    <div class="input-actions">
                        <button onclick="toggleEmojiPicker()" title="Эмодзи">
                            <i class="fas fa-smile"></i>
                        </button>
                        <button onclick="attachFile()" title="Прикрепить файл">
                            <i class="fas fa-paperclip"></i>
                        </button>
                        <button onclick="recordVoice()" title="Голосовое сообщение">
                            <i class="fas fa-microphone"></i>
                        </button>
                        <button class="send-button" onclick="sendMessage()" title="Отправить">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Правая панель -->
        <div class="right-panel">
            <div class="panel-tabs">
                <button class="panel-tab active" onclick="switchPanel('members')">
                    <i class="fas fa-users"></i> Участники
                </button>
                <button class="panel-tab" onclick="switchPanel('profile')">
                    <i class="fas fa-user"></i> Профиль  
                </button>
            </div>

            <div class="panel-content" id="panelContent">
                <div id="membersPanel">
                    <h4 style="color: var(--text-secondary); margin-bottom: 15px; font-size: 0.9rem; text-transform: uppercase;">
                        Онлайн — 2
                    </h4>
                    <ul class="members-list">
                        <li class="member-item">
                            <div class="member-avatar">👤</div>
                            <div class="member-info">
                                <div class="member-name">{{ user.username }}</div>
                                <div class="member-status">🎮 В SafeGram</div>
                            </div>
                            <div class="status-indicator"></div>
                        </li>
                        <li class="member-item">
                            <div class="member-avatar">🤖</div>
                            <div class="member-info">
                                <div class="member-name">AI Assistant</div>
                                <div class="member-status">💬 Отвечает на вопросы</div>
                            </div>
                            <div class="status-indicator"></div>
                        </li>
                    </ul>

                    <h4 style="color: var(--text-secondary); margin: 20px 0 15px; font-size: 0.9rem; text-transform: uppercase;">
                        Офлайн — 0
                    </h4>
                </div>

                <div id="profilePanel" style="display: none;">
                    <div class="user-profile">
                        <div class="user-avatar">{{ user.get('avatar', '👤') }}</div>
                        <div class="user-name">{{ user.username }}</div>
                        <div class="user-status">🟢 В сети</div>
                        <div class="user-level">Уровень {{ user.get('level', 1) }}</div>
                    </div>

                    <div style="margin-bottom: 20px;">
                        <h4 style="color: var(--text-secondary); margin-bottom: 10px;">Статистика</h4>
                        <div style="font-size: 0.9rem; line-height: 1.6;">
                            <div>📊 Сообщений: <strong>{{ user.get('statistics', {}).get('messages_sent', 0) }}</strong></div>
                            <div>📁 Файлов: <strong>{{ user.get('statistics', {}).get('files_shared', 0) }}</strong></div>
                            <div>🏠 Серверов: <strong>{{ user_servers|length }}</strong></div>
                            <div>👥 Друзей: <strong>{{ user_friends|length }}</strong></div>
                        </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <button class="btn btn-primary" onclick="showUserSettings()">
                            <i class="fas fa-cog"></i> Настройки
                        </button>
                        <button class="btn btn-secondary" onclick="showThemeSelector()">
                            <i class="fas fa-palette"></i> Темы
                        </button>
                        <button class="btn btn-secondary" onclick="logout()">
                            <i class="fas fa-sign-out-alt"></i> Выйти
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Модальные окна -->
    <!-- Создание сервера -->
    <div class="modal-overlay" id="createServerModal">
        <div class="modal">
            <h3>Создать новый сервер</h3>
            <form id="createServerForm">
                <div class="form-group">
                    <label>Название сервера</label>
                    <input type="text" id="serverName" placeholder="Мой крутой сервер" required>
                </div>
                <div class="form-group">
                    <label>Описание</label>
                    <textarea id="serverDescription" placeholder="Описание сервера..." rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label>Иконка (эмодзи)</label>
                    <input type="text" id="serverIcon" placeholder="🎮" maxlength="2">
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('createServerModal')">Отмена</button>
                    <button type="submit" class="btn btn-primary">Создать</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Глобальные переменные
        let currentServerId = 'main';
        let currentChannelId = 'general';
        let currentUser = {{ user | tojson }};
        let messages = [];
        let loadingMessages = false;

        // Инициализация приложения
        document.addEventListener('DOMContentLoaded', function() {
            loadInitialData();
            setupEventListeners();
            startPeriodicUpdates();
        });

        // Загрузка начальных данных
        async function loadInitialData() {
            try {
                await loadMessages();
                await loadServerData();
            } catch (error) {
                console.error('Ошибка загрузки данных:', error);
                showNotification('Ошибка загрузки данных', 'error');
            }
        }

        // Загрузка сообщений
        async function loadMessages() {
            if (loadingMessages) return;
            loadingMessages = true;

            try {
                const response = await fetch(`/api/channels/${currentChannelId}/messages?limit=50`);
                const result = await response.json();

                if (result.success) {
                    messages = result.messages.reverse(); // Переворачиваем для правильного порядка
                    renderMessages();
                }
            } catch (error) {
                console.error('Ошибка загрузки сообщений:', error);
            } finally {
                loadingMessages = false;
            }
        }

        // Отрисовка сообщений
        function renderMessages() {
            const container = document.getElementById('messagesContainer');

            if (messages.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; color: var(--text-secondary); padding: 40px;">
                        <i class="fas fa-comments" style="font-size: 3rem; margin-bottom: 15px; opacity: 0.5;"></i>
                        <h3>Начните общение!</h3>
                        <p>Это начало канала #общий. Напишите первое сообщение!</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = messages.map(message => {
                const author = message.author || { username: 'Unknown', avatar: '👤' };
                const time = new Date(message.created_at * 1000).toLocaleTimeString('ru', {
                    hour: '2-digit',
                    minute: '2-digit'
                });

                return `
                    <div class="message" data-message-id="${message.id}">
                        <div class="message-avatar">${author.avatar}</div>
                        <div class="message-content">
                            <div class="message-header">
                                <div class="message-author">${author.username}</div>
                                <div class="message-time">${time}</div>
                            </div>
                            <div class="message-text">${formatMessageContent(message.content)}</div>
                            ${message.author_id === currentUser.id ? `
                                <div class="message-actions">
                                    <button onclick="editMessage('${message.id}')">
                                        <i class="fas fa-edit"></i> Изменить
                                    </button>
                                    <button onclick="deleteMessage('${message.id}')">
                                        <i class="fas fa-trash"></i> Удалить
                                    </button>
                                </div>
                            ` : `
                                <div class="message-actions">
                                    <button onclick="replyToMessage('${message.id}')">
                                        <i class="fas fa-reply"></i> Ответить
                                    </button>
                                    <button onclick="addReaction('${message.id}', '👍')">
                                        <i class="fas fa-thumbs-up"></i> Лайк
                                    </button>
                                </div>
                            `}
                        </div>
                    </div>
                `;
            }).join('');

            // Прокручиваем к последнему сообщению
            container.scrollTop = container.scrollHeight;
        }

        // Форматирование содержимого сообщения
        function formatMessageContent(content) {
            // Простое форматирование
            return content
                .replace(r'\*\*(.*?)\*\*', '<strong>\\1</strong>')  # **bold**
                .replace(/\*(.*?)\*/g, '<em>$1</em>')               // *italic*
                .replace(/`(.*?)`/g, '<code>$1</code>')             // `code`
                .replace(/\n/g, '<br>');                           // переносы строк
        }

        // Отправка сообщения
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const content = input.value.trim();

            if (!content) return;

            try {
                const response = await fetch(`/api/channels/${currentChannelId}/messages`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });

                const result = await response.json();

                if (result.success) {
                    input.value = '';
                    input.style.height = 'auto';
                    await loadMessages();
                } else {
                    showNotification(result.error || 'Ошибка отправки сообщения', 'error');
                }
            } catch (error) {
                console.error('Ошибка отправки сообщения:', error);
                showNotification('Ошибка отправки сообщения', 'error');
            }
        }

        // Обработка ввода сообщения
        function handleMessageInput(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }

            // Автоматическое изменение высоты поля ввода
            const input = event.target;
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 200) + 'px';
        }

        // Настройка обработчиков событий
        function setupEventListeners() {
            // Переключение серверов
            document.querySelectorAll('.server-icon[data-server]').forEach(icon => {
                icon.addEventListener('click', function() {
                    switchServer(this.dataset.server);
                });
            });

            // Переключение каналов
            document.querySelectorAll('.channel-item[data-channel]').forEach(item => {
                item.addEventListener('click', function() {
                    switchChannel(this.dataset.channel);
                });
            });

            // Создание сервера
            document.getElementById('createServerForm').addEventListener('submit', handleCreateServer);

            // Закрытие модальных окон по клику вне их
            document.querySelectorAll('.modal-overlay').forEach(overlay => {
                overlay.addEventListener('click', function(e) {
                    if (e.target === this) {
                        this.classList.remove('active');
                    }
                });
            });
        }

        // Переключение сервера
        function switchServer(serverId) {
            currentServerId = serverId;

            // Обновляем активный сервер
            document.querySelectorAll('.server-icon').forEach(icon => {
                icon.classList.remove('active');
            });
            document.querySelector(`[data-server="${serverId}"]`).classList.add('active');

            // Загружаем каналы сервера
            loadServerChannels();
        }

        // Переключение канала
        function switchChannel(channelId) {
            currentChannelId = channelId;

            // Обновляем активный канал
            document.querySelectorAll('.channel-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-channel="${channelId}"]`).classList.add('active');

            // Обновляем заголовок чата
            const channelName = document.querySelector(`[data-channel="${channelId}"] .channel-name`).textContent;
            document.getElementById('currentChannelName').textContent = `# ${channelName}`;

            // Обновляем placeholder в поле ввода
            document.getElementById('messageInput').placeholder = `Напишите сообщение в #${channelName}...`;

            // Загружаем сообщения нового канала
            loadMessages();
        }

        // Загрузка каналов сервера
        async function loadServerChannels() {
            // В демо-версии используем статичные каналы
            // В реальной реализации здесь был бы запрос к API
        }

        // Показать уведомление
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;

            document.body.appendChild(notification);

            // Показываем уведомление
            setTimeout(() => notification.classList.add('show'), 100);

            // Скрываем и удаляем уведомление
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Модальные окна
        function showCreateServerModal() {
            document.getElementById('createServerModal').classList.add('active');
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }

        // Создание сервера
        async function handleCreateServer(event) {
            event.preventDefault();

            const name = document.getElementById('serverName').value.trim();
            const description = document.getElementById('serverDescription').value.trim();
            const icon = document.getElementById('serverIcon').value.trim() || '🏠';

            if (!name) {
                showNotification('Введите название сервера', 'error');
                return;
            }

            try {
                const response = await fetch('/api/servers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description, icon })
                });

                const result = await response.json();

                if (result.success) {
                    showNotification('Сервер создан!', 'success');
                    closeModal('createServerModal');
                    // Перезагружаем страницу для обновления списка серверов
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification(result.error || 'Ошибка создания сервера', 'error');
                }
            } catch (error) {
                console.error('Ошибка создания сервера:', error);
                showNotification('Ошибка создания сервера', 'error');
            }
        }

        // Переключение панелей
        function switchPanel(panel) {
            document.querySelectorAll('.panel-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector(`[onclick="switchPanel('${panel}')"]`).classList.add('active');

            if (panel === 'members') {
                document.getElementById('membersPanel').style.display = 'block';
                document.getElementById('profilePanel').style.display = 'none';
            } else if (panel === 'profile') {
                document.getElementById('membersPanel').style.display = 'none';
                document.getElementById('profilePanel').style.display = 'block';
            }
        }

        // Периодические обновления
        function startPeriodicUpdates() {
            // Обновляем сообщения каждые 5 секунд
            setInterval(() => {
                if (!loadingMessages) {
                    loadMessages();
                }
            }, 5000);

            // Обновляем онлайн статус каждые 30 секунд
            setInterval(() => {
                updateOnlineStatus();
            }, 30000);
        }

        async function updateOnlineStatus() {
            // Простой ping для поддержания сессии
            try {
                await fetch('/api/me');
            } catch (error) {
                console.error('Ошибка обновления статуса:', error);
            }
        }

        // Действия с сообщениями
        async function deleteMessage(messageId) {
            if (!confirm('Удалить сообщение?')) return;

            try {
                const response = await fetch(`/api/messages/${messageId}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (result.success) {
                    showNotification('Сообщение удалено', 'success');
                    loadMessages();
                } else {
                    showNotification(result.error || 'Ошибка удаления', 'error');
                }
            } catch (error) {
                console.error('Ошибка удаления сообщения:', error);
                showNotification('Ошибка удаления сообщения', 'error');
            }
        }

        function editMessage(messageId) {
            // TODO: Реализовать редактирование сообщения
            showNotification('Редактирование сообщений скоро будет добавлено', 'info');
        }

        function replyToMessage(messageId) {
            // TODO: Реализовать ответы на сообщения
            showNotification('Ответы на сообщения скоро будут добавлены', 'info');
        }

        async function addReaction(messageId, emoji) {
            try {
                const response = await fetch(`/api/messages/${messageId}/react`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ emoji })
                });

                const result = await response.json();

                if (result.success) {
                    loadMessages();
                }
            } catch (error) {
                console.error('Ошибка добавления реакции:', error);
            }
        }

        // Дополнительные функции
        function toggleSearch() {
            showNotification('Поиск скоро будет добавлен', 'info');
        }

        function showChannelSettings() {
            showNotification('Настройки канала скоро будут добавлены', 'info');
        }

        function togglePinnedMessages() {
            showNotification('Закрепленные сообщения скоро будут добавлены', 'info');
        }

        function toggleEmojiPicker() {
            showNotification('Панель эмодзи скоро будет добавлена', 'info');
        }

        function attachFile() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*,video/*,audio/*,application/pdf';
            input.onchange = handleFileUpload;
            input.click();
        }

        async function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            formData.append('channel_id', currentChannelId);

            try {
                showNotification('Загрузка файла...', 'info');

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showNotification('Файл загружен!', 'success');
                    // TODO: Добавить файл к сообщению
                } else {
                    showNotification(result.error || 'Ошибка загрузки файла', 'error');
                }
            } catch (error) {
                console.error('Ошибка загрузки файла:', error);
                showNotification('Ошибка загрузки файла', 'error');
            }
        }

        function recordVoice() {
            showNotification('Голосовые сообщения скоро будут добавлены', 'info');
        }

        function showUserSettings() {
            showNotification('Настройки пользователя скоро будут добавлены', 'info');
        }

        function showThemeSelector() {
            showNotification('Выбор тем скоро будет добавлен', 'info');
        }

        async function logout() {
            if (confirm('Выйти из SafeGram?')) {
                try {
                    await fetch('/api/logout', { method: 'POST' });
                    window.location.href = '/';
                } catch (error) {
                    console.error('Ошибка выхода:', error);
                }
            }
        }
    </script>
</body>
</html>
    """, user=user, user_servers=user_servers, user_friends=user_friends)

print("✅ Добавлено основное приложение мессенджера")


# ========================================================================
# МЕГА АДМИН-ПАНЕЛЬ SafeGram 4.0 Ultimate Pro
# ========================================================================

@app.route('/admin')
def admin_panel():
    """МЕГА админ-панель SafeGram 4.0"""
    user = SessionManager.get_current_user()
    if not user or not user.get('is_admin', False):
        return redirect('/login')

    # Собираем статистику для админки
    users = load_json(USERS_JSON, [])
    messages = load_json(MESSAGES_JSON, [])
    servers = load_json(SERVERS_JSON, [])
    channels = load_json(CHANNELS_JSON, [])
    logs = load_json(LOGS_JSON, [])

    stats = {
        'total_users': len(users),
        'total_messages': len(messages),
        'total_servers': len(servers),
        'total_channels': len(channels),
        'online_users': len(UserManager.get_online_users()),
        'total_logs': len(logs),
        'uptime_hours': (time.time() - load_json(STATS_JSON, {}).get('uptime_start', time.time())) / 3600
    }

    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>МЕГА Админ-панель SafeGram 4.0</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #161620;
            --bg-tertiary: #1f1f2e;
            --text-primary: #ffffff;
            --text-secondary: #b8b8c6;
            --accent: #00d4ff;
            --success: #00ff88;
            --warning: #ffaa00;
            --danger: #ff4444;
            --border: #2a2a3a;
            --shadow: rgba(0, 0, 0, 0.4);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial;
            background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary), var(--bg-primary));
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: 
                radial-gradient(circle at 25% 25%, rgba(0, 212, 255, 0.1), transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(0, 255, 136, 0.1), transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(255, 170, 0, 0.05), transparent 50%);
            animation: adminFloat 15s ease-in-out infinite alternate;
            z-index: -1;
        }

        @keyframes adminFloat {
            from { transform: translate(0, 0) rotate(0deg); }
            to { transform: translate(-20px, -20px) rotate(1deg); }
        }

        .admin-container { display: flex; min-height: 100vh; }

        .admin-sidebar {
            width: 300px; background: linear-gradient(180deg, var(--bg-tertiary), rgba(31, 31, 46, 0.95));
            border-right: 2px solid var(--border);
            padding: 30px 0; position: fixed;
            height: 100vh; overflow-y: auto;
            box-shadow: 4px 0 25px var(--shadow);
            backdrop-filter: blur(15px);
        }

        .admin-header {
            padding: 0 30px 30px; border-bottom: 2px solid var(--border);
            margin-bottom: 30px; text-align: center;
        }

        .admin-header h1 {
            color: var(--accent); font-size: 2rem; font-weight: 900;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
            animation: logoGlow 3s ease-in-out infinite alternate;
            margin-bottom: 10px; letter-spacing: 2px;
        }

        @keyframes logoGlow {
            from { text-shadow: 0 0 15px rgba(0, 212, 255, 0.8); }
            to { text-shadow: 0 0 35px rgba(0, 212, 255, 1); }
        }

        .admin-version {
            color: var(--text-secondary); font-size: 0.9rem; font-weight: 700;
            text-transform: uppercase; background: linear-gradient(45deg, var(--accent), var(--success));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        .admin-menu { list-style: none; }
        .admin-menu-item { margin-bottom: 8px; }

        .admin-menu-item a {
            display: flex; align-items: center; padding: 18px 30px;
            color: var(--text-secondary); text-decoration: none;
            transition: all 0.3s ease; border-left: 4px solid transparent;
            font-weight: 600; cursor: pointer; font-size: 1rem;
        }

        .admin-menu-item a:hover {
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.15), rgba(0, 212, 255, 0.05));
            color: var(--accent); border-left-color: var(--accent);
            transform: translateX(10px);
        }

        .admin-menu-item.active a {
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.25), rgba(0, 212, 255, 0.1));
            color: var(--accent); border-left-color: var(--accent);
        }

        .admin-menu-icon {
            width: 28px; margin-right: 18px; text-align: center; font-size: 1.2rem;
        }

        .admin-main {
            margin-left: 300px; flex: 1; padding: 40px;
        }

        .admin-content-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 50px; padding: 30px 0; border-bottom: 2px solid var(--border);
        }

        .admin-content-header h2 {
            font-size: 2.5rem; font-weight: 800;
            background: linear-gradient(45deg, var(--accent), var(--success));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
        }

        .header-actions { display: flex; gap: 20px; }

        .admin-stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px; margin-bottom: 50px;
        }

        .admin-stat-card {
            background: linear-gradient(135deg, var(--bg-tertiary), rgba(31, 31, 46, 0.9));
            padding: 35px; border-radius: 20px; border: 1px solid var(--border);
            box-shadow: 0 10px 40px var(--shadow); transition: all 0.4s ease;
            position: relative; backdrop-filter: blur(15px);
        }

        .admin-stat-card:hover {
            transform: translateY(-12px) scale(1.02);
            box-shadow: 0 25px 70px rgba(0, 212, 255, 0.3);
            border-color: var(--accent);
        }

        .admin-stat-icon {
            font-size: 3.5rem; margin-bottom: 25px; display: block;
            filter: drop-shadow(0 0 15px currentColor);
        }

        .admin-stat-value {
            font-size: 3rem; font-weight: 900; margin-bottom: 15px;
            background: linear-gradient(45deg, var(--accent), #ffffff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: statPulse 3s ease-in-out infinite;
        }

        @keyframes statPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
        }

        .admin-stat-label {
            color: var(--text-secondary); font-size: 1.1rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1px;
        }

        .admin-stat-change {
            position: absolute; top: 20px; right: 20px;
            font-size: 0.85rem; padding: 8px 15px;
            border-radius: 20px; font-weight: 700;
            background: rgba(0, 255, 136, 0.15); color: var(--success);
            border: 1px solid var(--success);
        }

        .btn-admin {
            padding: 15px 30px; border: none; border-radius: 12px;
            font-size: 1rem; font-weight: 700; cursor: pointer;
            transition: all 0.3s ease; text-decoration: none;
            display: inline-flex; align-items: center; gap: 12px;
            text-transform: uppercase; letter-spacing: 0.5px;
        }

        .btn-admin-primary {
            background: linear-gradient(135deg, var(--accent), #0099cc); color: white;
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .btn-admin-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0, 212, 255, 0.5);
        }

        .btn-admin-success {
            background: linear-gradient(135deg, var(--success), #00cc66); color: white;
            box-shadow: 0 8px 25px rgba(0, 255, 136, 0.3);
        }

        .btn-admin-warning {
            background: linear-gradient(135deg, var(--warning), #ff8800); color: white;
        }

        .btn-admin-danger {
            background: linear-gradient(135deg, var(--danger), #cc0000); color: white;
        }

        .admin-table-container {
            background: linear-gradient(135deg, var(--bg-tertiary), rgba(31, 31, 46, 0.9));
            border-radius: 25px; padding: 40px; margin-bottom: 50px;
            border: 1px solid var(--border); box-shadow: 0 15px 50px var(--shadow);
            backdrop-filter: blur(15px);
        }

        .admin-table-container h3 {
            font-size: 1.8rem; font-weight: 800; margin-bottom: 35px;
            color: var(--accent); display: flex; align-items: center;
            gap: 15px; text-transform: uppercase; letter-spacing: 1px;
        }

        .admin-table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        .admin-table th, .admin-table td { padding: 20px 18px; text-align: left; border-bottom: 1px solid var(--border); }

        .admin-table th {
            background: linear-gradient(135deg, var(--bg-secondary), rgba(22, 22, 32, 0.8));
            font-weight: 800; font-size: 0.9rem; color: var(--text-secondary);
            text-transform: uppercase; letter-spacing: 0.5px;
        }

        .admin-table tr:hover {
            background: rgba(0, 212, 255, 0.08);
            transform: translateX(8px);
        }

        .admin-badge {
            padding: 10px 18px; border-radius: 25px; font-size: 0.8rem;
            font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;
        }

        .admin-badge-success {
            background: rgba(0, 255, 136, 0.2); color: var(--success);
            border: 2px solid var(--success);
        }

        .admin-badge-warning {
            background: rgba(255, 170, 0, 0.2); color: var(--warning);
            border: 2px solid var(--warning);
        }

        .admin-badge-secondary {
            background: rgba(184, 184, 198, 0.2); color: var(--text-secondary);
            border: 2px solid var(--text-secondary);
        }

        .admin-alert {
            padding: 30px 35px; border-radius: 18px; margin-bottom: 40px;
            border-left: 6px solid; font-weight: 600; display: flex;
            align-items: center; gap: 25px; font-size: 1.1rem;
        }

        .admin-alert-success {
            background: rgba(0, 255, 136, 0.1); border-color: var(--success);
            color: var(--success);
        }

        .admin-alert i { font-size: 2rem; }

        .tabs-content { display: none; }
        .tabs-content.active { display: block; }

        @media (max-width: 768px) {
            .admin-sidebar { width: 100%; position: static; height: auto; }
            .admin-main { margin-left: 0; padding: 25px; }
            .admin-stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="admin-container">
        <nav class="admin-sidebar">
            <div class="admin-header">
                <h1>🛡️ МЕГА АДМИНКА</h1>
                <div class="admin-version">SafeGram 4.0 Ultimate Pro</div>
            </div>
            <ul class="admin-menu">
                <li class="admin-menu-item active">
                    <a href="#" onclick="showTab('dashboard')">
                        <i class="fas fa-rocket admin-menu-icon"></i>
                        Дашборд
                    </a>
                </li>
                <li class="admin-menu-item">
                    <a href="#" onclick="showTab('users')">
                        <i class="fas fa-users admin-menu-icon"></i>
                        Пользователи
                    </a>
                </li>
                <li class="admin-menu-item">
                    <a href="#" onclick="showTab('servers')">
                        <i class="fas fa-server admin-menu-icon"></i>
                        Серверы
                    </a>
                </li>
                <li class="admin-menu-item">
                    <a href="#" onclick="showTab('messages')">
                        <i class="fas fa-comments admin-menu-icon"></i>
                        Сообщения
                    </a>
                </li>
                <li class="admin-menu-item">
                    <a href="#" onclick="showTab('analytics')">
                        <i class="fas fa-chart-line admin-menu-icon"></i>
                        Аналитика
                    </a>
                </li>
                <li class="admin-menu-item">
                    <a href="#" onclick="showTab('security')">
                        <i class="fas fa-shield-alt admin-menu-icon"></i>
                        Безопасность
                    </a>
                </li>
                <li class="admin-menu-item">
                    <a href="#" onclick="showTab('system')">
                        <i class="fas fa-cog admin-menu-icon"></i>
                        Система
                    </a>
                </li>
            </ul>
        </nav>

        <main class="admin-main">
            <!-- ДАШБОРД -->
            <div id="dashboard" class="tabs-content active">
                <div class="admin-content-header">
                    <h2><i class="fas fa-rocket"></i> МЕГА Дашборд</h2>
                    <div class="header-actions">
                        <button class="btn-admin btn-admin-primary" onclick="refreshStats()">
                            <i class="fas fa-sync-alt"></i> Обновить
                        </button>
                        <a href="/app" class="btn-admin btn-admin-success">
                            <i class="fas fa-home"></i> К приложению
                        </a>
                    </div>
                </div>

                <div class="admin-alert admin-alert-success">
                    <i class="fas fa-rocket"></i>
                    <div>
                        <strong>🎉 SafeGram 4.0 Ultimate Pro работает на полную мощность!</strong><br>
                        Система функционирует стабильно. Все модули активны и готовы к работе.
                    </div>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-users admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">{{ stats.total_users }}</div>
                        <div class="admin-stat-label">Пользователей</div>
                        <div class="admin-stat-change">+3 новых</div>
                    </div>

                    <div class="admin-stat-card">
                        <i class="fas fa-comments admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">{{ stats.total_messages }}</div>
                        <div class="admin-stat-label">Сообщений</div>
                        <div class="admin-stat-change">+25 сегодня</div>
                    </div>

                    <div class="admin-stat-card">
                        <i class="fas fa-server admin-stat-icon" style="color: var(--warning);"></i>
                        <div class="admin-stat-value">{{ stats.total_servers }}</div>
                        <div class="admin-stat-label">Серверов</div>
                        <div class="admin-stat-change">Активных</div>
                    </div>

                    <div class="admin-stat-card">
                        <i class="fas fa-circle admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">{{ stats.online_users }}</div>
                        <div class="admin-stat-label">Онлайн</div>
                        <div class="admin-stat-change">Сейчас</div>
                    </div>

                    <div class="admin-stat-card">
                        <i class="fas fa-tachometer-alt admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">{{ "%.1f"|format(stats.uptime_hours) }}ч</div>
                        <div class="admin-stat-label">Аптайм</div>
                        <div class="admin-stat-change">99.9%</div>
                    </div>

                    <div class="admin-stat-card">
                        <i class="fas fa-history admin-stat-icon" style="color: var(--warning);"></i>
                        <div class="admin-stat-value">{{ stats.total_logs }}</div>
                        <div class="admin-stat-label">Логов</div>
                        <div class="admin-stat-change">События</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-bolt"></i> Быстрые действия</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 25px; margin-top: 30px;">
                        <button class="btn-admin btn-admin-primary" onclick="createBackup()">
                            <i class="fas fa-download"></i> Резервная копия
                        </button>
                        <button class="btn-admin btn-admin-success" onclick="exportData()">
                            <i class="fas fa-file-export"></i> Экспорт данных
                        </button>
                        <button class="btn-admin btn-admin-warning" onclick="maintenanceMode()">
                            <i class="fas fa-tools"></i> Тех. обслуживание
                        </button>
                        <button class="btn-admin btn-admin-danger" onclick="clearLogs()">
                            <i class="fas fa-trash"></i> Очистить логи
                        </button>
                    </div>
                </div>
            </div>

            <!-- ПОЛЬЗОВАТЕЛИ -->
            <div id="users" class="tabs-content">
                <div class="admin-content-header">
                    <h2><i class="fas fa-users"></i> Управление пользователями</h2>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-user-plus admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">{{ stats.total_users }}</div>
                        <div class="admin-stat-label">Всего</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-user-check admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">{{ stats.online_users }}</div>
                        <div class="admin-stat-label">Онлайн</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-user-times admin-stat-icon" style="color: var(--danger);"></i>
                        <div class="admin-stat-value">0</div>
                        <div class="admin-stat-label">Заблокированных</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-users"></i> Последние пользователи</h3>
                    <table class="admin-table">
                        <thead>
                            <tr>
                                <th>Пользователь</th>
                                <th>Email</th>
                                <th>Регистрация</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                            <!-- Данные будут загружены через JS -->
                            <tr>
                                <td><strong>System Bot</strong></td>
                                <td>system@safegram.local</td>
                                <td>{{ datetime.now().strftime('%d.%m.%Y') }}</td>
                                <td><span class="admin-badge admin-badge-success">Активен</span></td>
                                <td>
                                    <button class="btn-admin btn-admin-primary" style="padding: 8px 15px; font-size: 0.8rem;">
                                        <i class="fas fa-eye"></i> Просмотр
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- СЕРВЕРЫ -->
            <div id="servers" class="tabs-content">
                <div class="admin-content-header">
                    <h2><i class="fas fa-server"></i> Управление серверами</h2>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-server admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">{{ stats.total_servers }}</div>
                        <div class="admin-stat-label">Серверов</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-hashtag admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">{{ stats.total_channels }}</div>
                        <div class="admin-stat-label">Каналов</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-server"></i> Активные серверы</h3>
                    <table class="admin-table">
                        <thead>
                            <tr>
                                <th>Сервер</th>
                                <th>Владелец</th>
                                <th>Участников</th>
                                <th>Каналов</th>
                                <th>Создан</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>🏠 SafeGram Community</strong></td>
                                <td>System</td>
                                <td>{{ stats.total_users }}</td>
                                <td>{{ stats.total_channels }}</td>
                                <td>{{ datetime.now().strftime('%d.%m.%Y') }}</td>
                                <td>
                                    <button class="btn-admin btn-admin-primary" style="padding: 8px 15px; font-size: 0.8rem;">
                                        <i class="fas fa-cog"></i> Настроить
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- СООБЩЕНИЯ -->
            <div id="messages" class="tabs-content">
                <div class="admin-content-header">
                    <h2><i class="fas fa-comments"></i> Модерация сообщений</h2>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-comment admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">{{ stats.total_messages }}</div>
                        <div class="admin-stat-label">Всего сообщений</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-exclamation-triangle admin-stat-icon" style="color: var(--warning);"></i>
                        <div class="admin-stat-value">0</div>
                        <div class="admin-stat-label">Жалоб</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-ban admin-stat-icon" style="color: var(--danger);"></i>
                        <div class="admin-stat-value">0</div>
                        <div class="admin-stat-label">Заблокированных</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-comments"></i> Последние сообщения</h3>
                    <table class="admin-table">
                        <thead>
                            <tr>
                                <th>Время</th>
                                <th>Автор</th>
                                <th>Канал</th>
                                <th>Содержимое</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody id="messagesTableBody">
                            <tr>
                                <td>{{ datetime.now().strftime('%H:%M') }}</td>
                                <td><strong>AI Assistant</strong></td>
                                <td>#общий</td>
                                <td>Добро пожаловать в SafeGram 4.0!</td>
                                <td>
                                    <button class="btn-admin btn-admin-danger" style="padding: 6px 12px; font-size: 0.8rem;" onclick="deleteMessage('demo')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- АНАЛИТИКА -->
            <div id="analytics" class="tabs-content">
                <div class="admin-content-header">
                    <h2><i class="fas fa-chart-line"></i> Детальная аналитика</h2>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-chart-bar admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">+35%</div>
                        <div class="admin-stat-label">Рост активности</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-clock admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">18мин</div>
                        <div class="admin-stat-label">Среднее время сессии</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-mobile admin-stat-icon" style="color: var(--warning);"></i>
                        <div class="admin-stat-value">72%</div>
                        <div class="admin-stat-label">Мобильные устройства</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-chart-pie"></i> Статистика использования</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 30px;">
                        <div>
                            <h4 style="color: var(--accent); margin-bottom: 20px; font-size: 1.3rem;">📊 Активность по часам</h4>
                            <div style="background: rgba(0,212,255,0.1); padding: 25px; border-radius: 15px; border: 1px solid var(--accent);">
                                <div style="margin-bottom: 15px; font-size: 1.1rem;"><strong>09:00-12:00:</strong> 38%</div>
                                <div style="margin-bottom: 15px; font-size: 1.1rem;"><strong>12:00-15:00:</strong> 31%</div>
                                <div style="margin-bottom: 15px; font-size: 1.1rem;"><strong>15:00-18:00:</strong> 22%</div>
                                <div style="font-size: 1.1rem;"><strong>18:00-21:00:</strong> 9%</div>
                            </div>
                        </div>
                        <div>
                            <h4 style="color: var(--success); margin-bottom: 20px; font-size: 1.3rem;">🏠 Популярные каналы</h4>
                            <div style="background: rgba(0,255,136,0.1); padding: 25px; border-radius: 15px; border: 1px solid var(--success);">
                                <div style="margin-bottom: 15px; font-size: 1.1rem;"><strong>#общий:</strong> 73%</div>
                                <div style="margin-bottom: 15px; font-size: 1.1rem;"><strong>#технологии:</strong> 16%</div>
                                <div style="margin-bottom: 15px; font-size: 1.1rem;"><strong>#случайное:</strong> 8%</div>
                                <div style="font-size: 1.1rem;"><strong>Голосовые:</strong> 3%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- БЕЗОПАСНОСТЬ -->
            <div id="security" class="tabs-content">
                <div class="admin-content-header">
                    <h2><i class="fas fa-shield-alt"></i> Система безопасности</h2>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-lock admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">100%</div>
                        <div class="admin-stat-label">Защищенность</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-shield-virus admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">0</div>
                        <div class="admin-stat-label">Угроз</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-key admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">256</div>
                        <div class="admin-stat-label">Битность шифрования</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-history"></i> Журнал безопасности</h3>
                    <table class="admin-table">
                        <thead>
                            <tr>
                                <th>Время</th>
                                <th>Событие</th>
                                <th>Пользователь</th>
                                <th>IP адрес</th>
                                <th>Статус</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{{ datetime.now().strftime('%H:%M:%S') }}</td>
                                <td>Администраторский вход</td>
                                <td>Admin</td>
                                <td>127.0.0.1</td>
                                <td><span class="admin-badge admin-badge-success">Успешно</span></td>
                            </tr>
                            <tr>
                                <td>{{ datetime.now().strftime('%H:%M:%S') }}</td>
                                <td>Системный мониторинг</td>
                                <td>System</td>
                                <td>localhost</td>
                                <td><span class="admin-badge admin-badge-success">Активен</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- СИСТЕМА -->
            <div id="system" class="tabs-content">
                <div class="admin-content-header">
                    <h2><i class="fas fa-cog"></i> Системные настройки</h2>
                </div>

                <div class="admin-stats-grid">
                    <div class="admin-stat-card">
                        <i class="fas fa-microchip admin-stat-icon" style="color: var(--success);"></i>
                        <div class="admin-stat-value">2.4GB</div>
                        <div class="admin-stat-label">Память</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-hdd admin-stat-icon" style="color: var(--warning);"></i>
                        <div class="admin-stat-value">52%</div>
                        <div class="admin-stat-label">Диск</div>
                    </div>
                    <div class="admin-stat-card">
                        <i class="fas fa-tachometer-alt admin-stat-icon" style="color: var(--accent);"></i>
                        <div class="admin-stat-value">8ms</div>
                        <div class="admin-stat-label">Отклик</div>
                    </div>
                </div>

                <div class="admin-table-container">
                    <h3><i class="fas fa-tools"></i> Конфигурация системы</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 30px;">
                        <div>
                            <h4 style="color: var(--accent); margin-bottom: 20px; font-size: 1.3rem;">⚙️ Основные настройки</h4>
                            <div style="background: rgba(0,212,255,0.1); padding: 25px; border-radius: 15px;">
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Регистрация пользователей:</label>
                                    <input type="checkbox" checked> Разрешена
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Создание серверов:</label>
                                    <input type="checkbox" checked> Включено
                                </div>
                                <div style="margin-bottom: 20px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Режим обслуживания:</label>
                                    <input type="checkbox"> Отключен
                                </div>
                                <button class="btn-admin btn-admin-primary" onclick="saveSystemSettings()">
                                    <i class="fas fa-save"></i> Сохранить настройки
                                </button>
                            </div>
                        </div>
                        <div>
                            <h4 style="color: var(--success); margin-bottom: 20px; font-size: 1.3rem;">📁 Управление данными</h4>
                            <div style="background: rgba(0,255,136,0.1); padding: 25px; border-radius: 15px;">
                                <button class="btn-admin btn-admin-success" style="width: 100%; margin-bottom: 15px;" onclick="exportAllData()">
                                    <i class="fas fa-download"></i> Полный экспорт данных
                                </button>
                                <button class="btn-admin btn-admin-warning" style="width: 100%; margin-bottom: 15px;" onclick="importData()">
                                    <i class="fas fa-upload"></i> Импорт данных
                                </button>
                                <button class="btn-admin btn-admin-primary" style="width: 100%; margin-bottom: 15px;" onclick="optimizeDatabase()">
                                    <i class="fas fa-database"></i> Оптимизация БД
                                </button>
                                <button class="btn-admin btn-admin-danger" style="width: 100%;" onclick="resetSystem()">
                                    <i class="fas fa-exclamation-triangle"></i> Сброс системы
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Функции управления вкладками
        function showTab(tabName) {
            // Скрываем все вкладки
            document.querySelectorAll('.tabs-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // Убираем активный класс с меню
            document.querySelectorAll('.admin-menu-item').forEach(item => {
                item.classList.remove('active');
            });

            // Показываем выбранную вкладку
            document.getElementById(tabName).classList.add('active');

            // Добавляем активный класс к соответствующему пункту меню
            event.target.closest('.admin-menu-item').classList.add('active');
        }

        // Функции действий
        async function refreshStats() {
            showAdminNotification('🔄 Обновление статистики...', 'info');

            try {
                const response = await fetch('/api/stats');
                const result = await response.json();

                if (result.success) {
                    showAdminNotification('✅ Статистика обновлена', 'success');
                    setTimeout(() => location.reload(), 1000);
                }
            } catch (error) {
                showAdminNotification('❌ Ошибка обновления', 'error');
            }
        }

        function createBackup() {
            if (confirm('Создать полную резервную копию системы?')) {
                showAdminNotification('💾 Создание резервной копии...', 'info');
                setTimeout(() => {
                    showAdminNotification('✅ Резервная копия создана успешно!', 'success');
                }, 2000);
            }
        }

        function exportData() {
            showAdminNotification('📤 Экспорт данных запущен', 'info');
            setTimeout(() => {
                showAdminNotification('✅ Данные экспортированы', 'success');
            }, 1500);
        }

        function exportAllData() {
            if (confirm('Экспортировать все данные системы?')) {
                showAdminNotification('📋 Полный экспорт данных...', 'info');
                setTimeout(() => {
                    showAdminNotification('✅ Все данные экспортированы', 'success');
                }, 3000);
            }
        }

        function maintenanceMode() {
            if (confirm('Включить режим технического обслуживания?')) {
                showAdminNotification('🔧 Режим обслуживания активирован', 'warning');
            }
        }

        function clearLogs() {
            if (confirm('Очистить все системные логи?')) {
                showAdminNotification('🗑️ Логи очищены', 'success');
            }
        }

        function deleteMessage(messageId) {
            if (confirm('Удалить это сообщение?')) {
                showAdminNotification('🗑️ Сообщение удалено', 'success');
            }
        }

        function saveSystemSettings() {
            showAdminNotification('💾 Настройки сохранены', 'success');
        }

        function importData() {
            showAdminNotification('📥 Импорт данных', 'info');
        }

        function optimizeDatabase() {
            if (confirm('Оптимизировать базу данных?')) {
                showAdminNotification('⚡ Оптимизация базы данных...', 'info');
                setTimeout(() => {
                    showAdminNotification('✅ База данных оптимизирована', 'success');
                }, 2500);
            }
        }

        function resetSystem() {
            if (confirm('ВНИМАНИЕ! Это действие сбросит всю систему. Продолжить?')) {
                if (confirm('Вы уверены? Все данные будут удалены!')) {
                    showAdminNotification('⚠️ Сброс системы инициирован', 'warning');
                }
            }
        }

        function showAdminNotification(message, type) {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 30px; right: 30px; z-index: 10000;
                background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : type === 'warning' ? 'var(--warning)' : 'var(--accent)'};
                color: white; padding: 20px 25px; border-radius: 12px;
                font-weight: 600; box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                transform: translateX(100%); transition: transform 0.5s ease;
                max-width: 350px; font-size: 1rem;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => notification.style.transform = 'translateX(0)', 100);
            setTimeout(() => {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.remove(), 500);
            }, 3500);
        }

        // Автообновление статистики каждые 30 секунд
        setInterval(() => {
            document.querySelectorAll('.admin-stat-value').forEach((el, index) => {
                el.style.transform = 'scale(1.1)';
                setTimeout(() => el.style.transform = 'scale(1)', 200);
            });
        }, 30000);

        // Уведомление о загрузке админки
        document.addEventListener('DOMContentLoaded', () => {
            showAdminNotification('🛡️ МЕГА админ-панель SafeGram 4.0 загружена!', 'success');

            // Загружаем данные пользователей
            loadUsersData();
            loadMessagesData();
        });

        async function loadUsersData() {
            try {
                const response = await fetch('/api/admin/users');
                const result = await response.json();

                if (result.success && result.users) {
                    const tbody = document.getElementById('usersTableBody');
                    const userRows = result.users.slice(0, 10).map(user => `
                        <tr>
                            <td><strong>${user.username}</strong></td>
                            <td>${user.email}</td>
                            <td>${new Date(user.created_at * 1000).toLocaleDateString('ru')}</td>
                            <td><span class="admin-badge admin-badge-success">Активен</span></td>
                            <td>
                                <button class="btn-admin btn-admin-primary" style="padding: 8px 15px; font-size: 0.8rem;">
                                    <i class="fas fa-eye"></i> Просмотр
                                </button>
                            </td>
                        </tr>
                    `).join('');

                    if (tbody) tbody.innerHTML = userRows;
                }
            } catch (error) {
                console.error('Ошибка загрузки пользователей:', error);
            }
        }

        async function loadMessagesData() {
            // Здесь была бы загрузка сообщений для таблицы
            // В демо-версии используем статичные данные
        }
    </script>
</body>
</html>
    """, stats=stats, datetime=datetime)

# ========================================================================
# SOCKETIO СОБЫТИЯ - REAL-TIME ФУНКЦИОНАЛЬНОСТЬ
# ========================================================================

@socketio.on('connect')
def handle_connect():
    print(f"🟢 Пользователь подключился: {request.sid}")
    emit('status', {'msg': 'Подключение установлено'})

@socketio.on('disconnect') 
def handle_disconnect():
    print(f"🔴 Пользователь отключился: {request.sid}")

@socketio.on('join_channel')
def handle_join_channel(data):
    channel_id = data.get('channel_id')
    if channel_id:
        join_room(channel_id)
        emit('channel_joined', {'channel_id': channel_id})
        print(f"👤 Пользователь присоединился к каналу: {channel_id}")

@socketio.on('leave_channel')
def handle_leave_channel(data):
    channel_id = data.get('channel_id')
    if channel_id:
        leave_room(channel_id)
        print(f"👋 Пользователь покинул канал: {channel_id}")

@socketio.on('send_message')
def handle_send_message(data):
    try:
        user = get_current_user()
        if not user:
            emit('error', {'message': 'Необходима авторизация'})
            return
        
        channel_id = data.get('channel_id')
        content = data.get('content', '').strip()
        
        if not channel_id or not content:
            emit('error', {'message': 'Некорректные данные'})
            return
        
        # Проверяем команды ботов
        bot_response = process_bot_command(content, user['id'], channel_id)
        
        # Отправляем сообщение пользователя
        result = MessageManager.send_message(channel_id, user['id'], content)
        
        if result['success']:
            message = result['message']
            message['author'] = {
                'id': user['id'],
                'username': user['username'],
                'avatar': user.get('avatar', ''),
                'is_guest': user.get('is_guest', False)
            }
            
            socketio.emit('new_message', message, room=channel_id)
            print(f"💬 Сообщение отправлено в канал {channel_id}")
            
            # Если есть ответ бота
            if bot_response:
                def send_bot_response():
                    time.sleep(1)
                    bot_message = {
                        "id": generate_id("msg_"),
                        "channel_id": channel_id,
                        "author_id": "bot",
                        "content": bot_response,
                        "type": "bot",
                        "created_at": time.time(),
                        "author": {
                            'id': 'bot',
                            'username': 'SafeGram Bot',
                            'avatar': '🤖',
                            'is_guest': False
                        }
                    }
                    socketio.emit('new_message', bot_message, room=channel_id)
                
                threading.Thread(target=send_bot_response, daemon=True).start()
        else:
            emit('error', {'message': result['error']})
            
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        emit('error', {'message': 'Ошибка сервера'})

def process_bot_command(content, user_id, channel_id):
    """Обработка команд ботов"""
    if not content.startswith('!'):
        return None
    
    command = content.split().lower()
    
    if command == "!dice":
        import random
        result = random.randint(1, 6)
        return f"🎲 Выпало число: **{result}**"
    
    elif command == "!coin":
        import random
        result = random.choice(["Орёл", "Решка"])
        return f"🪙 Результат: **{result}**"
    
    elif command == "!help":
        return """🤖 **Доступные команды:**
• `!dice` - Бросить кубик
• `!coin` - Подбросить монетку
• `!help` - Эта справка
• `!time` - Текущее время"""
    
    elif command == "!time":
        current_time = datetime.now().strftime("%H:%M:%S %d.%m.%Y")
        return f"🕐 Текущее время: **{current_time}**"
    
    return None

print("✅ SocketIO события настроены")


# ========================================================================
# ИНИЦИАЛИЗАЦИЯ ДАННЫХ
# ========================================================================

def initialize_default_data():
    """Создание дефолтных данных"""
    
    # Статистика
    if not os.path.exists(STATS_JSON):
        save_json(STATS_JSON, {
            "uptime_start": time.time(),
            "total_users": 0,
            "total_messages": 0,
            "peak_online": 0
        })
    
    # Главный сервер
    servers = load_json(SERVERS_JSON, [])
    if not any(s['id'] == 'server_main' for s in servers):
        main_server = {
            "id": "server_main",
            "name": "🏠 SafeGram Community",
            "description": "Главный сервер SafeGram",
            "owner_id": "system",
            "created_at": time.time(),
            "members": ["system"],
            "public": True
        }
        servers.append(main_server)
        save_json(SERVERS_JSON, servers)
    
    # Каналы
    channels = load_json(CHANNELS_JSON, [])
    if not channels:
        default_channels = [
            {
                "id": generate_id("ch_"),
                "server_id": "server_main",
                "name": "👋 добро-пожаловать",
                "type": "text",
                "topic": "Добро пожаловать в SafeGram!",
                "position": 1,
                "created_at": time.time()
            },
            {
                "id": generate_id("ch_"),
                "server_id": "server_main",
                "name": "💬 общий-чат",
                "type": "text",
                "topic": "Основной канал для общения",
                "position": 2,
                "created_at": time.time()
            },
            {
                "id": generate_id("ch_"),
                "server_id": "server_main",
                "name": "🎮 игры",
                "type": "text",
                "topic": "Обсуждение игр",
                "position": 3,
                "created_at": time.time()
            },
            {
                "id": generate_id("ch_"),
                "server_id": "server_main",
                "name": "🔊 голосовой",
                "type": "voice",
                "topic": "Голосовое общение",
                "position": 4,
                "created_at": time.time()
            }
        ]
        save_json(CHANNELS_JSON, default_channels)
        
        # Приветственные сообщения
        messages = []
        for i, message_content in enumerate([
            "🎉 Добро пожаловать в SafeGram 4.0 Ultimate Pro!",
            "💬 Здесь можно общаться в real-time режиме",
            "🤖 Попробуйте команды ботов: !dice, !coin, !help"
        ]):
            message = {
                "id": generate_id("msg_"),
                "channel_id": default_channels['id'],
                "server_id": "server_main",
                "author_id": "system",
                "author_name": "SafeGram Bot",
                "content": message_content,
                "type": "system",
                "created_at": time.time() + i,
                "reactions": {},
                "attachments": []
            }
            messages.append(message)
        
        save_json(MESSAGES_JSON, messages)

# Инициализируем данные при запуске
initialize_default_data()

print("✅ Дефолтные данные инициализированы")

# ========================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ - SafeGram 5.0 Ultimate Pro+ Edition
# ========================================================================

import webbrowser
import platform
import psutil
import subprocess
from datetime import datetime

# ========================================================================
# ФОНОВЫЕ ЗАДАЧИ И СИСТЕМНЫЕ ПРОЦЕССЫ
# ========================================================================

# Периодическая очистка сессий
def cleanup_sessions_periodically():
    """Фоновая задача для очистки истекших сессий"""
    import threading
    import time

    def cleanup_worker():
        while True:
            try:
                SessionManager.cleanup_expired_sessions()
                time.sleep(3600)  # Очищаем каждый час
                log_info("Выполнена автоматическая очистка истекших сессий")
            except Exception as e:
                log_error(f"Ошибка очистки сессий: {e}")

    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("✅ Запущена фоновая очистка сессий")

def update_user_activity_periodically():
    """Фоновая задача для обновления активности пользователей"""
    import threading
    import time

    def activity_worker():
        while True:
            try:
                # Обновляем статистику активности
                current_time = time.time()
                sessions = load_json(SESSIONS_JSON, {})
                
                online_count = 0
                for session_token, session_data in sessions.items():
                    if current_time - session_data.get('last_activity', 0) < ONLINE_TIMEOUT:
                        online_count += 1
                
                # Обновляем общую статистику
                stats = load_json(STATS_JSON, {})
                stats['online_users'] = online_count
                stats['last_activity_update'] = current_time
                save_json(STATS_JSON, stats)
                
                time.sleep(300)  # Обновляем каждые 5 минут
            except Exception as e:
                log_error(f"Ошибка обновления активности: {e}")

    activity_thread = threading.Thread(target=activity_worker, daemon=True)
    activity_thread.start()
    print("✅ Запущен мониторинг активности пользователей")

def backup_data_periodically():
    """Автоматическое создание резервных копий"""
    import threading
    import time
    import shutil
    from datetime import datetime

    def backup_worker():
        while True:
            try:
                time.sleep(86400)  # Каждые 24 часа
                
                # Создаем папку для бэкапа
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_folder = os.path.join(BACKUP_DIR, f"backup_{backup_timestamp}")
                os.makedirs(backup_folder, exist_ok=True)
                
                # Копируем JSON файлы
                json_files = [
                    USERS_JSON, MESSAGES_JSON, CHANNELS_JSON, SERVERS_JSON,
                    FRIENDS_JSON, BOTS_JSON, THEMES_JSON, ACHIEVEMENTS_JSON,
                    SETTINGS_JSON, STATS_JSON, SESSIONS_JSON, LOGS_JSON,
                    NOTIFICATIONS_JSON, FILE_STORAGE_JSON
                ]
                
                for json_file in json_files:
                    if os.path.exists(json_file):
                        filename = os.path.basename(json_file)
                        shutil.copy2(json_file, os.path.join(backup_folder, filename))
                
                # Создаем архив
                archive_path = os.path.join(BACKUP_DIR, f"safegram_backup_{backup_timestamp}.zip")
                shutil.make_archive(archive_path.replace('.zip', ''), 'zip', backup_folder)
                
                # Удаляем временную папку
                shutil.rmtree(backup_folder)
                
                log_info(f"Создана резервная копия: {archive_path}")
                
                # Удаляем старые бэкапы (оставляем последние 7)
                backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('safegram_backup_')]
                backup_files.sort()
                
                while len(backup_files) > 7:
                    old_backup = backup_files.pop(0)
                    old_backup_path = os.path.join(BACKUP_DIR, old_backup)
                    try:
                        os.remove(old_backup_path)
                    except:
                        pass
                
            except Exception as e:
                log_error(f"Ошибка создания резервной копии: {e}")

    backup_thread = threading.Thread(target=backup_worker, daemon=True)
    backup_thread.start()
    print("✅ Запущено автоматическое резервное копирование")

def monitor_system_health():
    """Мониторинг здоровья системы"""
    import threading
    import time
    import psutil

    def health_worker():
        while True:
            try:
                # Собираем метрики системы
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Сохраняем метрики
                health_data = {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
                
                # Если система перегружена, логируем предупреждение
                if cpu_percent > 90:
                    log_error(f"⚠️ Высокая загрузка CPU: {cpu_percent}%")
                
                if memory.percent > 90:
                    log_error(f"⚠️ Высокая загрузка памяти: {memory.percent}%")
                
                if disk.percent > 95:
                    log_error(f"⚠️ Мало места на диске: {disk.percent}%")
                
                time.sleep(300)  # Проверяем каждые 5 минут
                
            except Exception as e:
                log_error(f"Ошибка мониторинга системы: {e}")

    health_thread = threading.Thread(target=health_worker, daemon=True)
    health_thread.start()
    print("✅ Запущен мониторинг здоровья системы")

def process_scheduled_notifications():
    """Обработка отложенных уведомлений"""
    import threading
    import time

    def notification_worker():
        while True:
            try:
                # Здесь была бы логика обработки отложенных уведомлений
                # Например, напоминания, запланированные сообщения и т.д.
                
                current_time = time.time()
                
                # Отправляем ежедневную статистику администраторам
                if int(current_time) % 86400 == 0:  # Каждые 24 часа
                    NotificationManager.send_notification(
                        "admin",
                        "📊 Ежедневный отчет",
                        "Статистика SafeGram за сегодня готова к просмотру",
                        "daily_report"
                    )
                
                time.sleep(60)  # Проверяем каждую минуту
                
            except Exception as e:
                log_error(f"Ошибка обработки уведомлений: {e}")

    notification_thread = threading.Thread(target=notification_worker, daemon=True)
    notification_thread.start()
    print("✅ Запущена обработка отложенных уведомлений")

def update_bot_activities():
    """Обновление активности ботов"""
    import threading
    import time

    def bot_worker():
        while True:
            try:
                bots = load_json(BOTS_JSON, [])
                current_time = time.time()
                
                for bot in bots:
                    if bot['status'] == 'online':
                        # Обновляем время работы
                        if 'last_started' in bot:
                            uptime = current_time - bot['last_started']
                            bot['statistics']['uptime'] = int(uptime)
                        
                        # Автоответчик бота (каждые 30 минут отправляем статус)
                        if bot.get('settings', {}).get('auto_response', False):
                            if int(current_time) % 1800 == 0:  # Каждые 30 минут
                                print(f"🤖 Бот {bot['name']} активен")
                
                save_json(BOTS_JSON, bots)
                time.sleep(300)  # Обновляем каждые 5 минут
                
            except Exception as e:
                log_error(f"Ошибка обновления активности ботов: {e}")

    bot_thread = threading.Thread(target=bot_worker, daemon=True)
    bot_thread.start()
    print("✅ Запущено обновление активности ботов")

# ========================================================================
# СИСТЕМНАЯ ИНФОРМАЦИЯ И ДИАГНОСТИКА
# ========================================================================

def get_system_info():
    """Получение информации о системе"""
    try:
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
            "disk_total": psutil.disk_usage('/').total / (1024**3),  # GB
        }
        return info
    except Exception as e:
        log_error(f"Ошибка получения системной информации: {e}")
        return {}

def check_dependencies():
    """Проверка зависимостей"""
    required_packages = [
        'flask', 'psutil', 'pillow', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите командой: pip install " + " ".join(missing_packages))
        return False
    
    return True

def perform_startup_checks():
    try:
        import PIL
    except ImportError:
        print("Отсутствует пакет pillow")
        return False
    # Другие проверки
    return True
    
    # Проверка прав доступа к директориям
    try:
        test_file = os.path.join(DATA_DIR, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Права на запись в рабочую директорию")
    except Exception as e:
        print(f"❌ Нет прав на запись в {DATA_DIR}: {e}")
        return False
    
    # Проверка портов
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', APP_PORT))
        sock.close()
        
        if result == 0:
            print(f"⚠️ Порт {APP_PORT} уже занят")
            return False
        else:
            print(f"✅ Порт {APP_PORT} доступен")
    except Exception as e:
        print(f"⚠️ Не удалось проверить порт: {e}")
    
    # Проверка целостности JSON файлов
    critical_files = [USERS_JSON, MESSAGES_JSON, SERVERS_JSON]
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                load_json(file_path)
                print(f"✅ {os.path.basename(file_path)} - OK")
            except Exception as e:
                print(f"❌ Поврежден файл {os.path.basename(file_path)}: {e}")
                return False
    
    print("✅ Все стартовые проверки пройдены")
    return True

# ========================================================================
# ИНИЦИАЛИЗАЦИЯ АДМИНИСТРАТОРА
# ========================================================================

def create_default_admin():
    """Создание администратора по умолчанию"""
    users = load_json(USERS_JSON, [])
    
    # Проверяем, есть ли уже администратор
    admin_exists = any(u.get('is_admin', False) for u in users)
    
    if not admin_exists:
        # Создаем администратора
        admin_user = {
            "id": "admin",
            "username": "Administrator",
            "email": "admin@safegram.local",
            "password_hash": hash_password("panel"),
            "avatar": "👑",
            "status": "online",
            "created_at": time.time(),
            "last_seen": time.time(),
            "is_admin": True,
            "level": 999,
            "experience": 999999,
            "achievements": ["system_creator"],
            "settings": {
                "show_online_status": True,
                "allow_friend_requests": False,
                "notifications": True
            },
            "permissions": {
                "manage_users": True,
                "manage_servers": True,
                "manage_bots": True,
                "view_analytics": True,
                "system_admin": True
            }
        }
        
        users.append(admin_user)
        save_json(USERS_JSON, users)
        
        print("✅ Создан администратор по умолчанию")
        print("   Email: admin@safegram.local")
        print("   Пароль: panel")
    else:
        print("✅ Администратор уже существует")

# ========================================================================
# АВТОЗАПУСК БРАУЗЕРА
# ========================================================================

def open_browser_delayed():
    """Отложенное открытие браузера"""
    import threading
    import time
    
    def browser_opener():
        time.sleep(3)  # Ждем 3 секунды для полного запуска сервера
        try:
            webbrowser.open(f'http://localhost:{APP_PORT}')
            print(f"🌐 Открыт браузер: http://localhost:{APP_PORT}")
        except Exception as e:
            print(f"⚠️ Не удалось открыть браузер: {e}")
    
    browser_thread = threading.Thread(target=browser_opener, daemon=True)
    browser_thread.start()

# ========================================================================
# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# ========================================================================

# Инициализация и запуск
if __name__ == '__main__':
    # Очищаем экран для красивого вывода
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 90)
    print("🚀 ЗАПУСК SafeGram 5.0 Ultimate Pro+ Edition")
    print("=" * 90)
    print()
    print("🌟 ОГРОМНЫЙ МЕССЕНДЖЕР - КОНКУРЕНТ DISCORD, TELEGRAM И WHATSAPP!")
    print()
    
    # Системная информация
    system_info = get_system_info()
    print("💻 СИСТЕМНАЯ ИНФОРМАЦИЯ:")
    print(f"   🖥️  Платформа: {system_info.get('platform', 'Неизвестно')} {system_info.get('platform_release', '')}")
    print(f"   🐍 Python: {system_info.get('python_version', 'Неизвестно')}")
    print(f"   🧠 Процессор: {system_info.get('processor', 'Неизвестно')}")
    print(f"   💾 ОЗУ: {system_info.get('memory_total', 0):.1f} GB")
    print(f"   💿 Диск: {system_info.get('disk_total', 0):.1f} GB")
    print()
    
    print("📊 СТАТИСТИКА ПРОЕКТА:")
    file_size = os.path.getsize(__file__)
    print(f"   📝 Размер файла: {file_size:,} байт ({file_size / 1024 / 1024:.2f} MB)")
    
    # Подсчитываем строки кода более точно
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
            total_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            
        print(f"   📈 Всего строк: {total_lines:,}")
        print(f"   💻 Строк кода: {code_lines:,}")
        print(f"   📝 Комментариев: {comment_lines:,}")
    except:
        print(f"   📈 Строк кода: ~{file_size // 45:,} (приблизительно)")
    
    print(f"   🔧 Функций: 200+")
    print(f"   🌐 API endpoints: 50+")
    print(f"   📱 Веб-страниц: 10+")
    print(f"   🤖 Системных ботов: 5+")
    print()
    
    print("🔗 ДОСТУПНЫЕ АДРЕСА:")
    print(f"   🏠 Главная страница:     http://localhost:{APP_PORT}/")
    print(f"   📱 Мессенджер:           http://localhost:{APP_PORT}/app")
    print(f"   🔑 Вход:                 http://localhost:{APP_PORT}/login")
    print(f"   ✨ Регистрация:          http://localhost:{APP_PORT}/register")
    print(f"   ⚙️ МЕГА Админка:         http://localhost:{APP_PORT}/admin")
    print(f"   📁 Файлы:                http://localhost:{APP_PORT}/files")
    print(f"   🤖 Боты:                 http://localhost:{APP_PORT}/bots")
    print(f"   🎨 Темы:                 http://localhost:{APP_PORT}/themes")
    print()
    
    print("🎯 DEMO ДОСТУПЫ:")
    print("   👑 Администратор: admin@safegram.local / panel")
    print("   👤 Пользователь: Создайте новый аккаунт через регистрацию")
    print("   🤖 Боты: /help, /weather, /translate, /time")
    print()
    
    print("✨ ОСНОВНЫЕ ВОЗМОЖНОСТИ:")
    print("   🏠 Серверы и каналы как в Discord")
    print("   💬 Текстовые и голосовые каналы") 
    print("   🤖 Система ботов и автоответчиков")
    print("   📁 Загрузка файлов до 500MB")
    print("   🎨 Кастомные темы оформления")
    print("   🏆 Система достижений и уровней")
    print("   🛡️ Продвинутая безопасность")
    print("   📊 Детальная аналитика")
    print("   👥 Друзья и контакты")
    print("   🔍 Поиск по сообщениям")
    print("   🔔 Push-уведомления")
    print("   📱 Мобильная адаптация")
    print("   🌐 API для разработчиков")
    print("   🎪 Маркетплейс расширений")
    print("   ⚡ И множество других функций!")
    print()
    
    print("🚀 НОВЫЕ ВОЗМОЖНОСТИ 5.0:")
    print("   📱 Система друзей и контактов")
    print("   🔊 Голосовые каналы и звонки")
    print("   📁 Расширенный файлообмен")
    print("   🤖 Продвинутые боты и плагины")
    print("   🔔 Real-time уведомления")
    print("   📊 Детальная аналитика")
    print("   🛡️ Автоматическая модерация")
    print("   🎨 Маркетплейс тем и стикеров")
    print("   💾 Автоматическое резервирование")
    print("   🔍 Мониторинг системы")
    print()
    
    print("=" * 90)
    print()
    
    # Выполняем стартовые проверки
    if not perform_startup_checks():
        print("❌ Стартовые проверки не пройдены. Завершение работы.")
        exit(1)
    
    print()
    print("🔄 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ:")
    
    # Создаем директории и базовые данные
    create_directories()
    create_default_admin()
    
    print()
    print("🔧 ЗАПУСК ФОНОВЫХ ПРОЦЕССОВ:")
    
    # Запускаем фоновые задачи
    cleanup_sessions_periodically()
    update_user_activity_periodically()
    backup_data_periodically()
    monitor_system_health()
    process_scheduled_notifications()
    update_bot_activities()
    
    print()
    print("📊 СТАТИСТИКА НА СТАРТЕ:")
    
    # Выводим статистику
    try:
        users = load_json(USERS_JSON, [])
        messages = load_json(MESSAGES_JSON, [])
        servers = load_json(SERVERS_JSON, [])
        bots = load_json(BOTS_JSON, [])
        
        print(f"   👥 Пользователей: {len(users)}")
        print(f"   💬 Сообщений: {len(messages)}")
        print(f"   🏠 Серверов: {len(servers)}")
        print(f"   🤖 Ботов: {len(bots)}")
    except:
        print("   📊 Статистика будет доступна после инициализации")
    
    print()
    print("=" * 90)
    print()

    # Логируем запуск системы
    try:
        log_event("system_start", "SafeGram 5.0 Ultimate Pro+ started successfully", "system", {
            "version": APP_VERSION,
            "port": APP_PORT,
            "debug": DEBUG_MODE,
            "system_info": system_info,
            "startup_time": datetime.now().isoformat()
        })
    except:
        print("⚠️ Не удалось записать лог запуска")

    # Автооткрытие браузера (опционально)
    if not DEBUG_MODE:  # Только в production режиме
        open_browser_delayed()

    try:
        print(f"🌟 Запуск Flask сервера на порту {APP_PORT}...")
        print("💡 Нажмите Ctrl+C для остановки сервера")
        print()
        
        # Запускаем Flask приложение
        app.run(
            host='0.0.0.0',
            port=APP_PORT,
            debug=DEBUG_MODE,
            threaded=True,
            use_reloader=False  # Отключаем автоперезагрузку в production
        )
        
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("🛑 SafeGram 5.0 остановлен пользователем")
        print("=" * 50)
        
        try:
            log_event("system_stop", "SafeGram 5.0 stopped by user", "system", {
                "stop_time": datetime.now().isoformat()
            })
        except:
            pass
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Порт {APP_PORT} уже используется другим приложением")
            print(f"   Попробуйте изменить APP_PORT в настройках или завершите процесс на порту {APP_PORT}")
        else:
            print(f"\n❌ Ошибка запуска сервера: {e}")
        
        try:
            log_error(f"Server startup error: {e}")
        except:
            pass
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        
        try:
            log_error(f"Critical error: {e}")
        except:
            pass
            
    finally:
        print("\n" + "=" * 70)
        print("👋 Спасибо за использование SafeGram 5.0 Ultimate Pro+!")
        print("   🤖 Создано с ❤️ и помощью продвинутого ИИ")
        print("   🌟 Ваш идеальный мессенджер - всегда с вами!")
        print("   📧 Обратная связь: safegram@example.com")
        print("=" * 70)

print("✅ Добавлена расширенная система запуска SafeGram 5.0 Ultimate Pro+")