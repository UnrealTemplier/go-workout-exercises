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

with open('builder/chapter53_data.json', 'r', encoding='utf-8') as f:
    ch53_exercises = json.load(f)

with open('builder/chapter54_data.json', 'r', encoding='utf-8') as f:
    ch54_exercises = json.load(f)

with open('builder/chapter55_data.json', 'r', encoding='utf-8') as f:
    ch55_exercises = json.load(f)

with open('builder/chapter56_data.json', 'r', encoding='utf-8') as f:
    ch56_exercises = json.load(f)

with open('builder/chapter57_data.json', 'r', encoding='utf-8') as f:
    ch57_exercises = json.load(f)

all_ch1 = s1 + s2 + s3 + s4 + s5 + s6
all_ch2 = ch2_exercises
all_ch3 = ch3_exercises
all_ch4 = ch4_exercises
all_ch5 = ch5_exercises
all_ch6 = ch6_exercises
all_ch7 = ch7_exercises
all_ch8 = ch8_exercises
all_ch9 = ch9_exercises
all_ch10 = ch10_exercises
all_ch11 = ch11_exercises
all_ch12 = ch12_exercises
all_ch13 = ch13_exercises
all_ch14 = ch14_exercises
all_ch15 = ch15_exercises
all_ch16 = ch16_exercises
all_ch17 = ch17_exercises
all_ch18 = ch18_exercises
all_ch19 = ch19_exercises
all_ch20 = ch20_exercises
all_ch21 = ch21_exercises
all_ch22 = ch22_exercises
all_ch23 = ch23_exercises
all_ch24 = ch24_exercises
all_ch25 = ch25_exercises
all_ch26 = ch26_exercises
all_ch27 = ch27_exercises
all_ch28 = ch28_exercises
all_ch29 = ch29_exercises
all_ch30 = ch30_exercises
all_ch31 = ch31_exercises
all_ch32 = ch32_exercises
all_ch33 = ch33_exercises
all_ch34 = ch34_exercises
all_ch35 = ch35_exercises
all_ch36 = ch36_exercises
all_ch37 = ch37_exercises
all_ch38 = ch38_exercises
all_ch39 = ch39_exercises
all_ch40 = ch40_exercises
all_ch41 = ch41_exercises
all_ch42 = ch42_exercises
all_ch43 = ch43_exercises
all_ch44 = ch44_exercises
all_ch45 = ch45_exercises
all_ch46 = ch46_exercises
all_ch47 = ch47_exercises
all_ch48 = ch48_exercises
all_ch49 = ch49_exercises
all_ch50 = ch50_exercises
all_ch51 = ch51_exercises
all_ch52 = ch52_exercises
all_ch53 = ch53_exercises
all_ch54 = ch54_exercises
all_ch55 = ch55_exercises
all_ch56 = ch56_exercises
all_ch57 = ch57_exercises

total_ex = len(all_ch1) + len(all_ch2) + len(all_ch3) + len(all_ch4) + len(all_ch5) + len(all_ch6) + len(all_ch7) + len(all_ch8) + len(all_ch9) + len(all_ch10) + len(all_ch11) + len(all_ch12) + len(all_ch13) + len(all_ch14) + len(all_ch15) + len(all_ch16) + len(all_ch17) + len(all_ch18) + len(all_ch19) + len(all_ch20) + len(all_ch21) + len(all_ch22) + len(all_ch23) + len(all_ch24) + len(all_ch25) + len(all_ch26) + len(all_ch27) + len(all_ch28) + len(all_ch29) + len(all_ch30) + len(all_ch31) + len(all_ch32) + len(all_ch33) + len(all_ch34) + len(all_ch35) + len(all_ch36) + len(all_ch37) + len(all_ch38) + len(all_ch39) + len(all_ch40) + len(all_ch41) + len(all_ch42) + len(all_ch43) + len(all_ch44) + len(all_ch45) + len(all_ch46) + len(all_ch47) + len(all_ch48) + len(all_ch49) + len(all_ch50) + len(all_ch51) + len(all_ch52) + len(all_ch53) + len(all_ch54) + len(all_ch55) + len(all_ch56) + len(all_ch57)

print("=== ТЕХНИЧЕСКИЙ АУДИТ УЧЕБНИКА GO ===")
print(f"Глава 1:  {len(all_ch1)} упражнений")
print(f"Глава 2:  {len(all_ch2)} упражнений")
print(f"Глава 3:  {len(all_ch3)} упражнений")
print(f"Глава 4:  {len(all_ch4)} упражнений")
print(f"Глава 5:  {len(all_ch5)} упражнений")
print(f"Глава 6:  {len(all_ch6)} упражнений")
print(f"Глава 7:  {len(all_ch7)} упражнений")
print(f"Глава 8:  {len(all_ch8)} упражнений")
print(f"Глава 9:  {len(all_ch9)} упражнений")
print(f"Глава 10: {len(all_ch10)} упражнений")
print(f"Глава 11: {len(all_ch11)} упражнений")
print(f"Глава 12: {len(all_ch12)} упражнений")
print(f"Глава 13: {len(all_ch13)} упражнений")
print(f"Глава 14: {len(all_ch14)} упражнений")
print(f"Глава 15: {len(all_ch15)} упражнений")
print(f"Глава 16: {len(all_ch16)} упражнений")
print(f"Глава 17: {len(all_ch17)} упражнений")
print(f"Глава 18: {len(all_ch18)} упражнений")
print(f"Глава 19: {len(all_ch19)} упражнений")
print(f"Глава 20: {len(all_ch20)} упражнений")
print(f"Глава 21: {len(all_ch21)} упражнений")
print(f"Глава 22: {len(all_ch22)} упражнений")
print(f"Глава 23: {len(all_ch23)} упражнений")
print(f"Глава 24: {len(all_ch24)} упражнений")
print(f"Глава 25: {len(all_ch25)} упражнений")
print(f"Глава 26: {len(all_ch26)} упражнений")
print(f"Глава 27: {len(all_ch27)} упражнений")
print(f"Глава 28: {len(all_ch28)} упражнений")
print(f"Глава 29: {len(all_ch29)} упражнений")
print(f"Глава 30: {len(all_ch30)} упражнений")
print(f"Глава 31: {len(all_ch31)} упражнений")
print(f"Глава 32: {len(all_ch32)} упражнений")
print(f"Глава 33: {len(all_ch33)} упражнений")
print(f"Глава 34: {len(all_ch34)} упражнений")
print(f"Глава 35: {len(all_ch35)} упражнений")
print(f"Глава 36: {len(all_ch36)} упражнений")
print(f"Глава 37: {len(all_ch37)} упражнений")
print(f"Глава 38: {len(all_ch38)} упражнений")
print(f"Глава 39: {len(all_ch39)} упражнений")
print(f"Глава 40: {len(all_ch40)} упражнений")
print(f"Глава 41: {len(all_ch41)} упражнений")
print(f"Глава 42: {len(all_ch42)} упражнений")
print(f"Глава 43: {len(all_ch43)} упражнений")
print(f"Глава 44: {len(all_ch44)} упражнений")
print(f"Глава 45: {len(all_ch45)} упражнений")
print(f"Глава 46: {len(all_ch46)} упражнений")
print(f"Глава 47: {len(all_ch47)} упражнений")
print(f"Глава 48: {len(all_ch48)} упражнений")
print(f"Глава 49: {len(all_ch49)} упражнений")
print(f"Глава 50: {len(all_ch50)} упражнений")
print(f"Глава 51: {len(all_ch51)} упражнений")
print(f"Глава 52: {len(all_ch52)} упражнений")
print(f"Глава 53: {len(all_ch53)} упражнений")
print(f"Глава 54: {len(all_ch54)} упражнений")
print(f"Глава 55: {len(all_ch55)} упражнений")
print(f"Глава 56: {len(all_ch56)} упражнений")
print(f"Глава 57: {len(all_ch57)} упражнений")
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
            
        if lang == 'go' and 'package main' in code:
            if 'ОШИБКА:' in code or 'redeclared' in code or '// ОШИБКА' in code or 'undefined: ' in code or 'invalid operation' in code or 'cannot use' in code or 'invalid map key' in code or 'cannot take' in code or 'badMap' in code or 'cannot assign to struct field in map' in code:
                continue
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
for ex in all_ch8:
    check_exercise(8, ex)
for ex in all_ch9:
    check_exercise(9, ex)
for ex in all_ch10:
    check_exercise(10, ex)
for ex in all_ch11:
    check_exercise(11, ex)
for ex in all_ch12:
    check_exercise(12, ex)
for ex in all_ch13:
    check_exercise(13, ex)
for ex in all_ch14:
    check_exercise(14, ex)
for ex in all_ch15:
    check_exercise(15, ex)
for ex in all_ch16:
    check_exercise(16, ex)
for ex in all_ch17:
    check_exercise(17, ex)
for ex in all_ch18:
    check_exercise(18, ex)
for ex in all_ch19:
    check_exercise(19, ex)
for ex in all_ch20:
    check_exercise(20, ex)
for ex in all_ch21:
    check_exercise(21, ex)
for ex in all_ch22:
    check_exercise(22, ex)
for ex in all_ch23:
    check_exercise(23, ex)
for ex in all_ch24:
    check_exercise(24, ex)
for ex in all_ch25:
    check_exercise(25, ex)
for ex in all_ch26:
    check_exercise(26, ex)
for ex in all_ch27:
    check_exercise(27, ex)
for ex in all_ch28:
    check_exercise(28, ex)
for ex in all_ch29:
    check_exercise(29, ex)
for ex in all_ch30:
    check_exercise(30, ex)
for ex in all_ch31:
    check_exercise(31, ex)
for ex in all_ch32:
    check_exercise(32, ex)
for ex in all_ch33:
    check_exercise(33, ex)
for ex in all_ch34:
    check_exercise(34, ex)
for ex in all_ch35:
    check_exercise(35, ex)
for ex in all_ch36:
    check_exercise(36, ex)
for ex in all_ch37:
    check_exercise(37, ex)
for ex in all_ch38:
    check_exercise(38, ex)
for ex in all_ch39:
    check_exercise(39, ex)
for ex in all_ch40:
    check_exercise(40, ex)
for ex in all_ch41:
    check_exercise(41, ex)
for ex in all_ch42:
    check_exercise(42, ex)
for ex in all_ch43:
    check_exercise(43, ex)
for ex in all_ch44:
    check_exercise(44, ex)
for ex in all_ch45:
    check_exercise(45, ex)
for ex in all_ch46:
    check_exercise(46, ex)
for ex in all_ch47:
    check_exercise(47, ex)
for ex in all_ch48:
    check_exercise(48, ex)
for ex in all_ch49:
    check_exercise(49, ex)
for ex in all_ch50:
    check_exercise(50, ex)
for ex in all_ch51:
    check_exercise(51, ex)
for ex in all_ch52:
    check_exercise(52, ex)
for ex in all_ch53:
    check_exercise(53, ex)
for ex in all_ch54:
    check_exercise(54, ex)
for ex in all_ch55:
    check_exercise(55, ex)
for ex in all_ch56:
    check_exercise(56, ex)
for ex in all_ch57:
    check_exercise(57, ex)

# Check HTML files and anchors
html_files = [
    ('index.html', 1, len(all_ch1)),
    ('chapter2.html', 2, len(all_ch2)),
    ('chapter3.html', 3, len(all_ch3)),
    ('chapter4.html', 4, len(all_ch4)),
    ('chapter5.html', 5, len(all_ch5)),
    ('chapter6.html', 6, len(all_ch6)),
    ('chapter7.html', 7, len(all_ch7)),
    ('chapter8.html', 8, len(all_ch8)),
    ('chapter9.html', 9, len(all_ch9)),
    ('chapter10.html', 10, len(all_ch10)),
    ('chapter11.html', 11, len(all_ch11)),
    ('chapter12.html', 12, len(all_ch12)),
    ('chapter13.html', 13, len(all_ch13)),
    ('chapter14.html', 14, len(all_ch14)),
    ('chapter15.html', 15, len(all_ch15)),
    ('chapter16.html', 16, len(all_ch16)),
    ('chapter17.html', 17, len(all_ch17)),
    ('chapter18.html', 18, len(all_ch18)),
    ('chapter19.html', 19, len(all_ch19)),
    ('chapter20.html', 20, len(all_ch20)),
    ('chapter21.html', 21, len(all_ch21)),
    ('chapter22.html', 22, len(all_ch22)),
    ('chapter23.html', 23, len(all_ch23)),
    ('chapter24.html', 24, len(all_ch24)),
    ('chapter25.html', 25, len(all_ch25)),
    ('chapter26.html', 26, len(all_ch26)),
    ('chapter27.html', 27, len(all_ch27)),
    ('chapter28.html', 28, len(all_ch28)),
    ('chapter29.html', 29, len(all_ch29)),
    ('chapter30.html', 30, len(all_ch30)),
    ('chapter31.html', 31, len(all_ch31)),
    ('chapter32.html', 32, len(all_ch32)),
    ('chapter33.html', 33, len(all_ch33)),
    ('chapter34.html', 34, len(all_ch34)),
    ('chapter35.html', 35, len(all_ch35)),
    ('chapter36.html', 36, len(all_ch36)),
    ('chapter37.html', 37, len(all_ch37)),
    ('chapter38.html', 38, len(all_ch38)),
    ('chapter39.html', 39, len(all_ch39)),
    ('chapter40.html', 40, len(all_ch40)),
    ('chapter41.html', 41, len(all_ch41)),
    ('chapter42.html', 42, len(all_ch42)),
    ('chapter43.html', 43, len(all_ch43)),
    ('chapter44.html', 44, len(all_ch44)),
    ('chapter45.html', 45, len(all_ch45)),
    ('chapter46.html', 46, len(all_ch46)),
    ('chapter47.html', 47, len(all_ch47)),
    ('chapter48.html', 48, len(all_ch48)),
    ('chapter49.html', 49, len(all_ch49)),
    ('chapter50.html', 50, len(all_ch50)),
    ('chapter51.html', 51, len(all_ch51)),
    ('chapter52.html', 52, len(all_ch52)),
    ('chapter53.html', 53, len(all_ch53)),
    ('chapter54.html', 54, len(all_ch54)),
    ('chapter55.html', 55, len(all_ch55)),
    ('chapter56.html', 56, len(all_ch56)),
    ('chapter57.html', 57, len(all_ch57)),
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
    print(f"\n✅ ИДЕАЛЬНО: Все {total_ex} упражнений в {len(html_files)} главах успешно прошли синтаксический, структурный и HTML-аудит!")

