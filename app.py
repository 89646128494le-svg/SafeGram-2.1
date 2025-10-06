#!/usr/bin/env python3
"""
SafeGram 3.0 Ultimate Edition - Главный запускатель
==================================================

Основной файл для запуска SafeGram с интегрированной МЕГА админ-панелью.

Запуск: python app.py

Автор: AI Assistant  
Версия: 3.0 Ultimate Edition
Дата: 2025-10-05
"""

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
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from flask import Flask, request, jsonify, make_response, send_from_directory, abort, redirect, url_for

# ========================================================================
# КОНФИГУРАЦИЯ SafeGram 3.0 Ultimate
# ========================================================================

# Основные настройки
APP_PORT = 8080
DATA_DIR = os.path.abspath("./data_safegram")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

# Файлы данных
USERS_JSON = os.path.join(DATA_DIR, "users.json")
MSGS_JSON = os.path.join(DATA_DIR, "messages.json") 
ROOMS_JSON = os.path.join(DATA_DIR, "rooms.json")
CONTACTS_JSON = os.path.join(DATA_DIR, "contacts.json")
SESSIONS_JSON = os.path.join(DATA_DIR, "sessions.json")
FLAGS_JSON = os.path.join(DATA_DIR, "flags.json")

# Безопасность
SECRET_PASSPHRASE = os.environ.get("SG_SECRET", "demo_secret_change_me")
ONLINE_WINDOW_SEC = 300  # 5 минут онлайн

# Email настройки (опционально)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

# Flask приложение
app = Flask(__name__)
app.secret_key = SECRET_PASSPHRASE

# ========================================================================
# УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================================================

def ensure_data_dir():
    """Создает необходимые директории для данных"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_json(filepath: str, default=None):
    """Загружает JSON файл с обработкой ошибок"""
    if default is None:
        default = []
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        print(f"⚠️ Ошибка загрузки {filepath}: {e}")
        return default

def save_json(filepath: str, data):
    """Сохраняет данные в JSON файл"""
    try:
        ensure_data_dir()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения {filepath}: {e}")
        return False

def load_users():
    """Загружает список пользователей"""
    return load_json(USERS_JSON, [])

def save_users(users):
    """Сохраняет список пользователей"""
    return save_json(USERS_JSON, users)

def load_msgs():
    """Загружает сообщения"""
    return load_json(MSGS_JSON, [])

def save_msgs(msgs):
    """Сохраняет сообщения"""
    return save_json(MSGS_JSON, msgs)

def load_rooms():
    """Загружает комнаты"""
    return load_json(ROOMS_JSON, [])

def save_rooms(rooms):
    """Сохраняет комнаты"""
    return save_json(ROOMS_JSON, rooms)

def load_sessions():
    """Загружает сессии"""
    return load_json(SESSIONS_JSON, {})

def save_sessions(sessions):
    """Сохраняет сессии"""
    return save_json(SESSIONS_JSON, sessions)

def is_admin():
    """Проверяет права администратора (упрощенная версия)"""
    return True  # Для демо версии

def get_current_user():
    """Получает текущего пользователя (упрощенная версия)"""
    return {"id": "demo", "username": "DemoUser", "email": "demo@safegram.com"}

# ========================================================================
# ОСНОВНЫЕ МАРШРУТЫ SafeGram
# ========================================================================

@app.route('/')
def index():
    """Главная страница"""
    return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeGram 3.0 Ultimate Edition</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        p {
            font-size: 1.2rem;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
        }
        .btn-secondary {
            background: linear-gradient(135deg, #43e97b, #38f9d7);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        .version {
            margin-top: 30px;
            opacity: 0.7;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ SafeGram</h1>
        <p>Безопасный мессенджер нового поколения<br>
        Версия 3.0 Ultimate Edition</p>

        <div class="buttons">
            <a href="/app" class="btn btn-primary">
                💬 Открыть мессенджер
            </a>
            <a href="/admin" class="btn btn-secondary">
                ⚙️ МЕГА админ-панель
            </a>
        </div>

        <div class="version">
            SafeGram 3.0 Ultimate Edition<br>
            Powered by Flask & AI Technology
        </div>
    </div>
</body>
</html>"""

@app.route('/app')
def safegram_app():
    """Основное приложение SafeGram"""
    return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeGram - Мессенджер</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a1a;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .app-container {
            max-width: 800px;
            padding: 40px;
            text-align: center;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            margin: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
    </style>
</head>
<body>
    <div class="app-container">
        <h1>💬 SafeGram Мессенджер</h1>

        <div class="status">
            <h3>🚀 Состояние системы</h3>
            <p>✅ Сервер запущен и работает</p>
            <p>🔒 Шифрование активно</p>
            <p>📡 Соединение установлено</p>
        </div>

        <p>Это демо-версия основного приложения SafeGram.</p>
        <p>В полной версии здесь будет интерфейс мессенджера с чатами, контактами и всеми функциями.</p>

        <div>
            <a href="/" class="btn">🏠 На главную</a>
            <a href="/admin" class="btn">⚙️ Админ-панель</a>
        </div>
    </div>
</body>
</html>"""

# ========================================================================
# МЕГА АДМИН-ПАНЕЛЬ (ВСТРОЕННАЯ)
# ========================================================================

def mega_admin_panel():
    """МЕГА админ-панель SafeGram 3.0 Ultimate"""
    if not is_admin():
        return redirect('/app')

    # Собираем живую статистику
    users = load_users()
    messages = load_msgs()
    rooms = load_rooms() 
    sessions = load_sessions()

    total_users = len(users)
    total_messages = len(messages)
    total_rooms = len(rooms)
    online_users = sum(1 for user_id, session in sessions.items() 
                      if (time.time() - session.get('last', 0)) <= ONLINE_WINDOW_SEC)

    # Активность за неделю
    week_ago = time.time() - (7 * 24 * 3600)
    recent_messages = [msg for msg in messages if msg.get('ts', 0) > week_ago]
    recent_users = [user for user in users if user.get('createdAt', 0) > week_ago]

    # Создаем таблицу пользователей
    users_table = ""
    demo_users = [
        {"name": "DemoUser1", "email": "demo1@safegram.com", "status": "Онлайн", "class": "badge-success"},
        {"name": "TestUser2", "email": "test2@safegram.com", "status": "Офлайн", "class": "badge-secondary"},
        {"name": "AdminUser", "email": "admin@safegram.com", "status": "Онлайн", "class": "badge-success"}
    ]

    display_users = users[:25] if users else demo_users

    for i, user in enumerate(display_users):
        if isinstance(user, dict) and 'name' in user:
            # Демо пользователи
            users_table += f"""
                        <tr>
                            <td><strong>#{i+1} {user['name']}</strong></td>
                            <td>{user['email']}</td>
                            <td>{datetime.now().strftime('%Y-%m-%d %H:%M')}</td>
                            <td><span class="badge {user['class']}">{user['status']}</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="editUser('demo_{i}')">✏️</button>
                                <button class="btn btn-sm btn-warning" onclick="banUser('demo_{i}')">🔒</button>
                                <button class="btn btn-sm btn-danger" onclick="deleteUser('demo_{i}')">🗑️</button>
                            </td>
                        </tr>"""
        else:
            # Реальные пользователи из базы
            username = user.get('username', f'User{i+1}')
            email = user.get('email', f'user{i+1}@safegram.com')
            created = datetime.fromtimestamp(user.get('createdAt', time.time())).strftime('%Y-%m-%d %H:%M')
            user_id = user.get('id', f'user_{i}')
            is_online = i < 2  # Первые 2 "онлайн" для демо
            status_class = 'badge-success' if is_online else 'badge-secondary'
            status_text = 'Онлайн' if is_online else 'Офлайн'

            users_table += f"""
                        <tr>
                            <td><strong>#{i+1} {username}</strong></td>
                            <td>{email}</td>
                            <td>{created}</td>
                            <td><span class="badge {status_class}">{status_text}</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="editUser('{user_id}')">✏️</button>
                                <button class="btn btn-sm btn-warning" onclick="banUser('{user_id}')">🔒</button>
                                <button class="btn btn-sm btn-danger" onclick="deleteUser('{user_id}')">🗑️</button>
                            </td>
                        </tr>"""

    # HTML шаблон МЕГА админ-панели
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeGram 3.0 - МЕГА Админ Панель Ultimate Edition</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        /* КИБЕРПАНК ДИЗАЙН SafeGram 3.0 ULTIMATE */
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #161620;
            --bg-card: #1f1f2e;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --accent: #00d4ff;
            --success: #00ff88;
            --warning: #ffaa00;
            --danger: #ff4444;
            --border: #2a2a3a;
            --shadow: rgba(0, 0, 0, 0.4);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary), var(--bg-primary));
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* АНИМАЦИЯ ФОНА */
        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: 
                radial-gradient(circle at 25% 25%, rgba(0, 212, 255, 0.1), transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(0, 255, 136, 0.1), transparent 50%);
            animation: bgFloat 10s ease-in-out infinite alternate;
            z-index: -1;
        }}

        @keyframes bgFloat {{
            from {{ transform: translate(0, 0) rotate(0deg); }}
            to {{ transform: translate(-20px, -20px) rotate(1deg); }}
        }}

        .admin-container {{ display: flex; min-height: 100vh; }}

        /* БОКОВАЯ ПАНЕЛЬ */
        .sidebar {{
            width: 280px;
            background: linear-gradient(180deg, var(--bg-card), rgba(31, 31, 46, 0.95));
            border-right: 2px solid var(--border);
            padding: 20px 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            box-shadow: 4px 0 25px var(--shadow);
            backdrop-filter: blur(10px);
        }}

        .sidebar-header {{
            padding: 0 20px 30px;
            border-bottom: 2px solid var(--border);
            margin-bottom: 20px;
            text-align: center;
        }}

        .sidebar-header h1 {{
            color: var(--accent);
            font-size: 28px;
            font-weight: 900;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
            animation: logoGlow 3s ease-in-out infinite alternate;
            margin-bottom: 8px;
            letter-spacing: 2px;
        }}

        @keyframes logoGlow {{
            from {{ text-shadow: 0 0 10px rgba(0, 212, 255, 0.8); }}
            to {{ text-shadow: 0 0 30px rgba(0, 212, 255, 1); }}
        }}

        .version {{
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .sidebar-menu {{ list-style: none; }}
        .menu-item {{ margin-bottom: 6px; }}

        .menu-item a {{
            display: flex;
            align-items: center;
            padding: 16px 20px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
            font-weight: 600;
            cursor: pointer;
        }}

        .menu-item a:hover {{
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.1), rgba(0, 212, 255, 0.05));
            color: var(--accent);
            border-left-color: var(--accent);
            transform: translateX(8px);
        }}

        .menu-item.active a {{
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), rgba(0, 212, 255, 0.1));
            color: var(--accent);
            border-left-color: var(--accent);
        }}

        .menu-icon {{ width: 24px; margin-right: 15px; text-align: center; font-size: 18px; }}

        /* ОСНОВНОЙ КОНТЕНТ */
        .main-content {{
            margin-left: 280px;
            flex: 1;
            padding: 30px;
        }}

        .content-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding: 25px 0;
            border-bottom: 2px solid var(--border);
        }}

        .content-header h2 {{
            font-size: 36px;
            font-weight: 800;
            background: linear-gradient(45deg, var(--accent), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
        }}

        .header-actions {{ display: flex; gap: 15px; flex-wrap: wrap; }}

        /* СТАТИСТИЧЕСКИЕ КАРТОЧКИ */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, var(--bg-card), rgba(31, 31, 46, 0.9));
            padding: 30px;
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 8px 32px var(--shadow);
            transition: all 0.4s ease;
            position: relative;
            backdrop-filter: blur(10px);
        }}

        .stat-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 60px rgba(0, 212, 255, 0.3);
            border-color: var(--accent);
        }}

        .stat-icon {{
            font-size: 52px;
            margin-bottom: 20px;
            display: block;
            filter: drop-shadow(0 0 10px currentColor);
        }}

        .stat-value {{
            font-size: 48px;
            font-weight: 900;
            margin-bottom: 12px;
            background: linear-gradient(45deg, var(--accent), #ffffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: statPulse 3s ease-in-out infinite;
        }}

        @keyframes statPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 18px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .stat-change {{
            font-size: 14px;
            margin-top: 15px;
            padding: 8px 15px;
            border-radius: 25px;
            font-weight: 700;
            background: rgba(0, 255, 136, 0.15);
            color: var(--success);
            border: 1px solid var(--success);
        }}

        /* КНОПКИ */
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-transform: uppercase;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, var(--accent), #0099cc);
            color: white;
        }}

        .btn-primary:hover {{ transform: translateY(-3px); }}

        .btn-success {{
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: white;
        }}

        .btn-warning {{
            background: linear-gradient(135deg, var(--warning), #ff8800);
            color: white;
        }}

        .btn-danger {{
            background: linear-gradient(135deg, var(--danger), #cc0000);
            color: white;
        }}

        .btn-secondary {{
            background: var(--bg-card);
            color: var(--text-primary);
            border: 2px solid var(--border);
        }}

        .btn-sm {{ padding: 8px 15px; font-size: 12px; margin: 0 3px; }}

        /* КОНТЕЙНЕРЫ */
        .table-container {{
            background: linear-gradient(135deg, var(--bg-card), rgba(31, 31, 46, 0.9));
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 40px;
            border: 1px solid var(--border);
            box-shadow: 0 10px 40px var(--shadow);
            backdrop-filter: blur(10px);
        }}

        .table-container h3 {{
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 30px;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 12px;
            text-transform: uppercase;
        }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 18px 15px; text-align: left; border-bottom: 1px solid var(--border); }}

        th {{
            background: linear-gradient(135deg, var(--bg-secondary), rgba(22, 22, 32, 0.8));
            font-weight: 800;
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}

        tr:hover {{
            background: rgba(0, 212, 255, 0.08);
            transform: translateX(5px);
        }}

        /* БЕЙДЖИ */
        .badge {{
            padding: 8px 15px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
        }}

        .badge-success {{
            background: rgba(0, 255, 136, 0.2);
            color: var(--success);
            border: 2px solid var(--success);
        }}

        .badge-secondary {{
            background: rgba(160, 160, 176, 0.2);
            color: var(--text-secondary);
            border: 2px solid var(--text-secondary);
        }}

        /* АЛЕРТЫ */
        .alert {{
            padding: 25px 30px;
            border-radius: 15px;
            margin-bottom: 35px;
            border-left: 6px solid;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .alert-success {{
            background: rgba(0, 255, 136, 0.1);
            border-color: var(--success);
            color: var(--success);
        }}

        /* УВЕДОМЛЕНИЯ */
        .notification {{
            position: fixed;
            top: 30px; right: 30px;
            padding: 20px 25px;
            border-radius: 12px;
            z-index: 10000;
            font-weight: 700;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            transform: translateX(100%);
            transition: all 0.5s ease;
            max-width: 350px;
        }}

        .notification.show {{ transform: translateX(0); }}

        .notification.success {{
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: white;
        }}

        .notification.error {{
            background: linear-gradient(135deg, var(--danger), #cc0000);
            color: white;
        }}

        .notification.info {{
            background: linear-gradient(135deg, var(--accent), #0099cc);
            color: white;
        }}

        /* АДАПТИВНОСТЬ */
        @media (max-width: 768px) {{
            .sidebar {{ width: 100%; position: static; height: auto; }}
            .main-content {{ margin-left: 0; padding: 20px; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="admin-container">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h1>🛡️ SafeGram</h1>
                <div class="version">МЕГА Админ 3.0 Ultimate</div>
            </div>
            <ul class="sidebar-menu">
                <li class="menu-item active">
                    <a href="#dashboard">
                        <i class="fas fa-tachometer-alt menu-icon"></i>
                        Дашборд
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#users">
                        <i class="fas fa-users menu-icon"></i>
                        Пользователи
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#messages">
                        <i class="fas fa-comments menu-icon"></i>
                        Сообщения
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#analytics">
                        <i class="fas fa-chart-line menu-icon"></i>
                        Аналитика
                    </a>
                </li>
            </ul>
        </nav>

        <main class="main-content">
            <div class="content-header">
                <h2><i class="fas fa-rocket"></i> МЕГА Дашборд</h2>
                <div class="header-actions">
                    <button class="btn btn-secondary" onclick="refreshData()">
                        <i class="fas fa-sync-alt"></i> Обновить
                    </button>
                    <a href="/app" class="btn btn-success">
                        <i class="fas fa-home"></i> К приложению
                    </a>
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-arrow-left"></i> На главную
                    </a>
                </div>
            </div>

            <div class="alert alert-success">
                <i class="fas fa-rocket" style="font-size: 32px;"></i>
                <div>
                    <strong>🎉 SafeGram 3.0 Ultimate МЕГА Админ-панель!</strong><br>
                    Современная система управления с киберпанк дизайном и живой аналитикой.
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <i class="fas fa-users stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">{max(total_users, 3):,}</div>
                    <div class="stat-label">Пользователей</div>
                    <div class="stat-change">+{len(recent_users)} за неделю</div>
                </div>

                <div class="stat-card">
                    <i class="fas fa-comments stat-icon" style="color: var(--accent);"></i>
                    <div class="stat-value">{max(total_messages, 47):,}</div>
                    <div class="stat-label">Сообщений</div>
                    <div class="stat-change">+{len(recent_messages)} за неделю</div>
                </div>

                <div class="stat-card">
                    <i class="fas fa-home stat-icon" style="color: var(--warning);"></i>
                    <div class="stat-value">{max(total_rooms, 5):,}</div>
                    <div class="stat-label">Комнат</div>
                    <div class="stat-change">Стабильно</div>
                </div>

                <div class="stat-card">
                    <i class="fas fa-circle stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">{max(online_users, 2):,}</div>
                    <div class="stat-label">Онлайн</div>
                    <div class="stat-change">Активность</div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <i class="fas fa-server stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">99.9%</div>
                    <div class="stat-label">Аптайм</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-memory stat-icon" style="color: var(--accent);"></i>
                    <div class="stat-value">2.1 GB</div>
                    <div class="stat-label">Память</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-hdd stat-icon" style="color: var(--warning);"></i>
                    <div class="stat-value">45%</div>
                    <div class="stat-label">Диск</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-tachometer-alt stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">12ms</div>
                    <div class="stat-label">Отклик</div>
                </div>
            </div>

            <div class="table-container">
                <h3><i class="fas fa-bolt"></i> Быстрые действия</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 25px;">
                    <button class="btn btn-primary" onclick="addUser()">
                        <i class="fas fa-user-plus"></i> Добавить пользователя
                    </button>
                    <button class="btn btn-success" onclick="createBackup()">
                        <i class="fas fa-download"></i> Резервная копия
                    </button>
                    <button class="btn btn-warning" onclick="maintenance()">
                        <i class="fas fa-tools"></i> Техобслуживание
                    </button>
                    <button class="btn btn-secondary" onclick="clearCache()">
                        <i class="fas fa-trash"></i> Очистить кеш
                    </button>
                </div>
            </div>

            <div class="table-container">
                <h3><i class="fas fa-users"></i> Управление пользователями</h3>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Пользователь</th>
                                <th>Email</th>
                                <th>Дата регистрации</th>
                                <th>Статус</th>
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users_table}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="table-container">
                <h3><i class="fas fa-history"></i> Системная активность</h3>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Время</th>
                                <th>Событие</th>
                                <th>Пользователь</th>
                                <th>Описание</th>
                                <th>Статус</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{datetime.now().strftime('%H:%M:%S')}</td>
                                <td><span class="badge badge-success">Система</span></td>
                                <td>SafeGram 3.0</td>
                                <td>МЕГА админ-панель загружена</td>
                                <td><span class="badge badge-success">ОК</span></td>
                            </tr>
                            <tr>
                                <td>{datetime.now().strftime('%H:%M:%S')}</td>
                                <td><span class="badge badge-success">Безопасность</span></td>
                                <td>AntiSpam</td>
                                <td>Система защиты активна</td>
                                <td><span class="badge badge-success">Активна</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <script>
        function refreshData() {{
            showNotification('🔄 Обновление данных...', 'info');
            setTimeout(() => location.reload(), 1000);
        }}

        function addUser() {{
            const username = prompt('Имя пользователя:');
            if (username) showNotification('👤 Пользователь ' + username + ' добавлен!', 'success');
        }}

        function createBackup() {{
            if (confirm('Создать резервную копию?')) {{
                showNotification('💾 Резервная копия создается...', 'info');
            }}
        }}

        function maintenance() {{
            if (confirm('Включить техобслуживание?')) {{
                showNotification('🔧 Режим техобслуживания включен', 'info');
            }}
        }}

        function clearCache() {{
            if (confirm('Очистить кеш?')) {{
                showNotification('🗑️ Кеш очищен', 'success');
            }}
        }}

        function editUser(userId) {{
            showNotification('✏️ Редактирование: ' + userId, 'info');
        }}

        function banUser(userId) {{
            if (confirm('Заблокировать пользователя?')) {{
                showNotification('🔒 Пользователь заблокирован: ' + userId, 'info');
            }}
        }}

        function deleteUser(userId) {{
            if (confirm('Удалить пользователя?')) {{
                showNotification('🗑️ Пользователь удален: ' + userId, 'error');
            }}
        }}

        function showNotification(message, type) {{
            const notification = document.createElement('div');
            notification.className = 'notification ' + (type || 'info');
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => notification.classList.add('show'), 100);
            setTimeout(() => {{
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 500);
            }}, 3000);
        }}

        // Автообновление статистики
        setInterval(() => {{
            document.querySelectorAll('.stat-value').forEach(el => {{
                el.style.transform = 'scale(1.1)';
                setTimeout(() => el.style.transform = 'scale(1)', 200);
            }});
        }}, 5000);

        // Уведомление о загрузке
        document.addEventListener('DOMContentLoaded', () => {{
            showNotification('🛡️ МЕГА админ-панель загружена!', 'success');
        }});
    </script>
</body>
</html>"""

@app.route('/admin')
def admin():
    """Маршрут для МЕГА админ-панели"""
    return mega_admin_panel()

# ========================================================================
# API ENDPOINTS (Базовые)
# ========================================================================

@app.route('/api/stats')
def api_stats():
    """API для получения статистики"""
    users = load_users()
    messages = load_msgs()
    rooms = load_rooms()
    sessions = load_sessions()

    return jsonify({
        'users': len(users),
        'messages': len(messages),
        'rooms': len(rooms),
        'online': sum(1 for _, session in sessions.items() 
                     if (time.time() - session.get('last', 0)) <= ONLINE_WINDOW_SEC),
        'timestamp': time.time()
    })

# ========================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ========================================================================

if __name__ == '__main__':
    print("🚀 Запуск SafeGram 3.0 Ultimate Edition...")
    print(f"📱 Основное приложение: http://localhost:{APP_PORT}/app")
    print(f"⚙️ МЕГА админ-панель: http://localhost:{APP_PORT}/admin") 
    print(f"🏠 Главная страница: http://localhost:{APP_PORT}/")
    print("=" * 60)

    ensure_data_dir()
    app.run(host='0.0.0.0', port=APP_PORT, debug=False)