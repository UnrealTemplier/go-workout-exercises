import json
import os
import subprocess
import tempfile
import sys

from section1 import exercises as s1
from section2 import exercises as s2
from section3 import exercises as s3
from section4 import exercises as s4
from section5 import exercises as s5
from section6 import exercises as s6

with open('builder/chapter2_data.json', 'r', encoding='utf-8') as f:
    ch2_exercises = json.load(f)

all_ch1 = s1 + s2 + s3 + s4 + s5 + s6
all_ch2 = ch2_exercises

print(f"Total Chapter 1 exercises: {len(all_ch1)}")
print(f"Total Chapter 2 exercises: {len(all_ch2)}")

# Let's verify each exercise structure and check code blocks
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
        issues.append(f"[Ch {ch_num} Ex {num}] Missing core required section")
        
    for i, cb in enumerate(code_blocks):
        fname = cb.get('filename', '')
        lang = cb.get('lang', '')
        code = cb.get('code', '')
        if not code.strip():
            issues.append(f"[Ch {ch_num} Ex {num}] Empty code block {i} ({fname})")
            
        # If it's a standalone go file (contains package main and func main), let's test parse/compile it
        if lang == 'go' and 'package main' in code and 'func main()' in code:
            # Check if it has unresolved pseudo-code or deliberate compilation errors
            if 'ОШИБКА:' in code or 'cannot find module' in code or 'redeclared' in code or '// ОШИБКА' in code:
                continue # Deliberate demonstration of error
            if 'import "C"' in code:
                continue
            if 'some-domain.com' in code or 'github.com/myuser' in code or 'mycompany' in code or 'v2' in code:
                continue # Example module path requiring external replace or network
                
            # Write to a temp file and run `go vet` or `gofmt` to check syntax
            with tempfile.NamedTemporaryFile('w', suffix='.go', delete=False) as tf:
                tf.write(code)
                tf_path = tf.name
            try:
                res = subprocess.run(['gofmt', '-e', tf_path], capture_output=True, text=True)
                if res.returncode != 0:
                    issues.append(f"[Ch {ch_num} Ex {num}] Go syntax error in {fname}: {res.stderr.strip()}")
            finally:
                if os.path.exists(tf_path):
                    os.remove(tf_path)

print("\n--- Auditing Chapter 1 ---")
for ex in all_ch1:
    check_exercise(1, ex)

print("\n--- Auditing Chapter 2 ---")
for ex in all_ch2:
    check_exercise(2, ex)

if issues:
    print(f"\nFound {len(issues)} issues:")
    for iss in issues:
        print(" - ", iss)
else:
    print("\n✅ All exercises passed automated syntax and structural validation!")
