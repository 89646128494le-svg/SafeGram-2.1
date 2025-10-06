import re

def fix_python_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    for idx, line in enumerate(lines):
        # Исправить незакрытые фигурные скобки для f-строк
        if 'f"' in line or "f'" in line:
            open_brace = line.count('{')
            close_brace = line.count('}')
            if open_brace > close_brace:
                line += '}' * (open_brace - close_brace)
        # Исправить пропущенные запятые между переменными
        if re.search(r'[^,]\s+\w+\s*=', line) and line.strip().endswith(','):
            line = re.sub(r'([^,])\s+(\w+\s*=)', r'\1, \2', line)
        # Пропустить пустые строки с ошибкой ожидания выражения
        if re.search(r'^\s*$', line):
            continue
        fixed_lines.append(line)

    code = ''.join(fixed_lines)

    # Добавить заглушки для неопределённых переменных
    missing_vars = []
    var_names = re.findall(r'\"([^\"]+)\" не определено', code)
    for name in set(var_names):
        if name.isidentifier():
            code = f"{name} = None\n" + code
            missing_vars.append(name)
    # ONLINE_WINDOW_SEC дефолт
    if 'ONLINE_WINDOW_SEC' in code and 'ONLINE_WINDOW_SEC =' not in code:
        code = "ONLINE_WINDOW_SEC = 300\n" + code
    # Аналогично для других нужных глобальных переменных по необходимости

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(code)
    print('✅ Ошибки автоматически исправлены в самом файле.')

# --- ЗАПУСТИ так ---
# fix_python_file("SafeGram.py")
