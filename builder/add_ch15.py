import re

with open('builder/build_all.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Load ch15_exercises
if 'chapter15_data.json' not in code:
    code = code.replace(
        "with open('builder/chapter14_data.json', 'r', encoding='utf-8') as f:\n    ch14_exercises = json.load(f)",
        "with open('builder/chapter14_data.json', 'r', encoding='utf-8') as f:\n    ch14_exercises = json.load(f)\nwith open('builder/chapter15_data.json', 'r', encoding='utf-8') as f:\n    ch15_exercises = json.load(f)"
    )

# 2. Add chapter 15 to known_pages in build_sidebar
if "15: ('chapter15.html', '127/127')" not in code:
    code = code.replace(
        "14: ('chapter14.html', '77/77'),",
        "14: ('chapter14.html', '77/77'),\n            15: ('chapter15.html', '127/127'),"
    )

# 3. Update chapter 14 next link
ch14_old_link = '<a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 15: Ошибки (Errors) (Скоро) →</a>'
ch14_new_link = '<a href="chapter15.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00ADD8; color: #0f172a; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 15 (ООП в Go: 127 упр.) →</a>'
code = code.replace(ch14_old_link, ch14_new_link)

# 4. Add build_chapter15_html function before if __name__ == '__main__':
ch15_func = '''
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
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-val">127 из 127</span><span class="stat-lbl">Упражнений решено</span></div>
            <div class="stat-item"><span class="stat-val">Composition</span><span class="stat-lbl">Embedding & Promotion</span></div>
            <div class="stat-item"><span class="stat-val">Method Sets</span><span class="stat-lbl">Value vs Pointer Receivers</span></div>
            <div class="stat-item"><span class="stat-val">Clean Arch</span><span class="stat-lbl">GoF Patterns & DIP</span></div>
        </div>
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
            <a href="chapter14.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 14 (Интерфейсы)</a>
            <a href="javascript:void(0)" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 173, 216, 0.2); color: #38bdf8; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid rgba(0, 173, 216, 0.4);">Глава 16: Дженерики (Generics) (Скоро) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', '15. ООП в Go (127/127)') + '\n' + sidebar_html + '\n' + '\n'.join(content_parts) + '\n' + HTML_FOOTER
'''

if 'build_chapter15_html' not in code:
    code = code.replace(
        "if __name__ == '__main__':",
        ch15_func + "\nif __name__ == '__main__':"
    )

# 5. Add chapter15.html to pages list
if "('chapter15.html', build_chapter15_html)" not in code:
    code = code.replace(
        "('chapter14.html', build_chapter14_html),",
        "('chapter14.html', build_chapter14_html),\n        ('chapter15.html', build_chapter15_html),"
    )

with open('builder/build_all.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated builder/build_all.py successfully!")
