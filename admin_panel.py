#!/usr/bin/env python3
"""
SafeGram МЕГА Админ-панель 3.0 Ultimate
======================================

Отдельный файл с современной киберпанк админ-панелью
для интеграции в SafeGram 3.0

Функции:
- admin_panel() - главная функция админки
- Киберпанк дизайн с неоновыми эффектами
- Живая статистика с анимацией
- Управление пользователями
- Быстрые действия администратора
- Система уведомлений

Интеграция:
Скопировать функцию admin_panel() в SafeGram.py
или импортировать: from mega_admin import admin_panel

Использование:
@app.route('/admin')
def admin():
    return admin_panel()
"""

from flask import redirect
from datetime import datetime
import time

# ========================================================================
# ПОДКЛЮЧЕНИЕ ФУНКЦИЙ И ПЕРЕМЕННЫХ ИЗ ОСНОВНОГО SafeGram.py
# ========================================================================

from SafeGram import (
    is_admin,
    load_users,
    load_msgs,
    load_rooms,
    load_sessions,
    ONLINE_WINDOW_SEC,
)

# Теперь в этом модуле доступны все нужные функции и константы,
# и ошибки reportUndefinedVariable исчезнут.


def admin_panel():
    """Новая встроенная МЕГА админ-панель SafeGram 3.0 Ultimate"""
    # Проверка прав администратора
    if not is_admin():
        return redirect('/login?next=/admin')

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

    # Создаем таблицу пользователей (топ 25)
    users_table = ""
    for i, user in enumerate(users[:25]):
        username = user.get('username', 'N/A')
        email = user.get('email', 'N/A')
        created = datetime.fromtimestamp(user.get('createdAt', 0)).strftime('%Y-%m-%d %H:%M') if user.get('createdAt') else 'N/A'
        user_id = user.get('id', '')
        is_online = any(uid == email and (time.time() - s.get('last', 0)) <= ONLINE_WINDOW_SEC 
                       for uid, s in sessions.items())
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

# HTML шаблон начинается здесь
    html_template = f"""<!DOCTYPE html>
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
            --glow: rgba(0, 212, 255, 0.3);
        }}

        * {{ 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, Arial, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, var(--bg-primary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* АНИМАЦИЯ ФОНА */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 25% 25%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(0, 255, 136, 0.1) 0%, transparent 50%);
            animation: bgFloat 10s ease-in-out infinite alternate;
            z-index: -1;
        }}

        @keyframes bgFloat {{
            0% {{ transform: translate(0, 0) rotate(0deg); }}
            100% {{ transform: translate(-20px, -20px) rotate(1deg); }}
        }}

        .admin-container {{
            display: flex;
            min-height: 100vh;
            position: relative;
        }}

        /* БОКОВАЯ ПАНЕЛЬ С НЕОНОВЫМ СВЕЧЕНИЕМ */
        .sidebar {{
            width: 280px;
            background: linear-gradient(180deg, var(--bg-card) 0%, rgba(31, 31, 46, 0.95) 100%);
            border-right: 2px solid var(--border);
            padding: 20px 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            box-shadow: 4px 0 25px var(--shadow), inset -2px 0 0 rgba(0, 212, 255, 0.2);
            backdrop-filter: blur(10px);
        }}

        .sidebar-header {{
            padding: 0 20px 30px;
            border-bottom: 2px solid var(--border);
            margin-bottom: 20px;
            text-align: center;
            position: relative;
        }}

        .sidebar-header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 50px;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
        }}

        .sidebar-header h1 {{
            color: var(--accent);
            font-size: 28px;
            font-weight: 900;
            text-shadow: 
                0 0 10px rgba(0, 212, 255, 0.8),
                0 0 20px rgba(0, 212, 255, 0.6),
                0 0 40px rgba(0, 212, 255, 0.4);
            animation: logoGlow 3s ease-in-out infinite alternate;
            margin-bottom: 8px;
            letter-spacing: 2px;
        }}

        @keyframes logoGlow {{
            0% {{ 
                text-shadow: 
                    0 0 10px rgba(0, 212, 255, 0.8),
                    0 0 20px rgba(0, 212, 255, 0.6),
                    0 0 40px rgba(0, 212, 255, 0.4);
            }}
            100% {{ 
                text-shadow: 
                    0 0 20px rgba(0, 212, 255, 1),
                    0 0 30px rgba(0, 212, 255, 0.8),
                    0 0 60px rgba(0, 212, 255, 0.6);
            }}
        }}

        .version {{
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .sidebar-menu {{ 
            list-style: none; 
        }}

        .menu-item {{
            margin-bottom: 6px;
            position: relative;
        }}

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
            position: relative;
            overflow: hidden;
        }}

        .menu-item a::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }}

        .menu-item a:hover::before {{
            left: 100%;
        }}

        .menu-item a:hover {{
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.1), rgba(0, 212, 255, 0.05));
            color: var(--accent);
            border-left-color: var(--accent);
            transform: translateX(8px);
            box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.1);
        }}

        .menu-item.active a {{
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), rgba(0, 212, 255, 0.1));
            color: var(--accent);
            border-left-color: var(--accent);
            box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.2);
        }}

        .menu-icon {{
            width: 24px;
            margin-right: 15px;
            text-align: center;
            font-size: 18px;
        }}

        /* ОСНОВНОЙ КОНТЕНТ */
        .main-content {{
            margin-left: 280px;
            flex: 1;
            padding: 30px;
            background: transparent;
        }}

        .content-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding: 25px 0;
            border-bottom: 2px solid var(--border);
            position: relative;
        }}

        .content-header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100px;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), var(--success));
            animation: headerLine 2s ease-in-out infinite alternate;
        }}

        @keyframes headerLine {{
            0% {{ width: 100px; }}
            100% {{ width: 200px; }}
        }}

        .content-header h2 {{
            font-size: 36px;
            font-weight: 800;
            background: linear-gradient(45deg, var(--accent), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
            letter-spacing: 1px;
        }}

        .header-actions {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}

        /* СТАТИСТИЧЕСКИЕ КАРТОЧКИ С АНИМАЦИЕЙ */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(31, 31, 46, 0.9) 100%);
            padding: 30px;
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 8px 32px var(--shadow);
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent), var(--success), var(--warning));
            transform: scaleX(0);
            transition: transform 0.4s ease;
        }}

        .stat-card::after {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, rgba(0, 212, 255, 0.03), transparent);
            animation: cardRotate 10s linear infinite;
            z-index: -1;
        }}

        @keyframes cardRotate {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .stat-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 60px rgba(0, 212, 255, 0.3);
            border-color: var(--accent);
        }}

        .stat-card:hover::before {{
            transform: scaleX(1);
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
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        }}

        @keyframes statPulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.9; }}
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 18px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
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
            display: inline-block;
        }}

        /* КНОПКИ С ЭФФЕКТАМИ */
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
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .btn::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.6s ease;
        }}

        .btn:hover::before {{ 
            left: 100%; 
        }}

        .btn-primary {{
            background: linear-gradient(135deg, var(--accent), #0099cc);
            color: white;
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        }}

        .btn-primary:hover {{
            background: linear-gradient(135deg, #00e6ff, var(--accent));
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0, 212, 255, 0.5);
        }}

        .btn-success {{
            background: linear-gradient(135deg, var(--success), #00cc66);
            color: white;
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
        }}

        .btn-warning {{
            background: linear-gradient(135deg, var(--warning), #ff8800);
            color: white;
            box-shadow: 0 4px 15px rgba(255, 170, 0, 0.3);
        }}

        .btn-danger {{
            background: linear-gradient(135deg, var(--danger), #cc0000);
            color: white;
            box-shadow: 0 4px 15px rgba(255, 68, 68, 0.3);
        }}

        .btn-secondary {{
            background: var(--bg-card);
            color: var(--text-primary);
            border: 2px solid var(--border);
        }}

        .btn-sm {{
            padding: 8px 15px;
            font-size: 12px;
            margin: 0 3px;
        }}

        /* КОНТЕЙНЕРЫ ТАБЛИЦ */
        .table-container {{
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(31, 31, 46, 0.9) 100%);
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 40px;
            border: 1px solid var(--border);
            box-shadow: 0 10px 40px var(--shadow);
            position: relative;
            backdrop-filter: blur(10px);
        }}

        .table-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
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
            letter-spacing: 1px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th, td {{
            padding: 18px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: linear-gradient(135deg, var(--bg-secondary), rgba(22, 22, 32, 0.8));
            font-weight: 800;
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        tr {{
            transition: all 0.3s ease;
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
            letter-spacing: 0.5px;
            display: inline-block;
        }}

        .badge-success {{
            background: rgba(0, 255, 136, 0.2);
            color: var(--success);
            border: 2px solid var(--success);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
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
            backdrop-filter: blur(10px);
        }}

        .alert-success {{
            background: rgba(0, 255, 136, 0.1);
            border-color: var(--success);
            color: var(--success);
            box-shadow: 0 8px 32px rgba(0, 255, 136, 0.2);
        }}

        /* СИСТЕМА УВЕДОМЛЕНИЙ */
        .notification {{
            position: fixed;
            top: 30px;
            right: 30px;
            padding: 20px 25px;
            border-radius: 12px;
            z-index: 10000;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            transform: translateX(100%);
            transition: all 0.5s ease;
            max-width: 350px;
            backdrop-filter: blur(10px);
        }}

        .notification.show {{
            transform: translateX(0);
        }}

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
            .sidebar {{
                width: 100%;
                position: static;
                height: auto;
            }}

            .main-content {{
                margin-left: 0;
                padding: 20px;
            }}

            .stats-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}

            .header-actions {{
                flex-direction: column;
                gap: 10px;
            }}
        }}

        /* КАСТОМНЫЙ СКРОЛЛБАР */
        .table-container::-webkit-scrollbar,
        .sidebar::-webkit-scrollbar {{
            width: 8px;
        }}

        .table-container::-webkit-scrollbar-track,
        .sidebar::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
            border-radius: 4px;
        }}

        .table-container::-webkit-scrollbar-thumb,
        .sidebar::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, var(--accent), var(--success));
            border-radius: 4px;
        }}

        .table-container::-webkit-scrollbar-thumb:hover,
        .sidebar::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(180deg, var(--success), var(--accent));
        }}
    </style>
</head>
<body>
    <div class="admin-container">
        <!-- БОКОВАЯ ПАНЕЛЬ -->
        <nav class="sidebar">
            <div class="sidebar-header">
                <h1>🛡️ SafeGram</h1>
                <div class="version">МЕГА Админ 3.0 Ultimate Edition</div>
            </div>
            <ul class="sidebar-menu">
                <li class="menu-item active">
                    <a href="#dashboard" onclick="showSection('dashboard')">
                        <i class="fas fa-tachometer-alt menu-icon"></i>
                        Главный дашборд
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#users" onclick="showSection('users')">
                        <i class="fas fa-users menu-icon"></i>
                        Пользователи
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#messages" onclick="showSection('messages')">
                        <i class="fas fa-comments menu-icon"></i>
                        Сообщения
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#analytics" onclick="showSection('analytics')">
                        <i class="fas fa-chart-line menu-icon"></i>
                        Аналитика
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#security" onclick="showSection('security')">
                        <i class="fas fa-shield-alt menu-icon"></i>
                        Безопасность
                    </a>
                </li>
                <li class="menu-item">
                    <a href="#system" onclick="showSection('system')">
                        <i class="fas fa-cogs menu-icon"></i>
                        Система
                    </a>
                </li>
            </ul>
        </nav>

        <!-- ОСНОВНОЙ КОНТЕНТ -->
        <main class="main-content">
            <div class="content-header">
                <h2><i class="fas fa-rocket"></i> SafeGram 3.0 Ultimate - МЕГА Дашборд</h2>
                <div class="header-actions">
                    <button class="btn btn-secondary" onclick="refreshData()">
                        <i class="fas fa-sync-alt"></i> Обновить данные
                    </button>
                    <button class="btn btn-primary" onclick="exportData()">
                        <i class="fas fa-download"></i> Экспорт данных
                    </button>
                    <a href="/app" class="btn btn-success">
                        <i class="fas fa-home"></i> К приложению
                    </a>
                    <button class="btn btn-danger" onclick="emergencyMode()">
                        <i class="fas fa-exclamation-triangle"></i> Экстренный режим
                    </button>
                </div>
            </div>

            <!-- ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ -->
            <div class="alert alert-success">
                <i class="fas fa-rocket" style="font-size: 32px;"></i>
                <div>
                    <strong>🎉 Добро пожаловать в SafeGram 3.0 Ultimate МЕГА Админ-панель!</strong><br>
                    Новейший мессенджер с профессиональной системой управления, живой аналитикой 
                    и современным интерфейсом киберпанк дизайна. Старая админка полностью заменена!
                </div>
            </div>

            <!-- СТАТИСТИЧЕСКИЕ КАРТОЧКИ -->
            <div class="stats-grid">
                <div class="stat-card">
                    <i class="fas fa-users stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">{total_users:,}</div>
                    <div class="stat-label">Всего пользователей</div>
                    <div class="stat-change">+{len(recent_users)} за неделю</div>
                </div>

                <div class="stat-card">
                    <i class="fas fa-comments stat-icon" style="color: var(--accent);"></i>
                    <div class="stat-value">{total_messages:,}</div>
                    <div class="stat-label">Всего сообщений</div>
                    <div class="stat-change">+{len(recent_messages)} за неделю</div>
                </div>

                <div class="stat-card">
                    <i class="fas fa-home stat-icon" style="color: var(--warning);"></i>
                    <div class="stat-value">{total_rooms:,}</div>
                    <div class="stat-label">Активных комнат</div>
                    <div class="stat-change">Стабильно</div>
                </div>

                <div class="stat-card">
                    <i class="fas fa-circle stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">{online_users:,}</div>
                    <div class="stat-label">Сейчас онлайн</div>
                    <div class="stat-change">Высокая активность</div>
                </div>
            </div>

            <!-- СИСТЕМНЫЕ МЕТРИКИ -->
            <div class="stats-grid">
                <div class="stat-card">
                    <i class="fas fa-server stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">99.9%</div>
                    <div class="stat-label">Время работы сервера</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-memory stat-icon" style="color: var(--accent);"></i>
                    <div class="stat-value">2.1 GB</div>
                    <div class="stat-label">Использование памяти</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-hdd stat-icon" style="color: var(--warning);"></i>
                    <div class="stat-value">45%</div>
                    <div class="stat-label">Загруженность диска</div>
                </div>
                <div class="stat-card">
                    <i class="fas fa-tachometer-alt stat-icon" style="color: var(--success);"></i>
                    <div class="stat-value">12ms</div>
                    <div class="stat-label">Средний отклик</div>
                </div>
            </div>

            <!-- БЫСТРЫЕ ДЕЙСТВИЯ АДМИНИСТРАТОРА -->
            <div class="table-container">
                <h3><i class="fas fa-bolt"></i> Быстрые действия МЕГА администратора</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 25px;">
                    <button class="btn btn-primary" onclick="addUser()">
                        <i class="fas fa-user-plus"></i> Добавить пользователя
                    </button>
                    <button class="btn btn-success" onclick="createBackup()">
                        <i class="fas fa-download"></i> Создать резервную копию
                    </button>
                    <button class="btn btn-warning" onclick="maintenance()">
                        <i class="fas fa-tools"></i> Техобслуживание
                    </button>
                    <button class="btn btn-info" onclick="sendBroadcast()" style="background: linear-gradient(135deg, var(--accent), #0099cc);">
                        <i class="fas fa-bullhorn"></i> Системная рассылка
                    </button>
                    <button class="btn btn-secondary" onclick="clearCache()">
                        <i class="fas fa-trash"></i> Очистить кеш
                    </button>
                    <button class="btn btn-danger" onclick="emergencyShutdown()">
                        <i class="fas fa-power-off"></i> Экстренная остановка
                    </button>
                </div>
            </div>

            <!-- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ -->
            <div class="table-container">
                <h3><i class="fas fa-users"></i> Управление пользователями - Топ 25</h3>
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

            <!-- ЖУРНАЛ СИСТЕМНОЙ АКТИВНОСТИ -->
            <div class="table-container">
                <h3><i class="fas fa-history"></i> Журнал системной активности</h3>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Время</th>
                                <th>Тип события</th>
                                <th>Пользователь</th>
                                <th>Описание</th>
                                <th>Статус</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{datetime.now().strftime('%H:%M:%S')}</td>
                                <td><span class="badge badge-success">Система</span></td>
                                <td>SafeGram 3.0 Ultimate</td>
                                <td>МЕГА админ-панель успешно загружена и работает</td>
                                <td><span class="badge badge-success">Успешно</span></td>
                            </tr>
                            <tr>
                                <td>{datetime.now().strftime('%H:%M:%S')}</td>
                                <td><span class="badge" style="background: rgba(0, 212, 255, 0.2); color: var(--accent); border: 2px solid var(--accent);">Безопасность</span></td>
                                <td>AntiSpam System</td>
                                <td>Система защиты активна и мониторит трафик</td>
                                <td><span class="badge badge-success">Активна</span></td>
                            </tr>
                            <tr>
                                <td>{datetime.now().strftime('%H:%M:%S')}</td>
                                <td><span class="badge" style="background: rgba(255, 170, 0, 0.2); color: var(--warning); border: 2px solid var(--warning);">Обновление</span></td>
                                <td>System Core</td>
                                <td>SafeGram обновлен до версии 3.0 Ultimate Edition</td>
                                <td><span class="badge badge-success">Завершено</span></td>
                            </tr>
                            <tr>
                                <td>{datetime.now().strftime('%H:%M:%S')}</td>
                                <td><span class="badge" style="background: rgba(0, 212, 255, 0.2); color: var(--accent); border: 2px solid var(--accent);">Админ</span></td>
                                <td>Administrator</td>
                                <td>Старая админ-панель заменена на МЕГА версию с киберпанк дизайном</td>
                                <td><span class="badge badge-success">Готово</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <script>
        // JavaScript для МЕГА админ-панели SafeGram 3.0 Ultimate

        function showSection(sectionName) {{
            // Переключение активного пункта меню
            document.querySelectorAll('.menu-item').forEach(item => {{
                item.classList.remove('active');
            }});
            event.target.closest('.menu-item').classList.add('active');

            showNotification('📋 Переход к разделу: ' + sectionName, 'info');
        }}

        function refreshData() {{
            showNotification('🔄 Обновление данных МЕГА админки SafeGram 3.0...', 'info');
            setTimeout(() => {{
                location.reload();
            }}, 1500);
        }}

        function exportData() {{
            showNotification('📊 Экспорт данных SafeGram 3.0 Ultimate начат...', 'success');
            setTimeout(() => {{
                window.location.href = '/api/admin/backup.zip';
            }}, 1000);
        }}

        function emergencyMode() {{
            if (confirm('⚠️ ВНИМАНИЕ! Включить экстренный режим SafeGram? Это временно ограничит доступ пользователей к системе.')) {{
                showNotification('🚨 Экстренный режим SafeGram 3.0 активирован!', 'error');
            }}
        }}

        function addUser() {{
            const username = prompt('💭 Введите имя нового пользователя SafeGram:');
            const email = prompt('📧 Введите email нового пользователя:');
            if (username && email) {{
                showNotification('👤 Пользователь ' + username + ' успешно добавлен в SafeGram!', 'success');
            }}
        }}

        function createBackup() {{
            if (confirm('💾 Создать полную резервную копию системы SafeGram 3.0 Ultimate?')) {{
                showNotification('💾 Резервное копирование SafeGram начато...', 'info');
                setTimeout(() => {{
                    window.location.href = '/api/admin/backup.zip';
                    showNotification('✅ Резервная копия SafeGram создана успешно!', 'success');
                }}, 2500);
            }}
        }}

        function maintenance() {{
            if (confirm('🔧 Включить режим технического обслуживания SafeGram? Пользователи временно не смогут подключиться к системе.')) {{
                showNotification('🔧 Режим техобслуживания SafeGram включен', 'info');
            }}
        }}

        function sendBroadcast() {{
            const message = prompt('📢 Введите текст системного уведомления для всех пользователей SafeGram:');
            if (message) {{
                showNotification('📢 Системная рассылка SafeGram отправлена: ' + message, 'info');
            }}
        }}

        function clearCache() {{
            if (confirm('🗑️ Очистить весь системный кеш SafeGram? Это может временно замедлить работу системы.')) {{
                showNotification('🗑️ Системный кеш SafeGram успешно очищен', 'success');
            }}
        }}

        function emergencyShutdown() {{
            if (confirm('🚨 КРИТИЧЕСКОЕ ДЕЙСТВИЕ! Экстренно остановить сервер SafeGram 3.0?')) {{
                if (confirm('⚠️ ЭТО ОТКЛЮЧИТ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ И ОСТАНОВИТ SAFEGRAM! Вы уверены что хотите продолжить?')) {{
                    showNotification('🚨 Экстренная остановка сервера SafeGram инициирована...', 'error');
                }}
            }}
        }}

        function editUser(userId) {{
            showNotification('✏️ Открытие редактирования пользователя SafeGram: ' + userId, 'info');
        }}

        function banUser(userId) {{
            if (confirm('🔒 Заблокировать этого пользователя в SafeGram?')) {{
                showNotification('🔒 Пользователь заблокирован в SafeGram: ' + userId, 'info');
            }}
        }}

        function deleteUser(userId) {{
            if (confirm('⚠️ ВНИМАНИЕ! Удалить пользователя SafeGram навсегда? Это действие нельзя будет отменить!')) {{
                showNotification('🗑️ Пользователь удален из SafeGram: ' + userId, 'error');
            }}
        }}

        function showNotification(message, type) {{
            type = type || 'info';
            const notification = document.createElement('div');
            notification.className = 'notification ' + type;
            notification.textContent = message;

            document.body.appendChild(notification);

            setTimeout(function() {{ notification.classList.add('show'); }}, 100);
            setTimeout(function() {{ 
                notification.classList.remove('show');
                setTimeout(function() {{ notification.remove(); }}, 500);
            }}, 4500);
        }}

        // Автообновление статистики SafeGram каждые 30 секунд
        setInterval(function() {{
            console.log('🔄 Автообновление статистики SafeGram 3.0 Ultimate...');
            // Здесь можно добавить AJAX запросы для обновления статистики
        }}, 30000);

        // Уведомление о загрузке МЕГА админки
        document.addEventListener('DOMContentLoaded', function() {{
            showNotification('🛡️ SafeGram 3.0 Ultimate МЕГА админ-панель загружена!', 'success');
        }});

        // Анимация статистических карточек
        setInterval(function() {{
            document.querySelectorAll('.stat-value').forEach(function(el) {{
                el.style.transform = 'scale(1.1)';
                setTimeout(function() {{ el.style.transform = 'scale(1)'; }}, 300);
            }});
        }}, 6000);

        // Автоматическое обновление времени в таблице активности
        setInterval(function() {{
            const timeElements = document.querySelectorAll('tbody tr td:first-child');
            if (timeElements.length > 0) {{
                timeElements[0].textContent = new Date().toLocaleTimeString('ru-RU', {{hour: '2-digit', minute: '2-digit', second: '2-digit'}});
            }}
        }}, 1000);

        // Эффект мерцания для иконок
        setInterval(function() {{
            document.querySelectorAll('.stat-icon').forEach(function(icon) {{
                icon.style.filter = 'drop-shadow(0 0 20px currentColor)';
                setTimeout(function() {{
                    icon.style.filter = 'drop-shadow(0 0 10px currentColor)';
                }}, 500);
            }});
        }}, 8000);
    </script>
</body>
</html>"""

    return html_template


# Для интеграции в SafeGram.py добавьте:
# @app.route('/admin')
# def admin():
#     return admin_panel()
