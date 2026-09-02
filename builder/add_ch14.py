with open('builder/build_all.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add import
old_import = "with open('builder/chapter13_data.json', 'r', encoding='utf-8') as f:\n    ch13_exercises = json.load(f)"
new_import = old_import + "\n\nwith open('builder/chapter14_data.json', 'r', encoding='utf-8') as f:\n    ch14_exercises = json.load(f)"
code = code.replace(old_import, new_import)

# 2. Add status_map entry
old_status = "            13: ('chapter13.html', '71/71'),"
new_status = old_status + "\n            14: ('chapter14.html', '77/77'),"
code = code.replace(old_status, new_status)

# 3. Add link in Chapter 13 footer
old_ch13_footer = '<a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 14: Методы (Скоро) →</a>'
new_ch13_footer = '<a href="chapter14.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #000; font-weight: 700; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 14: Интерфейсы →</a>'
code = code.replace(old_ch13_footer, new_ch13_footer)

# 4. Add build_chapter14_html function
ch14_fn = """def build_chapter14_html(chapters):
    sidebar_html = build_sidebar(chapters, active_chapter_num=14, current_exercises=ch14_exercises)
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    content_parts.append(\"\"\"
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
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">77 из 77</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">Duck Typing</span><span class="stat-lbl">Implicit Satisfaction</span></div>
            <div class="stat-item"><span class="stat-val">iface & eface</span><span class="stat-lbl">itab + data Layout</span></div>
            <div class="stat-item"><span class="stat-val">Postel\\'s Law</span><span class="stat-lbl">Accept IFace, Return Struct</span></div>
        </div>
    </section>
    \"\"\")
    section_groups_ch14 = [
        (1, 26, "Раздел 1: Неявная Реализация, Полиморфизм, Type Switch, io.Reader/Writer и Method Sets", "Greeter и Animal, срез []Speaker, Type Switch над any, опасность одинарного Type Assertion v.(string), безопасный comma-ok, конвертер ToInt, интерфейс Shape (Area/Perimeter), io.Reader для MyBuffer, каверзный случай Value vs Pointer Receiver, io.Writer и композиция Triathlete"),
        (27, 52, "Раздел 2: Comma-Ok, Композиция Потоков, Опциональные Интерфейсы, Кастомные Ошибки и Ловушка Nil Interface", "Type Assertion str, ok, ReadWriteCloser, динамическая проверка fmt.Stringer, ProcessStream, кастомная ошибка ValidationError (errors.As), sort.Interface, супер-ловушка nil interface vs nil pointer, IsReallyNil через reflect, Postel\\'s Law и адаптер функций HandlerFunc"),
        (53, 77, "Раздел 3: Compile-Time Checks, Method Set, Mocking & DI, Бесконечные Ридеры, Декораторы и Generics", "Статическая проверка var _ io.Writer = (*Type)(nil), асимметрия Method Set для T и *T, MockDB для юнит-тестов, DI в Service, RandomLetterReader, ValidatorAll, Middleware Chain, запрет конвертации []Developer в []Worker, UpperWriter, DeepEqual, Interface Pollution, Sorter (Strategy), Generics против any и встраивание bytes.Buffer")
    ]
    ex_dict = {e["num"]: e for e in ch14_exercises}
    for start_n, end_n, title, desc in section_groups_ch14:
        content_parts.append(f\"\"\"
        <div class="section-separator">
            <div><h2>{title}</h2><div style="color: #94a3b8; font-size: 0.9rem; margin-top: 4px;">{desc}</div></div>
            <span class="tag">Упражнения {start_n}–{end_n}</span>
        </div>
        \"\"\")
        for n in range(start_n, end_n + 1):
            if n in ex_dict:
                content_parts.append(build_exercise_card(ex_dict[n]))
    content_parts.append(\"\"\"
    <section style="margin-top: 60px; padding: 32px; background: #0f172a; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 1.5rem; margin-bottom: 12px;">🎉 Поздравляем! Глава 14 полностью завершена!</h3>
        <p style="color: #94a3b8; max-width: 700px; margin: 0 auto 20px; line-height: 1.6;">
            Вы в совершенстве освоили интерфейсы в Go: модель iface/eface, обработку nil interface, полиморфизм потоков io, паттерны DI и статические проверки.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter13.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 13 (Структуры)</a>
            <a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 15: Ошибки (Errors) (Скоро) →</a>
        </div>
    </section>
    \"\"\")
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '14. Интерфейсы (77/77)') + '\\n' + sidebar_html + '\\n' + '\\n'.join(content_parts) + '\\n' + HTML_FOOTER
"""

old_main = "if __name__ == '__main__':"
code = code.replace(old_main, ch14_fn + "\n" + old_main)

# 5. Add to pages
old_pages = "        ('chapter13.html', build_chapter13_html),"
new_pages = old_pages + "\n        ('chapter14.html', build_chapter14_html),"
code = code.replace(old_pages, new_pages)

with open('builder/build_all.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated builder/build_all.py successfully!")
