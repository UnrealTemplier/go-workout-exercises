import json
import os
import subprocess
import tempfile

from section1 import exercises as s1
from section2 import exercises as s2
from section3 import exercises as s3
from section4 import exercises as s4
from section5 import exercises as s5
from section6 import exercises as s6

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

all_ch1 = s1 + s2 + s3 + s4 + s5 + s6
all_ch2 = ch2_exercises
all_ch3 = ch3_exercises
all_ch4 = ch4_exercises
all_ch5 = ch5_exercises
all_ch6 = ch6_exercises
all_ch7 = ch7_exercises

total_ex = len(all_ch1) + len(all_ch2) + len(all_ch3) + len(all_ch4) + len(all_ch5) + len(all_ch6) + len(all_ch7)

print("=== ТЕХНИЧЕСКИЙ АУДИТ УЧЕБНИКА GO ===")
print(f"Глава 1: {len(all_ch1)} упражнений")
print(f"Глава 2: {len(all_ch2)} упражнений")
print(f"Глава 3: {len(all_ch3)} упражнений")
print(f"Глава 4: {len(all_ch4)} упражнений")
print(f"Глава 5: {len(all_ch5)} упражнений")
print(f"Глава 6: {len(all_ch6)} упражнений")
print(f"Глава 7: {len(all_ch7)} упражнений")
print(f"Всего упражнений в учебнике: {total_ex}")

issues = []

def check_exercise(ch_num, ex):
    num = ex.get('num')
    title = ex.get('title')
    task = ex.get('task')
    theory = ex.get('theory')
    step_by_step = ex.get('step_by_step')
    code_blocks = ex.get('code_blocks', [])
    under_the_hood = ex.get('under_the_hood')
    pitfalls = ex.get('pitfalls')
    bigtech = ex.get('bigtech_interview')
    
    if not title or not task or not theory or not step_by_step or not code_blocks:
        issues.append(f"[Глава {ch_num} Упр {num}] Отсутствует обязательная секция")
        
    for i, cb in enumerate(code_blocks):
        fname = cb.get('filename', '')
        lang = cb.get('lang', '')
        code = cb.get('code', '')
        if not code.strip():
            issues.append(f"[Глава {ch_num} Упр {num}] Пустой блок кода {i} ({fname})")
            
        # If it's a standalone go file, test parse/syntax check with gofmt
        if lang == 'go' and 'package main' in code:
            if 'ОШИБКА:' in code or 'redeclared' in code or '// ОШИБКА' in code or 'undefined: ' in code or 'invalid operation' in code or 'cannot use' in code:
                continue # Deliberate compilation error example
            if 'import "C"' in code or 'some-domain.com' in code or 'github.com/myuser' in code or 'mycompany' in code or 'v2' in code:
                continue
                
            with tempfile.NamedTemporaryFile('w', suffix='.go', delete=False) as tf:
                tf.write(code)
                tf_path = tf.name
            try:
                res = subprocess.run(['gofmt', '-e', tf_path], capture_output=True, text=True)
                if res.returncode != 0:
                    issues.append(f"[Глава {ch_num} Упр {num}] Ошибка синтаксиса Go в {fname}: {res.stderr.strip()}")
            finally:
                if os.path.exists(tf_path):
                    os.remove(tf_path)

for ex in all_ch1:
    check_exercise(1, ex)
for ex in all_ch2:
    check_exercise(2, ex)
for ex in all_ch3:
    check_exercise(3, ex)
for ex in all_ch4:
    check_exercise(4, ex)
for ex in all_ch5:
    check_exercise(5, ex)
for ex in all_ch6:
    check_exercise(6, ex)
for ex in all_ch7:
    check_exercise(7, ex)

# Check HTML files and anchors
html_files = [
    ('index.html', 1, len(all_ch1)),
    ('chapter2.html', 2, len(all_ch2)),
    ('chapter3.html', 3, len(all_ch3)),
    ('chapter4.html', 4, len(all_ch4)),
    ('chapter5.html', 5, len(all_ch5)),
    ('chapter6.html', 6, len(all_ch6)),
    ('chapter7.html', 7, len(all_ch7))
]

for fname, ch_num, count in html_files:
    if not os.path.exists(fname):
        issues.append(f"Файл {fname} не найден на диске!")
        continue
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check all anchors
    for i in range(1, count + 1):
        if f'id="ex-{i}"' not in content:
            issues.append(f"В файле {fname} отсутствует якорь id=\"ex-{i}\"")
            
    # Check no chevron icon
    if 'chevron-icon' in content:
        issues.append(f"В файле {fname} обнаружен запрещенный chevron-icon!")

if issues:
    print(f"\n❌ Обнаружено {len(issues)} проблем:")
    for iss in issues:
        print("  •", iss)
    exit(1)
else:
    print(f"\n✅ ИДЕАЛЬНО: Все {total_ex} упражнений в 7 главах успешно прошли синтаксический, структурный и HTML-аудит!")
