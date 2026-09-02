import html
import json
import os
import re
import sys

from chapters import get_all_chapters
from section1 import exercises as s1
from section2 import exercises as s2
from section3 import exercises as s3
from section4 import exercises as s4
from section5 import exercises as s5
from section6 import exercises as s6
from template import HTML_HEAD, HTML_FOOTER

ch1_exercises = s1 + s2 + s3 + s4 + s5 + s6

with open('builder/chapter2_data.json', 'r', encoding='utf-8') as f:
    ch2_exercises = json.load(f)

with open('builder/chapter3_data.json', 'r', encoding='utf-8') as f:
    ch3_exercises = json.load(f)

with open('builder/chapter4_data.json', 'r', encoding='utf-8') as f:
    ch4_exercises = json.load(f)

with open('builder/chapter5_data.json', 'r', encoding='utf-8') as f:
    ch5_exercises = json.load(f)

with open('builder/chapter6_data.json', 'r', encoding='utf-8') as f:
    ch6_exercises = json.load(f)

with open('builder/chapter7_data.json', 'r', encoding='utf-8') as f:
    ch7_exercises = json.load(f)

with open('builder/chapter8_data.json', 'r', encoding='utf-8') as f:
    ch8_exercises = json.load(f)

with open('builder/chapter9_data.json', 'r', encoding='utf-8') as f:
    ch9_exercises = json.load(f)

with open('builder/chapter10_data.json', 'r', encoding='utf-8') as f:
    ch10_exercises = json.load(f)

def format_text(txt):
    if not txt:
        return ""
    lines = txt.strip().split('\n')
    out_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                out_lines.append('</ul>')
                in_list = False
            out_lines.append('<div style="height: 8px;"></div>')
            continue
            
        # Bullet list
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                out_lines.append('<ul style="margin: 8px 0 8px 20px;">')
                in_list = True
            content = stripped[2:]
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
            out_lines.append(f'<li style="margin-bottom: 4px;">{content}</li>')
            continue
            
        # Numbered list
        m_num = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if m_num:
            if in_list:
                out_lines.append('</ul>')
                in_list = False
            num_idx = m_num.group(1)
            content = m_num.group(2)
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
            out_lines.append(f'<div style="margin: 6px 0;"><span style="color: #38bdf8; font-weight: 700;">{num_idx}.</span> {content}</div>')
            continue
            
        if in_list:
            out_lines.append('</ul>')
            in_list = False
            
        content = stripped
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
        out_lines.append(f'<p style="margin-bottom: 6px;">{content}</p>')
        
    if in_list:
        out_lines.append('</ul>')
        
    return '\n'.join(out_lines)

def build_sidebar(chapters, active_chapter_num, current_exercises):
    sb = []
    sb.append('<aside class="sidebar">')
    sb.append('  <div class="sidebar-header">')
    sb.append('    <a href="#top" class="logo-badge">')
    sb.append('      <span class="go-logo-icon">GO</span>')
    sb.append('      <span>Backend Workout</span>')
    sb.append('    </a>')
    sb.append('    <div class="sidebar-search">')
    sb.append('      <span class="search-icon">🔍</span>')
    sb.append('      <input type="text" id="search-input" placeholder="Поиск упражнений и тем..." autocomplete="off">')
    sb.append('    </div>')
    sb.append('  </div>')
    sb.append('  <nav class="sidebar-nav">')
    sb.append('    <div class="nav-group-title">Оглавление курса (83 модуля)</div>')
    
    for ch in chapters:
        num = ch['num']
        title = ch['title']
        
        status_map = {
            1: ('index.html', '91/91'),
            2: ('chapter2.html', '25/25'),
            3: ('chapter3.html', '65/65'),
            4: ('chapter4.html', '111/111'),
            5: ('chapter5.html', '64/64'),
            6: ('chapter6.html', '64/64'),
            7: ('chapter7.html', '32/32'),
            8: ('chapter8.html', '74/74'),
            9: ('chapter9.html', '62/62'),
            10: ('chapter10.html', '100/100'),
        }
        
        if num in status_map:
            href, badge = status_map[num]
            if active_chapter_num == num:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>{num}. {title}</strong></span>')
                sb.append(f'      <span class="status-badge done">{badge}</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append(f'    <a href="{href}" class="chapter-link">')
                sb.append(f'      <span>{num}. {title}</span>')
                sb.append(f'      <span class="status-badge done">{badge}</span>')
                sb.append('    </a>')
        else:
            sb.append('    <a href="javascript:void(0)" class="chapter-link" style="opacity: 0.65;" title="Глава в разработке">')
            sb.append(f'      <span>{num}. {title}</span>')
            sb.append('      <span class="status-badge soon">Скоро</span>')
            sb.append('    </a>')
            
    sb.append('  </nav>')
    sb.append('</aside>')
    return '\n'.join(sb)

def build_exercise_card(ex):
    ec = []
    ec.append(f'<div class="exercise-card" id="ex-{ex["num"]}">')
    
    # Header
    ec.append('  <div class="exercise-header">')
    ec.append(f'    <div class="exercise-num-badge">Упражнение #{ex["num"]}</div>')
    ec.append(f'    <div style="flex: 1;"><h3 class="exercise-title">{ex["title"]}</h3></div>')
    ec.append('  </div>')
    
    # 1. Task Callout
    ec.append('  <div class="callout callout-task">')
    ec.append('    <div class="callout-title">📌 Условие задачи</div>')
    ec.append(f'    <div>{format_text(ex["task"])}</div>')
    ec.append('  </div>')
    
    # 2. Theory Callout
    if ex.get("theory"):
        ec.append('  <div class="callout callout-theory">')
        ec.append('    <div class="callout-title">💡 Теоретический фундамент и концепция</div>')
        ec.append(f'    <div>{format_text(ex["theory"])}</div>')
        ec.append('  </div>')
        
    # 3. Step by step & thinking process
    if ex.get("step_by_step"):
        ec.append('  <div style="margin: 18px 0 10px;">')
        ec.append('    <h4 style="color: #38bdf8; font-size: 1.05rem; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">')
        ec.append('      <span>🔍</span> Пошаговый ход решения и ход мысли инженера')
        ec.append('    </h4>')
        ec.append(f'    <div style="color: #cbd5e1; font-size: 0.94rem;">{format_text(ex["step_by_step"])}</div>')
        ec.append('  </div>')
        
    # 4. Code Blocks
    if ex.get("code_blocks"):
        for cb in ex["code_blocks"]:
            ec.append('  <div class="code-container">')
            ec.append('    <div class="code-header">')
            ec.append(f'      <span class="code-filename">📄 {html.escape(cb["filename"])}</span>')
            ec.append('      <button class="copy-btn" title="Копировать код в буфер">Копировать</button>')
            ec.append('    </div>')
            lang_class = f'language-{cb.get("lang", "go")}'
            ec.append(f'    <pre class="{lang_class}"><code class="{lang_class}">{html.escape(cb["code"].strip())}</code></pre>')
            if cb.get("note"):
                ec.append(f'    <div class="code-note">ℹ️ {html.escape(cb["note"])}</div>')
            ec.append('  </div>')
            
    # 5. Under the Hood
    if ex.get("under_the_hood"):
        ec.append('  <div class="callout callout-hood">')
        ec.append('    <div class="callout-title">⚙️ Под капотом Go (Compiler, Linker & Runtime)</div>')
        ec.append(f'    <div>{format_text(ex["under_the_hood"])}</div>')
        ec.append('  </div>')
        
    # 6. Pitfalls & Traps
    if ex.get("pitfalls"):
        ec.append('  <div class="callout callout-pitfalls">')
        ec.append('    <div class="callout-title">⚠️ Частые грабли и ошибки новичков</div>')
        ec.append(f'    <div>{format_text(ex["pitfalls"])}</div>')
        ec.append('  </div>')
        
    # 7. BigTech & Interviews
    if ex.get("bigtech_interview"):
        ec.append('  <div class="callout callout-bigtech">')
        ec.append('    <div class="callout-title">🏢 В продакшене BigTech и на собеседованиях</div>')
        ec.append(f'    <div>{format_text(ex["bigtech_interview"])}</div>')
        ec.append('  </div>')
        
    ec.append('</div>')
    return '\n'.join(ec)

def build_chapter1_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=1, current_exercises=ch1_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🚀 Модуль 01 • Старт карьеры Go-разработчика</div>
        <h1 class="hero-title">Пакеты, Модули и Архитектура Проекта в Go</h1>
        <p class="hero-desc">
            Фундаментальный интерактивный учебник-тренажер для уверенно-начинающих бэкенд-инженеров, 
            нацеленных на трудоустройство в сильные технологические компании и BigTech (Яндекс, Ozon, Авито, Т-Банк, ВК). 
            Полный пошаговый разбор всех 91 упражнений курса с глубоким анализом работы компилятора, рантайма и продакшен-практик.
        </p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-val">91 из 91</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">100%</span>
                <span class="stat-lbl">Теория + Практика</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">83</span>
                <span class="stat-lbl">Главы курса</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Go 1.22+</span>
                <span class="stat-lbl">Стандарт индустрии</span>
            </div>
        </div>
    </section>
    """)
    
    section_groups = [
        (1, 15, "Раздел 1: Введение, Окружение, Компиляция и Базовые Пакеты", "Основы Go-модулей, многофайловые пакеты main, go run, go build, error handling и первые пакеты"),
        (16, 30, "Раздел 2: Внешние Зависимости, Инкапсуляция, Init() и Качество Кода", "Подключение библиотек, правила экспорта, жизненный цикл функций init(), go fmt и go vet"),
        (31, 45, "Раздел 3: SemVer, Локальный Replace, Кросс-компиляция и UUID", "Директива replace, семантическое версионирование v1/v2, флаги GOOS/GOARCH и runtime-инициализация"),
        (46, 60, "Раздел 4: CLI на Cobra, Структурированные Логи, Дженерики и Тесты", "Разработка CLI-утилит на Cobra, logrus с multi-writer, constraints.Ordered и табличные юнит-тесты"),
        (61, 75, "Раздел 5: Анатомия go.mod, Безопасность govulncheck, GOPRIVATE и Internal", "Глубокий анализ go.mod/go.sum, аудит уязвимостей, приватные репозитории и правила каталога internal/"),
        (76, 91, "Раздел 6: Паттерн Registry, Бенчмаркинг, Ldflags, Vendor и Standard Layout", "Драйверы плагинов, снятие pprof-профилей, тестирование производительности benchmem, вендоринг и эталонный Standard Go Project Layout")
    ]
    
    ex_dict = {e["num"]: e for e in ch1_exercises}
    for start_n, end_n, title, desc in section_groups:
        content_parts.append(f"""
        <div class="section-separator">
            <div>
                <h2>{title}</h2>
                <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div>
            </div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
                
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 01 полностью пройдена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы успешно изучили фундаментальные механизмы пакетов и модулей Go. Переходите к следующей главе!
        </p>
        <a href="chapter2.html" style="display: inline-flex; align-items: center; gap: 8px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 20px; border-radius: 8px; text-decoration: none; transition: transform 0.2s;">
            <span>Перейти к Главе 02: Компиляция, сборка и запуск</span> →
        </a>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter2_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=2, current_exercises=ch2_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">⚡ Модуль 02 • Компиляция и Сборка Проектов</div>
        <h1 class="hero-title">Компиляция, Сборка и Запуск Go-программ</h1>
        <p class="hero-desc">
            Полный практический курс по низкоуровневой механике компилятора Go, флагам линкера, кросс-компиляции, 
            детектору гонок данных (-race), перехвату сигналов ОС (Graceful Shutdown), автоматизации сборки и 
            ультра-компактной Docker-контейнеризации (от 5 МБ Scratch). Все 25 упражнений решены шаг за шагом.
        </p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">25 из 25</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">Multi-stage</span><span class="stat-lbl">Docker Scratch</span></div>
            <div class="stat-item"><span class="stat-val">-race</span><span class="stat-lbl">ThreadSanitizer</span></div>
            <div class="stat-item"><span class="stat-val">-ldflags</span><span class="stat-lbl">DWARF Strip & Inject</span></div>
        </div>
    </section>
    """)
    section_groups_ch2 = [
        (1, 4, "Раздел 1: Базовая Компиляция, go run и go build", "Анатомия компилятора, нативные бинарники, запуск автономных модулей"),
        (5, 9, "Раздел 2: Кросс-компиляция и Установка через go install", "Переменные GOOS/GOARCH, установка в GOPATH/bin, флаг кастомизации -o"),
        (10, 14, "Раздел 3: Статанализ, Детектор Гонок и Форматы Бинарников", "Рекурсивный go fmt, ThreadSanitizer -race, go vet и матричные скрипты"),
        (15, 18, "Раздел 4: Жизненный Цикл, Многофайловый main и Стриппинг", "Хронология init(), структура пакета main, оптимизация размера через -ldflags='-s -w'"),
        (19, 22, "Раздел 5: CLI Флаги, Подкоманды и Устранение Data Race", "Парсинг через flag.NewFlagSet, инъекция версий -X, синхронизация через sync.Mutex"),
        (23, 25, "Раздел 6: Graceful Shutdown, CI Скрипты и Docker Scratch", "Мягкая остановка при SIGINT/SIGTERM, CI-пайплайн и Dockerfile сборка от 5 МБ")
    ]
    ex_dict = {e["num"]: e for e in ch2_exercises}
    for start_n, end_n, title, desc in section_groups_ch2:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 02 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 01</a>
            <a href="chapter3.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 03: fmt и ввод-вывод →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '02. Компиляция, сборка и запуск (25/25)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter3_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=3, current_exercises=ch3_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">💻 Модуль 03 • Консольный Ввод-Вывод и fmt</div>
        <h1 class="hero-title">Пакет fmt и Консольный Ввод-Вывод в Go</h1>
        <p class="hero-desc">Глубокое практическое руководство по потоковому вводу-выводу в Go: спецификаторы fmt, bufio.Reader/Scanner, UTF-8 руны, Stringer и ANSI-стилизация. 65 упражнений решено.</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">65 из 65</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">bufio</span><span class="stat-lbl">Reader & Scanner</span></div>
            <div class="stat-item"><span class="stat-val">fmt.Stringer</span><span class="stat-lbl">Кастомная печать</span></div>
            <div class="stat-item"><span class="stat-val">ANSI & TUI</span><span class="stat-lbl">Цветные терминалы</span></div>
        </div>
    </section>
    """)
    section_groups_ch3 = [
        (1, 15, "Раздел 1: Базовые функции fmt, Спецификаторы и Первые Чтения", "Print, Println, Printf, %d/%f/%s/%t, буферизованный ReadByte, выравнивание %4d, парсинг Sscanf и время"),
        (16, 30, "Раздел 2: Потоки, Инспекция Типов, Точность Float и Stderr", "Эхо-сканер, сложение с валидацией, глагол %T, точность %.2f, экранирование %q, запись в os.Stderr и fmt.Sprintf"),
        (31, 45, "Раздел 3: Проблема Пробелов, Scanln, Файловый Fprintf и EOF", "Механика токенизации Scan, Scanln, календарный Scanf, запись в io.Writer, обработка io.EOF и CLI-анкеты"),
        (46, 55, "Раздел 4: Unicode Руны, Интерфейс fmt.Stringer, Stderr 2> и os.Args", "ReadRune, UTF-8 кодовые точки, Stringer/GoStringer контракты, флаги командной строки flag.Int"),
        (56, 65, "Раздел 5: Продвинутый REPL, ScanWords, Таблицы, Прогресс-бар и ANSI", "Сравнительный анализ семейств Scan, REPL-шелл, суммирование потока ScanWords, анимация \\r и цветной вывод")
    ]
    ex_dict = {e["num"]: e for e in ch3_exercises}
    for start_n, end_n, title, desc in section_groups_ch3:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 03 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter2.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 02</a>
            <a href="chapter4.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 04: Базовые типы →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '03. Пакет fmt и консольный ввод-вывод (65/65)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter4_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=4, current_exercises=ch4_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🧬 Модуль 04 • Система Типов и Память Go</div>
        <h1 class="hero-title">Базовые Типы, Переменные и Константы в Go</h1>
        <p class="hero-desc">Zero Values, IEEE 754, переполнение, выравнивание памяти (Memory Padding & Alignment), iota и битовые маски. Все 111 упражнений решены.</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">111 из 111</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">Zero Values</span><span class="stat-lbl">Memory Safety</span></div>
            <div class="stat-item"><span class="stat-val">iota & Bitmasks</span><span class="stat-lbl">State Enums</span></div>
            <div class="stat-item"><span class="stat-val">Padding</span><span class="stat-lbl">Memory Alignment</span></div>
        </div>
    </section>
    """)
    section_groups_ch4 = [
        (1, 20, "Раздел 1: Объявление Переменных, Zero Values, Размеры Типов и Первые Константы", "var, :=, Zero values, unsafe.Sizeof, Pi, iota, нетипизированные константы, затенение и UTF-8 руны"),
        (21, 40, "Раздел 2: Хэш-таблицы, Комплексные Числа, Структуры, strconv и Битовые Операции", "map с comma-ok, complex128, композиция структур, strconv, побитовые &, |, ^, &^, strings и Constant Folding"),
        (41, 60, "Раздел 3: Явное Приведение, Безопасная Арифметика, Переполнение и Области Видимости", "Приведение типов, SafeAdd с проверкой границ, множественный swap a, b = b, a, bare blocks и глобальные переменные"),
        (61, 80, "Раздел 4: Указатели new(), Точность Float32/Float64, Лимиты math и Битовые Маски", "Выделение памяти new(int), IEEE 754 погрешности, пределы типов math.Max, KB/MB/GB на iota, типы Celsius/Fahrenheit и битовые права"),
        (81, 95, "Раздел 5: Type Definitions, Выравнивание Памяти (Padding), Лимиты и Циклический Сдвиг", "Кастомные типы, паддинг в структурах, AlmostEqual с эпсилон, все 6 способов объявления, math.Min/Max и циклический сдвиг a, b, c = b, c, a"),
        (96, 111, "Раздел 6: Самоссылающиеся Структуры, defer LIFO, make(), Raw Strings и Защита Иммутабельности", "Связный список Node, LIFO в defer, make() для срезов/мап/каналов, BigInt 1<<100, Raw Strings, обход отсутствия const-слайсов и Jump Table в switch")
    ]
    ex_dict = {e["num"]: e for e in ch4_exercises}
    for start_n, end_n, title, desc in section_groups_ch4:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 04 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter3.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 03</a>
            <a href="chapter5.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 05: Условные конструкции →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '04. Базовые типы, переменные и константы (111/111)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter5_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=5, current_exercises=ch5_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🔀 Модуль 05 • Управляющие Конструкции и Ветвления</div>
        <h1 class="hero-title">Условные Конструкции (if, switch) в Go</h1>
        <p class="hero-desc">Каскадные условия if/else, if with short init, Guard Clauses, Tagless Switch, Type Switch, fallthrough, comma-ok и FSM. 64 упражнения решено.</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">64 из 64</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">if with init</span><span class="stat-lbl">Scope Isolation</span></div>
            <div class="stat-item"><span class="stat-val">Tagless Switch</span><span class="stat-lbl">Jump Table $O(1)$</span></div>
            <div class="stat-item"><span class="stat-val">Guard Clauses</span><span class="stat-lbl">Clean Code Pattern</span></div>
        </div>
    </section>
    """)
    section_groups_ch5 = [
        (1, 16, "Раздел 1: Базовый if, Четность, Инициализация в if, Каскады и Зодиак", "Каскадные if/else, проверка четности %, if x := init(); cond, классификация возраста, 100-балльная шкала, Divide с err, затенение в if, високосный год и булевы упрощения"),
        (17, 32, "Раздел 2: Классический switch, Строковый switch, True Switch, Группировка и Type Switch", "Дни недели, команды CLI, tagless switch, множественные значения case 1, 2, 3:, сезоны года, Type Switch над any, сужение типов v.(type) и семантика fallthrough"),
        (33, 48, "Раздел 3: Имитация Тернарного Оператора, Guard Clauses, Short-Circuit, for-while и Валидация Пароля", "Функция Max, каскадный fallthrough, инспекция типов, инициализация в switch, рефакторинг вложенности, break в switch, инверсия условий, битовые предикаты, FizzBuzz, for как while и поиск Min/Max"),
        (49, 64, "Раздел 4: Comma-ok в if, Вложенный switch, goto, Права Файлов, Dispatch Table и Конечный Автомат (FSM)", "Группировка Yes/No, чтение из map, шорткаты предикатов, подсчет гласных, goto в матрицах, битовые флаги 0755, CLI-калькулятор, Dispatch Table на map[string]func(), FSM игрового NPC и меню с labeled break")
    ]
    ex_dict = {e["num"]: e for e in ch5_exercises}
    for start_n, end_n, title, desc in section_groups_ch5:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 05 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter4.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 04</a>
            <a href="chapter6.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 06: Циклы →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '05. Условные конструкции (64/64)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter6_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=6, current_exercises=ch6_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🔄 Модуль 06 • Итерации и Управление Потоком</div>
        <h1 class="hero-title">Циклы (for, for-range) и Итераторы в Go</h1>
        <p class="hero-desc">Итерационные алгоритмы, Two Pointers (In-place $O(1)$), Loopvar Scope Go 1.22+, каналы chan, defer в циклах, недетерминированный map и батчинг. 64 упражнения решено.</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">64 из 64</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">for range</span><span class="stat-lbl">Slices, Maps, Chans</span></div>
            <div class="stat-item"><span class="stat-val">Go 1.22+</span><span class="stat-lbl">Loopvar Per-Iteration Scope</span></div>
            <div class="stat-item"><span class="stat-val">Two Pointers</span><span class="stat-lbl">In-place $O(1)$ Space</span></div>
        </div>
    </section>
    """)
    section_groups_ch6 = [
        (1, 16, "Раздел 1: Простые Числа, Two Pointers, 2D Слайсы, Шаг i+=2, Степени Двойки и Анализ Строк", "Trial division с sqrt, проверка палиндрома, угадай число, таблица 2D, трехкомпонентный for, for-while, for range по map и Unicode руны"),
        (17, 32, "Раздел 2: Бесконечные Циклы, Таблица Умножения, Loopvar Scope в Go 1.22, Labeled Break и Ловушка Defer", "Break по exit, моноширинный %4d, for x < 100, &item указатели, for i := range, Labeled Break/Continue в матрицах, рандомизация map, UTF-8 байты и изоляция defer"),
        (33, 48, "Раздел 3: Разворот In-Place, Локальность Break, UTF-8 Привет, Каналы chan int и Паттерн Do-While", "Три способа суммирования, two pointers reverse, игнорирование параметров, break Label синтаксис, побайтовый vs посимвольный обход, ловушка копирования v*=10, range по каналу и do-while"),
        (49, 64, "Раздел 4: Копирование Структур []Person, Массив [5]int vs Срез, Мутация Map/Slice, Скобки и Пагинация", "Копирование структур по значению, array vs slice в range, UTF-8 Привет Go!, поиск первого вхождения, мутация map во время range, опасность append в range, безопасный nil-range, стек скобок и батчинг по 10 штук")
    ]
    ex_dict = {e["num"]: e for e in ch6_exercises}
    for start_n, end_n, title, desc in section_groups_ch6:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 06 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter5.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 05</a>
            <a href="chapter7.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 07: Массивы →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '06. Циклы (64/64)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter7_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=7, current_exercises=ch7_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">📦 Модуль 07 • Структуры Данных и Память</div>
        <h1 class="hero-title">Массивы (Arrays) и Модель Памяти в Go</h1>
        <p class="hero-desc">Фиксированные массивы в Go: семантика значений (Pass by Value & Deep Copy), непрерывное расположение в стеке, unsafe.Sizeof/Alignof, ключи в map и static bounds check. 32 упражнения решено.</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">32 из 32</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">Value Semantics</span><span class="stat-lbl">Deep Copy $O(N)$</span></div>
            <div class="stat-item"><span class="stat-val">Comparable</span><span class="stat-lbl">Keys in map[K]V</span></div>
            <div class="stat-item"><span class="stat-val">Zero Overhead</span><span class="stat-lbl">0B Header Size</span></div>
        </div>
    </section>
    """)
    section_groups_ch7 = [
        (1, 16, "Раздел 1: Инициализация, Zero Values, Value Semantics, Сравнение и 2D Матрицы", "3 способа инициализации, len() константа, значимая семантика b:=a, массив строк, SumArray по значению, comparable ==, палиндром, матрица [3][4]int, синтаксис [...] и сетка 3x3"),
        (17, 32, "Раздел 2: Указатели *[N]T, unsafe.Sizeof/Alignof, Массив как Ключ Map и Защита Границ", "Удвоение массива, Zero Values [3]bool/[2]string, мутация через *[5]int, массив указателей [3]*int, размер в памяти unsafe, Bubble Sort, экстремумы, RGB палитра map[[3]int]string, In-place reverse и Bounds Checking")
    ]
    ex_dict = {e["num"]: e for e in ch7_exercises}
    for start_n, end_n, title, desc in section_groups_ch7:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 07 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter6.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 06</a>
            <a href="chapter8.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 08: Срезы (Slices) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '07. Массивы (32/32)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter8_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=8, current_exercises=ch8_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🍰 Модуль 08 • Динамические Коллекции</div>
        <h1 class="hero-title">Срезы (Slices) и Модель Памяти в Go</h1>
        <p class="hero-desc">Дескриптор SliceHeader (Data, Len, Cap), геометрический рост append, трехзначный слайсинг s[low:high:max], предотвращение утечек памяти, In-Place фильтрация и пакет slices. 74 упражнения решено.</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">74 из 74</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">SliceHeader</span><span class="stat-lbl">Data, Len, Cap (24B)</span></div>
            <div class="stat-item"><span class="stat-val">Zero Alloc</span><span class="stat-lbl">In-Place & Pre-alloc</span></div>
            <div class="stat-item"><span class="stat-val">slices (1.21+)</span><span class="stat-lbl">Generics & Fast Sort</span></div>
        </div>
    </section>
    """)
    section_groups_ch8 = [
        (1, 18, "Раздел 1: Базовый Массив, Создание Срезов, make, Рост append, Трехзначный Слайсинг и InspectSlice", "len/cap свойства, [...] vs [], окно в массив arr[1:4], make(3, 5), несравнимость [2][]int, стратегия роста append, вариативный append..., ре-слайсинг s[:cap], cap(s[1:3]), паника out of bounds, s[low:high:max], расщепление связи, безопасный copy, срез строк, утилита InspectSlice и трюк удаления"),
        (19, 37, "Раздел 2: Ловушка Реаллокации в Функциях, Вставка со Сдвигом, Overlapping Copy, Nil vs Empty в JSON и s[:0]", "make([]int, 3), потеря мутаций в функциях, пошаговый append, вставка append+copy, InsertAt, безопасный сдвиг memmove, Filter, срез из [6]int, матрица [][]int, nil vs empty срез в REST API, переиспользование s[:0], возврат copy и запись вне len"),
        (38, 56, "Раздел 3: Копирование Структур, DeleteByIndex, Смена Адресов &s[0], In-Place Filter, Fast Delete и Утечки Памяти", "for range по []Person, сохранение underlying array при удалении, коллизии s2[0]=99, отслеживание смены &s[0], идиоматичный возврат срезов, FilterInPlace за 0B, FastDelete за O(1), ChunkSlice, memory leak 1MB и предвыделение make(0, 100)"),
        (57, 74, "Раздел 4: In-Place Reverse, Пакет slices (Go 1.21+), LIFO Стек, Multi-Sort, Jagged Arrays и Треугольные Срезы", "Разворот на месте, утечка в суффиксе big, s[:0] в sync.Pool, IsSorted на cmp.Ordered, стек Push/Pop, sort.Slice, O(1) vs O(N) удаление, современный пакет slices, Union без дубликатов, slices.DeleteFunc, сбор указателей []*int, slices.SortFunc и треугольный срез")
    ]
    ex_dict = {e["num"]: e for e in ch8_exercises}
    for start_n, end_n, title, desc in section_groups_ch8:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 08 полностью завершена!</h3>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter7.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 07</a>
            <a href="chapter9.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 09: Хэш-таблицы (Maps) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '08. Слайсы (74/74)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter9_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=9, current_exercises=ch9_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🗺️ Модуль 09 • Хэш-Таблицы и Ассоциативные Массивы</div>
        <h1 class="hero-title">Мапы (Maps) и Модель Памяти в Go</h1>
        <p class="hero-desc">
            Глубокое инженерное руководство по ассоциативным массивам и хэш-таблицам в Go: 
            детальный разбор внутреннего устройства `hmap` и бакетов `bmap` (8 пар на бакет, tophash), 
            идиома `comma-ok` для различения нуля и отсутствия, реализация множеств (Set) на `struct{}` с нулевым оверхедом, 
            таблицы диспетчеризации `map[string]func`, потокобезопасность и детектор гонок `concurrent map writes`, 
            устранение скрытых утечек памяти при массовых удалениях, мемоизация и пакет `maps` (Go 1.21+). 
            Все 62 упражнения курса решены шаг за шагом.
        </p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">62 из 62</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">hmap & bmap</span><span class="stat-lbl">8 слотов на бакет</span></div>
            <div class="stat-item"><span class="stat-val">Set struct{}</span><span class="stat-lbl">Zero-Byte Overhead</span></div>
            <div class="stat-item"><span class="stat-val">maps (1.21+)</span><span class="stat-lbl">Clone, Copy, Equal</span></div>
        </div>
    </section>
    """)
    section_groups_ch9 = [
        (1, 15, "Раздел 1: Базовые Операции, Zero Values, Nil Map, Comma-ok, delete и Comparable Структуры", "Чтение несуществующего ключа, паника записи в nil, литералы, comma-ok val, ok := m[k], SafeGet, delete без паник, вложенные мапы, Point как ключ, append к срезу в мапе, несравнимость m1 == m2, частотный словарь слов и рун"),
        (16, 31, "Раздел 2: Указатели как Ключи, Set на struct{}, Command Dispatcher, Инверсия и Сортировка", "*Point по адресу памяти, Set на struct{} (0 байт), Command Dispatcher map[string]func, CLI-калькулятор, детекция коллизий при инверсии, ловушка for _, v := range m { v++ }, Comma-ok для столиц и детерминированная сортировка ключей"),
        (32, 47, "Раздел 3: Очистка clear(m), Недетерминированность, Запрет Срезов в Ключах, Конкурентная Запись и Top-K", "Встроенный clear(m) Go 1.21+, fastrand в итераторе, запрет map[[]int], fatal error: concurrent map writes, sync.RWMutex, указатели на структуры map[int]*User, Multi-Map со срезами, GetOrCreate, Top-K частых слов и частота рун"),
        (48, 62, "Раздел 4: Безопасный delete в range, MergeMaps, Запрет Адресации &m[k], Утечка Памяти Бакетов и Мемоизация", "delete в цикле for k := range m, MergeMaps с nil-защитой, Set на struct{} vs bool, инверсия с группировкой в срез, запрет &m[k] из-за эвакуации, классификация типов ключей, EqualMaps, пакет maps (Go 1.21+), утечка памяти в hmap.B, мемоизация Фибоначчи и иерархическое расписание")
    ]
    ex_dict = {e["num"]: e for e in ch9_exercises}
    for start_n, end_n, title, desc in section_groups_ch9:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 09 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили хэш-таблицы, устройство бакетов hmap, потокобезопасность с мьютексами и предотвращение утечек памяти.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter8.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 08 (Слайсы)</a>
            <a href="chapter10.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 10: Функции →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '09. Мапы (62/62)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter10_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=10, current_exercises=ch10_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">⚙️ Модуль 10 • Функциональное Программирование и Управление Вызовами</div>
        <h1 class="hero-title">Функции (все виды и вариации) в Go</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по функциям в Go: именованные возвраты и ловушки Naked Return, 
            вариативные параметры `...T` и распаковка срезов, замыкания (Closures) и Escape-анализ переменных в кучу, 
            стековый порядок выполнения `defer` (LIFO) и замер времени `time.Since`, безопасный перехват паники через `recover()`, 
            паттерн Декоратор (Middleware), функции высшего порядка (Map/Filter/Reduce), оптимизация рекурсии через мемоизацию за $O(N)$ 
            и параметрический полиморфизм (Дженерики `cmp.Ordered`). Все 100 упражнений решены шаг за шагом.
        </p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">100 из 100</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">Closures</span><span class="stat-lbl">Heap Escape</span></div>
            <div class="stat-item"><span class="stat-val">defer & recover</span><span class="stat-lbl">Zero-Cost LIFO</span></div>
            <div class="stat-item"><span class="stat-val">cmp.Ordered</span><span class="stat-lbl">Type Parameters</span></div>
        </div>
    </section>
    """)
    section_groups_ch10 = [
        (1, 25, "Раздел 1: Базовые Функции, Именованные Возвраты, Вариативность, Unicode Реверс и Замыкания", "Сигнатуры без возврата, Named Returns, Naked Return, variadic ...T, распаковка среза slice..., инверсия рун []rune, MakeCounter, множественный возврат (T, error), рекурсия факториала, каррирование и семантика передачи массивов по значению"),
        (26, 50, "Раздел 2: Чистые Функции, Методы на Структурах, Stringer, Type Switch, IIFE и Затенение", "Инлайнинг, defer в main, методы с указателем-получателем (r *Rectangle), fmt.Stringer, группировка параметров, закрытие файлов RAII, Type Switch .(type), чистые функции, исторический баг замыканий в цикле и ловушка затенения в Naked Return"),
        (51, 75, "Раздел 3: Функции Высшего Порядка, Сортировка sort.Slice, Диспетчеризация, Деревья и Декораторы", "ApplyOperation, многокритериальная сортировка, строковые заголовки, калькулятор map[string]func, Sentinel ошибки, рекурсивный String() дерева, переменные функций, изоляция defer в циклах, ID-генератор, каверзный случай defer и паттерн Декоратор (Middleware)"),
        (76, 100, "Раздел 4: Функциональные Типы, Замер Времени time.Since, Panic/Recover, Reduce, Мемоизация и Дженерики", "Пользовательские функциональные типы type MathFunc, time.Since(start) в defer, фабрика множителей, каскадная размотка стека при панике, свертка Reduce/Fold, безопасный факториал int64, бенчмарк мемоизации Фибоначчи за O(N), таймер defer Timer()() и дженерики cmp.Ordered")
    ]
    ex_dict = {e["num"]: e for e in ch10_exercises}
    for start_n, end_n, title, desc in section_groups_ch10:
        content_parts.append(f"""
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 10 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве изучили все вариации функций в Go: замыкания, стек defer, перехват паник через recover, функции высшего порядка и дженерики.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter9.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 09 (Мапы)</a>
            <a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 11: Указатели (Скоро) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '10. Функции (100/100)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

if __name__ == '__main__':
    chapters = get_all_chapters()
    
    pages = [
        ('index.html', build_chapter1_html),
        ('chapter2.html', build_chapter2_html),
        ('chapter3.html', build_chapter3_html),
        ('chapter4.html', build_chapter4_html),
        ('chapter5.html', build_chapter5_html),
        ('chapter6.html', build_chapter6_html),
        ('chapter7.html', build_chapter7_html),
        ('chapter8.html', build_chapter8_html),
        ('chapter9.html', build_chapter9_html),
        ('chapter10.html', build_chapter10_html),
    ]
    
    for filename, builder_fn in pages:
        path = os.path.join('/home/ut/work/go-workout', filename)
        content = builder_fn(chapters)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Written {path} ({os.path.getsize(path)} bytes)")
