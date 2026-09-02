import json

with open('builder/chapter9_data.json', 'r', encoding='utf-8') as f:
    exercises = json.load(f)

for ex in exercises:
    for cb in ex.get('code_blocks', []):
        if cb.get('lang') == 'go':
            lines = cb['code'].split('\n')
            fixed_lines = []
            in_unclosed_str = False
            curr = ""
            for line in lines:
                unescaped_quotes = 0
                skip = False
                for idx, ch in enumerate(line):
                    if skip:
                        skip = False
                        continue
                    if ch == '\\':
                        skip = True
                        continue
                    if ch == '"':
                        unescaped_quotes += 1
                
                if in_unclosed_str:
                    curr += "\\n" + line
                    if unescaped_quotes % 2 != 0:
                        fixed_lines.append(curr)
                        in_unclosed_str = False
                        curr = ""
                else:
                    if unescaped_quotes % 2 != 0:
                        in_unclosed_str = True
                        curr = line
                    else:
                        fixed_lines.append(line)
            if curr:
                fixed_lines.append(curr)
            cb['code'] = '\n'.join(fixed_lines)

with open('builder/chapter9_data.json', 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print('Fixed builder/chapter9_data.json')
