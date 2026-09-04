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

with open('builder/chapter11_data.json', 'r', encoding='utf-8') as f:
    ch11_exercises = json.load(f)

with open('builder/chapter12_data.json', 'r', encoding='utf-8') as f:
    ch12_exercises = json.load(f)

with open('builder/chapter13_data.json', 'r', encoding='utf-8') as f:
    ch13_exercises = json.load(f)

with open('builder/chapter14_data.json', 'r', encoding='utf-8') as f:
    ch14_exercises = json.load(f)
with open('builder/chapter15_data.json', 'r', encoding='utf-8') as f:
    ch15_exercises = json.load(f)
with open('builder/chapter16_data.json', 'r', encoding='utf-8') as f:
    ch16_exercises = json.load(f)
with open('builder/chapter17_data.json', 'r', encoding='utf-8') as f:
    ch17_exercises = json.load(f)
with open('builder/chapter18_data.json', 'r', encoding='utf-8') as f:
    ch18_exercises = json.load(f)
with open('builder/chapter19_data.json', 'r', encoding='utf-8') as f:
    ch19_exercises = json.load(f)
with open('builder/chapter20_data.json', 'r', encoding='utf-8') as f:
    ch20_exercises = json.load(f)
with open('builder/chapter21_data.json', 'r', encoding='utf-8') as f:
    ch21_exercises = json.load(f)
with open('builder/chapter22_data.json', 'r', encoding='utf-8') as f:
    ch22_exercises = json.load(f)
with open('builder/chapter23_data.json', 'r', encoding='utf-8') as f:
    ch23_exercises = json.load(f)
with open('builder/chapter24_data.json', 'r', encoding='utf-8') as f:
    ch24_exercises = json.load(f)
with open('builder/chapter25_data.json', 'r', encoding='utf-8') as f:
    ch25_exercises = json.load(f)
with open('builder/chapter26_data.json', 'r', encoding='utf-8') as f:
    ch26_exercises = json.load(f)
with open('builder/chapter27_data.json', 'r', encoding='utf-8') as f:
    ch27_exercises = json.load(f)
with open('builder/chapter28_data.json', 'r', encoding='utf-8') as f:
    ch28_exercises = json.load(f)
with open('builder/chapter29_data.json', 'r', encoding='utf-8') as f:
    ch29_exercises = json.load(f)
with open('builder/chapter30_data.json', 'r', encoding='utf-8') as f:
    ch30_exercises = json.load(f)
with open('builder/chapter31_data.json', 'r', encoding='utf-8') as f:
    ch31_exercises = json.load(f)
with open('builder/chapter32_data.json', 'r', encoding='utf-8') as f:
    ch32_exercises = json.load(f)
with open('builder/chapter33_data.json', 'r', encoding='utf-8') as f:
    ch33_exercises = json.load(f)
with open('builder/chapter34_data.json', 'r', encoding='utf-8') as f:
    ch34_exercises = json.load(f)
with open('builder/chapter35_data.json', 'r', encoding='utf-8') as f:
    ch35_exercises = json.load(f)
with open('builder/chapter36_data.json', 'r', encoding='utf-8') as f:
    ch36_exercises = json.load(f)
with open('builder/chapter37_data.json', 'r', encoding='utf-8') as f:
    ch37_exercises = json.load(f)
with open('builder/chapter38_data.json', 'r', encoding='utf-8') as f:
    ch38_exercises = json.load(f)
with open('builder/chapter39_data.json', 'r', encoding='utf-8') as f:
    ch39_exercises = json.load(f)
with open('builder/chapter40_data.json', 'r', encoding='utf-8') as f:
    ch40_exercises = json.load(f)
with open('builder/chapter41_data.json', 'r', encoding='utf-8') as f:
    ch41_exercises = json.load(f)
with open('builder/chapter42_data.json', 'r', encoding='utf-8') as f:
    ch42_exercises = json.load(f)
with open('builder/chapter43_data.json', 'r', encoding='utf-8') as f:
    ch43_exercises = json.load(f)
with open('builder/chapter44_data.json', 'r', encoding='utf-8') as f:
    ch44_exercises = json.load(f)
with open('builder/chapter45_data.json', 'r', encoding='utf-8') as f:
    ch45_exercises = json.load(f)
with open('builder/chapter46_data.json', 'r', encoding='utf-8') as f:
    ch46_exercises = json.load(f)
with open('builder/chapter47_data.json', 'r', encoding='utf-8') as f:
    ch47_exercises = json.load(f)
with open('builder/chapter48_data.json', 'r', encoding='utf-8') as f:
    ch48_exercises = json.load(f)
with open('builder/chapter49_data.json', 'r', encoding='utf-8') as f:
    ch49_exercises = json.load(f)
with open('builder/chapter50_data.json', 'r', encoding='utf-8') as f:
    ch50_exercises = json.load(f)
with open('builder/chapter51_data.json', 'r', encoding='utf-8') as f:
    ch51_exercises = json.load(f)
with open('builder/chapter52_data.json', 'r', encoding='utf-8') as f:
    ch52_exercises = json.load(f)

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
            11: ('chapter11.html', '49/49'),
            12: ('chapter12.html', '67/67'),
            13: ('chapter13.html', '71/71'),
            14: ('chapter14.html', '77/77'),
            15: ('chapter15.html', '127/127'),
            16: ('chapter16.html', '131/131'),
            17: ('chapter17.html', '58/58'),
            18: ('chapter18.html', '100/100'),
            19: ('chapter19.html', '84/84'),
            20: ('chapter20.html', '124/124'),
            21: ('chapter21.html', '95/95'),
            22: ('chapter22.html', '52/52'),
            23: ('chapter23.html', '132/132'),
            24: ('chapter24.html', '63/63'),
            25: ('chapter25.html', '45/45'),
            26: ('chapter26.html', '158/158'),
            27: ('chapter27.html', '163/163'),
            28: ('chapter28.html', '115/115'),
            29: ('chapter29.html', '96/96'),
            30: ('chapter30.html', '107/107'),
            31: ('chapter31.html', '120/120'),
            32: ('chapter32.html', '189/189'),
            33: ('chapter33.html', '89/89'),
            34: ('chapter34.html', '78/78'),
            35: ('chapter35.html', '78/78'),
            36: ('chapter36.html', '130/130'),
            37: ('chapter37.html', '88/88'),
            38: ('chapter38.html', '77/77'),
            39: ('chapter39.html', f'{len(ch39_exercises)}/{len(ch39_exercises)}'),
            40: ('chapter40.html', f'{len(ch40_exercises)}/{len(ch40_exercises)}'),
            41: ('chapter41.html', f'{len(ch41_exercises)}/{len(ch41_exercises)}'),
            42: ('chapter42.html', f'{len(ch42_exercises)}/{len(ch42_exercises)}'),
            43: ('chapter43.html', f'{len(ch43_exercises)}/{len(ch43_exercises)}'),
            44: ('chapter44.html', f'{len(ch44_exercises)}/{len(ch44_exercises)}'),
            45: ('chapter45.html', f'{len(ch45_exercises)}/{len(ch45_exercises)}'),
            46: ('chapter46.html', f'{len(ch46_exercises)}/{len(ch46_exercises)}'),
            47: ('chapter47.html', f'{len(ch47_exercises)}/{len(ch47_exercises)}'),
            48: ('chapter48.html', f'{len(ch48_exercises)}/{len(ch48_exercises)}'),
            49: ('chapter49.html', f'{len(ch49_exercises)}/{len(ch49_exercises)}'),
            50: ('chapter50.html', f'{len(ch50_exercises)}/{len(ch50_exercises)}'),
            51: ('chapter51.html', f'{len(ch51_exercises)}/{len(ch51_exercises)}'),
            52: ('chapter52.html', f'{len(ch52_exercises)}/{len(ch52_exercises)}'),
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
    sb.append('  <div class="sidebar-resizer" id="sidebar-resizer" title="Потяните для изменения ширины (двойной клик — сброс)"></div>')
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
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
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
            <span>Глава 02 Компиляция, сборка и запуск</span> →
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
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 01 Пакеты и модули</a>
            <a href="chapter3.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 03 fmt и ввод-вывод →</a>
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
            <a href="chapter2.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 02 Компиляция, сборка и запуск</a>
            <a href="chapter4.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 04 Базовые типы →</a>
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
            <a href="chapter3.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 03 Пакет fmt и консольный ввод-вывод</a>
            <a href="chapter5.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 05 Условные конструкции →</a>
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
            <a href="chapter4.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 04 Базовые типы</a>
            <a href="chapter6.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 06 Циклы →</a>
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
            <a href="chapter5.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 05 Условные конструкции</a>
            <a href="chapter7.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 07 Массивы →</a>
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
            <a href="chapter6.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 06 Циклы</a>
            <a href="chapter8.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 08 Слайсы →</a>
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
            <a href="chapter7.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 07 Массивы</a>
            <a href="chapter9.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 09 Мапы →</a>
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
            <a href="chapter8.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 08 Слайсы</a>
            <a href="chapter10.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 10 Функции →</a>
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
            <a href="chapter9.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 09 Мапы</a>
            <a href="chapter11.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 11 Указатели →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '10. Функции (100/100)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter11_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=11, current_exercises=ch11_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🎯 Модуль 11 • Указатели и Модель Памяти</div>
        <h1 class="hero-title">Указатели, Адресация и Escape-Анализ в Go</h1>
        <p class="hero-desc">
            Глубокое практическое руководство по низкоуровневой работе с памятью в Go: 
            семантика значений против семантики указателей (Value vs Pointer Semantics), 
            встроенная функция `new(T)` и литеральное взятие адреса `&T{}`, авто-разыменование структур (`u.Field`), 
            работа с указателями на срезы `*[]T` и массивы `*[N]T`, механика Escape-анализа компилятора (`go build -gcflags="-m"`), 
            двойные указатели `**T`, защита от `nil pointer dereference`, паттерны опциональных полей (Nullable DTO) 
            и инвариант 8-байтных указателей в `unsafe.Sizeof`. Все 49 упражнений решены шаг за шагом.
        </p>
    </section>
    """)
    section_groups_ch11 = [
        (1, 25, "Раздел 1: new(T) vs &T{}, Срезы и Массивы, Авто-разыменование, Побег в Кучу и Swap", "new(T) против &User{}, мутация среза vs append, указатель на массив *[N]T, операторы & и *, синтаксический сахар u.Name, ClearSlice s[:0], Escape Analysis, nil-разыменование, двойные указатели **int, ловушка &v в цикле for range, типы *T и Swap"),
        (26, 49, "Раздел 2: Указатели на Срезы, Рефлексия, Nil-Safety Helpers, Связные Списки и unsafe.Sizeof", "AppendWithPointer, указатель на элемент &arr[0], Identity == против Equality *, new(int) vs &x, мутация через reflect.ValueOf.Elem(), Zeroify, Nil Map паника, массивы указателей [3]*int, связный список Node, опциональные поля Profile и инвариант 8 байт unsafe.Sizeof")
    ]
    ex_dict = {e["num"]: e for e in ch11_exercises}
    for start_n, end_n, title, desc in section_groups_ch11:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 11 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили работу с указателями, управление памятью, Escape-анализ и безопасное разыменование в Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter10.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 10 Функции</a>
            <a href="chapter12.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 12 Передача аргументов →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '11. Указатели (49/49)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter12_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=12, current_exercises=ch12_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🔄 Модуль 12 • Семантика Передачи Аргументов</div>
        <h1 class="hero-title">Передача Аргументов (По Значению vs По Ссылке) в Go</h1>
        <p class="hero-desc">
            Глубокое практическое исследование механизмов передачи параметров в Go: 
            строгая семантика Pass by Value, анатомия дескрипторов срезов (SliceHeader) и ловушки `append` без возврата, 
            ссылочное поведение хэш-таблиц (`*hmap`) и каналов (`*hchan`), иммутабельность строк (`StringHeader`), 
            утечка состояния при поверхностном копировании структур с указателями (Pointer Aliasing) и паттерн Deep Copy, 
            бенчмаркинг копирования 8 МБ массивов против 8-байтных указателей, транзакционная логика переводов `Transfer` 
            и адресная арифметика в пакете `unsafe`. Все 67 упражнений решены шаг за шагом.
        </p>
    </section>
    """)
    section_groups_ch12 = [
        (1, 23, "Раздел 1: Примитивы, Срезы vs Массивы, Мапы, Каналы, Неизменяемость Строк и Ловушки Append", "Изоляция стека, передача int, массив [3]int vs срез []int, ссылки на hmap и hchan, StringHeader (16B), ChangeName User vs *User, ловушка append без возврата, срезы s[:0], каверзный случай cap > len и реаллокация базового массива"),
        (24, 45, "Раздел 2: Антипаттерн *any, Поверхностные Копии Структур, Escape-Анализ, Бенчмарк BigData и Разворот Списка", "Указатель на интерфейс *any, структуры со срезами Team.Members, escape analysis, aliasing в структурах с указателями, замер 8 МБ массива vs 8 байт указателя, Value Receiver, ловушка AppendAndModify, разворот связного списка ReverseList и анонимные структуры"),
        (46, 67, "Раздел 3: Интерфейсы, Транзакционный Transfer, Защита Мап, Deep Copy Config и Адресная Арифметика unsafe", "Интерфейсы Stringer, защита от dangling pointers, *[]int с гарантией реаллокации, приватные поля, безопасный перевод денег Transfer с валидацией, попытка обнуления мап, иммутабельность массивов [5]int, Deep Copy метод Clone() и вычисление смещения unsafe.Offsetof")
    ]
    ex_dict = {e["num"]: e for e in ch12_exercises}
    for start_n, end_n, title, desc in section_groups_ch12:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 12 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили механику передачи аргументов в Go: изоляцию стека, ссылочную семантику мап/каналов, ловушки срезов и глубокое копирование.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter11.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 11 Указатели</a>
            <a href="chapter13.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 13 Структуры →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '12. Передача аргументов (67/67)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter13_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=13, current_exercises=ch13_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🏗️ Модуль 13 • Пользовательские Типы и Модели Данных</div>
        <h1 class="hero-title">Структуры (Structs), Композиция и Методы в Go</h1>
        <p class="hero-desc">
            Глубокое практическое руководство по структурам и объектной модели в Go: 
            именованная и позиционная инициализация, инкапсуляция неэкспортируемых полей и геттеры/сеттеры, 
            композиция вместо наследования (Embedding), автоматическое всплытие полей (Promoted Fields) и методов, 
            разрешение коллизий (Ambiguous Selectors), оптимизация выравнивания полей в памяти (Memory Padding & Alignment), 
            теги структур `struct tags` (JSON `omitempty`, мульти-теги `db`/`validate`), потокобезопасные структуры с `sync.Mutex`, 
            паттерн Functional Options, глубокое копирование (Deep Copy), пустая структура `struct{}` (0 байт), 
            решение каверзной ошибки `cannot assign to struct field in map` и реализация двоичного дерева поиска (BST). 
            Все 71 упражнение решено шаг за шагом.
        </p>
    </section>
    """)
    section_groups_ch13 = [
        (1, 24, "Раздел 1: Базовые Структуры, Инкапсуляция, Встраивание, Всплытие Полей и Коллизии Имен", "Инициализация User, геттеры/сеттеры, анонимные структуры, pointer receiver, автоматическое разыменование u.Name, композиция Address в Person, Promoted Fields/Methods, разрешение коллизий ambiguous selector, конструкторы и правила comparable"),
        (25, 48, "Раздел 2: Теги JSON/DB, Затенение, Инспекция Рефлексией, Выравнивание Памяти и Functional Options", "Теги omitempty, мульти-теги db/validate, затенение полей emp.City, срез указателей []*Point, Memory Padding 24B vs 16B, sync.Mutex в структуре, JSON Marshal/Unmarshal, встраивание io.Reader, Functional Options NewServer и дженерик-сортировка"),
        (49, 71, "Раздел 3: Поля-Коллбэки, Strict JSON, Deep Copy, Пустая struct{}, Ловушка Map и Дерево BST", "Button с OnClick, DisallowUnknownFields, глубокое клонирование DeepClone, контейнеры any, пустая структура struct{} (0 байт), иммутабельные WithName, ошибка m['key'].Age = 30 в мапе структур, LIFO стек, дерево поиска BST и переопределение методов Parent/Child")
    ]
    ex_dict = {e["num"]: e for e in ch13_exercises}
    for start_n, end_n, title, desc in section_groups_ch13:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 13 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве изучили структуры, композицию, выравнивание памяти, теги сериализации и объектные паттерны в Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter12.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 12 Передача аргументов</a>
            <a href="chapter14.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 14 Интерфейсы →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '13. Структуры (71/71)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter14_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=14, current_exercises=ch14_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🧩 Модуль 14 • Полиморфизм, Контракты и Модель Памяти</div>
        <h1 class="hero-title">Интерфейсы (Interfaces) и Duck Typing в Go</h1>
        <p class="hero-desc">
            Глубокое инженерное руководство по интерфейсам и полиморфизму в Go: 
            структурная утиная типизация (Implicit Interface Satisfaction) без ключевого слова implements, 
            внутреннее устройство интерфейсов в рантайме (`iface` с `*itab` против `eface` с `*_type`), 
            безопасное утверждение типов (Type Assertion с `comma-ok`) и переключатели типов (Type Switch), 
            стандартные потоковые контракты (`io.Reader`, `io.Writer`, `io.ReadWriter`), 
            главная ловушка собеседований BigTech: *nil interface vs nil pointer in interface*, 
            правила Method Set для `T` и `*T`, паттерн Adapter для функций (`http.HandlerFunc`), 
            архитектурный закон *Accept Interfaces, Return Structs*, устранение Interface Pollution, 
            статическая проверка реализации на этапе компиляции `var _ io.Writer = (*Type)(nil)` 
            и сравнение пустых интерфейсов с Generics (`cmp.Ordered`). Все 77 упражнений решены шаг за шагом.
        </p>
    </section>
    """)
    section_groups_ch14 = [
        (1, 26, "Раздел 1: Неявная Реализация, Полиморфизм, Type Switch, io.Reader/Writer и Method Sets", "Greeter и Animal, срез []Speaker, Type Switch над any, опасность одинарного Type Assertion v.(string), безопасный comma-ok, конвертер ToInt, интерфейс Shape (Area/Perimeter), io.Reader для MyBuffer, каверзный случай Value vs Pointer Receiver, io.Writer и композиция Triathlete"),
        (27, 52, "Раздел 2: Comma-Ok, Композиция Потоков, Опциональные Интерфейсы, Кастомные Ошибки и Ловушка Nil Interface", "Type Assertion str, ok, ReadWriteCloser, динамическая проверка fmt.Stringer, ProcessStream, кастомная ошибка ValidationError (errors.As), sort.Interface, супер-ловушка nil interface vs nil pointer, IsReallyNil через reflect, Postel\'s Law и адаптер функций HandlerFunc"),
        (53, 77, "Раздел 3: Compile-Time Checks, Method Set, Mocking & DI, Бесконечные Ридеры, Декораторы и Generics", "Статическая проверка var _ io.Writer = (*Type)(nil), асимметрия Method Set для T и *T, MockDB для юнит-тестов, DI в Service, RandomLetterReader, ValidatorAll, Middleware Chain, запрет конвертации []Developer в []Worker, UpperWriter, DeepEqual, Interface Pollution, Sorter (Strategy), Generics против any и встраивание bytes.Buffer")
    ]
    ex_dict = {e["num"]: e for e in ch14_exercises}
    for start_n, end_n, title, desc in section_groups_ch14:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 14 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили интерфейсы в Go: модель iface/eface, обработку nil interface, полиморфизм потоков io, паттерны DI и статические проверки.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter13.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 13 Структуры</a>
            <a href="chapter15.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #0f172a; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 15 ООП в Go →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '14. Интерфейсы (77/77)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER


def build_chapter15_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=15, current_exercises=ch15_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">🏛️ Модуль 15 • Объектно-Ориентированный Go, Паттерны и Архитектура</div>
        <h1 class="hero-title">ООП в Go: Композиция, Механика Ресиверов и Паттерны</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по объектно-ориентированной парадигме в Go: 
            композиция вместо наследования (Composition over Inheritance), всплытие методов и полей (Method & Field Promotion), 
            разрешение коллизий имен (Ambiguous Selectors) и затенение (Shadowing), 
            методы-значения (Method Values) и методы-выражения (Method Expressions), 
            методы на nil-получателях (Nil Receivers), правила Method Sets для <code>T</code> и <code>*T</code>, 
            строгая инкапсуляция на уровне пакетов, паттерны проектирования GoF (Builder, Functional Options, Strategy, Observer, 
            Decorator, Adapter, State Machine, Object Pool, Unit of Work) и построение сервисов по Clean Architecture. 
            Все 127 упражнений решены от базовых концепций до уровня Middle/Senior BigTech.
        </p>
    </section>
    """)
    section_groups_ch15 = [
        (1, 33, "Раздел 1: Пользовательские Типы, Ресиверы, Инкапсуляция и Семантика Значений/Указателей", "MyDuration, Point.Distance, авто-разыменование, bank.account, Fluent Counter, Method Sets T vs *T, Person.SetAge, nil pointer receiver Tree.Sum, MyString.IsPalindrome, Ad-hoc interfaces, HandlerFunc"),
        (34, 65, "Раздел 2: Встраивание Структур, Разрешение Коллизий, Полиморфизм и Паттерны", "Describer, bytes.Buffer embedding, SafeCounter с *sync.Mutex, GPS + MobilePhone ambiguous selectors, CreditAccount, crypto/sha256 пароли, sort.Interface для Student, deep promotion A->B->C, Strategy Payment, Mixins, безопасность unsafe, Value Object Counter"),
        (66, 96, "Раздел 3: Поведенческие Паттерны, Ловушка Типизированного Nil и Context", "Decorator Logger, Method Value vs Pointer, HouseBuilder, Functional Options Server, Fluent Validator, Factory Method, супер-ловушка nil error, Singleton sync.Once, TextProcessor, Method Expression Greeter.Greet, неадресуемость map, State Machine Order, LSP Bird/Ostrich, Deep Copy Clone, Middleware Chain, Command Pattern, context.Context DataFetcher"),
        (97, 127, "Раздел 4: Промышленные Паттерны, Конкурентность, Рефлексия и Clean Architecture", "ServerConfig с валидацией, StructInfo через reflect, Observer/PubSub, UserRepository, Function Adapter, (T, nil) vs (nil, nil), Mutex Copy Trap go vet, Data Race -race, Singleton package, DI UserService, TrafficLight State, QueryBuilder SQL, Event Emitter, Stateless struct{}, ISP GodInterface, Fragile Base Class, APIError errors.Is, LoggedHTTPClient, Object Pool, Benchmark Value vs Pointer, Unit of Work, Финальный проект Clean Architecture")
    ]
    ex_dict = {e["num"]: e for e in ch15_exercises}
    for start_n, end_n, title, desc in section_groups_ch15:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 15 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили объектно-ориентированный Go: композицию и всплытие методов, разрешение конфликтов селекторов, nil-ресиверы, Method Values/Expressions, паттерны GoF и принципы Clean Architecture.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter14.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 14 Интерфейсы</a>
            <a href="chapter16.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 16 Дженерики →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '15. ООП в Go (127/127)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter16_html(chapters):
    sidebar_html = build_sidebar(chapters, 16, ch16_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 16</div>
        <h1 class="hero-title">Дженерики (Generics & Type Parameters)</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по параметрическому полиморфизму в Go 1.18+. Полный разбор Type Parameters, 
            Type Sets, кастомных интерфейсов-ограничений (Constraints), объединений типов (Unions), оператора тильды (<code>~</code>), 
            ограничений <code>comparable</code> и <code>cmp.Ordered</code>, алгоритма Type Inference (вывод типов аргументов и ограничений), 
            стандартных библиотек <code>slices</code> и <code>maps</code> (Go 1.21+), обобщенных структур данных (Stack, Queue, Set, LinkedList, 
            BST, PriorityQueue, SafeMap, Graph), паттернов Fan-In / Concurrency, и глубокого сравнения дженериков с интерфейсами на уровне 
            рантайма (GC Shape Stenciling + Dictionaries). Все 131 упражнение с нуля до уровня Senior/Staff BigTech.
        </p>
    </section>
    """)
    section_groups_ch16 = [
        (1, 33, "Раздел 1: Параметры Типов, Встроенные Ограничения any/comparable и Вывод Типов", "Синтаксис [T any], [T comparable], [T cmp.Ordered], Type Inference, инверсия среза Reverse, стек Stack[T], Set[T], Filter/Map, поиск Max/Min, бинарный поиск, Swap, SafeSlice, Either[L,R], Optional[T]"),
        (34, 66, "Раздел 2: Кастомные Constraints, Оператор Тильды ~ и Обобщенные Структуры", "Unique comparable, OrderedStringer, Keys map, GenericMap, Numeric, FindIndex, Reduce, StringOrInt union, тильда ~, Pair[T, U], BytesOrString, List[T], Ptr[T], NamedOrdered, reflect в дженериках, WrapWithLogging, underlying type, Closer, MaxBy, FIFO Queue, Cache, Set union/intersection, Result[T], запрет generic-методов на структурах"),
        (67, 99, "Раздел 3: Продвинутые Структуры Данных, Функциональные Паттерны и Ограничения Методов", "MapSlice, Validator[T], Intersect Set, LinkedList (Prepend/Append/Find), BinarySearchTree BST, Result (Success/Failure), AnyInteger & побитовые операции, Pair.GetValues, Join Stringer, Retry с backoff, Channel[T], Type inference trap, Fluent Slice API, SafeMap RWMutex, Repository[T], Matrix, Calculator[T], UserRepository, Pool sync.Pool, EventEmitter, Memoize, RingBuffer, MergeMaps, Partition, Graph BFS, PriorityQueue min-heap, BatchProcess"),
        (100, 131, "Раздел 4: Concurrency, Пакеты slices/maps, Constraint Type Inference и Архитектура", "Fan-In MergeChannels, variadic Sum, ChanToSlice, slices.Sort/Contains, DoublyLinkedList, type switch workaround any(v).(type), AreEqual, InOrder BST, Method Sets, Result.Unwrap, почему нельзя вызвать метод без constraint, ловушка return nil / var zero T, maps.Clone/Equal, shared underlying array append, Increment ~, JSON Marshal/Unmarshal, GroupBy, Closures, StringableNumeric, Stringify, Clone generic struct, Allowed, CountOccurrences, collections пакет + BFS, Constraint Type Inference CloneSlice[S ~[]E, E any], Generic Repository User/Product, Дженерики vs Интерфейсы (itab vs monomorphization), Min-Heap, Type-Safe Enum")
    ]
    ex_dict = {e["num"]: e for e in ch16_exercises}
    for start_n, end_n, title, desc in section_groups_ch16:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 16 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили обобщенное программирование (Generics) в Go: Type Sets, аппроксимацию типов (~), Constraint Type Inference, реализацию обобщенных коллекций и понимание мономорфизации рантайма (GC Shape Stenciling).
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter15.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 15 ООП в Go</a>
            <a href="chapter17.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 17 Обработка ошибок →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '16. Дженерики (131/131)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter17_html(chapters):
    sidebar_html = build_sidebar(chapters, 17, ch17_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 17</div>
        <h1 class="hero-title">Обработка ошибок (Error Handling)</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по идиоматичной обработке ошибок в Go. Полный разбор интерфейса <code>error</code>, 
            паттерна Sentinel Errors, создания структурированных кастомных ошибок, цепочек оборачивания через <code>fmt.Errorf("%w")</code>, 
            рекурсивной проверки <code>errors.Is</code> и извлечения типов <code>errors.As</code>, агрегации ошибок через <code>errors.Join</code> 
            (Go 1.20+), работы с <code>panic</code> и <code>recover</code>, паттерна <code>Must</code>, deferred error handling, 
            конкурентного сбора ошибок из горутин и устранения антипаттерна Log-and-Return. Все 58 упражнений от базовых концепций 
            до уровня Senior/Lead BigTech.
        </p>
    </section>
    """)
    section_groups_ch17 = [
        (1, 20, "Раздел 1: Базовые Ошибки, Оборачивание %w, Sentinel Errors и Проверка errors.Is", "Деление на 0, AppError, errors.New vs fmt.Errorf, sentinel ErrNotFound, if err != nil Line of Sight, %v vs %w, errors.As, errors.Unwrap, ValidationError, цепочка readFile->parseJSON->validate, паттерн Retry, системные ошибки os.PathError"),
        (21, 40, "Раздел 2: errors.Join, Извлечение errors.As, Guard Clauses, Паника и Recover", "errors.Join форма, AppError HTTPCode, NotFoundError Resource/ID, switch errors.Is, ErrPermissionDenied, QueryError, Guard Clauses, сбор ошибок в цикле, recover на верхнем уровне, Deferred Error Handling (rollback/commit), SafeParseInt, паттерн MustLoadConfig/MustOpen, Best Effort, ошибки os.File.Sync"),
        (41, 58, "Раздел 3: Concurrency, Таймауты, Graceful Degradation и Чистая Архитектура", "Retry с задержкой, errors.Is внутри Join, деление на 0 с recover, context.WithTimeout и DeadlineExceeded, Panic-to-Error трансформация, CloseResource, централизованный роутер, Fail-Fast vs Best-Effort, опасность игнорирования _, ProcessAndSave, ParseConfig JSON, позиционный контекст строки, устранение Log-and-Return, Graceful degradation, сбор ошибок из горутин через канал и sync.WaitGroup")
    ]
    ex_dict = {e["num"]: e for e in ch17_exercises}
    for start_n, end_n, title, desc in section_groups_ch17:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 17 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили идиоматичную обработку ошибок в Go: цепочки оборачивания с %w, рекурсивные проверки через errors.Is/As, древовидную агрегацию через errors.Join, паттерны Must и Deferred Rollback, а также безопасную изоляцию паник через recover.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter16.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 16 Дженерики</a>
            <a href="chapter18.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 18 Работа с файлами →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '17. Обработка ошибок (58/58)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter18_html(chapters):
    sidebar_html = build_sidebar(chapters, 18, ch18_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 18</div>
        <h1 class="hero-title">Работа с файлами (File I/O & Binary Streams)</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по работе с файловой системой, потоковым вводом-выводом и бинарными 
            форматами данных в Go. Полный разбор пакетов <code>os</code>, <code>io</code>, <code>bufio</code>, 
            <code>path/filepath</code>, <code>encoding/binary</code>, <code>encoding/csv</code>, <code>encoding/gob</code> 
            и <code>encoding/json</code>. Построчное сканирование больших файлов (<code>bufio.Scanner</code>), высокоскоростная 
            буферизованная запись (<code>bufio.Writer</code>), низкоуровневые системные вызовы (<code>Seek</code>, <code>Stat</code>, 
            <code>Chmod</code>), рекурсивный обход каталогов (<code>filepath.WalkDir</code>), ротация логов, создание временных 
            файлов (<code>os.CreateTemp</code>) и реализация собственных типов <code>io.Reader</code> / <code>io.Writer</code>. 
            Все 100 упражнений от базового открытия файлов до уровня Senior BigTech.
        </p>
    </section>
    """)
    section_groups_ch18 = [
        (1, 33, "Раздел 1: Базовые Операции, Чтение/Запись, Буферизация и Права Доступа", "os.ReadFile, os.OpenFile (O_APPEND, O_CREATE), bufio.Scanner, бинарные int32, filepath.Walk, binary.Write/Read, os.Chmod, defer file.Close, os.CreateTemp, io.Copy, блочное копирование, fast.txt, слияние файлов, CSV, Stdout, os.Stat/os.IsNotExist, рекурсивное копирование, file.WriteString, ReadLines, os.Remove, замена слов, bufio.NewWriter.Flush, SHA256, file.Seek, os.Mkdir"),
        (34, 66, "Раздел 2: Анализ Текста, Каталоги, Бинарные Форматы и JSON Стриминг", "Утилита wc (ScanLines/ScanWords/ScanRunes), AppendToFile, Grep, os.MkdirAll, FileMode.Perm, fmt.Fprintf, метаданные Stat, os.ReadDir, режимы O_RDONLY/O_RDWR/O_TRUNC, io.ReadAll, ручной WalkTree, create test.txt, path/filepath (Join, Dir, Base, Ext), encoding/gob, чтение raw bytes io.EOF, sed замена с бэкапом, определение MIME по magic bytes, стриминг article.txt, io.CopyBuffer, json.NewEncoder/NewDecoder, ASCII байты, экспорт структур в CSV, теги json, поиск .txt"),
        (67, 100, "Раздел 3: Продвинутый I/O, Файловые СУБД, Ротация Логов и Кастомный Reader/Writer", "Заголовок PNG, os.RemoveAll, chmod 0755 скрипта, бинарный int32 LittleEndian, нарезка/сборка чанков (Split/Merge), CRUD файловая БД на Seek, bufio.NewReader 1024B, утилита tail на SeekEnd, io.Copy direct, пословный Scanner, мониторинг Polling, расчет размера папки, gob срезы структур, точный буфер Stat.Size, 10 000 строк Flush, ротация логов, модификация O_RDWR, data/logs/2026/07, PlayerData binary, подсчет ERROR, io.MultiWriter, CLI утилита с флагами, MemoryBuffer ReadWriter")
    ]
    ex_dict = {e["num"]: e for e in ch18_exercises}
    for start_n, end_n, title, desc in section_groups_ch18:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 18 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили файловый ввод-вывод и потоковую обработку данных в Go: потоковое сканирование bufio.Scanner, высокоскоростную запись bufio.Writer, низкоуровневые системные вызовы Seek/Stat/Chmod, бинарную сериализацию binary/gob/json и проектирование кастомных io.Reader / io.Writer.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter17.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 17 Обработка ошибок</a>
            <a href="chapter19.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 19 Логирование →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '18. Работа с файлами (100/100)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter19_html(chapters):
    sidebar_html = build_sidebar(chapters, 19, ch19_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 19</div>
        <h1 class="hero-title">Логирование (Logging & Observability)</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по структурированному логированию, трассировке и наблюдаемости (Observability) 
            в Go. Полный разбор пакетов <code>log</code> и <code>log/slog</code> (стандарт Go 1.21+), архитектуры JSON-хендлеров, 
            динамического изменения уровня логов через <code>slog.LevelVar</code> и сигналы ОС (<code>SIGUSR1</code>), кастомных 
            <code>slog.Handler</code> (инжект контекста, OpenTelemetry <code>trace_id</code>/<code>span_id</code> корреляция, 
            Sentry алертинг), маскирования персональных данных (PII/PCI-DSS) через <code>slog.LogValuer</code> и <code>ReplaceAttr</code>, 
            log sampling (интервальное и вероятностное), zero-allocation логирования через <code>slog.LogAttrs</code>, асинхронных 
            очередей на каналах, ротации логов на диске (lumberjack) и интеграции с Grafana Loki (LogQL) и ELK. Все 84 упражнения 
            от базового <code>log.Println</code> до уровня Senior SRE / Staff Engineer.
        </p>
    </section>
    """)
    section_groups_ch19 = [
        (1, 28, "Раздел 1: Структурированный slog, Динамические Уровни, Маскирование PII и Trace Correlation", "slog.LevelVar (HTTP PUT /loglevel), zerolog/slog JSON stdout, ReplaceAttr (PII password/email), slog.Group/Attr, RequestID middleware, LevelDebug фильтрация, slog.LogValuer (User), SplitHandler (Error в файл, Info в stdout), Sentry alert handler, контекстный slog (NewContext), полный HTTP audit middleware, ContextInjectHandler, zero-allocation slog.LogAttrs, logger.WithGroup, X-Request-ID, sampling (100% Error, 10% Info), защита секретов, Stack Trace JSON array, OpenTelemetry (trace_id, span_id)"),
        (29, 56, "Раздел 2: Cloud-Native Observability, Grafana Loki, LogQL и Стандартный Пакет log", "WithContext helper, идеальный HTTP middleware (defer latency/status/IP), AddSource (caller), Jaeger link, probabilistic sampling (10%), Log Shipping архитектура (Fluent Bit / Vector), Grafana Loki (LogQL queries), Log-based metrics (count_over_time), log.SetOutput в файл, стандартный log.Println/Printf, сравнение log vs fmt, атомарность вывода, log.SetFlags (Ldate, Ltime, Lmicroseconds, Lshortfile), log.Fatalf (os.Exit 1, defer), Cloud-Native JSON стандарты, изолированный log.New, io.MultiWriter, дозапись O_APPEND, slog.NewTextHandler, Daily Logger, DI логгера, SRE Incident Response Workflow, stderr логгер"),
        (57, 84, "Раздел 3: Паника, Кастомные Хендлеры, Модульные Логгеры и Безопасность (Security Observability)", "log.Panicf vs Fatalf (recover), сравнительный анализ паники, O_APPEND|O_CREATE|O_WRONLY, структурный slog.Info/Error, JSONHandler для ELK, infoLogger vs errorLogger, маскирование чувствительных данных, logger.With(\"module\", \"db\"), AppLogger обертка с фильтрацией, модульные [DB]/[API], универсальный middleware, базовый slog.Info, fallback на slog.Default(), глобальный slog.SetDefault, Security Observability (GDPR audit trail, data exfiltration alert), форматирование атрибутов, No-Op silent logger (io.Discard), фатальные ошибки, debug.Stack() при панике, кастомная ротация 1MB, slog.LevelWarn, runtime.Caller хелпер, комплексный UserService, градация Warn/Error при открытии файла, кастомный JSON логгер, вложенные группы, structured error logging, строгая фильтрация уровней")
    ]
    ex_dict = {e["num"]: e for e in ch19_exercises}
    for start_n, end_n, title, desc in section_groups_ch19:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 19 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили структурированное логирование и основы Cloud-Native Observability в Go: современный пакет log/slog, динамическое управление уровнями через LevelVar, OpenTelemetry распределенную трассировку, маскирование PII-данных (152-ФЗ/GDPR), log sampling, интеграцию с Grafana Loki (LogQL) и проектирование отказоустойчивых асинхронных конвейеров.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter18.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 18 Работа с файлами</a>
            <a href="chapter20.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 20 Горутины и синхронизация →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '19. Логирование (84/84)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter20_html(chapters):
    sidebar_html = build_sidebar(chapters, 20, ch20_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 20</div>
        <h1 class="hero-title">Горутины и синхронизация (Concurrency & Primitives)</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по модели конкурентности в Go: архитектура планировщика GMP 
            (Goroutine, Machine, Processor), вытесняющая многозадачность (Async Preemption на сигналах <code>SIGURG</code> в Go 1.14+), 
            мониторинг <code>runtime.NumGoroutine</code> и утечки горутин (Goroutine Leaks), примитивы синхронизации пакета <code>sync</code> 
            (<code>WaitGroup</code>, <code>Mutex</code>, <code>RWMutex</code>, <code>Once</code>, <code>Pool</code>, <code>Cond</code>), 
            потокобезопасные коллекции <code>sync.Map</code>, библиотека <code>errgroup</code> с контекстной отменой, и низкоуровневые 
            Lock-Free алгоритмы на <code>sync/atomic</code> (<code>atomic.Int64</code>, <code>atomic.Pointer</code>, <code>atomic.Value</code>, 
            CAS-лупы, Memory Ordering, защита от False Sharing). Все 124 упражнения от базового <code>go func()</code> до уровня 
            Senior / Staff Concurrency Engineer.
        </p>
    </section>
    """)
    section_groups_ch20 = [
        (1, 41, "Раздел 1: Горутины, Жизненный Цикл main(), Планировщик GMP и Базовый sync.WaitGroup", "Старт горутин, завершение main(), антипаттерн time.Sleep, Fan-Out воркеры, sync.WaitGroup (Add, Done, Wait), замыкание переменной цикла (семантика до и после Go 1.22), копирование WaitGroup по значению (copylocks), параллельный MapReduce, runtime.NumGoroutine и утечки памяти, GOMAXPROCS и automaxprocs, SafeCounter с sync.Mutex, SafeGo с защитой от паники, асинхронное вытеснение Go 1.14+, детекция дедлоков рантайма и паника отрицательного счетчика"),
        (42, 82, "Раздел 2: Мьютексы (sync.Mutex, sync.RWMutex), Deadlock, sync.Once, sync.Pool и sync.Cond", "select {} зомби-горутины, защита критических секций, иерархия горутин, RWMutex для кэша (Read-Heavy), runtime.Goexit с сохранением defer, нереентерабельность Mutex (двойной Lock), defer mu.Unlock(), аудит ThreadSanitizer (-race), sync/atomic инкременты, потокобезопасный синглтон sync.Once, пул буферов sync.Pool (снижение нагрузки на GC), методы *Locked(), условные переменные sync.Cond (Wait, Signal, Broadcast), бенчмарк Mutex vs RWMutex (90/10), флаги atomic.Load/Store, sync.Map (Store, Load, Range), фиксация Once при панике, раздувание буферов и барьер синхронизации"),
        (83, 124, "Раздел 3: Продвинутая Конкурентность: errgroup, Lock-Free Стек Трейбера, atomic.Pointer, Memory Ordering и Паттерны", "Забытый Unlock, библиотека errgroup (обработка первой ошибки, контекстная отмена ctx.Done, лимитер SetLimit), двухфазный барьер, неблокирующий TryLock (Go 1.18+), Priority Inversion и starvation mode, классический перекрестный дедлок (Lock Ordering), Lock-Free стек Трейбера на atomic.Pointer[T] (Go 1.19+), утечки горутин на небуферизованных каналах, горячая перезагрузка конфига atomic.Value/Pointer, Spin-Lock на atomic.Bool, барьеры памяти (Happens-Before), Lock-Free Max (CAS-loop), проблема ABA в Go, One-Shot сигналы, False Sharing и 64-байтный CPU Padding, Lazy Singleton, Producer-Consumer очередь с Graceful Shutdown")
    ]
    ex_dict = {e["num"]: e for e in ch20_exercises}
    for start_n, end_n, title, desc in section_groups_ch20:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 20 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили базовую модель конкурентности и примитивы синхронизации в Go: планировщик GMP, безопасную работу с горутинами, пакеты <code>sync</code> (WaitGroup, Mutex, RWMutex, Once, Pool, Cond, Map), библиотеку <code>errgroup</code>, и низкоуровневые Lock-Free алгоритмы на <code>sync/atomic</code>.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter19.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 19 Логирование</a>
            <a href="chapter21.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 21 Каналы и select →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '20. Горутины и синхронизация (124/124)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter21_html(chapters):
    sidebar_html = build_sidebar(chapters, 21, ch21_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 21</div>
        <h1 class="hero-title">Каналы и мультиплексирование select (Channels & Multiplexing)</h1>
        <p class="hero-desc">
            Глубокое практическое руководство по модели взаимодействующих последовательных процессов (CSP — Communicating 
            Sequential Processes) в Go: внутренняя архитектура структуры <code>runtime.hchan</code>, небуферизованные каналы и прямое 
            копирование со стека на стек (Rendezvous), буферизованные кольцевые очереди (FIFO) и защита от Bufferbloat, однонаправленные 
            контракты (<code>chan&lt;-</code> / <code>&lt;-chan</code>), идиома comma-ok (<code>val, ok := &lt;-ch</code>), 
            мультиплексирование с <code>select</code> (псевдослучайный uniform выбор, non-blocking polling через <code>default</code>, 
            динамическое отключение веток через <code>nil</code>-каналы), паттерны отмены (Done Channel, Or-Done, Graceful Shutdown) 
            и классические конвейеры (Pipeline, Fan-In, Fan-Out, Throttle, Debounce, Futures/Promises, Heartbeat, Rate Limiter). 
            Все 95 упражнений от базового <code>make(chan int)</code> до уровня Senior / Staff Concurrency Engineer.
        </p>
    </section>
    """)
    section_groups_ch21 = [
        (1, 32, "Раздел 1: Основы Каналов, Буферизация, Закрытие и Базовые Конвейеры", "Небуферизованные каналы (Rendezvous), емкость буфера и порядок FIFO, закрытие канала и comma-ok протокол, передача строк и структур, ловушка 100% CPU при чтении из закрытого канала, цепочки передачи (Pipeline Stage Square), однонаправленные контракты (chan<- и <-chan), Backpressure при заполнении буфера, функция Drain для вычитывания остатка, анатомия дедлока рантайма, генераторы потоков (Generate), sentinel-значение 'stop', паттерн слияния Merge (Fan-In), SafeClose с sync.Once, свойства nil-каналов и фильтрация Filter"),
        (33, 64, "Раздел 2: Мультиплексирование с select, Семафоры, Таймауты и Детекция Утечек", "Ограничение параллелизма (Bounded Parallelism семафор), for range по каналам, статический контроль типов компилятора, опустошение буфера закрытого канала, паника send on closed channel, мультиплексирование потоков с разной задержкой, псевдослучайный выбор (Random Uniform), неблокирующий опрос (default в select), таймаут time.After, паттерн Heartbeat (пульс горутины), ловушка забытого close(), приоритет отмены (done vs work), Drop Overflow паттерн, Priority Select через вложенный select, предотвращение Goroutine Leak через буфер емкостью 1, защита от Busy Loop в select и Rate Limiter на тикерах"),
        (65, 95, "Раздел 3: Продвинутые Паттерны: Debounce, Throttle, Graceful Shutdown, Or-Done и nil-каналы", "Однонаправленные типы API, паттерн Debounce с time.Timer, мультиплексор fanIn, антипаттерн закрытия канала получателем, паттерн Throttle, перехват системных сигналов OS (SIGINT/SIGTERM Graceful Shutdown), паттерн Futures/Promises, динамическое выключение веток через ch = nil, таймеры time.Tick, утечка памяти с time.After в цикле и рефакторинг на time.NewTimer/Reset, выход из select через Labeled Break, Circuit Breaker таймауты к БД, паника close(nil), Drop Pattern телеметрии, рекурсивный Or-Done Channel и широковещательная отмена воркеров (Broadcast Cancellation)")
    ]
    ex_dict = {e["num"]: e for e in ch21_exercises}
    for start_n, end_n, title, desc in section_groups_ch21:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 21 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили модель каналов и мультиплексирование select в Go: внутреннее устройство runtime.hchan, безопасную передачу данных между горутинами, неблокирующие операции, отмену через Done-каналы, и полный спектр конкурентных паттернов (Pipeline, Fan-In, Debounce, Throttle, Rate Limiter).
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter20.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 20 Горутины и синхронизация</a>
            <a href="chapter22.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 22 Пакет context →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '21. Каналы и select (95/95)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter22_html(chapters):
    sidebar_html = build_sidebar(chapters, 22, ch22_exercises)
    content_parts = []
    content_parts.append('<main class="main-content">')
    content_parts.append("""
    <section class="hero-section">
        <div class="hero-tag">Глава 22</div>
        <h1 class="hero-title">Пакет context (Жизненный цикл горутин, дедлайны и метаданные)</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по пакету <code>context</code> в Go: управление жизненным циклом горутин, 
            кооперативная отмена операций (Cooperative Cancellation), иерархические деревья контекстов (Context Trees) и однонаправленная 
            пропагация отмены, дедлайны и таймауты (<code>WithTimeout</code>, <code>WithDeadline</code>, <code>context.DeadlineExceeded</code>), 
            безопасная передача сквозных метаданных запроса (<code>WithValue</code>, типизированные приватные ключи <code>ctxKey</code>, 
            предотвращение утечек памяти и коллизий), интеграция с сетевым стеком (<code>net/http.RequestWithContext</code>, <code>req.Context()</code>, 
            Server <code>readLoop</code>), системными сигналами ОС (<code>signal.NotifyContext</code>) и новыми возможностями Go 1.21+ 
            (<code>context.AfterFunc</code>, <code>context.WithoutCancel</code>). Все 52 упражнения с полным разбором низкоуровневых 
            структур (<code>emptyCtx</code>, <code>cancelCtx</code>, <code>timerCtx</code>, <code>valueCtx</code>) и практик BigTech-инженерии.
        </p>
    </section>
    """)
    section_groups_ch22 = [
        (1, 26, "Раздел 1: Основы Контекста, Ручная Отмена, Таймауты и Пропагация в Дереве", "Ручная отмена (WithCancel), таймауты операций (WithTimeout), передача метаданных (WithValue), проверка ctx.Err() в цикле, генераторы с защитой от утечек, семантика Background() vs TODO(), дерево контекстов и однонаправленная отмена, идиома первого аргумента ctx, сквозной RequestID, массовая широковещательная остановка, обязательный defer cancel(), функция Or() для слияния каналов отмены, абсолютный WithDeadline vs относительный WithTimeout, детекция Context Leak через runtime.NumGoroutine(), интеграция с HTTP-клиентом (NewRequestWithContext) и Graceful Shutdown с signal.NotifyContext"),
        (27, 52, "Раздел 2: Безопасность Метаданных, Worker Pool, AfterFunc и Серверная Интеграция", "Неэкспортируемые типы ключей contextKey, отменяемый сон SleepWithContext, антипаттерны бизнес-данных в контексте, Worker Pool с контекстной отменой, серверные обработчики с req.Context(), параллельный опрос реплик (Parallel Fetch), разделение ошибок DeadlineExceeded vs Canceled, каскадное закрытие Parent->Child->SubChild, автоматические колбэки context.AfterFunc (Go 1.21+), гарантированный Safe Cleanup при отмене, пирамида дедлайнов, принудительный опрос в CPU-bound циклах, защита от горутин-зомби и серверная отмена при закрытии соединения клиентом")
    ]
    ex_dict = {e["num"]: e for e in ch22_exercises}
    for start_n, end_n, title, desc in section_groups_ch22:
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
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 22 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили пакет <code>context</code> в Go: управление жизненным циклом горутин, каскадную отмену, дедлайны и таймауты, типобезопасные метаданные WithValue, Graceful Shutdown, а также новые функции Go 1.21+ (AfterFunc и WithoutCancel).
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter21.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 21 Каналы и select</a>
            <a href="chapter23.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #080c14; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 23 Паттерны конкурентности →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '22. Пакет context (52/52)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter23_html(chapters):
    active_chapter_num = 23
    current_exercises = ch23_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 23 • HighLoad Concurrency & Architecture</div>
      <h1 class="hero-title">Паттерны и каверзные случаи конкурентности (Race, Leaks, Worker Pool)</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по конкурентному программированию в Go: проектирование высокопроизводительных конвейеров (Pipelines), масштабируемых пулов воркеров (Worker Pools), алгоритмов ограничения частоты (Token Bucket & Leaky Bucket), паттернов Singleflight, Debounce, Throttle, K-Way Merge, шардированных кэшей с TTL, выявления и устранения Data Races, дедлоков и утечек горутин, а также промышленного Graceful Shutdown микросервисов.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 44, 'Раздел 1: Архитектурные паттерны: Fan-Out/Fan-In, Pipeline, Worker Pool, Семафоры и Rate Limiting'),
        (45, 88, 'Раздел 2: Каверзные случаи: Deadlocks, Goroutine Leaks, Race Detector, Singleflight, Debounce и sync.Pool'),
        (89, 132, 'Раздел 3: Промышленные паттерны: Sharded Map, K-Way Merge, Leader Election, Memoizer и Graceful Shutdown'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 23 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили все ключевые паттерны конкурентности и тонкие нюансы рантайма Go: от многостадийных конвейеров и пулов воркеров до ликвидации утечек памяти, шардирования мьютексов и реализации отказоустойчивых HighLoad микросервисов.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter22.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 22 Пакет context</a>
            <a href="chapter24.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #080c14; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 24 Низкоуровневая сеть TCP и UDP →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '23. Паттерны конкурентности (132/132)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter24_html(chapters):
    active_chapter_num = 24
    current_exercises = ch24_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 24 • Low-Level Networking & Sockets</div>
      <h1 class="hero-title">Низкоуровневая сеть (TCP и UDP)</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по сетевому программированию сокетов в Go: архитектура TCP/IP и UDP стека, системные сокеты net.Listen и net.Dial, асинхронный Netpoller (epoll/kqueue) рантайма, решение проблемы TCP stream framing (Length-Prefixed и TLV бинарные протоколы), построчные протоколы команд, полнодуплексные TCP-прокси и широковещательные чаты, многопоточные сканеры портов, тюнинг сокетов (TCP_NODELAY, Keep-Alive, буферы SO_RCVBUF/SO_SNDBUF), DNS-резолюция, протокол Reliable UDP с подтверждениями и in-memory тестирование через net.Pipe.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 32, 'Раздел 1: Фундамент сетевых сокетов: TCP Listen/Accept, Echo-серверы, Горутины, Таймауты и Проксирование'),
        (33, 63, 'Раздел 2: Промышленные сетевые протоколы: Мультиплексирование, TLV, Broadcast, DNS, Reliable UDP и net.Pipe'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 24 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили низкоуровневое сетевое программирование на Go: работу с TCP и UDP сокетами, управление тайм-аутами и дедлайнами, создание кастомных бинарных TLV протоколов, реализацию масштабируемых прокси и сетевых демонов.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter23.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 23 Паттерны конкурентности</a>
            <a href="chapter25.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #080c14; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 25 HTTP-клиент →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '24. Низкоуровневая сеть (63/63)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter25_html(chapters):
    active_chapter_num = 25
    current_exercises = ch25_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 25 • HTTP Client & Networking</div>
      <h1 class="hero-title">HTTP-клиент</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по работе с HTTP-клиентом в Go: архитектура net/http, безопасная инициализация http.Client с таймаутами, глубокий тюнинг http.Transport и пула Keep-Alive сокетов для HighLoad (MaxIdleConnsPerHost), отправка GET/POST/HEAD запросов, потоковая передача JSON (json.NewDecoder) и файлов через io.Copy, безопасная сборка URL в net/url, загрузка файлов multipart/form-data, сессионные CookieJar, клиентские Middleware на базе http.RoundTripper, паттерны ретраев с Exponential Backoff и контекстной отменой.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 23, 'Раздел 1: Базовые HTTP-запросы, таймауты, пулинг сокетов и потоковая обработка'),
        (24, 45, 'Раздел 2: Промышленные паттерны: Middleware RoundTripper, CookieJar, Retry Backoff и многопоточный сбор данных'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 25 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили клиентский HTTP-стек в Go: от базовых запросов и управления дедлайнами до тюнинга Keep-Alive пулов, реализации отказоустойчивых ретраев и кастомных клиентских Middleware на RoundTripper.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter24.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 24 Низкоуровневая сеть TCP и UDP</a>
            <a href="chapter26.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #080c14; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 26 HTTP-сервер и REST API →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '25. HTTP-клиент (45/45)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER


def build_chapter26_html(chapters):
    active_chapter_num = 26
    current_exercises = ch26_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 26 • HTTP Server, REST API & WebSockets</div>
      <h1 class="hero-title">HTTP-сервер, REST API и Middleware</h1>
      <p class="hero-desc">
        Полное руководство по разработке масштабируемых веб-сервисов и REST API на Go: стандартная библиотека net/http, новая маршрутизация Go 1.22+ с методами и PathValue, луковая архитектура Middleware (декораторы, структурированное логирование, аутентификация Bearer, rate limiting на токенах, перехват паник Recovery), потоковая передача данных (NDJSON, SSE через http.Flusher), загрузка и отдача файлов (multipart/form-data), полнодуплексные WebSocket-соединения (эхо, чат-румы, Hub/Broker с мьютексами), запуск защищенных HTTPS и Mutual TLS (mTLS) серверов с генерацией X.509 сертификатов, gRPC сервисы и Protobuf контракты, балансировка нагрузки (Round-Robin на ReverseProxy), паттерн Circuit Breaker, Single Page Application (SPA fallback) и промышленный Graceful Shutdown.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 40, 'Раздел 1: Основы HTTP-сервера, маршрутизация Go 1.22+ и базовые Middleware'),
        (41, 80, 'Раздел 2: Защита сервисов: Rate Limiting, CORS, таймауты и юнит-тестирование'),
        (81, 120, 'Раздел 3: Продвинутые сетевые протоколы: WebSockets, HTTPS, mTLS и gRPC'),
        (121, 158, 'Раздел 4: Архитектура HighLoad: API Gateway, Балансировщики, Circuit Breaker и Graceful Shutdown'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 26 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили серверное веб-программирование на Go: от современной маршрутизации Go 1.22 и проектирования REST API до луковой архитектуры Middleware, полнодуплексных WebSockets, взаимной аутентификации mTLS, gRPC микросервисов и построения надежных HighLoad шлюзов API Gateway.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter25.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 25 HTTP-клиент</a>
            <a href="chapter27.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 27 Реляционные базы данных SQL и PostgreSQL →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '26. HTTP-сервер, REST API и Middleware (158/158)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter27_html(chapters):
    active_chapter_num = 27
    current_exercises = ch27_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 27 • Relational Databases, PostgreSQL & SQL in Go</div>
      <h1 class="hero-title">Реляционные базы данных (SQL и PostgreSQL)</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по взаимодействию с реляционными СУБД в Go на примере PostgreSQL: стандартный пакет database/sql и архитектура пула соединений (*sql.DB), параметризованные запросы и защита от SQL Injection, транзакции ACID, уровни изоляции и retry-политики при serialization failure, пессимистичные и оптимистичные блокировки, нативный драйвер pgx/v5 (pgxpool, конвейеризация pgx.Batch, стриминг pgx.CopyFrom, реактивный LISTEN/NOTIFY), библиотека sqlx (Get, Select, NamedExec), генератор типобезопасного кода sqlc без рантайм-рефлексии, построитель запросов squirrel, версионирование схемы с golang-migrate, полуструктурированные данные JSONB, полнотекстовый поиск FTS и паттерны тестирования с Testcontainers и go-sqlmock.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 40, 'Раздел 1: Основы database/sql, параметризация, CRUD-операции и управление транзакциями'),
        (41, 80, 'Раздел 2: Тюнинг пула соединений, протокол COPY, блокировки и продвинутые типы PostgreSQL'),
        (81, 120, 'Раздел 3: Библиотеки sqlx, нативный драйвер pgx/v5, миграции golang-migrate и генератор sqlc'),
        (121, 163, 'Раздел 4: Чистая архитектура Repository, оптимизация индексов, Testcontainers и HighLoad паттерны'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 27 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили работу с реляционными базами данных в Go: от пула соединений database/sql и нативного pgxpool до продвинутых транзакций ACID, блокировок SKIP LOCKED, потокового импорта pgx.CopyFrom, кодогенерации sqlc, миграций схемы и паттернов надежного HighLoad бэкенда.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter26.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 26 HTTP-сервер, REST API и Middleware</a>
            <a href="chapter28.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 28 Базы данных NoSQL и кэширование Redis →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '27. Реляционные базы данных (SQL и PostgreSQL) (163/163)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter28_html(chapters):
    active_chapter_num = 28
    current_exercises = ch28_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 28 • NoSQL Databases & In-Memory Caching (Redis)</div>
      <h1 class="hero-title">Базы данных NoSQL и кэширование (Redis)</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по In-Memory СУБД Redis в микросервисах на Go: архитектура ядра (Event Loop, сетевой стек, однопоточный движок, структуры данных SDS/listpack/quicklist/skiplist/rax), библиотека go-redis/v9 и пул соединений, базовые и продвинутые типы данных (Strings, Hashes, Lists, Sets, Sorted Sets ZSET, Bitmaps, HyperLogLog, Streams), атомарные счетчики и конвейеризация Pipeline/TxPipeline, скриптинг на Lua (EVAL/EVALSHA), распределенные блокировки (Distributed Lock, Redlock, Watchdog), архитектурные паттерны кэширования (Cache-Aside, Write-Through, Write-Behind, CQRS), предотвращение Cache Stampede (Singleflight, Mutex), Cache Penetration (Bloom Filter) и Cache Avalanche (Jitter), реализация Rate Limiting (Token Bucket, Sliding Window Log, GCRA), персистентность (RDB snapshots, AOF fsync), репликация, Sentinel, Redis Cluster (16384 слота, Hash Tags, CRC16) и паттерны тестирования с miniredis и Testcontainers.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 30, 'Раздел 1: Подключение go-redis, базовые типы (Strings, Hashes, Sets, ZSET) и атомарные счетчики'),
        (31, 60, 'Раздел 2: Сериализация структур, очереди FIFO на списках, Bitmaps, HyperLogLog и основы Streams'),
        (61, 90, 'Раздел 3: Транзакции MULTI/EXEC, конвейеры Pipeline, Lua-скрипты, Singleflight и Consumer Groups'),
        (91, 115, 'Раздел 4: Распределенные блокировки Redlock, сессии, CQRS, Rate Limiter и интеграционные тесты'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 28 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили работу с NoSQL СУБД и кэшированием в Redis на Go: от структур данных и атомарных счетчиков до транзакций MULTI/EXEC, конвейеризации Pipeline, Lua-скриптов, распределенных блокировок Redlock, брокера Redis Streams, защиты от Cache Stampede и архитектуры Redis Cluster.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter27.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 27 Реляционные базы данных SQL и PostgreSQL</a>
            <a href="chapter29.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 29 Модульное тестирование Unit Testing и Assertions →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '28. Базы данных NoSQL и кэширование (Redis) (115/115)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter29_html(chapters):
    active_chapter_num = 29
    current_exercises = ch29_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 29 • Unit Testing, Testable Examples & Assertions in Go</div>
      <h1 class="hero-title">Модульное тестирование (Unit Testing) и Assertions</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по модульному тестированию на Go: стандартный фреймворк testing и анатомия *testing.T, соглашения об именовании, стратегии Errorf vs Fatalf, отказоустойчивые табличные тесты (Table-Driven Tests) с изолированными подтестами t.Run, параллельное тестирование t.Parallel() и эволюция семантики переменных цикла в Go 1.22, детекция гонок с флагом -race, надежное управление ресурсами через t.Cleanup, t.TempDir, t.Setenv и t.Chdir, тестирование паник (defer/recover), запуск тестов по шаблонам (-run, -short, -count, -failfast), библиотека testify (пакеты assert, require, suite, mock), анализ и визуализация покрытия кода (-cover, -covermode=atomic, go tool cover -html), самопроверяющиеся примеры (Testable Examples) с директивой // Output: как живая документация и настройка CI/CD в GitHub Actions.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 32, 'Раздел 1: Основы testing.T, команды go test, Table-Driven подход, параллелизм и t.Cleanup'),
        (33, 64, 'Раздел 2: Покрытие кода (-cover), библиотека testify/assert, обработка ошибок и фикстуры testdata'),
        (65, 96, 'Раздел 3: testify/suite, мокирование mock.Mock, Testable Examples, httptest и автоматизация в CI/CD'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 29 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили модульное тестирование в Go: от базовых соглашений тестирования и Table-Driven архитектуры до параллелизма, детекции гонок с -race, библиотеки testify, мокирования зависимостей, самопроверяющихся Testable Examples и построения надежных CI/CD пайплайнов.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter28.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 28 Базы данных NoSQL и кэширование Redis</a>
            <a href="chapter30.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 30 Мокирование и интеграционное тестирование →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '29. Модульное тестирование (Unit Testing) и Assertions (96/96)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter30_html(chapters):
    active_chapter_num = 30
    current_exercises = ch30_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 30 • Mocking, Test Doubles & Integration Testing in Go</div>
      <h1 class="hero-title">Мокирование и интеграционное тестирование</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по мокированию и интеграционному тестированию в Go: архитектура тестовых дублеров (Dummy, Stub, Spy, Mock, Fake), принципы чистой и гексагональной архитектуры (Ports &amp; Adapters), кодогенерация с mockgen (go.uber.org/mock) и mockery, декларативные ассерты с testify/mock и testify/suite, тестирование HTTP-слоя через net/http/httptest (ResponseRecorder, NewServer, NewTLSServer) и кастомный RoundTripper, изоляция базы данных через DATA-DOG/go-sqlmock и транзакционные откаты (Transaction Rollback), легковесный in-memory Redis с miniredis, подъем реальной контейнерной инфраструктуры (PostgreSQL, Redis, Kafka, MinIO) через testcontainers-go со стратегиями ожидания и переиспользования (WithReuse), миграции схемы через golang-migrate, виртуальная файловая система с testing/fstest и spf13/afero, снимочное тестирование (Golden Files &amp; Approval Tests), детекция утечек горутин с go.uber.org/goleak, расчет перцентилей задержки (p50, p95, p99) и тестирование устойчивости к хаосу (Chaos Engineering).
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 36, 'Раздел 1: Ручные моки, Dependency Injection, gomock, testify/mock и тестирование HTTP'),
        (37, 72, 'Раздел 2: Мокирование БД (go-sqlmock), miniredis, откаты транзакций и основы Testcontainers'),
        (73, 107, 'Раздел 3: Testcontainers в продакшене, Golden Files, детекция утечек goleak, деградация и CLI тестирование'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 30 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили мокирование и интеграционное тестирование в Go: от ручных моков, шпионов вызовов и кодогенерации gomock/mockery до тестирования HTTP через httptest, мокирования БД с go-sqlmock, виртуализации файловой системы с afero и запуска реальных Docker-контейнеров с testcontainers-go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter29.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 29 Модульное тестирование Unit Testing и Assertions</a>
            <a href="chapter31.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 31 Бенчмарки, фаззинг и продвинутые методы тестирования →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '30. Мокирование и интеграционное тестирование (107/107)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter31_html(chapters):
    active_chapter_num = 31
    current_exercises = ch31_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 31 • Benchmarks, Fuzzing & Advanced Testing in Go</div>
      <h1 class="hero-title">Бенчмарки, фаззинг и продвинутые методы тестирования</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по исследованию производительности и устойчивости систем на Go: микро- и макро-бенчмаркинг с testing.B, циклы калибровки b.N и новый синтаксис Go 1.24 b.Loop(), контроль таймеров b.ResetTimer/b.StopTimer/b.StartTimer, аудит расхода оперативной памяти (-benchmem, allocs/op, B/op), кастомные метрики b.ReportMetric, параллельный бенчмаркинг b.RunParallel, статистический анализ ускорений и дельт через benchstat (p-value, U-тест Манна-Уитни), встроенный coverage-guided фаззинг с testing.F, синтез и минимизация контрпримеров (Shrinking), обнаружение повреждений кодировок UTF-8 и целочисленных переполнений, тестирование инвариантов и математических свойств (Property-Based Testing с testing/quick), профилирование pprof (CPU, heap, block, mutex профили) и построение интерактивных графов вызовов/Flame Graphs, детектор гонок ThreadSanitizer (-race) и локализация Data Races, виртуальные часы и Mock Clock для моментального тестирования таймаутов, каналов и TTL-кэша, снимки состояния Golden Files с поддержкой флага -update, паттерн Test Helpers с t.Helper(), изоляция замыканий в параллельных тестах t.Parallel(), организация TestMain и построение production-ready CI/CD пайплайнов с автоматическим контролем Quality Gate.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 40, 'Раздел 1: Микробенчмарки, калибровка b.N, аллокации, Go 1.24 b.Loop, benchstat и базовый фаззинг'),
        (41, 80, 'Раздел 2: Fuzzing-инварианты, профилирование pprof, гонки данных, Worker Pool и Property-Based тесты'),
        (81, 120, 'Раздел 3: Mock Clock, TestMain, Golden Files, параллелизм t.Parallel, нагрузочные тесты и TDD босс'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 31 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили бенчмарки, фаззинг и передовые инженерные практики тестирования в Go: от микробенчмаркинга с b.N и Go 1.24 b.Loop() до статистического анализа через benchstat, фаззинга граничных условий с coverage-guided мутациями, профилирования pprof, устранения гонок данных с -race, работы с виртуальным временем и Golden Files.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter30.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 30 Мокирование и интеграционное тестирование</a>
            <a href="chapter32.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 32 Protocol Buffers и gRPC →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '31. Бенчмарки, фаззинг и продвинутые методы тестирования (120/120)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter32_html(chapters):
    active_chapter_num = 32
    current_exercises = ch32_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 32 • Protocol Buffers & gRPC Architecture in Go</div>
      <h1 class="hero-title">Protocol Buffers и gRPC</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по высокопроизводительным межсервисным коммуникациям на базе Protocol Buffers v3 и gRPC в Go 1.22+: синтаксис схем proto3, числовые теги полей и Wire Types (Varint, Fixed64, Length-Delimited), WKT (Well-Known Types: Timestamp, Duration, Any, Empty), кодогенерация с protoc и Buf CLI, компиляция pb.go и _grpc.pb.go, все четыре типа RPC (Unary, Server Streaming, Client Streaming, Bidirectional Streaming), управление жизненным циклом соединений через Context, Deadlines и таймауты grpc-timeout, низкоуровневая архитектура фреймов HTTP/2 (HEADERS, DATA, RST_STREAM, GOAWAY, WINDOW_UPDATE) и мультиплексирование потоков через единый сокет, Flow Control и Backpressure, сквозная безопасность с TLS 1.3 и двусторонней аутентификацией mTLS (RequireAndVerifyClientCert), передача метаданных (Metadata headers и trailers), каноническая обработка ошибок gRPC (16 кодов) и стандарты Google Rich Errors (errdetails.BadRequest, FieldViolations, RetryInfo, QuotaFailure), многослойные интерцепторы Unary и Stream (Recovery, Tracing W3C TraceContext, Prometheus Metrics, Access Logging, Token Bucket Rate Limiting, RBAC авторизация), интроспекция API через Server Reflection и grpcurl/grpcui, балансировка нагрузки Client-Side Load Balancing (round_robin, DNS resolver, headless-сервисы), трансляция REST JSON в gRPC через gRPC-Gateway и аннотации google.api.http, мультиплексирование портов cmux, тестирование на виртуальных сокетах bufconn, паттерны распределенных систем (Saga оркестрация, Transactional Outbox, Circuit Breaker, Service Mesh) и эксплуатационные практики HighLoad (pprof оптимизации, zero-allocation сериализация, Blue-Green деплой и Disaster Recovery).
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 47, 'Раздел 1: Синтаксис Proto3, скалярные типы, теги, protoc тулчейн, enum, oneof, WKT и базовые RPC'),
        (48, 95, 'Раздел 2: Потоковая передача (Streaming), дедлайны, контекст, HTTP/2 фреймы и безопасность TLS/mTLS'),
        (96, 142, 'Раздел 3: Архитектура интерцепторов (Auth, Logging, Metrics, Tracing, Rate Limiting), Rich Errors и gRPC-Gateway'),
        (143, 189, 'Раздел 4: In-Memory тестирование (bufconn), оркестрация Saga, Service Mesh, HighLoad оптимизации и аудит'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 32 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили Protocol Buffers и gRPC в Go: от составления схем proto3, типизации и кодогенерации до всех видов потоковой передачи, многослойных интерцепторов, сквозной безопасности mTLS, трансляции gRPC-Gateway, тестирования на in-memory сокетах и архитектуры высоконагруженных распределенных микросервисов.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter31.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 31 Бенчмарки, фаззинг и продвинутые методы тестирования</a>
            <a href="chapter33.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 33 Микросервисная архитектура и паттерны →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '32. Protocol Buffers и gRPC (189/189)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter33_html(chapters):
    active_chapter_num = 33
    current_exercises = ch33_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 33 • Microservices Architecture & Distributed Patterns in Go</div>
      <h1 class="hero-title">Микросервисная архитектура и паттерны</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по проектированию, декомпозиции и эксплуатации распределенных микросервисных систем на Go 1.22+: определение границ контекстов Bounded Context по методологии DDD, построение высокопроизводительных API Gateway и BFF (Backend for Frontend) с параллельной агрегацией через errgroup, динамическое обнаружение сервисов (Service Discovery в Consul и etcd) с арендой TTL и Watch-каналами, централизованная конфигурация и Hot Reload, клиентская балансировка нагрузки (Client-Side Load Balancing: round_robin, Least Connection, Peak EWMA, Headless Services), распределенные транзакции Saga (оркестрация и хореография) с компенсирующими действиями, гарантированная доставка сообщений Transactional Outbox с CDC, событийно-ориентированная архитектура (Event-Driven Architecture на Kafka, NATS и gRPC Streaming), CQRS с материализованными представлениями (ClickHouse, Elasticsearch) и аудит лага репликации, полный контур устойчивости к сбоям (Circuit Breaker на gobreaker, Bulkhead семафоры, Fallback деградация, Token Bucket Rate Limiting, Retry с Full Jitter и сквозной Context Deadline Propagation), сквозная наблюдаемость (OpenTelemetry distributed tracing с W3C TraceContext, экспорт в Jaeger, RED-метрики Prometheus и перцентили p50/p95/p99, pprof профилирование в production), контейнеризация Docker (multi-stage сборка на базе scratch/distroless до 15 МБ), Kubernetes манифесты (Deployment, ClusterIP Service, Ingress gRPC, HPA, preStop hooks для безопасного Connection Draining), Istio Service Mesh (Envoy sidecar, mTLS, Canary releases 90/10), GitOps пайплайны с ArgoCD, современный тулчейн Buf CLI (buf.yaml, buf lint, buf breaking) и паттерн безопасной миграции данных без простоев Strangler Fig.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 30, 'Раздел 1: Декомпозиция монолита, API Gateway, Service Discovery, Saga, Outbox, CQRS и отказоустойчивость'),
        (31, 60, 'Раздел 2: Наблюдаемость (Prometheus, Jaeger, pprof), Docker, Kubernetes (Deployment, Service, HPA), Istio и CI/CD'),
        (61, 89, 'Раздел 3: Chaos Engineering, расширенный Circuit Breaker, BFF, Buf CLI, миграция Strangler Fig и E-Commerce платформа'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 33 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили микросервисную архитектуру и паттерны распределенных систем в Go: от декомпозиции монолита и шлюзов API Gateway до паттернов Saga, Transactional Outbox, CQRS, Event Sourcing, Circuit Breaker, Service Mesh Istio, GitOps ArgoCD и проектирования высоконагруженных платформ e-commerce.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter32.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 32 Protocol Buffers и gRPC</a>
            <a href="chapter34.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 34 GraphQL →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '33. Микросервисная архитектура и паттерны (89/89)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter34_html(chapters):
    active_chapter_num = 34
    current_exercises = ch34_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 34 • GraphQL APIs & gqlgen in Go</div>
      <h1 class="hero-title">GraphQL</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по проектированию, разработке и оптимизации GraphQL API на Go 1.22+: парадигма Schema-First и кодогенерация на базе gqlgen, строгая типизация SDL (скаляры, перечисления Enum, Non-Null типы, Input Objects, Interfaces, Unions), архитектура многоуровневых резолверов (Query, Mutation, Subscription), решение проблемы N+1 запросов через DataLoaders (батчинг, мемоизация, окно задержки, dataloadgen на дженериках), эффективная пагинация (Offset-based и Relay Cursor Connections), безопасность и защита от DoS (анализ сложности Query Complexity, глубина вложенности Depth Limiting, автоматические персистентные запросы APQ по SHA-256 хэшу), декларативная безопасность через директивы (@auth, @constraint, @deprecated), потоковая передача в реальном времени (Subscriptions по WebSocket протоколу graphql-ws на Go-каналах), распределенный трейсинг OpenTelemetry, Apollo Federation v2 и построение высокопроизводительных гибридных платформ GraphQL BFF + gRPC бэкенд.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 25, 'Раздел 1: Основы GraphQL, Schema-First, кодогенерация gqlgen, скаляры, Enums и мутации'),
        (26, 50, 'Раздел 2: Проблема N+1, вложенные резолверы, DataLoaders, пагинация и оптимизация запросов'),
        (51, 78, 'Раздел 3: Кастомные скаляры, директивы, Subscriptions (WebSockets), Apollo Federation и гибридная платформа'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 34 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили GraphQL и кодогенерацию на Go: от строгой типизации SDL схем и написания надежных резолверов до ликвидации проблемы N+1 с помощью DataLoaders, Relay Cursor пагинации, защиты от атак через Query Complexity, масштабирования подписок в реальном времени и федеративной микросервисной архитектуры Apollo Federation.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter33.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 33 Микросервисная архитектура и паттерны</a>
            <a href="chapter35.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 35 WebSockets и Real-time →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '34. GraphQL (78/78)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter35_html(chapters):
    active_chapter_num = 35
    current_exercises = ch35_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 35 • WebSockets & HighLoad Real-Time Systems in Go</div>
      <h1 class="hero-title">WebSockets и Real-time</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по разработке и оптимизации полнодуплексных сетевых приложений реального времени на Go 1.22+: протокол WebSocket (RFC 6455), механизм рукопожатия (HTTP Upgrade) и тонкая конфигурация gorilla/websocket и coder/websocket, архитектура Hub/Client (комнаты чатов, топики, Echo Cancellation), потокобезопасность сокетов и канонический паттерн Write Pump, управление обратным давлением (Backpressure) и защита от Slow Consumer, надежный Heartbeat (Ping/Pong детекция полуоткрытых сокетов), сжатие сетевого трафика permessage-deflate, бинарные протоколы на Protocol Buffers, GraphQL Subscriptions поверх WebSocket (graphql-ws), бесконфликтная репликация документов на базе CRDT (LWW-Element-Set), сетевые игровые движки с фиксированным 60 FPS Game Loop, горизонтальное масштабирование через Redis Pub/Sub и проектирование высоконагруженных платформ стриминга.
      </p>
    </section>
    """)
    
    # Sections
    sections = [
        (1, 25, 'Раздел 1: Протокол RFC 6455, HTTP Upgrade, Echo-сервер, клиенты, Hub/Client архитектура и Heartbeat'),
        (26, 50, 'Раздел 2: Безопасность, Rate Limiting, Backpressure, потокобезопасность Write Pump и Protobuf'),
        (51, 78, 'Раздел 3: GraphQL Subscriptions, Redis Pub/Sub, CRDT, игровые серверы 60 FPS и стриминг-платформа'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 35 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили разработку распределенных систем реального времени на Go: от низкоуровневых фреймов WebSocket и канонических циклов readPump/writePump до горизонтального масштабирования подписок через Redis Pub/Sub, бесконфликтной синхронизации данных CRDT, сетевых игровых движков с тикрейтом 60 FPS и архитектуры стриминговых платформ уровня Twitch.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter34.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 34 GraphQL</a>
            <a href="chapter36.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 36 RabbitMQ →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '35. WebSockets и Real-time (78/78)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter36_html(chapters):
    active_chapter_num = 36
    current_exercises = ch36_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 36 • Enterprise Message Queues & Event-Driven Architecture with RabbitMQ in Go</div>
      <h1 class="hero-title">RabbitMQ</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по проектированию и эксплуатации отказоустойчивых распределенных систем обмена сообщениями на Go 1.22+ с использованием RabbitMQ: протокол AMQP 0-9-1, подключение через amqp091-go, топология обменников (Direct, Fanout, Topic, Headers, Default), семантика доставок и подтверждений (Ack, Nack с requeue, Reject), надежная изоляция сбоев через Dead Letter Exchanges (DLX) и очереди DLQ, управление сроком жизни сообщений (TTL) и очередей (x-expires), контроль обратного давления (Backpressure / QoS Prefetch limits), потоковые подтверждения издателя (Publisher Confirms, PublishWithDeferredConfirm), очереди с приоритетами (x-max-priority), отказоустойчивые Quorum Queues на базе алгоритма Raft, паттерн Transactional Outbox, дедупликация и идемпотентность через Redis, сквозной распределенный трейсинг (OpenTelemetry W3C TraceContext в AMQP Headers), распределенные транзакции Saga (Orchestration & Choreography) и построение масштабируемых Event-Driven платформ.
      </p>
    </section>
    """)
    
    # Sections (130 exercises)
    sections = [
        (1, 30, 'Раздел 1: Протокол AMQP 0-9-1, типы обменников (Direct, Fanout, Topic, Headers), очереди, подтверждения Ack/Nack и QoS'),
        (31, 65, 'Раздел 2: Топология, Dead Letter Exchange (DLX), TTL, Publisher Confirms, Priority Queues и Graceful Reconnect'),
        (66, 95, 'Раздел 3: Graceful Shutdown, Transactional Outbox, Quorum Queues (Raft), кластеризация, Circuit Breakers и Saga'),
        (96, 130, 'Раздел 4: Observability, Prometheus, Distributed Tracing, безопасность TLS/ACL, бенчмарки и Финальный босс'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 36 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили брокер сообщений RabbitMQ и архитектуру Event-Driven систем на Go: от низкоуровневых фреймов AMQP 0-9-1 и тонкой маршрутизации обменников до отказоустойчивых Quorum Queues на базе Raft, Transactional Outbox с гарантией At-Least-Once доставки, идемпотентных консьюмеров, координации распределенных транзакций Saga и высоконагруженных платформ уровня Uber и Lyft.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter35.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 35 WebSockets и Real-time</a>
            <a href="chapter37.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 37 Apache Kafka →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '36. RabbitMQ (130/130)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter37_html(chapters):
    active_chapter_num = 37
    current_exercises = ch37_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 37 • High-Throughput Distributed Commit Log & Event Streaming with Apache Kafka in Go</div>
      <h1 class="hero-title">Apache Kafka</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по разработке, масштабированию и оптимизации распределенных событийно-ориентированных систем на Go 1.22+ с использованием Apache Kafka: архитектура распределенного журнала (Commit Log) и режим KRaft (Zero-ZooKeeper), клиенты segmentio/kafka-go и twmb/franz-go, детерминированное партиционирование по ключу (Murmur2/FNV-1a) и строгое сохранение порядка событий (Ordering Guarantee), управление консьюмер-группами (Consumer Groups, Group Coordinator) и современные протоколы ребалансировки (Cooperative Sticky Assignor), ручной контроль смещений (Manual Offset Commit) и семантика At-Least-Once, пакетная буферизация (Batching) и сжатие трафика (Snappy, Zstd, Gzip), отказоустойчивые топологии кластера (RF=3, min.insync.replicas=2), сквозная семантика Exactly-Once (Idempotent Producer, Transactional Coordinator, isolation.level=read_committed), изоляция отравленных сообщений (Retry & Dead Letter Queues), компактизация журнала (Log Compaction, KTable, Tombstones), Change Data Capture (PostgreSQL WAL, Debezium Connect), паттерн Transactional Outbox, управление контрактами через Confluent Schema Registry (Avro, Protobuf, Backward/Forward Compatibility), мульти-региональная репликация MirrorMaker 2, Follower Fetching, потоковая обработка (Goka, Windowing, HyperLogLog) и сквозной трейсинг OpenTelemetry.
      </p>
    </section>
    """)
    
    # Sections (88 exercises)
    sections = [
        (1, 25, 'Раздел 1: Протокол Kafka, клиенты Go, детерминированное партиционирование, Consumer Groups, ручной коммит и Retry/DLQ'),
        (26, 50, 'Раздел 2: Log Compaction, мониторинг Lag, политики хранения (Retention), транзакции, Goka Streams и Debezium CDC'),
        (51, 70, 'Раздел 3: Observability брокера (JMX/Prometheus), Graceful Shutdown, Interactive Queries, Финальный босс и Schema Registry'),
        (71, 88, 'Раздел 4: Schema Evolution, Kafka Connect, Multi-region и Follower Fetch, безопасность TLS/ACL, CQRS, OTel и GDPR Crypto-Shredding'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 37 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили распределенный брокер Apache Kafka и стриминговую архитектуру на Go: от низкоуровневых фреймов сетевого протокола и детерминированного партиционирования по ключу до транзакционного Exactly-Once процессинга, Change Data Capture (Debezium), эволюции схем Avro/Protobuf через Confluent Schema Registry, оконной аналитики 100K RPS и построения отказоустойчивых платформ уровня BigTech.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter36.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 36 RabbitMQ</a>
            <a href="chapter38.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 38 NATS и NATS JetStream →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '37. Apache Kafka (88/88)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter38_html(chapters):
    active_chapter_num = 38
    current_exercises = ch38_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 38 • Ultra-Low Latency Messaging, Pub/Sub & JetStream Persistence in Go</div>
      <h1 class="hero-title">NATS и NATS JetStream</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по разработке, масштабированию и оптимизации высокопроизводительных микросервисных систем на Go 1.22+ с использованием NATS и NATS JetStream: архитектура Core NATS (in-memory Fire-and-Forget, субмиллисекундная задержка), паттерны One-to-Many Pub/Sub и One-to-One Queue Groups, иерархическая маршрутизация тем и подстановочные знаки (* и >), синхронный RPC-протокол Request/Reply (замена HTTP/gRPC без Envoy и Consul), устойчивость соединения (Connection Resilience, автореконнект, Backoff Jitter), метаданные и трассировка в NATS Headers (HPUB/HMSG), безопасное завершение nc.Drain() vs nc.Close(), персистентный движок JetStream на консенсусе Raft (Zero-ZooKeeper), политики хранения (LimitsPolicy, InterestPolicy, WorkQueuePolicy), сравнительный анализ Push и Pull консьюмеров, пакетное чтение (Batch Fetching) и управление темпом (Backpressure), семантика доставки At-Least-Once и Exactly-Once с дедупликацией по Nats-Msg-Id, обработка ошибок и жизненный цикл сообщений (Ack, Nak, Term, InProgress), изоляция отравленных сообщений (Dead Letter Queues), распределенное хранилище Key-Value (CAS-блокировки, реактивные вотчеры Watch), хранилище больших файлов Object Store (чанкинг >1 МБ), Service Discovery на базе KV с TTL, событийно-ориентированная архитектура (CQRS, Event Sourcing, Transactional Outbox, Saga Orchestrator), телеметрия Prometheus (:8222/varz, /connz), многоарендность (NATS 2.0 Accounts, JWT) и мульти-облачные мосты CloudEvents.
      </p>
    </section>
    """)
    
    # Sections (77 exercises)
    sections = [
        (1, 19, 'Раздел 1: Основы NATS Core, Pub/Sub, Queue Groups, иерархия тем (* и >), Request/Reply и устойчивость соединения'),
        (20, 38, 'Раздел 2: Движок JetStream, политики хранения, Push vs Pull консьюмеры, сигналы Ack/Nak/Term, дедупликация и кластеризация Raft'),
        (39, 58, 'Раздел 3: JetStream Key-Value, Object Store, Финальный босс, распределенный лок, Outbox, Saga Orchestrator и CQRS'),
        (59, 77, 'Раздел 4: Продвинутые шаблоны, бенчмарк 100K msg/s, Hot Reload конфигураций, пайплайн 1M IoT, CloudEvents и Cross-Cloud Bridge'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 38 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили сверхбыструю систему сообщений NATS и персистентную платформу JetStream на Go: от субмикросекундного in-memory обмена Core NATS и синхронного Request/Reply до распределенного консенсуса Raft, надежных очередей WorkQueue, встроенных хранилищ Key-Value и Object Store, паттернов Outbox, Saga и построения высоконагруженных платформ уровня BigTech.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter37.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 37 Apache Kafka</a>
            <a href="chapter39.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 39 Метрики и мониторинг (Prometheus) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '38. NATS и NATS JetStream (77/77)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER

def build_chapter39_html(chapters):
    active_chapter_num = 39
    current_exercises = ch39_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 39 • Observability, Prometheus Metrics, RED/USE Methods, OpenTelemetry & Grafana in Go</div>
      <h1 class="hero-title">Метрики и мониторинг (Prometheus)</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по разработке и внедрению полноценной платформы наблюдаемости (Full-Stack Observability) на Go 1.22+: архитектура pull-модели скрейпинга Prometheus, спецификация OpenMetrics, типы данных Go SDK (Counter, Gauge, Histogram, Summary), пакет client_golang и promauto, системные метрики рантайма Go (go_goroutines, go_memstats, go_gc, scheduler latency), HTTP middleware и gRPC interceptors, методологии мониторинга RED (Rate, Errors, Duration) и USE (Utilization, Saturation, Errors), защита от высокой кардинальности (High Cardinality) и очистка динамических серий через DeleteLabelValues, разработка кастомных сборщиков prometheus.Collector (Describe и Collect для PostgreSQL, Redis, RabbitMQ, Kafka), изоляция метрик через Custom Registry, встроенные декораторы promhttp, интеграция с OpenTelemetry Metrics (MeterProvider, OTLP gRPC), долговременное хранение Remote Write (Thanos, Cortex, VictoriaMetrics), Kubernetes Service Discovery (ServiceMonitor, PodMonitor CRD), правила алертинга Prometheus Alerting Rules (состояния Pending/Firing, параметр for: 5m), маршрутизация Alertmanager (группировка, ингибирование, ресиверы Slack, PagerDuty, Telegram), Prometheus Pushgateway для эфемерных batch jobs, трассировка OpenTelemetry (Exemplars, связка Logs + Traces в slog), математика надежности SRE (SLI, SLO, SLA, Error Budget в минутах, 14.4x Burn Rate, Multi-Window Multi-Burn-Rate), пробы Kubernetes (Liveness, Readiness, Startup Probes), Chaos Engineering и культура Observability-Driven Development (ODD).
      </p>
    </section>
    """)
    
    # Sections (114 exercises)
    sections = [
        (1, 28, 'Раздел 1: Фундамент Prometheus, Counter, Gauge, Histogram, Summary, HTTP middleware и рантайм Go'),
        (29, 57, 'Раздел 2: Кардинальность, кастомные Collector\'ы, мониторинг БД и кэша, Alerting Rules, Alertmanager и Pushgateway'),
        (58, 86, 'Раздел 3: Thanos Remote Write, Grafana дашборды, методология RED/USE, Service Discovery, метрики Kafka и RabbitMQ'),
        (87, 114, 'Раздел 4: Сквозной трейсинг в slog, SRE математика Error Budget, Kubernetes Probes, Chaos Engineering, Финальный босс и ODD'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 39 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили индустриальные стандарты метрик, мониторинга и телеметрии на Go: от базовых типов Counter и Gauge до калиброванных гистограмм, кастомных коллекторов, архитектуры Thanos Remote Write, дашбордов Grafana, методологий RED и USE, практик Google SRE (SLO, Error Budget, 14.4x Burn Rate) и культуры Observability-Driven Development.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter38.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 38 NATS и NATS JetStream</a>
            <a href="chapter40.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 40 Распределенная трассировка (OpenTelemetry) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '39. Метрики и мониторинг (Prometheus) (114/114)') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter40_html(chapters):
    active_chapter_num = 40
    current_exercises = ch40_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 40 • Distributed Tracing, OpenTelemetry SDK, W3C Trace Context, Jaeger & Tempo in Go</div>
      <h1 class="hero-title">Распределенная трассировка (OpenTelemetry)</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по разработке и внедрению распределенной трассировки OpenTelemetry в экосистеме микросервисов на Go 1.22+: архитектура разделения API и SDK, жизненный цикл спана (tracer.Start, defer span.End), внутрипроцессная передача контекста через context.Context и сетевое распространение по стандарту W3C Trace Context (traceparent, tracestate), семантический статус ошибки codes.Error против детальных событий span.RecordError, иерархия вызовов (Parent-Child) и причинно-следственные связи Span Links в асинхронных пакетных очередях Kafka, RabbitMQ и NATS, сквозная передача бизнес-контекста через W3C Baggage (tenant_id, feature_flag), подключение экспортеров OTLP over gRPC (:4317) и HTTP (:4318) в Jaeger и Grafana Tempo, семантические конвенции OpenTelemetry Resource и стандарты semconv, автоматическое инструментирование otelhttp (серверное middleware и клиентский транспорт RoundTripper), перехватчики otelgrpc (StatsHandler, Unary и Streaming RPC), трассировка базы данных database/sql через otelsql и драйвера jackc/pgx/v5 (pgxotel), мониторинг кэша Redis (redisotel), стратегии сэмплирования (AlwaysOn, TraceIDRatioBased, ParentBased), архитектура OpenTelemetry Collector (топология локального агента Sidecar/DaemonSet и централизованного шлюза Gateway), единый конвейер telemetry pipeline (receivers -> processors -> exporters), процессоры memory_limiter (защита от OOM), batch (пакетирование и сжатие), filter (удаление шума healthcheck) и tail_sampling (хвостовое сэмплирование 100% ошибок), автоматическая генерация RED-метрик из спанов через процессор spanmetrics, связка метрик и трейсов через OpenMetrics Exemplars для перехода в один клик от графика задержек в трейс инцидента, сквозная корреляция Traces -> Logs в Grafana (Tempo -> Loki по trace_id), построение карты микросервисов Service Graph, методология Distributed Trace Analysis для поиска узких мест и блокировок СУБД, детектор медленных запросов Slow Query Alert и надежная защита от утечки трейсов при Graceful Shutdown (defer tp.Shutdown).
      </p>
    </section>
    """)
    
    # Sections (79 exercises)
    sections = [
        (1, 20, 'Раздел 1: Фундамент OpenTelemetry SDK, TracerProvider, W3C Trace Context, Baggage, OTLP gRPC и базовая авто-инструментация'),
        (21, 40, 'Раздел 2: Docker окружение, Jaeger/Tempo UI, внутрипроцессный propagation, gRPC интерцепторы, базы данных и сэмплирование'),
        (41, 60, 'Раздел 3: Tail-Based Sampling, pgxotel, uptrace, обработка паник, топология OTel Collector, memory_limiter и batch'),
        (61, 79, 'Раздел 4: Ручной W3C Inject/Extract, Loki correlation, Service Graph, Exemplars, Distributed Trace Analysis и Slow Query Alert'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 40 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили распределенную трассировку OpenTelemetry на Go: от инициализации TracerProvider и протокола W3C Trace Context до сквозной передачи Baggage, интеграции с Jaeger, Grafana Tempo и Loki, настройки Tail-Based Sampling, защиты OTel Collector от OOM и глубокого анализа производительности распределенных транзакций.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter39.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 39 Метрики и мониторинг (Prometheus)</a>
            <a href="chapter41.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 41 Профилирование и рантайм-диагностика →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '40. Распределенная трассировка (OpenTelemetry) (79/79)') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter41_html(chapters):
    active_chapter_num = 41
    current_exercises = ch41_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 41 • CPU & Memory Profiling, Goroutine Leaks, pprof, runtime/trace, Pyroscope & FinOps in Go</div>
      <h1 class="hero-title">Профилирование и рантайм-диагностика</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по профилированию, рантайм-диагностике и анализу производительности микросервисов на Go 1.22+ в условиях HighLoad: стандартный пакет net/http/pprof и архитектурный паттерн Dual-Port (полная физическая изоляция служебного порта :6060 от публичного роутера для предотвращения утечек исходного кода, дампов памяти и DoS-атак), снятие 30-секундных профилей CPU через go tool pprof с интерактивным анализом Flame Graph, команд top и list, локализация утечек памяти в куче (debug/pprof/heap) с разграничением флагов -inuse_space и -alloc_space, выявление утечек горутин (Goroutine Leaks) и обнаружение дедлоков в состояниях semacquire и chan receive, детальное профилирование аллокаций в бенчмарках (-benchmem, -memprofile), архитектура непрерывного профилирования 24/7 (Continuous Profiling через Grafana Pyroscope и Parca) для выявления регрессий релизов на ранних стадиях, дифференциальный анализ профилей (pprof -base old.prof new.prof), трассировка выполнения рантайма runtime/trace (миллисекундная хронология планировщика GMP, Stop-The-World фаз сборщика мусора GC и задержек системных вызовов Syscalls в go tool trace), прямой экспорт системной телеметрии через runtime.ReadMemStats, а также практические FinOps-стратегии планирования мощностей (Capacity Planning с линейной экстраполяцией и запасом Headroom 30%) и оптимизации стоимости инфраструктуры (Cost Optimization по метрике cost_per_request).
      </p>
    </section>
    """)
    
    # Sections (24 exercises)
    sections = [
        (1, 12, 'Раздел 1: Архитектура pprof, CPU-bound нагрузка, утечки памяти и горутин, дедлоки, Pyroscope и goroutine profile'),
        (13, 24, 'Раздел 2: Трассировка runtime/trace, alloc_objects, MemStats, защита в проде, диффы pprof -base, Capacity Planning и FinOps'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 41 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили профилирование и рантайм-диагностику в Go: от подключения изолированного pprof на порту :6060 и поиска утечек памяти в куче до работы с runtime/trace, настройки непрерывного профилирования Pyroscope, дифференциального анализа -base и управления инфраструктурной стоимостью в рамках FinOps.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter40.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 40 Распределенная трассировка (OpenTelemetry)</a>
            <a href="chapter42.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 42 Проектирование чистой архитектуры и DDD →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '41. Профилирование и рантайм-диагностика (24/24)') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter42_html(chapters):
    active_chapter_num = 42
    current_exercises = ch42_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append("""
    <section class="hero-section" id="top">
      <div class="hero-tag">Модуль 42 • Clean Architecture, DDD, Hexagonal (Ports & Adapters), CQRS, Event Sourcing & Sagas in Go</div>
      <h1 class="hero-title">Проектирование чистой архитектуры и DDD</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по чистой архитектуре, Domain-Driven Design (DDD) и распределенным архитектурным паттернам в Go 1.22+ для HighLoad бэкенда: плоская и слоистая структура проектов (Flat Layout, Package by Layer vs Package by Feature, стандарт golang-standards/project-layout), принцип инверсии зависимостей (Dependency Inversion Principle, DIP: объявление узких интерфейсов на стороне потребителя), 4 канонических слоя Clean Architecture Uncle Bob (Entities, Use Cases, Interface Adapters, Frameworks & Drivers) и правило центростремительных зависимостей (Dependency Rule), гексагональная архитектура Алистера Кокберна (Hexagonal Architecture / Ports & Adapters: Inbound и Outbound порты), тактический дизайн DDD (богатые сущности Rich Domain Model против анемичных моделей, неизменяемые объекты-значения Value Objects, границы транзакций Aggregate Roots, доменные сервисы Domain Services и спецификации Specification Pattern), Anti-Corruption Layer (ACL) для безопасной интеграции с legacy-монолитами, распределенные транзакции (Saga Orchestration через конечные автоматы и Saga Choreography с компенсирующими действиями), Event Sourcing с воспроизведением (Replay) из Append-Only лога событий и материализованными представлениями (Materialized Views), архитектура CQRS с разделением потоков Command Bus и Query Bus, паттерны Unit of Work и Transactional Outbox, защита периметра API Gateway (Token Bucket Rate Limiting, Circuit Breaker, Idempotency Keys), инкрементальная миграция Strangler Fig и разработка API-First со сквозным дипломным HighLoad-проектом сервиса коротких ссылок.
      </p>
    </section>
    """)
    
    # Sections (98 exercises)
    sections = [
        (1, 25, 'Раздел 1: Архитектурные стили Go, Clean & Hexagonal Architecture, DIP, Composition Root, Monolith First и Bounded Contexts'),
        (26, 50, 'Раздел 2: Anti-Corruption Layer, Rich Entities, Aggregate Roots, Domain Events, Saga Orchestration, CQRS и Event Sourcing'),
        (51, 74, 'Раздел 3: Модульный монолит, BFF, Circuit Breaker, трансляция ошибок, Unit of Work и Idempotency Keys'),
        (75, 98, 'Раздел 4: Value Objects, Спецификации, Transactional Outbox, Google Wire, Sharding, Backpressure и HighLoad Shortener'),
    ]
    
    ex_dict = {e['num']: e for e in current_exercises}
    
    for start_n, end_n, sec_title in sections:
        content_parts.append(f"""
        <div class="section-separator">
            <h2>{sec_title}</h2>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        """)
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    
    content_parts.append("""
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 42 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили проектирование чистой архитектуры и предметно-ориентированное проектирование (DDD) в Go: от организации слоев и инверсии зависимостей DIP до тактических шаблонов Aggregate Roots, Value Objects, распределенных саг с компенсацией, Event Sourcing, CQRS, Transactional Outbox и создания масштабируемого HighLoad сервиса коротких ссылок.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter41.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 41 Профилирование и рантайм-диагностика</a>
            <a href="chapter43.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 43 Шаблоны проектирования распределенных и enterprise-систем →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'42. Проектирование чистой архитектуры и DDD ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter43_html(chapters):
    active_chapter_num = 43
    current_exercises = ch43_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 43</div>
      <h1 class="hero-title">Шаблоны проектирования распределенных и enterprise-систем</h1>
      <p class="hero-desc">
        Фундаментальное руководство по паттернам проектирования современных распределенных, высоконадежных и корпоративных систем на Go: архитектура API Gateway и Backend-for-Frontend (BFF), Apollo GraphQL Federation, gRPC-Gateway, Sidecar прокси и Service Mesh (Istio/Envoy), паттерн Database-per-Service, распределенные саги с Transactional Outbox и Inbox, Change Data Capture (CDC Debezium), Polyglot Persistence, шардирование с Consistent Hashing, CQRS и множественные проекции Event Sourcing, синхронный gRPC против асинхронного обмена событиями, Circuit Breaker с Fallback, Bulkhead изоляция пулов горутин, Retry с Exponential Backoff и Full Jitter, ключи идемпотентности, мультитенантность (Shared Schema с RLS, Separate Schemas и Separate Databases), безопасность Zero Trust с взаимным mTLS, W3C Distributed Tracing, соблюдение регуляторных требований (GDPR, HIPAA, PCI DSS), канареечные релизы, автоматический откат, инженерия хаоса, Patroni HA, Singleflight Cache Stampede, а также практический системный дизайн платформ E-commerce, Banking Core, Real-Time Bidding, IoT Platform, Collaborative Editing CRDT, Social Network и AI/ML Platform.
      </p>
    </section>
    """)
    
    # Sections (112 exercises)
    sections = [
        (1, 28, 'Раздел 1: Сетевые шлюзы, BFF, хранилища Database-per-Service, надежность транзакций и основы мультитенантности'),
        (29, 56, 'Раздел 2: Безопасность Zero Trust, шифрование PII, аудит, идемпотентность API, RBAC/ABAC и стандарты Compliance'),
        (57, 84, 'Раздел 3: Канареечные релизы, инженерия хаоса, высокая доступность Patroni, Singleflight, GitOps и отраслевые кейсы'),
        (85, 112, 'Раздел 4: Мультикластерный Service Mesh, FinOps, Active-Active репликация, неблокирующий аудит и системный дизайн Enterprise-платформ')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 43!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве изучили архитектурные паттерны распределенных и enterprise-систем на Go: от проектирования шлюзов, изоляции хранилищ и саг с Outbox/Inbox до мультитенантности, Zero Trust, канареечных релизов, Patroni HA и системного дизайна высоконагруженных платформ e-commerce, финтеха, RTB и AI/ML.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter42.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 42 Проектирование чистой архитектуры и DDD</a>
            <a href="chapter44.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 44 Проектирование высоконагруженных и отказоустойчивых систем →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'43. Шаблоны проектирования распределенных и enterprise-систем ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter44_html(chapters):
    active_chapter_num = 44
    current_exercises = ch44_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 44</div>
      <h1 class="hero-title">Проектирование высоконагруженных и отказоустойчивых систем</h1>
      <p class="hero-desc">
        Комплексное практическое руководство по проектированию экстремально высоконагруженных (HighLoad) и отказоустойчивых распределенных систем на языке Go: CQRS, Event Sourcing, многоуровневое кэширование (Cache-Aside, Write-Through, Write-Behind, Refresh-Ahead), алгоритмы Rate Limiting (Token Bucket, Leaky Bucket, Sliding Window Counter), L7 балансировка с Weighted Round-Robin, защита от каскадных сбоев через Bulkhead и Circuit Breaker, пулы соединений и дедупликация через singleflight.Group. Разбор механизмов Load Shedding, Backpressure, хаос-тестирования, шардирования с Consistent Hashing, катастрофоустойчивости (Disaster Recovery/PITR), динамического пула воркеров, а также сквозная реализация отказоустойчивого HighLoad SaaS-бэкенда и неблокирующего TCP-сервера на Linux epoll для преодоления барьера C10k/C100k.
      </p>
    </section>
    """)
    
    # Sections (64 exercises)
    sections = [
        (1, 16, 'Раздел 1: CQRS, Event Sourcing, стратегии кэширования и алгоритмы Rate Limiting'),
        (17, 32, 'Раздел 2: L7 балансировка, Bulkhead, Circuit Breaker, пулы соединений и Singleflight'),
        (33, 48, 'Раздел 3: Отказоустойчивость, дедупликация запросов, префетчинг, Load Shedding и инженерия хаоса'),
        (49, 64, 'Раздел 4: Согласованное хеширование, DR/PITR, динамические воркеры, Final Boss SaaS и C10k epoll')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 44!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы успешно освоили ключевые дисциплины HighLoad и Fault Tolerance инженерии на Go: от тонкой настройки кэширования, лимитирования запросов и защиты пулов до согласованного хеширования, катастрофоустойчивости и неблокирующего сетевого ввода-вывода через системные вызовы Linux epoll.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter43.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 43 Шаблоны проектирования распределенных и enterprise-систем</a>
            <a href="chapter45.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 45 Контейнеризация и Docker →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'44. Проектирование высоконагруженных и отказоустойчивых систем ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter45_html(chapters):
    active_chapter_num = 45
    current_exercises = ch45_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 45</div>
      <h1 class="hero-title">Контейнеризация и Docker</h1>
      <p class="hero-desc">
        Исчерпывающее практическое руководство по контейнеризации Go-микросервисов на базе Docker и экосистемы OCI: анатомия одноэтапных и многоэтапных сборок (Multi-stage build), уменьшение размера продакшн-образов с 850 МБ до 5–15 МБ на базе Alpine, Google Distroless и чистого scratch. Техники изоляции кэша зависимостей (go.mod/go.sum) и ускорения сборок в 10 раз с помощью BuildKit cache mounts, безопасная передача токенов через secret mounts, мультиплатформенные образы (Multi-Arch AMD64/ARM64) с Docker Buildx. Разбор каверзных кейсов статической линковки CGO (musl против glibc), работа с SSL-сертификатами (ca-certificates) и базой таймзон (tzdata). Комплексное развертывание многокомпонентных сред в Docker Compose (Go, PostgreSQL, Redis, Kafka, NATS, Jaeger), управление сетями, томами (Named Volumes, Bind Mounts, tmpfs), политиками перезапуска, ротацией логов и лимитами ресурсов cgroups v2. Реализация горячей перезагрузки с Air, паттерн Init Container для безопасных миграций баз данных, статический аудит слоев утилитой dive и глубокое сканирование уязвимостей (CVE) через govulncheck и Trivy в соответствии со стандартами Security by Default.
      </p>
    </section>
    """)
    
    # Sections (75 exercises)
    sections = [
        (1, 19, 'Раздел 1: Основы Dockerfile, многоэтапная сборка (Multi-stage), Scratch, Distroless и кэширование слоев'),
        (20, 38, 'Раздел 2: Безопасность образов, Non-Root, BuildKit кэш и секреты, Multi-Arch сборка и статический CGO'),
        (39, 57, 'Раздел 3: Docker Compose, управление сетью и томами, переменные окружения, Health Checks и лимиты ресурсов'),
        (58, 75, 'Раздел 4: Hot-reload с Air, Init-контейнеры, сканирование уязвимостей, аудит слоев и профили Compose')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 45!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы досконально изучили технологии контейнеризации Go-микросервисов на уровне Senior/Staff инженера: от проектирования минималистичных и безопасных OCI-образов до оркестрации распределенных стеков разработки в Docker Compose, аудита безопасности DevSecOps и защиты от атак Container Escape.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter44.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 44 Проектирование высоконагруженных и отказоустойчивых систем</a>
            <a href="chapter46.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #090d16; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 46 Автоматизация CI-CD →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'45. Контейнеризация и Docker ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter46_html(chapters):
    active_chapter_num = 46
    current_exercises = ch46_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 46</div>
      <h1 class="hero-title">Автоматизация CI-CD</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по проектированию, оптимизации и защите корпоративных конвейеров Continuous Integration и Continuous Delivery (CI/CD) для микросервисов на Go. Полный разбор декларативных пайплайнов GitHub Actions, GitLab CI, Jenkinsfile и Cloud-Native фреймворка Tekton: настройка матричного тестирования кросс-платформенного кода (Go 1.21–1.24, Linux/macOS/Windows), параллелизация тест-сьютов и оптимизация DAG-графов исполнения. Углубленные техники кэширования модулей Go (GOPATH/pkg/mod, GOCACHE) и слоев OCI-образов BuildKit через GitHub Actions Cache (gha) и удаленные реестры. Безопасность цепочки поставок ПО (Software Supply Chain Security / DevSecOps): статический анализ govulncheck на базе Call Graph Reachability, мета-линтер golangci-lint с fail-fast политиками, сканирование OCI-образов утилитой Trivy, инвентаризация SBOM с Syft и криптографическая подпись артефактов через Cosign (Sigstore Keyless OIDC). Мультиплатформенная кросс-компиляция (AMD64/ARM64) с QEMU и Buildx. Продвинутые практики развертывания: автоматизация релизов GoReleaser и SemVer-версионирование, интеграционные тесты с Service Containers (Redis, PostgreSQL), GitOps-оркестрация на базе ArgoCD (Application CRD, паттерн App of Apps) и Flux CD (ImageUpdateAutomation), прогрессивная доставка Canary-релизов в Argo Rollouts с автооткатом по метрикам Prometheus, защита веток через Branch Protection Rules и принципы Platform Engineering (Self-Service IDP).
      </p>
    </section>
    """)
    
    # Sections (57 exercises)
    sections = [
        (1, 14, 'Раздел 1: Базовые пайплайны GitHub Actions, матричные сборки, линтинг и кэширование зависимостей'),
        (15, 28, 'Раздел 2: Сборка и публикация Docker-образов, GitLab CI, Jenkins, покрытие тестами и SAST аудит'),
        (29, 43, 'Раздел 3: Сканирование образов Trivy, GitOps с ArgoCD, релизы через GoReleaser и версионирование SemVer'),
        (44, 57, 'Раздел 4: Продвинутый CD, канареечные релизы Argo Rollouts, Flux CD, секреты и Platform Engineering')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 46!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили проектирование промышленных CI/CD конвейеров для Go: от матричных сборок, линтинга и криптографической подписи артефактов до GitOps-доставки через ArgoCD, канареечных релизов в Argo Rollouts и платформ самообслуживания разработчиков.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter45.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 45 Контейнеризация и Docker</a>
            <a href="chapter47.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #38bdf8;">Глава 47 Оркестрация в Kubernetes →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'46. Автоматизация CI-CD ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter47_html(chapters):
    active_chapter_num = 47
    current_exercises = ch47_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 47</div>
      <h1 class="hero-title">Оркестрация в Kubernetes</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по промышленной оркестрации высоконагруженных распределенных систем на Go в Kubernetes (K8s). Полный разбор базовых и продвинутых примитивов кластера: Pods, ReplicaSets, Deployments (RollingUpdate c maxSurge/maxUnavailable, Recreate), Services (ClusterIP, NodePort, LoadBalancer, Headless для gRPC) и CoreDNS Service Discovery. Управление конфигурациями и секретами: ConfigMaps (проекция томов и symlink rotation), Secrets (KMS шифрование, External Secrets Operator для синхронизации с HashiCorp Vault и AWS Secrets Manager). Персистентное хранилище: PersistentVolumes, PersistentVolumeClaims, StorageClasses с динамическим провижинингом (CSI драйверы) и StatefulSets. Механизмы надежности рантайма Go: тонкий тюнинг GOMEMLIMIT и Linux cgroups для исключения OOMKilled, Liveness/Readiness/Startup Probes и гарантированный Zero-Downtime Graceful Shutdown через связку lifecycle.preStop со sleep и signal.NotifyContext. Продвинутое планирование и автомасштабирование: Taints, Tolerations, NodeAffinity, PodAntiAffinity, TopologySpreadConstraints, Horizontal Pod Autoscaler (HPA v2 по CPU и кастомным метрикам KEDA), Vertical Pod Autoscaler (VPA), PodDisruptionBudget (PDB), Cluster Autoscaler и новое поколение Karpenter с bin-packing Spot инстансов. Пакетные менеджеры и декларативные манифесты: глубокое сравнение Helm 3 (шаблонизация Go/Sprig, субчарты, lifecycle hooks) и Kustomize (base/overlays, patches). Безопасность и комплаенс: Pod Security Standards (PSS/PSA Restricted profile), OPA Gatekeeper (Policy-as-Code на Rego), Kyverno и сетевая изоляция Zero-Trust NetworkPolicies (Calico/Cilium eBPF). Наблюдаемость (Observability): Prometheus Operator (ServiceMonitor), сбор логов Grafana Loki и Promtail, распределенная трассировка с OpenTelemetry Collector и Jaeger, runtime аудит ядра с Falco. Service Mesh: внедрение Istio (Envoy sidecar injection, mTLS STRICT, L7 AuthorizationPolicy, канареечные релизы через VirtualService и DestinationRule). GitOps и прогрессивная доставка: развертывание флота кластеров через ArgoCD (паттерны App-of-Apps и ApplicationSet Matrix Generator), автоматизация обновления образов ArgoCD Image Updater, автоматический анализ SLO в Argo Rollouts (Canary/Blue-Green) и практика Chaos Engineering с LitmusChaos.
      </p>
    </section>
    """)
    
    # Sections (180 exercises)
    sections = [
        (1, 45, 'Раздел 1: Базовые примитивы Kubernetes — Pods, Deployments, Services, ConfigMaps, Secrets, Probes и лимиты ресурсов'),
        (46, 90, 'Раздел 2: Автомасштабирование (HPA, VPA), Affinity, Taints/Tolerations, NetworkPolicies, StatefulSets и PDB'),
        (91, 135, 'Раздел 3: Управление конфигурациями (Helm, Kustomize), безопасность RBAC, Admission Controllers и CRD/Операторы'),
        (136, 180, 'Раздел 4: Продвинутая оркестрация, Service Mesh, Observability, прогрессивная доставка и High Availability')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 47!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы завершили один из самых объемных и фундаментальных модулей курса! Теперь вы в совершенстве владеете полным стеком оркестрации в Kubernetes: от архитектуры базовых примитивов до создания отказоустойчивых Cloud Native платформ, GitOps автоматизации, внедрения Service Mesh и проектирования систем с надежностью 99.99%.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter46.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 46 Автоматизация CI-CD</a>
            <a href="chapter48.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #38bdf8;">Глава 48 Планировщик GMP →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'47. Оркестрация в Kubernetes ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter48_html(chapters):
    active_chapter_num = 48
    current_exercises = ch48_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 48</div>
      <h1 class="hero-title">Планировщик GMP</h1>
      <p class="hero-desc">
        Глубокое погружение в рантайм Go и внутреннее устройство планировщика GMP (Goroutine, Machine, Processor). Архитектура и жизненный цикл сущностей G, M, P: локальные очереди выполнения runq (256 слотов), runnext с наивысшим приоритетом, глобальная очередь sched.runq и спинлоки. Алгоритмы балансировки нагрузки: Work Stealing (кража половины горутин из случайного P), периодическая проверка глобальной очереди (каждые 61 тик для предотвращения голодания), а также сетевой поллер (Netpoller на epoll/kqueue) и интеграция дескрипторов со статусом _Gwaiting. Обработка блокирующих операций и системных вызовов: entersyscall / exitsyscall, отсоединение P от M, перехват через фоновый системный монитор sysmon. Эволюция вытеснения: от кооперативного переключения на вызовах функций (проверка morestack и stackguard0) до асинхронного вытеснения сигналом SIGURG в Go 1.14+. Инструменты профилирования и диагностики планировщика: GODEBUG с флагами schedtrace и scheddetail, runtime/trace, Block и Mutex профилирование pprof, измерение scheduler latency и джиттера вытеснения, оптимизация Bounds Check Elimination (BCE) и анализ сгенерированного ассемблера Plan 9.
      </p>
    </section>
    """)
    
    # Sections (93 exercises)
    sections = [
        (1, 25, 'Раздел 1: Архитектура GMP, Очереди и Планирование (Упр. 1–25)'),
        (26, 50, 'Раздел 2: Системные вызовы, Netpoller и Work Stealing (Упр. 26–50)'),
        (51, 75, 'Раздел 3: Вытеснение, Трассировка и Сигналы Прерывания (Упр. 51–75)'),
        (76, 93, 'Раздел 4: Низкоуровневая Оптимизация, BCE и Внутренности Рантайма (Упр. 76–93)')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 48!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы завершили фундаментальное исследование планировщика GMP и рантайма Go! Теперь вы обладаете кристальным пониманием того, как выполняются миллионы горутин на системных потоках ОС, как рантайм вытесняет вычисления, мультиплексирует ввод-вывод через Netpoller и как тонко настраивать параметры исполнения в высоконагруженном production.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter47.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 47 Оркестрация в Kubernetes</a>
            <a href="chapter49.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #38bdf8;">Глава 49 Аллокатор кучи и управление памятью →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'48. Планировщик GMP ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter49_html(chapters):
    active_chapter_num = 49
    current_exercises = ch49_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 49</div>
      <h1 class="hero-title">Аллокатор кучи и управление памятью</h1>
      <p class="hero-desc">
        Исчерпывающее руководство по внутреннему устройству аллокатора кучи Go и управлению оперативной памятью. Архитектура TCMalloc: трехуровневая модель Lock-Free mcache (per-P кэш спанов), центральный пул mcentral (по 136 классам размеров scan/noscan со спинлоками) и глобальная куча mheap (страницы по 8 КБ, arenas по 64 МБ, системные вызовы mmap и madvise). Анатомия структуры mspan: квантование памяти на 67 классов размеров (Size Classes), расчет внутренней фрагментации, побитовые карты allocBits и gcmarkBits. Механика Escape Analysis: алгоритмы анализа побега компилятора Go (-gcflags="-m"), причины перемещения переменных со стека в кучу (возврат указателей, замыкания, интерфейсный боксинг, срезы динамической емкости). Оптимизация памяти: выравнивание полей структур (Memory Alignment) и устранение ложного разделения кэш-линий (False Sharing). Мониторинг и профилирование: метрики runtime.MemStats (HeapAlloc, HeapSys, HeapIdle, HeapReleased), поиск утечек в pprof heap (inuse_space vs alloc_space), тонкая настройка GOMEMLIMIT, переиспользование буферов в sync.Pool и реализация кастомного Arena Allocator.
      </p>
    </section>
    """)
    
    # Sections (66 exercises)
    sections = [
        (1, 17, 'Раздел 1: Архитектура TCMalloc, mcache, mcentral и mheap (Упр. 1–17)'),
        (18, 34, 'Раздел 2: Анализ побега (Escape Analysis), Стеки и Классы размеров (Упр. 18–34)'),
        (35, 51, 'Раздел 3: Фрагментация, sync.Pool, Выравнивание памяти и Scavenger (Упр. 35–51)'),
        (52, 66, 'Раздел 4: Анатомия mallocgc, Профилирование pprof и Custom Allocator (Упр. 52–66)')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 49!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве изучили механику управления памятью в Go: от ассемблерных инструкций выделения памяти на стеке до многоуровневой архитектуры TCMalloc, профилирования утечек в pprof и создания высокоскоростных ареных аллокаторов для HighLoad.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter48.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 48 Планировщик GMP</a>
            <a href="chapter50.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">Глава 50 Garbage Collector и тюнинг памяти →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'49. Аллокатор кучи и управление памятью ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter50_html(chapters):
    active_chapter_num = 50
    current_exercises = ch50_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 50</div>
      <h1 class="hero-title">Garbage Collector и тюнинг памяти</h1>
      <p class="hero-desc">
        Глубокое практическое и теоретическое руководство по внутреннему устройству сборщика мусора Go и экстремальному тюнингу памяти в HighLoad. Четыре фазы работы GC: микросекундные паузы Stop-The-World (Mark Setup и Mark Termination), конкурентная маркировка (Concurrent Marking) на 25% CPU и ленивая очистка (Lazy Sweeping). Математика трехцветного автомата (Tri-color Mark-and-Sweep) и защита от потери объектов с помощью Hybrid Write Barrier (Dijkstra + Yuasa). Управление темпом сборки: адаптивный контроллер mgcpacer.go, алгоритм Mark Assist, расчет HeapGoal и калибровка параметров GOGC и GOMEMLIMIT (Go 1.19+). Архитектурные паттерны снижения давления на GC: переиспользование буферов в sync.Pool, noscan типы данных, интернирование строк, работа с off-heap памятью через mmap и профилирование утечек в pprof и go tool trace.
      </p>
    </section>
    """)
    
    # Sections (87 exercises)
    sections = [
        (1, 22, 'Раздел 1: Архитектура Tri-color, Фазы GC и Барьеры записи (Упр. 1–22)'),
        (23, 44, 'Раздел 2: GC Pacing, Mark Assist и Тюнинг GOGC/GOMEMLIMIT (Упр. 23–44)'),
        (45, 66, 'Раздел 3: Scavenger, Профилирование gctrace и Оптимизация памяти (Упр. 45–66)'),
        (67, 87, 'Раздел 4: Deep Dive в mgcpacer.go, OOM Prevention и Архитектурный тюнинг (Упр. 67–87)')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 50!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили механику работы сборщика мусора Go: от битовых карт gcmarkBits и ассемблерных инструкций барьера записи до тонкого тюнинга GOMEMLIMIT, предотвращения OOM в Kubernetes и устранения задержек Mark Assist в HighLoad.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter49.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 49 Аллокатор кучи и управление памятью</a>
            <a href="chapter51.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #080d1a; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 51 Работа с unsafe и низкоуровневой памятью →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'50. Garbage Collector и тюнинг памяти ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter51_html(chapters):
    active_chapter_num = 51
    current_exercises = ch51_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 51</div>
      <h1 class="hero-title">Работа с unsafe и низкоуровневой памятью</h1>
      <p class="hero-desc">
        Исчерпывающее практическое и теоретическое руководство по пакету unsafe и прямому управлению физической памятью в Go. Фундаментальные типы и канонические правила: взаимное преобразование указателей через unsafe.Pointer, целочисленная адресная арифметика с типом uintptr, вычисление размеров и смещений полей структур с помощью unsafe.Sizeof, unsafe.Alignof и unsafe.Offsetof. Современный API Go 1.17+ и Go 1.20+: безопасное смещение указателей unsafe.Add, мгновенное конструирование срезов и строк из сырой памяти через unsafe.Slice, unsafe.SliceData, unsafe.String и unsafe.StringData. Экстремальные HighLoad паттерны: Zero-Copy сериализация бинарных протоколов, эмуляция C-union и Type Punning без битовых сдвигов, обход инкапсуляции и чтение неэкспортированных приватных полей, построение кастомных arena-аллокаторов и lock-free структур данных на атомарных CAS-указателях. Анализ критических ловушек: перемещение стека при Stack Growth, инвалидация uintptr при GC safepoints, гонки данных в обход компилятора, строгие проверки go vet -unsafeptr и гарантированное предотвращение преждевременного сбора мусора с runtime.KeepAlive.
      </p>
    </section>
    """)
    
    # Sections (85 exercises)
    sections = [
        (1, 21, 'Раздел 1: Основы unsafe.Pointer, uintptr и выравнивание типов (Упр. 1–21)'),
        (22, 42, 'Раздел 2: Арифметика указателей, доступ к приватным полям и struct offset (Упр. 22–42)'),
        (43, 64, 'Раздел 3: Zero-Copy String/Bytes, Type Punning и reflect.SliceHeader (Упр. 43–64)'),
        (65, 85, 'Раздел 4: Атомарные операции с unsafe, выравнивание шины памяти и правила безопасности (Упр. 65–85)')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 51!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили низкоуровневую работу с памятью в Go: от правил адресной арифметики и выравнивания структур до экстремальных Zero-Copy техник, кастомных арен и атомарных lock-free структур данных, применяемых в ведущих HighLoad системах мира.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter50.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 50 Garbage Collector и тюнинг памяти</a>
            <a href="chapter52.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #080d1a; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 52 Интеграция с C-кодом через CGO →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'51. Работа с unsafe и низкоуровневой памятью ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter52_html(chapters):
    active_chapter_num = 52
    current_exercises = ch52_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 52</div>
      <h1 class="hero-title">Интеграция с C-кодом через CGO</h1>
      <p class="hero-desc">
        Исчерпывающее практическое и архитектурное руководство по интеграции Go с нативными библиотеками на языках C и C++ с помощью инструмента CGO. Анатомия CGO-моста: специальный псевдопакет import "C", C-преамбула и правила компиляции. Взаимное отображение типов данных: целочисленные и вещественные типы, преобразование строк через C.CString, C.GoString, C.GoStringN и обязательное освобождение памяти с C.free. Работа со сложными структурами, объединениями union, перечислениями enum, массивами и срезами через unsafe.Pointer и unsafe.Slice. Межъязыковая модель исполнения: механизм смены стека между горутинами Go и системными потоками ОС (crosscall2, asmcgocall, cgocallback), накладные расходы и бенчмаркинг. Строгие правила безопасности указателей Go 1.6+ (cgocheck): запрет передачи указателей на Go-память в C-структуры и предотвращение use-after-free. Двусторонний интероп: экспорт Go-функций в Си через //export, реализация C-коллбэков и безопасный проброс хэндлов с cgo.Handle. Управление сборкой и компоновкой: флаги компилятора #cgo CFLAGS, LDFLAGS, статическая линковка архивов .a и динамическая загрузка .so библиотек в рантайме через dlopen/dlsym. Архитектурные альтернативы и оптимизации: паттерн Zero-Allocation Shared Memory Bridge с Lock-Free Ring Buffer для High-Frequency Trading и принципы полной статической сборки с CGO_ENABLED=0.
      </p>
    </section>
    """)
    
    # Sections (70 exercises)
    sections = [
        (1, 18, 'Раздел 1: Введение в CGO, C preamble, примитивные типы и базовые строки (Упр. 1–18)'),
        (19, 36, 'Раздел 2: Управление памятью C.CString, C.free, структуры и слайсы (Упр. 19–36)'),
        (37, 53, 'Раздел 3: C-указатели, callback-функции, //export и правила cgocheck (Упр. 37–53)'),
        (54, 70, 'Раздел 4: Статическая и динамическая линковка, флаги CFLAGS/LDFLAGS и оптимизация накладных расходов (Упр. 54–70)')
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_end, s_title = sections[current_sec_idx]
            if num == s_start:
                content_parts.append(f"""
                <div class="section-separator">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 52!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили интеграцию Go с C и C++ кодом: от C-преамбулы, преобразования типов и строгих правил cgocheck до экспорта коллбэков, статической компоновки и построения экстремальных zero-allocation мостов на разделяемой памяти.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter51.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 51 Работа с unsafe и низкоуровневой памятью</a>
            <a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 53 Системные вызовы и взаимодействие с ОС (Скоро) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'52. Интеграция с C-кодом через CGO ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

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
        ('chapter11.html', build_chapter11_html),
        ('chapter12.html', build_chapter12_html),
        ('chapter13.html', build_chapter13_html),
        ('chapter14.html', build_chapter14_html),
        ('chapter15.html', build_chapter15_html),
        ('chapter16.html', build_chapter16_html),
        ('chapter17.html', build_chapter17_html),
        ('chapter18.html', build_chapter18_html),
        ('chapter19.html', build_chapter19_html),
        ('chapter20.html', build_chapter20_html),
        ('chapter21.html', build_chapter21_html),
        ('chapter22.html', build_chapter22_html),
        ('chapter23.html', build_chapter23_html),
        ('chapter24.html', build_chapter24_html),
        ('chapter25.html', build_chapter25_html),
        ('chapter26.html', build_chapter26_html),
        ('chapter27.html', build_chapter27_html),
        ('chapter28.html', build_chapter28_html),
        ('chapter29.html', build_chapter29_html),
        ('chapter30.html', build_chapter30_html),
        ('chapter31.html', build_chapter31_html),
        ('chapter32.html', build_chapter32_html),
        ('chapter33.html', build_chapter33_html),
        ('chapter34.html', build_chapter34_html),
        ('chapter35.html', build_chapter35_html),
        ('chapter36.html', build_chapter36_html),
        ('chapter37.html', build_chapter37_html),
        ('chapter38.html', build_chapter38_html),
        ('chapter39.html', build_chapter39_html),
        ('chapter40.html', build_chapter40_html),
        ('chapter41.html', build_chapter41_html),
        ('chapter42.html', build_chapter42_html),
        ('chapter43.html', build_chapter43_html),
        ('chapter44.html', build_chapter44_html),
        ('chapter45.html', build_chapter45_html),
        ('chapter46.html', build_chapter46_html),
        ('chapter47.html', build_chapter47_html),
        ('chapter48.html', build_chapter48_html),
        ('chapter49.html', build_chapter49_html),
        ('chapter50.html', build_chapter50_html),
        ('chapter51.html', build_chapter51_html),
        ('chapter52.html', build_chapter52_html),
    ]
    
    for filename, builder_fn in pages:
        path = os.path.join('/home/ut/work/go-workout', filename)
        content = builder_fn(chapters)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Written {path} ({os.path.getsize(path)} bytes)")

