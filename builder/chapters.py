import os
import glob
import re

def get_all_chapters():
    files = glob.glob('/home/ut/work/go-workout/*.md')
    def sort_key(f):
        base = os.path.basename(f)
        m = re.match(r'^(\d+)', base)
        return int(m.group(1)) if m else 9999

    files.sort(key=sort_key)
    
    chapters = []
    for f in files:
        base = os.path.basename(f)
        name_without_ext = os.path.splitext(base)[0]
        m = re.match(r'^(\d+)\.\s*(.*)$', name_without_ext)
        if m:
            num = int(m.group(1))
            title = m.group(2)
        else:
            num = 999
            title = name_without_ext
            
        chapters.append({
            'num': num,
            'title': title,
            'filename': base,
            'is_current': (num == 1),
            'status': 'Готово (91/91)' if num == 1 else 'В разработке'
        })
    return chapters

if __name__ == '__main__':
    ch = get_all_chapters()
    print(f"Loaded {len(ch)} chapters.")
    print("First chapter:", ch[0])
    print("Last chapter:", ch[-1])
