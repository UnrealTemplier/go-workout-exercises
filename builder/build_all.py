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
        
        if num == 1:
            if active_chapter_num == 1:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>1. {title}</strong></span>')
                sb.append('      <span class="status-badge done">91/91</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="index.html" class="chapter-link">')
                sb.append(f'      <span>1. {title}</span>')
                sb.append('      <span class="status-badge done">91/91</span>')
                sb.append('    </a>')
        elif num == 2:
            if active_chapter_num == 2:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>2. {title}</strong></span>')
                sb.append('      <span class="status-badge done">25/25</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="chapter2.html" class="chapter-link">')
                sb.append(f'      <span>2. {title}</span>')
                sb.append('      <span class="status-badge done">25/25</span>')
                sb.append('    </a>')
        elif num == 3:
            if active_chapter_num == 3:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>3. {title}</strong></span>')
                sb.append('      <span class="status-badge done">65/65</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="chapter3.html" class="chapter-link">')
                sb.append(f'      <span>3. {title}</span>')
                sb.append('      <span class="status-badge done">65/65</span>')
                sb.append('    </a>')
        elif num == 4:
            if active_chapter_num == 4:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>4. {title}</strong></span>')
                sb.append('      <span class="status-badge done">111/111</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="chapter4.html" class="chapter-link">')
                sb.append(f'      <span>4. {title}</span>')
                sb.append('      <span class="status-badge done">111/111</span>')
                sb.append('    </a>')
        elif num == 5:
            if active_chapter_num == 5:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>5. {title}</strong></span>')
                sb.append('      <span class="status-badge done">64/64</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="chapter5.html" class="chapter-link">')
                sb.append(f'      <span>5. {title}</span>')
                sb.append('      <span class="status-badge done">64/64</span>')
                sb.append('    </a>')
        elif num == 6:
            if active_chapter_num == 6:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>6. {title}</strong></span>')
                sb.append('      <span class="status-badge done">64/64</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="chapter6.html" class="chapter-link">')
                sb.append(f'      <span>6. {title}</span>')
                sb.append('      <span class="status-badge done">64/64</span>')
                sb.append('    </a>')
        elif num == 7:
            if active_chapter_num == 7:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>7. {title}</strong></span>')
                sb.append('      <span class="status-badge done">32/32</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {ex["title"]}">{ex["num"]}. {ex["title"]}</a>')
                sb.append('    </div>')
            else:
                sb.append('    <a href="chapter7.html" class="chapter-link">')
                sb.append(f'      <span>7. {title}</span>')
                sb.append('      <span class="status-badge done">32/32</span>')
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
    
    # Hero Section
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
    
    # Hero Section
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
            <div class="stat-item">
                <span class="stat-val">25 из 25</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Multi-stage</span>
                <span class="stat-lbl">Docker Scratch</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">-race</span>
                <span class="stat-lbl">ThreadSanitizer</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">-ldflags</span>
                <span class="stat-lbl">DWARF Strip & Inject</span>
            </div>
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 02 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили весь цикл сборки, профилирования, кросс-компиляции, безопасного завершения сервисов и упаковки в Docker.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">
                ← Вернуться к Главе 01 (Пакеты и модули)
            </a>
            <a href="chapter3.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">
                Перейти к Главе 03: Пакет fmt и консольный ввод-вывод →
            </a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '02. Компиляция, сборка и запуск (25/25)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter3_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=3, current_exercises=ch3_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">💻 Модуль 03 • Консольный Ввод-Вывод и fmt</div>
        <h1 class="hero-title">Пакет fmt и Консольный Ввод-Вывод в Go</h1>
        <p class="hero-desc">
            Глубокое практическое руководство по потоковому вводу-выводу в Go: детальный разбор всех спецификаторов пакета fmt, 
            буферизованное чтение через bufio.Reader/Scanner, посимвольная обработка UTF-8 рун, интерфейсы fmt.Stringer и fmt.GoStringer, 
            валидация потоков Stdin/Stdout/Stderr, создание надежных CLI REPL-интерпретаторов и цветная ANSI-стилизация. 
            Все 65 упражнений курса решены с пошаговым объяснением.
        </p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-val">65 из 65</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">bufio</span>
                <span class="stat-lbl">Reader & Scanner</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">fmt.Stringer</span>
                <span class="stat-lbl">Кастомная печать</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">ANSI & TUI</span>
                <span class="stat-lbl">Цветные терминалы</span>
            </div>
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 03 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы освоили весь арсенал работы с потоками ввода-вывода, интерфейсами Stringer, форматированием и терминальной графикой.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter2.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">
                ← Вернуться к Главе 02 (Компиляция и сборка)
            </a>
            <a href="chapter4.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">
                Перейти к Главе 04: Базовые типы, переменные и константы →
            </a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '03. Пакет fmt и консольный ввод-вывод (65/65)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter4_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=4, current_exercises=ch4_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🧬 Модуль 04 • Система Типов и Память Go</div>
        <h1 class="hero-title">Базовые Типы, Переменные и Константы в Go</h1>
        <p class="hero-desc">
            Фундаментальное инженерное погружение в статическую систему типов языка Go: Zero Values, разрядная сетка процессора, 
            стандарты IEEE 754 чисел с плавающей точкой, переполнение (Integer Overflow), выравнивание памяти (Memory Padding & Alignment), 
            нетипизированные константы, генератор перечислений iota, битовые маски и безопасное управление иммутабельностью. 
            Все 111 упражнений курса решены с пошаговым разбором.
        </p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-val">111 из 111</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Zero Values</span>
                <span class="stat-lbl">Memory Safety</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">iota & Bitmasks</span>
                <span class="stat-lbl">State Enums</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Padding</span>
                <span class="stat-lbl">Memory Alignment</span>
            </div>
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 04 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы досконально изучили устройство типов, память, константы, iota и внутренние оптимизации компилятора Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter3.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">
                ← Вернуться к Главе 03 (Пакет fmt)
            </a>
            <a href="chapter5.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">
                Перейти к Главе 05: Условные конструкции (if, switch) →
            </a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '04. Базовые типы, переменные и константы (111/111)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter5_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=5, current_exercises=ch5_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🔀 Модуль 05 • Управляющие Конструкции и Ветвления</div>
        <h1 class="hero-title">Условные Конструкции (if, switch) в Go</h1>
        <p class="hero-desc">
            Глубокое практическое освоение механизмов управления потоком исполнения в Go: каскадные условия if/else, 
            изоляция переменных через if с инициализацией (short statement), плоский стиль Guard Clauses (Early Return), 
            оптимизация ветвлений через Tagless Switch (Switch True), инспекция динамических типов в Type Switch v.(type), 
            механика fallthrough, короткое замыкание предикатов (Short-Circuit), идиома comma-ok и построение конечных автоматов (FSM). 
            Все 64 упражнения курса решены с пошаговым объяснением.
        </p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-val">64 из 64</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">if with init</span>
                <span class="stat-lbl">Scope Isolation</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Tagless Switch</span>
                <span class="stat-lbl">Jump Table $O(1)$</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Guard Clauses</span>
                <span class="stat-lbl">Clean Code Pattern</span>
            </div>
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 05 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили условные ветвления, Guard Clauses, Type Switch и конечные автоматы на Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter4.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">
                ← Вернуться к Главе 04 (Базовые типы)
            </a>
            <a href="chapter6.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">
                Перейти к Главе 06: Циклы (for, for-range) →
            </a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '05. Условные конструкции (64/64)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter6_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=6, current_exercises=ch6_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🔄 Модуль 06 • Итерации и Управление Потоком</div>
        <h1 class="hero-title">Циклы (for, for-range) и Итераторы в Go</h1>
        <p class="hero-desc">
            Исчерпывающий практический курс по итерационным алгоритмам и низкоуровневой механике циклов в Go: 
            трехкомпонентный for, while-стиль, бесконечные REPL-серверы, алгоритмы Two Pointers (In-place $O(1)$), 
            глубокий разбор бага замыкания Loop Variables до и после Go 1.22+, обход каналов `chan`, предотвращение утечек 
            дескрипторов в `defer`, UTF-8 смещения рун, недетерминированная итерация по `map`, стек скобок и промышленная пагинация (Batching). 
            Все 64 упражнения курса решены шаг за шагом.
        </p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-val">64 из 64</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">for range</span>
                <span class="stat-lbl">Slices, Maps, Chans</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Go 1.22+</span>
                <span class="stat-lbl">Loopvar Per-Iteration Scope</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Two Pointers</span>
                <span class="stat-lbl">In-place $O(1)$ Space</span>
            </div>
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 06 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили все виды циклов, Two Pointers, каналы, Labeled-метки и эффективную работу с памятью в Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter5.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">
                ← Вернуться к Главе 05 (Условные конструкции)
            </a>
            <a href="chapter7.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">
                Перейти к Главе 07: Массивы (Arrays) →
            </a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '06. Циклы (64/64)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter7_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=7, current_exercises=ch7_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">📦 Модуль 07 • Структуры Данных и Память</div>
        <h1 class="hero-title">Массивы (Arrays) и Модель Памяти в Go</h1>
        <p class="hero-desc">
            Глубокое практическое освоение фиксированных массивов в языке Go: семантика значений (Pass by Value & Deep Copy), 
            непрерывное расположение в стеке (Contiguous Memory Layout), zero values, вычисление размера через unsafe.Sizeof и unsafe.Alignof, 
            сравнение через операторы == / !=, многомерные матрицы [N][M]T, разворот In-Place через указатели *[N]T, 
            использование массивов как ключей в hash-map и двухуровневая защита границ (Static vs Runtime Bounds Checking). 
            Все 32 упражнения курса решены шаг за шагом.
        </p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-val">32 из 32</span>
                <span class="stat-lbl">Упражнений решено</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Value Semantics</span>
                <span class="stat-lbl">Deep Copy $O(N)$</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Comparable</span>
                <span class="stat-lbl">Keys in map[K]V</span>
            </div>
            <div class="stat-item">
                <span class="stat-val">Zero Overhead</span>
                <span class="stat-lbl">0B Header Size</span>
            </div>
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 07 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы досконально изучили массивы, передачу по значению, указатели и низкоуровневую модель памяти в Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter6.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">
                ← Вернуться к Главе 06 (Циклы)
            </a>
            <a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">
                Глава 08: Срезы (Slices) (Скоро) →
            </a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '07. Массивы (32/32)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

if __name__ == '__main__':
    chapters = get_all_chapters()
    
    # 1. Build index.html (Chapter 1)
    ch1_html = build_chapter1_html(chapters)
    with open('/home/ut/work/go-workout/index.html', 'w', encoding='utf-8') as f:
        f.write(ch1_html)
    print(f"Chapter 1 written to /home/ut/work/go-workout/index.html ({os.path.getsize('/home/ut/work/go-workout/index.html')} bytes)")
    
    # 2. Build chapter2.html (Chapter 2)
    ch2_html = build_chapter2_html(chapters)
    with open('/home/ut/work/go-workout/chapter2.html', 'w', encoding='utf-8') as f:
        f.write(ch2_html)
    print(f"Chapter 2 written to /home/ut/work/go-workout/chapter2.html ({os.path.getsize('/home/ut/work/go-workout/chapter2.html')} bytes)")

    # 3. Build chapter3.html (Chapter 3)
    ch3_html = build_chapter3_html(chapters)
    with open('/home/ut/work/go-workout/chapter3.html', 'w', encoding='utf-8') as f:
        f.write(ch3_html)
    print(f"Chapter 3 written to /home/ut/work/go-workout/chapter3.html ({os.path.getsize('/home/ut/work/go-workout/chapter3.html')} bytes)")

    # 4. Build chapter4.html (Chapter 4)
    ch4_html = build_chapter4_html(chapters)
    with open('/home/ut/work/go-workout/chapter4.html', 'w', encoding='utf-8') as f:
        f.write(ch4_html)
    print(f"Chapter 4 written to /home/ut/work/go-workout/chapter4.html ({os.path.getsize('/home/ut/work/go-workout/chapter4.html')} bytes)")

    # 5. Build chapter5.html (Chapter 5)
    ch5_html = build_chapter5_html(chapters)
    with open('/home/ut/work/go-workout/chapter5.html', 'w', encoding='utf-8') as f:
        f.write(ch5_html)
    print(f"Chapter 5 written to /home/ut/work/go-workout/chapter5.html ({os.path.getsize('/home/ut/work/go-workout/chapter5.html')} bytes)")

    # 6. Build chapter6.html (Chapter 6)
    ch6_html = build_chapter6_html(chapters)
    with open('/home/ut/work/go-workout/chapter6.html', 'w', encoding='utf-8') as f:
        f.write(ch6_html)
    print(f"Chapter 6 written to /home/ut/work/go-workout/chapter6.html ({os.path.getsize('/home/ut/work/go-workout/chapter6.html')} bytes)")

    # 7. Build chapter7.html (Chapter 7)
    ch7_html = build_chapter7_html(chapters)
    with open('/home/ut/work/go-workout/chapter7.html', 'w', encoding='utf-8') as f:
        f.write(ch7_html)
    print(f"Chapter 7 written to /home/ut/work/go-workout/chapter7.html ({os.path.getsize('/home/ut/work/go-workout/chapter7.html')} bytes)")
