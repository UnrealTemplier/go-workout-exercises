import os
import glob
import re

def get_all_chapters():
    files = glob.glob('/home/ut/work/go-workout/*.md')
    chapters = []
    for f in files:
        base = os.path.basename(f)
        name_without_ext = os.path.splitext(base)[0]
        m = re.match(r'^(\d+)\.\s*(.*)$', name_without_ext)
        if not m:
            continue
        num = int(m.group(1))
        title = m.group(2)
            
        chapters.append({
            'num': num,
            'title': title,
            'filename': base,
            'is_current': (num == 1),
            'status': 'Готово (91/91)' if num == 1 else 'В разработке'
        })
    chapters.sort(key=lambda c: c['num'])
    return chapters

if __name__ == '__main__':
    ch = get_all_chapters()
    print(f"Loaded {len(ch)} chapters.")
    print("First chapter:", ch[0])
    print("Last chapter:", ch[-1])
