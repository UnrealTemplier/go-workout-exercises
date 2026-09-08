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
with open('builder/chapter58_data.json', 'r', encoding='utf-8') as f:
    ch58_exercises = json.load(f)
with open('builder/chapter59_data.json', 'r', encoding='utf-8') as f:
    ch59_exercises = json.load(f)
with open('builder/chapter60_data.json', 'r', encoding='utf-8') as f:
    ch60_exercises = json.load(f)
with open('builder/chapter61_data.json', 'r', encoding='utf-8') as f:
    ch61_exercises = json.load(f)
with open('builder/chapter62_data.json', 'r', encoding='utf-8') as f:
    ch62_exercises = json.load(f)
with open('builder/chapter63_data.json', 'r', encoding='utf-8') as f:
    ch63_exercises = json.load(f)
with open('builder/chapter64_data.json', 'r', encoding='utf-8') as f:
    ch64_exercises = json.load(f)
with open('builder/chapter65_data.json', 'r', encoding='utf-8') as f:
    ch65_exercises = json.load(f)
with open('builder/chapter66_data.json', 'r', encoding='utf-8') as f:
    ch66_exercises = json.load(f)
with open('builder/chapter67_data.json', 'r', encoding='utf-8') as f:
    ch67_exercises = json.load(f)
with open('builder/chapter68_data.json', 'r', encoding='utf-8') as f:
    ch68_exercises = json.load(f)
with open('builder/chapter69_data.json', 'r', encoding='utf-8') as f:
    ch69_exercises = json.load(f)
with open('builder/chapter70_data.json', 'r', encoding='utf-8') as f:
    ch70_exercises = json.load(f)
with open('builder/chapter71_data.json', 'r', encoding='utf-8') as f:
    ch71_exercises = json.load(f)
with open('builder/chapter72_data.json', 'r', encoding='utf-8') as f:
    ch72_exercises = json.load(f)
with open('builder/chapter73_data.json', 'r', encoding='utf-8') as f:
    ch73_exercises = json.load(f)
with open('builder/chapter74_data.json', 'r', encoding='utf-8') as f:
    ch74_exercises = json.load(f)
with open('builder/chapter75_data.json', 'r', encoding='utf-8') as f:
    ch75_exercises = json.load(f)
with open('builder/chapter76_data.json', 'r', encoding='utf-8') as f:
    ch76_exercises = json.load(f)
with open('builder/chapter77_data.json', 'r', encoding='utf-8') as f:
    ch77_exercises = json.load(f)
with open('builder/chapter78_data.json', 'r', encoding='utf-8') as f:
    ch78_exercises = json.load(f)
with open('builder/chapter79_data.json', 'r', encoding='utf-8') as f:
    ch79_exercises = json.load(f)
with open('builder/chapter80_data.json', 'r', encoding='utf-8') as f:
    ch80_exercises = json.load(f)
with open('builder/chapter81_data.json', 'r', encoding='utf-8') as f:
    ch81_exercises = json.load(f)
with open('builder/chapter82_data.json', 'r', encoding='utf-8') as f:
    ch82_exercises = json.load(f)
with open('builder/chapter83_data.json', 'r', encoding='utf-8') as f:
    ch83_exercises = json.load(f)
with open('builder/chapter84_data.json', 'r', encoding='utf-8') as f:
    ch84_exercises = json.load(f)
with open('builder/chapter85_data.json', 'r', encoding='utf-8') as f:
    ch85_exercises = json.load(f)
with open('builder/chapter86_data.json', 'r', encoding='utf-8') as f:
    ch86_exercises = json.load(f)
with open('builder/chapter87_data.json', 'r', encoding='utf-8') as f:
    ch87_exercises = json.load(f)
with open('builder/chapter88_data.json', 'r', encoding='utf-8') as f:
    ch88_exercises = json.load(f)
with open('builder/chapter89_data.json', 'r', encoding='utf-8') as f:
    ch89_exercises = json.load(f)
with open('builder/chapter90_data.json', 'r', encoding='utf-8') as f:
    ch90_exercises = json.load(f)
with open('builder/chapter91_data.json', 'r', encoding='utf-8') as f:
    ch91_exercises = json.load(f)
with open('builder/chapter92_data.json', 'r', encoding='utf-8') as f:
    ch92_exercises = json.load(f)
with open('builder/chapter93_data.json', 'r', encoding='utf-8') as f:
    ch93_exercises = json.load(f)
with open('builder/chapter94_data.json', 'r', encoding='utf-8') as f:
    ch94_exercises = json.load(f)
with open('builder/chapter95_data.json', 'r', encoding='utf-8') as f:
    ch95_exercises = json.load(f)
with open('builder/chapter96_data.json', 'r', encoding='utf-8') as f:
    ch96_exercises = json.load(f)
with open('builder/chapter97_data.json', 'r', encoding='utf-8') as f:
    ch97_exercises = json.load(f)
with open('builder/chapter98_data.json', 'r', encoding='utf-8') as f:
    ch98_exercises = json.load(f)
with open('builder/chapter99_data.json', 'r', encoding='utf-8') as f:
    ch99_exercises = json.load(f)

def format_text(txt):
    if not txt:
        return ""
    if isinstance(txt, list):
        txt = "\n".join(txt)
    lines = txt.strip().split('\n')
    out_lines = []
    in_list = False
    in_code = False
    code_lang = ""
    code_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Multi-line code block handling (```lang ... ```)
        if stripped.startswith('```'):
            if in_code:
                in_code = False
                code_text = '\n'.join(code_lines)
                escaped_code = html.escape(code_text)
                lang_cls = f"language-{code_lang}" if code_lang else "language-none"
                out_lines.append(f'<div class="code-container" style="margin: 10px 0;"><pre class="{lang_cls}"><code class="{lang_cls}">{escaped_code}</code></pre></div>')
                code_lines = []
                code_lang = ""
            else:
                if in_list:
                    out_lines.append('</ul>')
                    in_list = False
                in_code = True
                code_lang = stripped[3:].strip()
                code_lines = []
            continue
            
        if in_code:
            code_lines.append(line)
            continue
            
        if not stripped:
            if in_list:
                out_lines.append('</ul>')
                in_list = False
            out_lines.append('<div style="height: 8px;"></div>')
            continue
            
        # Headings
        if stripped.startswith('### '):
            if in_list:
                out_lines.append('</ul>')
                in_list = False
            content = html.escape(stripped[4:])
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
            out_lines.append(f'<h5 style="color: #38bdf8; font-size: 1rem; margin: 14px 0 6px 0; font-weight: 600;">{content}</h5>')
            continue
            
        if stripped.startswith('#### '):
            if in_list:
                out_lines.append('</ul>')
                in_list = False
            content = html.escape(stripped[5:])
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
            out_lines.append(f'<h6 style="color: #94a3b8; font-size: 0.95rem; margin: 10px 0 4px 0; font-weight: 600;">{content}</h6>')
            continue

        # Bullet list
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                out_lines.append('<ul style="margin: 8px 0 8px 20px;">')
                in_list = True
            content = html.escape(stripped[2:])
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
            content = html.escape(m_num.group(2))
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
            out_lines.append(f'<div style="margin: 6px 0;"><span style="color: #38bdf8; font-weight: 700;">{num_idx}.</span> {content}</div>')
            continue
            
        if in_list:
            out_lines.append('</ul>')
            in_list = False
            
        content = html.escape(stripped)
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 173, 216, 0.12); color: #38bdf8; padding: 2px 5px; border-radius: 4px; font-size: 0.88em;">\1</code>', content)
        out_lines.append(f'<p style="margin-bottom: 6px;">{content}</p>')
        
    if in_code:
        code_text = '\n'.join(code_lines)
        escaped_code = html.escape(code_text)
        lang_cls = f"language-{code_lang}" if code_lang else "language-none"
        out_lines.append(f'<div class="code-container" style="margin: 10px 0;"><pre class="{lang_cls}"><code class="{lang_cls}">{escaped_code}</code></pre></div>')
        
    if in_list:
        out_lines.append('</ul>')
        
    return '\n'.join(out_lines)

def build_sidebar(chapters, active_chapter_num, current_exercises):
    sb = []
    sb.append('<aside class="sidebar">')
    sb.append('  <div class="sidebar-header">')
    sb.append('    <a href="index.html" class="logo-badge" title="Главная страница и треки">')
    sb.append('      <span class="go-logo-icon">GO</span>')
    sb.append('      <span>Backend Workout</span>')
    sb.append('    </a>')
    sb.append('    <div class="sidebar-search">')
    sb.append('      <span class="search-icon">🔍</span>')
    sb.append('      <input type="text" id="search-input" placeholder="Поиск упражнений и тем..." autocomplete="off">')
    sb.append('    </div>')
    sb.append('  </div>')
    sb.append('  <nav class="sidebar-nav">')
    if active_chapter_num == 0 or active_chapter_num is None:
        sb.append('    <a href="index.html" class="chapter-link active portal-nav-link" style="background: rgba(56, 189, 248, 0.15); border: 1px solid #38bdf8; margin-bottom: 12px; border-radius: 8px;" title="Главная страница курса и образовательные треки">')
        sb.append('      <span style="color: #38bdf8; font-weight: 700;">🏠 Главная / Треки</span>')
        sb.append('      <span class="status-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-weight: 700;">100 тем</span>')
        sb.append('    </a>')
    else:
        sb.append('    <a href="index.html" class="chapter-link portal-nav-link" style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); margin-bottom: 12px; border-radius: 8px;" title="Главная страница курса и образовательные треки">')
        sb.append('      <span style="color: #38bdf8; font-weight: 700;">🏠 Главная / Треки</span>')
        sb.append('      <span class="status-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-weight: 700;">100 тем</span>')
        sb.append('    </a>')
    sb.append('    <div class="nav-group-title">Оглавление курса (100 модулей)</div>')
    
    for ch in chapters:
        num = ch['num']
        title = ch['title']
        
        status_map = {
            1: ('chapter1.html', '91/91'),
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
            53: ('chapter53.html', f'{len(ch53_exercises)}/{len(ch53_exercises)}'),
            54: ('chapter54.html', f'{len(ch54_exercises)}/{len(ch54_exercises)}'),
            55: ('chapter55.html', f'{len(ch55_exercises)}/{len(ch55_exercises)}'),
            56: ('chapter56.html', f'{len(ch56_exercises)}/{len(ch56_exercises)}'),
            57: ('chapter57.html', f'{len(ch57_exercises)}/{len(ch57_exercises)}'),
            58: ('chapter58.html', f'{len(ch58_exercises)}/{len(ch58_exercises)}'),
            59: ('chapter59.html', f'{len(ch59_exercises)}/{len(ch59_exercises)}'),
            60: ('chapter60.html', f'{len(ch60_exercises)}/{len(ch60_exercises)}'),
            61: ('chapter61.html', f'{len(ch61_exercises)}/{len(ch61_exercises)}'),
            62: ('chapter62.html', f'{len(ch62_exercises)}/{len(ch62_exercises)}'),
            63: ('chapter63.html', f'{len(ch63_exercises)}/{len(ch63_exercises)}'),
            64: ('chapter64.html', f'{len(ch64_exercises)}/{len(ch64_exercises)}'),
            65: ('chapter65.html', f'{len(ch65_exercises)}/{len(ch65_exercises)}'),
            66: ('chapter66.html', f'{len(ch66_exercises)}/{len(ch66_exercises)}'),
            67: ('chapter67.html', f'{len(ch67_exercises)}/{len(ch67_exercises)}'),
            68: ('chapter68.html', f'{len(ch68_exercises)}/{len(ch68_exercises)}'),
            69: ('chapter69.html', f'{len(ch69_exercises)}/{len(ch69_exercises)}'),
            70: ('chapter70.html', f'{len(ch70_exercises)}/{len(ch70_exercises)}'),
            71: ('chapter71.html', f'{len(ch71_exercises)}/{len(ch71_exercises)}'),
            72: ('chapter72.html', f'{len(ch72_exercises)}/{len(ch72_exercises)}'),
            73: ('chapter73.html', f'{len(ch73_exercises)}/{len(ch73_exercises)}'),
            74: ('chapter74.html', f'{len(ch74_exercises)}/{len(ch74_exercises)}'),
            75: ('chapter75.html', f'{len(ch75_exercises)}/{len(ch75_exercises)}'),
            76: ('chapter76.html', f'{len(ch76_exercises)}/{len(ch76_exercises)}'),
            77: ('chapter77.html', f'{len(ch77_exercises)}/{len(ch77_exercises)}'),
            78: ('chapter78.html', f'{len(ch78_exercises)}/{len(ch78_exercises)}'),
            79: ('chapter79.html', f'{len(ch79_exercises)}/{len(ch79_exercises)}'),
            80: ('chapter80.html', f'{len(ch80_exercises)}/{len(ch80_exercises)}'),
            81: ('chapter81.html', f'{len(ch81_exercises)}/{len(ch81_exercises)}'),
            82: ('chapter82.html', f'{len(ch82_exercises)}/{len(ch82_exercises)}'),
            83: ('chapter83.html', f'{len(ch83_exercises)}/{len(ch83_exercises)}'),
            84: ('chapter84.html', f'{len(ch84_exercises)}/{len(ch84_exercises)}'),
            85: ('chapter85.html', f'{len(ch85_exercises)}/{len(ch85_exercises)}'),
            86: ('chapter86.html', f'{len(ch86_exercises)}/{len(ch86_exercises)}'),
            87: ('chapter87.html', f'{len(ch87_exercises)}/{len(ch87_exercises)}'),
            88: ('chapter88.html', f'{len(ch88_exercises)}/{len(ch88_exercises)}'),
            89: ('chapter89.html', f'{len(ch89_exercises)}/{len(ch89_exercises)}'),
            90: ('chapter90.html', f'{len(ch90_exercises)}/{len(ch90_exercises)}'),
            91: ('chapter91.html', f'{len(ch91_exercises)}/{len(ch91_exercises)}'),
            92: ('chapter92.html', f'{len(ch92_exercises)}/{len(ch92_exercises)}'),
            93: ('chapter93.html', f'{len(ch93_exercises)}/{len(ch93_exercises)}'),
            94: ('chapter94.html', f'{len(ch94_exercises)}/{len(ch94_exercises)}'),
            95: ('chapter95.html', f'{len(ch95_exercises)}/{len(ch95_exercises)}'),
            96: ('chapter96.html', f'{len(ch96_exercises)}/{len(ch96_exercises)}'),
            97: ('chapter97.html', f'{len(ch97_exercises)}/{len(ch97_exercises)}'),
            98: ('chapter98.html', f'{len(ch98_exercises)}/{len(ch98_exercises)}'),
            99: ('chapter99.html', f'{len(ch99_exercises)}/{len(ch99_exercises)}'),
        }
        
        if num in status_map:
            href, badge = status_map[num]
            if active_chapter_num == num:
                sb.append('    <a href="javascript:void(0)" class="chapter-link active" id="active-chapter-toggle" title="Нажмите, чтобы свернуть/развернуть список упражнений">')
                sb.append(f'      <span><strong>{num}. {html.escape(title)}</strong></span>')
                sb.append(f'      <span class="status-badge done">{badge}</span>')
                sb.append('    </a>')
                sb.append('    <div class="sub-exercises-list" id="active-sub-exercises">')
                for ex in current_exercises:
                    t_esc = html.escape(ex["title"])
                    sb.append(f'      <a href="#ex-{ex["num"]}" class="sub-exercise-link" title="Упр {ex["num"]}: {t_esc}">{ex["num"]}. {t_esc}</a>')
                sb.append('    </div>')
            else:
                sb.append(f'    <a href="{href}" class="chapter-link">')
                sb.append(f'      <span>{num}. {html.escape(title)}</span>')
                sb.append(f'      <span class="status-badge done">{badge}</span>')
                sb.append('    </a>')
        else:
            sb.append('    <a href="javascript:void(0)" class="chapter-link" style="opacity: 0.65;" title="Глава в разработке">')
            sb.append(f'      <span>{num}. {html.escape(title)}</span>')
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
    ec.append(f'    <div style="flex: 1;"><h3 class="exercise-title">{html.escape(ex["title"])}</h3></div>')
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
            <a href="chapter1.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 01 Пакеты и модули</a>
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
            <a href="chapter53.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 53 Системные вызовы и взаимодействие с ОС →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'52. Интеграция с C-кодом через CGO ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter53_html(chapters):
    active_chapter_num = 53
    current_exercises = ch53_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 53</div>
      <h1 class="hero-title">Системные вызовы и взаимодействие с ОС</h1>
      <p class="hero-desc">
        Исчерпывающее практическое и архитектурное руководство по прямому взаимодействию Go с ядром операционной системы через системные вызовы. Механика перехода Ring 3 → Ring 0: таблицы прерываний, инструкции SYSCALL/SYSENTER и соглашения о вызовах ABI. Работа со стандартным пакетом syscall и расширением golang.org/x/sys/unix: syscall.Syscall, RawSyscall и оптимизация накладных расходов. Файловые дескрипторы и процессная модель: открытые файлы, каналы pipe, управление процессами через fork/exec, clone, wait4 и системные лимиты rlimit. Виртуальная память ядра: отображение файлов и анонимных страниц через mmap, управление защитой памяти с mprotect, синхронизация с диском через msync и подсказки кэширования madvise. Высокопроизводительный асинхронный ввод-вывод: мультиплексирование через epoll и kqueue, устройство внутреннего Netpoller рантайма Go, режимы Level-Triggered и Edge-Triggered (EPOLLET), неблокирующий I/O и обработка EAGAIN. Расширенные механизмы ядра Linux: мониторинг файловой системы inotify, прецизионные таймеры timerfd, обработка сигналов через signalfd, разделяемая память POSIX SHM и высокопроизводительные сетевые серверы без горутин.
      </p>
    </section>
    """)
    
    # Sections (75 exercises)
    sections = [
        (1, 18, 'Раздел 1: Базовые системные вызовы, дескрипторы файлов и процессная модель (Упр. 1–18)'),
        (19, 37, 'Раздел 2: Память mmap, защита mprotect и основы сетевого ввода-вывода (Упр. 19–37)'),
        (38, 56, 'Раздел 3: Асинхронный I/O, архитектура epoll, kqueue и Go Netpoller (Упр. 38–56)'),
        (57, 75, 'Раздел 4: Расширенные механизмы ядра: inotify, timerfd, signalfd и zero-copy (Упр. 57–75)')
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
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 53!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили системное программирование в Go: от низкоуровневых интерфейсов ядра, файловых дескрипторов и mmap до архитектуры epoll, signalfd, timerfd и построения сверхбыстрых сетевых движков на базе неблокирующего I/O.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter52.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 52 Интеграция с C-кодом через CGO</a>
            <a href="chapter54.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 54 Продвинутая рефлексия (reflect) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'53. Системные вызовы и взаимодействие с ОС ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter54_html(chapters):
    active_chapter_num = 54
    current_exercises = ch54_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 54</div>
      <h1 class="hero-title">Продвинутая рефлексия (reflect)</h1>
      <p class="hero-desc">
        Исчерпывающее практическое и инженерное руководство по глубокому метапрограммированию и рантайм-инспекции типов в Go с помощью пакета reflect. Три фундаментальных закона рефлексии: переход от interface к объектам рефлексии, восстановление статических типов через Interface() и правила модификации данных (адресуемость CanAddr и CanSet). Механика типов и значений: детальное исследование reflect.Type и reflect.Value, различие между статическим Type и базовым Kind, разыменование указателей через Elem() и безопасная обработка nil. Инспекция и манипуляция структурами: чтение и валидация структурных тегов reflect.StructTag, динамический поиск полей FieldByName и FieldByIndex, обработка анонимных встраиваемых полей (embedding) и затенение идентификаторов. Динамическое создание структур данных на лету: инстанцирование слайсов (MakeSlice), ассоциативных массивов (MakeMap), каналов (MakeChan) и структур (StructOf). Создание функций в рантайме через reflect.MakeFunc: динамические перехватчики, логирующие прокси, мокирование интерфейсов и событийные шины (EventBus). Продвинутая конкурентность с reflect.Select для мультиплексирования динамических наборов каналов. Анализ производительности: аллокации в куче, escape analysis при передаче в any, издержки reflect.Call и reflectcall, а также безопасная интеграция с unsafe.Pointer и высокоскоростное кэширование метаданных в HighLoad-системах.
      </p>
    </section>
    """)
    
    # Sections (114 exercises)
    sections = [
        (1, 28, 'Раздел 1: Законы рефлексии, основы reflect.Type, reflect.Value, Kind и адресуемость (Упр. 1–28)'),
        (29, 56, 'Раздел 2: Динамический вызов методов, парсинг структурных тегов и манипуляция полями (Упр. 29–56)'),
        (57, 84, 'Раздел 3: Создание динамических структур данных, проверка интерфейсов и DeepEqual (Упр. 57–84)'),
        (85, 114, 'Раздел 4: Продвинутые техники: reflect.Select, кэширование, unsafe-интеграция и архитектура метапрограммирования (Упр. 85–114)')
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
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 54!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили рефлексию в Go: от законов рефлексии, манипуляции типами, полями и тегами до динамического создания функций через MakeFunc, построения mock-объектов, RPC-движков и оптимизации аллокаций в HighLoad.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter53.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 53 Системные вызовы и взаимодействие с ОС</a>
            <a href="chapter55.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 55 Анализ AST и статический анализ кода →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'54. Продвинутая рефлексия (reflect) ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter55_html(chapters):
    active_chapter_num = 55
    current_exercises = ch55_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 55</div>
      <h1 class="hero-title">Анализ AST и статический анализ кода</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по синтаксическому и семантическому анализу исходного кода на Go: лексический анализ с go/token и go/scanner, синтаксический разбор в абстрактное синтаксическое дерево (AST) с go/parser, инспекция деклараций, операторов и выражений с ast.Inspect и ast.Walk, семантический анализ типов и областей видимости с go/types, построение графов вызовов функций (callgraph), разработка production-линтеров на базе фреймворка go/analysis, трансформация кода через astutil.Apply и интеграция проверок качества и автофиксов (SuggestedFix) в пайплайны CI/CD и golangci-lint.
      </p>
    </section>
    """)
    
    sections = [
        (1, 22, "Раздел 1: Основы синтаксического анализа: go/token, go/scanner, go/parser и структура AST (Упр. 1–22)"),
        (23, 44, "Раздел 2: Обход и инспекция AST: ast.Inspect, ast.Walk, извлечение типов, функций и комментариев (Упр. 23–44)"),
        (45, 66, "Раздел 3: Семантический анализ с go/types, построение графов вызовов и линтинг (Упр. 45–66)"),
        (67, 85, "Раздел 4: Фреймворк go/analysis, трансформация AST (astutil), автофикс и интеграция в CI/CD (Упр. 67–85)"),
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
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 55!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили синтаксический и статический анализ кода в Go: от токенизации и обхода AST-деревьев до проверки типов в go/types, создания собственных линтеров на фреймворке go/analysis, автоисправления кода (SuggestedFixes) и интеграции в golangci-lint.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter54.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 54 Продвинутая рефлексия (reflect)</a>
            <a href="chapter56.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 56 Кодогенерация и шаблонизация →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'55. Анализ AST и статический анализ кода ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER

def build_chapter56_html(chapters):
    active_chapter_num = 56
    current_exercises = ch56_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 56</div>
      <h1 class="hero-title">Кодогенерация и шаблонизация</h1>
      <p class="hero-desc">
        Исчерпывающее практическое и инженерное руководство по промышленной кодогенерации и метапрограммированию в Go. Автоматизация сборки через директивы //go:generate и встроенные переменные окружения ($GOFILE, $GOPACKAGE, $GOLINE). Работа с официальными генераторами: stringer, моки интерфейсов и DI-контейнеры времени компиляции (Google Wire). Внедрение статических ресурсов и SQL-миграций через директиву //go:embed. Мощный синтаксис текстового процессора text/template: управление контекстом (with, range), пользовательские функции template.FuncMap, вложенные шаблоны define и обработка экранирования. Автоматическое форматирование исходного кода с помощью go/format и пакета imports. Разработка собственных CLI-генераторов полного цикла: AST-препроцессоры аннотаций, zero-allocation сериализаторы, типобезопасные клиенты OpenAPI/gRPC, ORM-репозитории и интеграция проверок чистоты генерации в пайплайны CI/CD и Makefile.
      </p>
    </section>
    """)
    
    sections = [
        (1, 20, "Раздел 1: Директива //go:generate, окружение и утилита stringer (Упр. 1–20)"),
        (21, 40, "Раздел 2: Шаблонизатор text/template: синтаксис, функции, циклы и форматирование (Упр. 21–40)"),
        (41, 60, "Раздел 3: Продвинутая шаблонизация, генерация моков, ORM и сериализации (Упр. 41–60)"),
        (61, 77, "Раздел 4: Промышленные генераторы: DI, DDL, архитектурные слои и CI/CD (Упр. 61–77)"),
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
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 56!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили кодогенерацию и шаблонизацию в Go: от базовых директив go:generate и stringer до глубокого парсинга AST, шаблонов text/template, построения собственных ORM, DI-контейнеров, генераторов моков и интеграции в CI/CD пайплайны.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter55.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 55 Анализ AST и статический анализ кода</a>
            <a href="chapter57.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #070d19; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 57 Симметричное и асимметричное шифрование →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'56. Кодогенерация и шаблонизация ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter57_html(chapters):
    active_chapter_num = 57
    current_exercises = ch57_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 57</div>
      <h1 class="hero-title">Симметричное и асимметричное шифрование</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по криптографии и сетевой безопасности в Go. Криптографически стойкая энтропия (crypto/rand) против math/rand. Симметричное шифрование: блочные шифры AES-128/256 (crypto/aes), потоковые AEAD-шифры AES-GCM и ChaCha20-Poly1305. Аутентификация сообщений с помощью HMAC (SHA-256, SHA-512) и формирование ключей через HKDF. Асимметричная криптография: RSA (генерация, сериализация PKCS#1/PKCS#8 PEM, безопасное шифрование OAEP и вероятностные цифровые подписи PSS), эллиптические кривые (crypto/ecdsa, Curve25519/Ed25519, X25519 Key Exchange). Паттерн гибридного шифрования (Envelope Encryption) больших данных. Инфраструктура открытых ключей (PKI): парсинг и генерация сертификатов X.509 v3 с SAN, создание CSR и локального CA, OCSP Stapling, аудит Certificate Transparency (CT). Сетевая безопасность: эталонная конфигурация TLS 1.3/1.2 и cipher suites, Mutual TLS (mTLS) в архитектуре Zero Trust, автоматический заказ сертификатов Let's Encrypt (ACME), Certificate Pinning, Session Tickets и динамический виртуальный хостинг SNI. Низкоуровневая безопасность памяти: zeroing secrets, crypto/subtle, memory-hard KDF (Argon2id, PBKDF2) и токены PASETO v4.
      </p>
    </section>
    """)
    
    sections = [
        (1, 25, "Раздел 1: Криптографическая энтропия и симметричные шифры (AES-GCM, ChaCha20-Poly1305) (Упр. 1–25)"),
        (26, 50, "Раздел 2: Режимы блочного шифрования, HMAC и потоковая обработка (Упр. 26–50)"),
        (51, 75, "Раздел 3: Асимметричная криптография: RSA (OAEP, PSS) и эллиптические кривые (ECDSA, Ed25519, X25519) (Упр. 51–75)"),
        (76, 100, "Раздел 4: Промышленная криптография: TLS 1.3, X.509, Envelope Encryption, KMS и защита памяти (Упр. 76–100)"),
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
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 57!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили симметричное и асимметричное шифрование в Go: от блочных и AEAD-шифров AES/ChaCha20 до RSA-OAEP, RSA-PSS, ECDSA, Ed25519, инфраструктуры открытых ключей X.509, взаимного mTLS в Zero Trust, автоматизации ACME Let's Encrypt и защиты памяти секретов.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter56.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 56 Кодогенерация и шаблонизация</a>
            <a href="chapter58.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">Глава 58 Хеширование паролей и криптографическая стойкость →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'57. Симметричное и асимметричное шифрование ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter58_html(chapters):
    active_chapter_num = 58
    current_exercises = ch58_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 58</div>
      <h1 class="hero-title">Хеширование паролей и криптографическая стойкость</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по защите учетных данных и криптографическому хранению паролей в Go. Криптографическая энтропия (crypto/rand) против детерминированного math/rand. Опасности быстрых дайджестов (MD5, SHA-1, SHA-256) и механика коллизий. Радужные таблицы (Rainbow Tables), генерация криптосолей и стандарт PBKDF2 (HMAC-SHA256). Промышленный стандарт bcrypt (golang.org/x/crypto/bcrypt): ключевое расписание Eksblowfish, калибровка фактора стоимости (cost factor), защита от DoS-атак через семафоры и пулы горутин, интеграция с PostgreSQL и GORM. Лимит длины 72 байта и техника Pre-hashing. Современный золотой стандарт Argon2id (RFC 9106, golang.org/x/crypto/argon2) и scrypt: устойчивость к GPU/ASIC перебору, компромисс память-время (TMTO) и канонический формат хранения PHC. Корпоративная безопасность: серверный перец (HMAC-SHA256 Pepper) вне базы данных, токены сессий PASETO (v4.local) против JWT, валидация паролей через протокол k-anonymity HaveIBeenPwned API, защита от тайминг-атак User Enumeration (Dummy Hash), ротация ключей (Key Ring) с поддержкой grace period, авторизация OAuth 2.0 (Authorization Code Flow) и OpenID Connect (OIDC) с валидацией JWKS, принудительное затирание секретов в памяти (Zeroing Memory) с защитой от Dead Code Elimination.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Криптографическая энтропия и опасности быстрых хэшей (Упражнения 1–18)"),
        (19, "Раздел 2: Промышленный стандарт bcrypt и защита от атак (Упражнения 19–37)"),
        (38, "Раздел 3: Современный стандарт Argon2id, scrypt и KDF (Упражнения 38–47)"),
        (48, "Раздел 4: Корпоративная безопасность: Peppering, PASETO, OAuth2/OIDC и память (Упражнения 48–56)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 58!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили современные методы безопасного хранения паролей и токены аутентификации в Go: от bcrypt и pre-hashing до Argon2id PHC, scrypt, HMAC Pepper, защищенных токенов PASETO, k-anonymity HaveIBeenPwned API, OAuth2/OIDC и гарантированного затирания секретов в памяти.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter57.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 57 Симметричное и асимметричное шифрование</a>
            <a href="chapter59.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">Глава 59 Токены аутентификации и авторизация →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'58. Хеширование паролей и криптографическая стойкость ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter59_html(chapters):
    active_chapter_num = 59
    current_exercises = ch59_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 59</div>
      <h1 class="hero-title">Токены аутентификации и авторизация</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по архитектуре токенов аутентификации и протоколам авторизации в Go. Фундамент Base64URL без паддинга (RFC 4648) и ручная сборка JWT. Криптографические алгоритмы цифровой подписи: HMAC-SHA256 (HS256), RSA PKCS#1 v1.5 (RS256), RSA-PSS (PS256), ECDSA (ES256) и Ed25519 (EdDSA). Канонический стандарт PASETO v4 (RFC): устранение уязвимостей алгоритмической гибкости (alg: none, Algorithm Confusion), аутентифицированное шифрование v4.local (XChaCha20-Poly1305 AEAD), асимметричные подписи v4.public и Pre-Authentication Encoding (PAE). Продвинутые примитивы авторизации: Macaroons с контекстными оговорками (First-Party и Third-Party Caveats), токены Biscuit на базе Datalog-политик и оффлайн-аттенюации. Протокол OAuth 2.0 (RFC 6749) и OAuth 2.1: Authorization Code Flow с бэк-ченнел обменом, PKCE (RFC 7636, S256), защита от Login CSRF через привязку state в HttpOnly/SameSite=Lax cookie, Client Credentials Flow (M2M) с пулом кэширования, Device Authorization Grant (RFC 8628). Ротация токенов (Refresh Token Rotation) с детекцией повторного использования (Token Family / Replay Detection) и окном Grace Period, безопасное хранение SHA-256 хешей в БД. Sender-Constrained токены DPoP (RFC 9449) с криптографическим подтверждением владения. OpenID Connect (OIDC Core 1.0): динамическое обнаружение (RFC 8414 /.well-known/openid-configuration), валидация ID Token через JWKS (RFC 7517) с On-Demand Refresh и защитой от Thundering Herd. Сессионные куки со строгой изоляцией (__Host- префикс, HttpOnly, Secure, SameSite=Strict). Интроспекция (RFC 7662) и отзыв токенов (RFC 7009). Тонкости интеграции Social Login (Google, GitHub, Apple ID с динамическим ES256 секретом).
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Фундамент токенов: Base64URL, ручная сборка JWT и PASETO v4 (Упражнения 1–15)"),
        (16, "Раздел 2: Уязвимости токенов, алгоритмические атаки и криптографическая защита (Упражнения 16–25)"),
        (26, "Раздел 3: Продвинутая авторизация: Macaroons, Biscuit, Token Family и сессии (Упражнения 26–44)"),
        (45, "Раздел 4: Протоколы OAuth 2.0, OpenID Connect (OIDC) и корпоративный контроль доступа (Упражнения 45–66)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 59!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили токены аутентификации и протоколы авторизации в Go: от ручной сборки JWT и PASETO v4 до PKCE, Refresh Token Rotation, DPoP, OIDC Discovery, JWKS кэширования и проектирования собственного OAuth 2.0 сервера.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter58.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 58 Хеширование паролей и криптографическая стойкость</a>
            <a href="chapter60.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 60 Безопасность веб-приложений и защита API →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'59. Токены аутентификации и авторизация ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter60_html(chapters):
    active_chapter_num = 60
    current_exercises = ch60_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section (БЕЗ hero-stats)
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 60</div>
      <h1 class="hero-title">Безопасность веб-приложений и защита API</h1>
      <p class="hero-desc">
        Комплексное практическое руководство по безопасности веб-приложений и защите REST API в Go. Защита от DoS-атак: сетевые таймауты (ReadHeaderTimeout, ReadTimeout, WriteTimeout, IdleTimeout), лимитирование объема входящих тел запросов через http.MaxBytesReader и multipart-форм, защита от Slowloris и memory exhaustion. Полномасштабная защита от SSRF: блокировка приватных подсетей (RFC 1918, Link-Local 169.254.169.254, loopback), предотвращение атак TOCTOU и DNS Rebinding через закрепление IP (IP pinning) в кастомном DialContext, разбор альтернативных форматов IP (Decimal DWORD, Hex, Octal). Инъекционные векторы: предотвращение SQLi в динамических выражениях ORDER BY и идентификаторах через строгий Whitelist Mapping, Command Injection в os/exec (безопасный вызов без shell sh -c), XSS и контекстно-зависимое экранирование в html/template vs text/template, предотвращение Path Traversal с использованием filepath.Rel и виртуальной fs os.DirFS. Межсайтовые угрозы и безопасность браузера: Stateless HMAC и Stateful CSRF токены, Double Submit Cookie, промышленный CORS middleware со строгим Whitelist и preflight кэшированием (Max-Age), Open Redirect санитизация, Nonce-based Content Security Policy (CSP Level 3), защита от Clickjacking (X-Frame-Options и frame-ancestors). Управление секретами: интеграция с HashiCorp Vault (AppRole, динамические PostgreSQL credentials, аренда и heartbeat renewal), AWS Secrets Manager через IRSA без статичных ключей, Memory Zeroing чувствительных данных в RAM и защита от атак по времени через crypto/subtle.ConstantTimeCompare.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Базовая сетевая защита: DoS, Payload Limit, SSRF и Timing Attacks (Упражнения 1–15)"),
        (16, "Раздел 2: Инъекционные уязвимости: SQLi, Command Injection, XSS и Path Traversal (Упражнения 16–31)"),
        (32, "Раздел 3: Межсайтовые угрозы и безопасность браузера: CSRF, CORS, Open Redirect и CSP (Упражнения 32–45)"),
        (46, "Раздел 4: Корпоративная безопасность: Vault, Secrets Manager, XXE и Hardening (Упражнения 46–63)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 60!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы освоили полный стек защиты веб-приложений и API в Go: от предотвращения DoS, SSRF, SQLi, XSS, Path Traversal и CSRF до интеграции с HashiCorp Vault, AWS Secrets Manager, Strict CSP, Double Submit Cookie и создания промышленного фасада безопасности.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter59.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 59 Токены аутентификации и авторизация</a>
            <a href="chapter61.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 61 Документоориентированная база данных MongoDB →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'60. Безопасность веб-приложений и защита API ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter61_html(chapters):
    active_chapter_num = 61
    current_exercises = ch61_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 61</div>
      <h1 class="hero-title">Документоориентированная база данных MongoDB</h1>
      <p class="hero-desc">
        Комплексное практическое руководство по работе с NoSQL СУБД MongoDB в Go с использованием официального драйвера go.mongodb.org/mongo-driver. Архитектура движка хранения WiredTiger: организация структур данных на базе B-деревьев, кэширование страниц в памяти, checkpointing и журналы упреждающей записи (WAL/WiredTiger.wt). Внутреннее представление и форматы BSON: bson.D (строго упорядоченный срез пар ключ-значение для системных команд, пайплайнов и индексов), bson.M (неупорядоченная хэш-мапа), bson.A (BSON-массивы), 12-байтный primitive.ObjectID (4 байта Unix timestamp, 5 байт криптографически случайного процесса, 3 байта инкрементного счетчика) и primitive.Decimal128 для прецизионных финансовых вычислений без погрешностей плавающей запятой IEEE-754. Тонкая настройка пула сетевых соединений (MaxPoolSize, MinPoolSize, MaxConnIdleTime) и надежная обработка контекстных дедлайнов. Индексирование: Single field, Compound indexes с соблюдением правила ESR (Equality, Sort, Range), покрывающие индексы (covered queries), TTL-индексы для автоудаления устаревших сессий, Partial и Sparse индексы, полнотекстовые Text indexes, хэшированные (Hashed) и геопространственные 2dsphere индексы ($nearSphere, $geoWithin). Аналитический конвейер Aggregation Framework: $match, $project, $group с аккумуляторами ($sum, $avg, $push), $sort, $lookup (левое внешнее соединение коллекций с оптимизацией correlated subqueries), $unwind, параллельная обработка фасетов $facet, $bucketAuto, графовый обход $graphLookup и оконные функции $setWindowFields. Уровни консистентности и отказоустойчивости: Read Concern (local, available, majority, linearizable, snapshot), Write Concern (w:1, w:\"majority\", j:true, wtimeout) и Read Preference (primary, primaryPreferred, secondary, secondaryPreferred, nearest). Распределенные транзакции ACID поверх Replica Set с автоматическим повтором при TransientTransactionError и UnknownTransactionCommitResult. Репликация (Raft-подобные выборы Primary, oplog.rs), реактивные Change Streams для построения Event-Driven архитектур и CDC (Change Data Capture) с надежным возобновлением по Resume Token. Шардирование: кластерная маршрутизация mongos, распределение чанков (Chunk Split & Balance), выбор между Range и Hashed Shard Key. Специализированные сценарии: Time Series коллекции с бакетированием и гранулярностью (seconds, minutes, hours), векторный поиск Atlas Vector Search для RAG/LLM, блочное хранилище медиафайлов GridFS с чанками по 255 КБ, пулинг буферов BSON-сериализации и экстремальная HighLoad-оптимизация.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура WiredTiger, BSON-типы, пул соединений и CRUD-операции (Упражнения 1–30)"),
        (31, "Раздел 2: Индексы, Aggregation Framework и аналитические конвейеры (Упражнения 31–60)"),
        (61, "Раздел 3: Read/Write Concerns, ACID-транзакции, Change Streams и шардирование (Упражнения 61–88)"),
        (89, "Раздел 4: Time Series, Atlas Vector Search, GridFS и HighLoad оптимизация (Упражнения 89–113)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 61!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы досконально изучили работу с MongoDB в Go: от внутреннего устройства BSON и индексов WiredTiger до распределенных ACID-транзакций, реактивных Change Streams, сложных агрегаций, Time Series коллекций, Atlas Vector Search и GridFS.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter60.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 60 Безопасность веб-приложений и защита API</a>
            <a href="chapter62.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 62 Аналитическая СУБД ClickHouse →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'61. Документоориентированная база данных MongoDB ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter62_html(chapters):
    active_chapter_num = 62
    current_exercises = ch62_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 62</div>
      <h1 class="hero-title">Аналитическая СУБД ClickHouse</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по колоночной аналитической СУБД ClickHouse для Go-разработчиков высоконагруженных платформ. Сетевые протоколы и драйвер: сравнительный анализ нативного бинарного TCP-протокола (порт 9000) и HTTP-интерфейса (порт 8123) в официальном драйвере github.com/ClickHouse/clickhouse-go/v2, сжатие блоков на лету (LZ4, ZSTD), потоковое чтение (Streaming Read) через rows.Next() с константным расходом оперативной памяти O(1) и векторизованный интерфейс Columnar Batch API (batch.Column(i).Append) для исключения накладных расходов рефлексии. Архитектура семейства MergeTree: физическое устройство хранения партов (Parts), разреженный первичный индекс (primary.cidx) с шагом index_granularity=8192, марк-файлы (.mrk2) для точечной адресации сжатых блоков, физическое партиционирование (PARTITION BY) против сортировки (ORDER BY), жизненный цикл данных (TTL) на уровне таблиц и отдельных колонок. Специализированные движки хранения: ReplacingMergeTree (дедупликация версий, модификатор FINAL и функция argMax), SummingMergeTree (автоматическое схлопывание счетчиков), AggregatingMergeTree с комбинаторами промежуточных состояний (-State и -Merge) и SimpleAggregateFunction, CollapsingMergeTree и VersionedCollapsingMergeTree с эмуляцией мутаций через знаковый признак Sign (+1 / -1). Вторичные индексы пропуска данных (Data Skipping Indexes): minmax, set, bloom_filter, tokenbf_v1 и n-граммный поиск по подстрокам LIKE через ngrambf_v1. Инкрементальные предагрегации: Materialized Views со связыванием TO target_table, Live Views и оконные стримы. Сложные типы: Array(T) с лямбда-функциями высшего порядка (arrayMap, arrayFilter, arrayReduce, arrayJoin), Tuple, Map(K, V), IPv4/IPv6, DateTime64(3) и высокоскоростной парсинг JSON (simdjson). Распределенная кластерная архитектура: фасад Distributed(cluster, db, table, sharding_key), двухуровневая репликация ReplicatedMergeTree с координацией через ClickHouse Keeper/ZooKeeper, потоковый импорт из Apache Kafka (Kafka Engine), аналитика локальных файлов через clickhouse-local и интеграция с внешними Data Lake (S3 Engine).
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура MergeTree, нативный бинарный протокол и пакетная вставка (Упражнения 1–18)"),
        (19, "Раздел 2: Специализированные движки, индексы пропуска данных и компрессия (Упражнения 19–35)"),
        (36, "Раздел 3: Сложные типы данных, партиционирование, Materialized Views и словари (Упражнения 36–53)"),
        (54, "Раздел 4: Оконные функции, шардирование, интеграции и архитектурный синтез (Упражнения 54–71)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 62!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили аналитическую СУБД ClickHouse в Go: от физического устройства MergeTree и нативного бинарного протокола до специализированных движков, оконных функций, Materialized Views, шардирования и потокового импорта из Apache Kafka.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter61.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 61 Документоориентированная база данных MongoDB</a>
            <a href="chapter63.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 63 Поисковые движки Elasticsearch и OpenSearch →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'62. Аналитическая СУБД ClickHouse ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter63_html(chapters):
    active_chapter_num = 63
    current_exercises = ch63_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 63</div>
      <h1 class="hero-title">Поисковые движки Elasticsearch и OpenSearch</h1>
      <p class="hero-desc">
        Исчерпывающее практическое руководство по распределенным поисковым и аналитическим движкам Elasticsearch и OpenSearch для Go-разработчиков высоконагруженных систем. Внутренняя архитектура Apache Lucene: инвертированный индекс (Inverted Index), префиксные автоматы FST (Finite State Transducers), иммутабельность сегментов, журнал упреждающей записи translog, колоночное хранилище doc_values и сжатые битовые карты Roaring Bitmaps. Официальные клиенты go-elasticsearch/v8 и opensearch-go: пулы HTTP/2 соединений, векторизованная пакетная индексация через esutil.NewBulkIndexer с неблокирующими очередями, стратегиями сброса и обработкой HTTP 429 Too Many Requests. Проектирование схем: принцип Mapping First, предотвращение Mapping Explosion через dynamic: strict, глубокое сравнение типов text и keyword, многопоточные анализаторы, токенизаторы, фильтры стоп-слов, синонимов и стемминга. Сложные поисковые конструкции: составные Bool-запросы (must vs filter vs should vs must_not), исключение оверхеда скоринга в Filter Context, расчет релевантности по алгоритму BM25, нечеткий поиск опечаток Fuzzy Search по расстоянию Левенштейна-Дамерау. Глубокая пагинация: ограничение max_result_window, Point in Time (PIT) со search_after. Фасетная навигация и многомерная аналитика e-commerce каталогов через агрегации terms, histogram и nested. Эксплуатация и HighLoad: политики жизненного цикла индексов (ILM) для time-series данных, data streams, скрипты Painless в UpdateByQuery, инкрементальные снапшоты, шардирование и мониторинг восстановления кластера через _cat/recovery.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура Lucene, CRUD, маппинг и Bulk API (Упражнения 1–15)"),
        (16, "Раздел 2: Анализаторы, полнотекстовый поиск и сложные Bool-запросы (Упражнения 16–30)"),
        (31, "Раздел 3: Глубокая пагинация, Highlighting, Geo и вложенные структуры (Упражнения 31–45)"),
        (46, "Раздел 4: Агрегации, ILM, отказоустойчивость и HighLoad архитектура (Упражнения 46–60)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 63!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили поисковые движки Elasticsearch и OpenSearch в Go: от физического устройства инвертированного индекса Lucene и высокопроизводительного BulkIndexer до сложных Bool-запросов, фасетных агрегаций, глубокой пагинации через PIT + search_after, скриптов Painless и time-series архитектуры с ILM.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter62.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 62 Аналитическая СУБД ClickHouse</a>
            <a href="chapter64.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 64 Логическая репликация и Change Data Capture →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'63. Поисковые движки Elasticsearch и OpenSearch ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter64_html(chapters):
    active_chapter_num = 64
    current_exercises = ch64_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 64</div>
      <h1 class="hero-title">Логическая репликация и Change Data Capture</h1>
      <p class="hero-desc">
        Исчерпывающее практическое руководство по логической репликации и Change Data Capture (CDC) для Go-разработчиков высоконагруженных распределенных систем. Внутренняя архитектура PostgreSQL Write-Ahead Log (WAL): сегменты, контрольные точки (checkpoints), порядковые номера LSN (Log Sequence Number) и плагины логического декодирования (pgoutput, test_decoding, wal2json). Репликационные слоты (Replication Slots): предотвращение удаления несчитанных WAL-сегментов, управление lag, мониторинг pg_stat_replication и системные процедуры pg_replication_slot_advance. Реализация CDC-клиента на чистом Go с использованием pglogrepl и pgx/v5: протокол потоковой передачи данных (streaming replication protocol), декодирование бинарных сообщений XLogData, обработка транзакционных границ (Begin, Commit, Relation, Insert, Update, Delete, Type). Обработка эволюции схем и топология типов: REPLICA IDENTITY (DEFAULT, NOTHING, FULL, INDEX), сопоставление OID системного каталога pg_type, разбор TOAST-значений (unchanged toast columns) и миграции таблиц без потери консистентности. Гарантии доставки сообщений: расчет и отправка Standby Status Update (WriteLSN, FlushLSN, ApplyLSN) для предотвращения разрастания WAL на мастере, семантика At-Least-Once, дедупликация и сохранение чекпоинтов в распределенном хранилище. Архитектурные паттерны: транзакционный Outbox без опроса БД (Polling publisher vs CDC tailer), организация репликации в реальном времени из PostgreSQL в Apache Kafka (debezium-совместимые события JSON/Avro), ClickHouse и Elasticsearch. Эксплуатация и отказоустойчивость: безопасный реконнект с последнего подтвержденного LSN, мониторинг replication delay/lag в Prometheus, обработка аварийных ситуаций, предотвращение переполнения дискового пространства и HighLoad-оптимизация пропускной способности стриминга.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура WAL, слоты репликации и плагин pgoutput (Упражнения 1–15)"),
        (16, "Раздел 2: Протокол потоковой передачи, типизация и эволюция схем (Упражнения 16–30)"),
        (31, "Раздел 3: CDC в распределенных системах: Kafka, Elasticsearch и ClickHouse (Упражнения 31–45)"),
        (46, "Раздел 4: Промышленный CDC-пайплайн, отказоустойчивость и мониторинг (Упражнения 46–57)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 64!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили логическую репликацию и Change Data Capture в Go: от физического устройства WAL и репликационных слотов PostgreSQL до низкоуровневого парсинга протокола pgoutput, построения надежного CDC-пайплайна с At-Least-Once семантикой и стриминга изменений в Kafka, ClickHouse и Elasticsearch без оверхеда опроса базы данных.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter63.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 63 Поисковые движки Elasticsearch и OpenSearch</a>
            <a href="chapter65.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 65 Вебхуки и платформы обратных вызовов →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'64. Логическая репликация и Change Data Capture ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter65_html(chapters):
    active_chapter_num = 65
    current_exercises = ch65_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 65</div>
      <h1 class="hero-title">Вебхуки и платформы обратных вызовов</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по архитектуре, доставке и безопасности вебхуков промышленного уровня (Stripe-grade Webhook Engine) для Go-разработчиков высоконагруженных платформ. Архитектура конвертов событий (Event Envelopes), каноническая структура полезной нагрузки и эволюция схем (Payload Versioning). Криптографическая безопасность: цифровая подпись HMAC-SHA256, связывание метки времени (Timestamp + Payload), предотвращение атак повторного воспроизведения (Replay Attacks) и сравнение подписей за строго константное время (crypto/subtle.ConstantTimeCompare). Защита сетевого контура: перехват сокетов на уровне net.Dialer.Control для 100% защиты от SSRF и атак DNS Rebinding, строгая политика запрета HTTP-редиректов (CheckRedirect), сжатие gzip с пулом sync.Pool, лимитирование размеров тел (MaxBytesReader) и Claim Check паттерн с оффлоадингом в S3. Высоконагруженная доставка и планирование: пулы воркеров фиксированного размера (Worker Pool), алгоритм Full Jitter для ликвидации эффекта Thundering Herd, поклиентские и глобальные Token Bucket ограничители скорости (Rate Limiting), семафоры и изоляция аномальных клиентов (Hot Endpoint Detection). Надежность и транзакционность: гарантии At-Least-Once, паттерн Transactional Outbox без поллинга базы данных, очередь мертвых сообщений (Dead Letter Queue, DLQ) с ручным перезапуском, долговременное хранение истории в ClickHouse (TTL 90 дней) и идемпотентная обработка на стороне получателя (Receiver Idempotency). Сравнительный анализ транспортных протоколов: Webhooks vs SSE vs WebSockets vs gRPC vs JSON-RPC 2.0, тонкости CORS Preflight, сквозная трассировка W3C traceparent и сквозное бюджетирование ресурсов операционной системы.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Конверты событий, криптографическая подпись HMAC-SHA256 и базовый диспетчер (Упражнения 1–30)"),
        (31, "Раздел 2: Экспоненциальный Backoff, Jitter, Circuit Breakers и очереди доставки (Упражнения 31–60)"),
        (61, "Раздел 3: Безопасность, SSRF, mTLS, Rate Limiting и защита от Replay Attacks (Упражнения 61–90)"),
        (91, "Раздел 4: Корпоративная платформа вебхуков, Outbox-паттерн и мультипротокольная интеграция (Упражнения 91–116)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 65!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили проектирование и эксплуатацию платформ вебхуков корпоративного уровня в Go: от криптографической защиты HMAC-SHA256 и перехвата сокетов против SSRF/DNS Rebinding до построения надежного Transactional Outbox, управления очередями с Full Jitter бэкоффом, изоляции очередей DLQ и мультипротокольной интеграции с Server-Sent Events и gRPC.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter64.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 64 Логическая репликация и Change Data Capture</a>
            <a href="chapter66.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 66 Server-Sent Events →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'65. Вебхуки и платформы обратных вызовов ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter66_html(chapters):
    active_chapter_num = 66
    current_exercises = ch66_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 66</div>
      <h1 class="hero-title">Server-Sent Events (SSE)</h1>
      <p class="hero-desc">
        Глубокое инженерное руководство по архитектуре, реализации и масштабированию потоковой передачи данных в реальном времени с использованием протокола Server-Sent Events (SSE) на языке Go. Спецификация W3C SSE и анатомия текстового кадрирования: разметка полей event, id, retry, data, обработка многострочных полезных нагрузок и служебных комментариев keep-alive. Низкоуровневое управление буферизацией в сетевом стеке: интерфейс http.Flusher и современный http.ResponseController (Go 1.20+), сокетные опции TCP_NODELAY, заголовок X-Accel-Buffering: no для обхода прокси-буферов Nginx, Envoy и CDN (Cloudflare). Гарантии надежности и отказоустойчивости: сквозное возобновление сессий с заголовком Last-Event-ID, кольцевые replay-буферы в оперативной памяти и Redis Streams, алгоритмы Exponential Backoff с Full Jitter и детекция разрыва связи через Context. Проектирование высоконагруженных многопользовательских брокеров (Hub/Broker): шардированные мьютексы, паттерн Single Writer per Connection для гарантии порядка доставки (In-Order Delivery), неблокирующая отправка сообщений и защита от медленных клиентов (Backpressure, Drop Oldest и Slow Consumer Eviction). Горизонтальное масштабирование через распределенную шину Redis Pub/Sub, мультиплексирование потоков поверх единого соединения HTTP/2 и HTTP/3, ChatGPT-style потоковая генерация токенов для LLM и клиентская координация вкладок через BroadcastChannel API.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Протокол SSE, Event ID, Flusher и именованные события (Упражнения 1–18)"),
        (19, "Раздел 2: Мультиплексирование, брокеры сообщений и устойчивый реконнект (Упражнения 19–35)"),
        (36, "Раздел 3: HighLoad масштабирование, Netpoller, Redis Streams и сжатие (Упражнения 36–52)"),
        (53, "Раздел 4: Промышленная платформа стриминга, безопасность и мониторинг (Упражнения 53–69)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 66!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили проектирование высоконагруженных платформ потоковой передачи данных на Server-Sent Events в Go: от спецификации W3C текстового кадрирования и низкоуровневого управления буферизацией через ResponseController до проектирования брокеров с защитой от медленных клиентов, организации бесшовного возобновления связи по Last-Event-ID и стриминга ответов LLM в стиле ChatGPT.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter65.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 65 Вебхуки и платформы обратных вызовов</a>
            <a href="chapter67.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 67 Альтернативные RPC-протоколы →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'66. Server-Sent Events ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter67_html(chapters):
    active_chapter_num = 67
    current_exercises = ch67_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 67</div>
      <h1 class="hero-title">Альтернативные RPC-протоколы (JSON-RPC 2.0, gRPC-Web, ConnectRPC)</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по архитектуре, спецификациям и реализации альтернативных протоколов удаленного вызова процедур (RPC) в экосистеме Go. Спецификация JSON-RPC 2.0: семантика 4 типов сообщений (Request, Response success, Response error, Notification), канонические коды системных ошибок (-32700..-32600), пакетные запросы (Batching) для устранения проблемы N+1 сетевых вызовов, транзакционные батчи и полнодуплексный транспорт поверх WebSocket с управлением состоянием клиентских сессий и защитой от Slow Consumer. Архитектура и спецификация gRPC-Web: фундаментальное ограничение браузерного Fetch API в работе с HTTP/2 Trailers, кадрирование данных и трейлеров (флаги 0x00 и 0x80), развертывание и тюнинг Envoy Proxy (фильтры grpc_web, cors, router, circuit breakers) и встраиваемая in-process обертка на чистом Go (improbable-eng/grpc-web). Фреймворк нового поколения ConnectRPC (connect-go): zero-proxy архитектура, нативная поддержка браузеров без Envoy, мультипротокольные эндпоинты (gRPC, gRPC-Web, Connect на едином порту), интеграция с HTTP/2 Cleartext (h2c), потоковые обработчики Server/Client/Bidi streaming и фронтенд-интеграция с TanStack Query. Protobuf-first подход, кодогенерация SDK через Buf CLI, автоматическая генерация документации через Protobuf Reflection и системный сравнительный анализ протоколов REST, gRPC, Connect, JSON-RPC, SSE и GraphQL в HighLoad архитектуре BigTech.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Спецификация JSON-RPC 2.0, диспетчеризация и пакетные запросы (Упражнения 1–23)"),
        (24, "Раздел 2: Двунаправленный сокет, OpenRPC, архитектура gRPC-Web и Envoy (Упражнения 24–46)"),
        (47, "Раздел 3: Connect-go, мультипротокольные эндпоинты, интерцепторы и CORS (Упражнения 47–69)"),
        (70, "Раздел 4: Промышленная RPC-платформа, кодогенерация, трейсинг и бенчмарки (Упражнения 70–92)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 67!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы глубоко освоили весь спектр современных RPC-технологий на Go: от чистого JSON-RPC 2.0 с пакетным батчингом и сокетными нотификациями до промышленной настройки Envoy Proxy для gRPC-Web, сквозной разработки сервисов на ConnectRPC без сторонних прокси и построения контрактов по методологии Protobuf-first.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter66.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 66 Server-Sent Events</a>
            <a href="chapter68.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 68 Паттерн Saga и компенсационные транзакции →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'67. Альтернативные RPC-протоколы ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter68_html(chapters):
    active_chapter_num = 68
    current_exercises = ch68_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 68</div>
      <h1 class="hero-title">Паттерн Saga и компенсационные транзакции</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по теории, архитектуре и практической реализации распределенных транзакций в микросервисных системах на Go. Почему двухфазный коммит (2PC / XA Transactions) неприменим в современных HighLoad микросервисах: CAP/PACELC теорема, блокирующая природа протокола, каскадные дедлоки и переход к модели BASE (Basically Available, Soft state, Eventual consistency). Архитектурные паттерны реализации Саги: Хореография (Choreography) — децентрализованный обмен доменными событиями через Apache Kafka/NATS с мониторингом через Saga Tracker Service, и Оркестрация (Orchestration) — централизованный FSM координатор, детерминированные воркфлоу в Temporal/Cadence и воспроизведение истории событий (Event Sourcing Replay). Теория и механика компенсаций: каскадный LIFO-откат (Last-In-First-Out), Backward Recovery против Forward Recovery (повтор до победного конца), концепция Pivot Transactions (точка невозврата) и строгое соблюдение идемпотентности компенсаций с защитой от двойного начисления остатков. Сквозная надежность (End-to-End Reliability): устранение проблемы Dual Write через Transactional Outbox, стриминг изменений через Debezium CDC, упорядочивание партиций Kafka по correlation_id и дедупликация входящих сообщений через Transactional Inbox с ограничениями Unique Constraint. Решение проблемы отсутствия изоляции (Lack of Isolation в ACID): защита от Dirty Reads и Lost Updates через семантические блокировки (Semantic Lock / HTTP 423 Locked), разрешение распределенных дедлоков фоновым демоном Sweeper/Watchdog с таймаутами, Dead Letter Queue (DLQ) для ядовитых сообщений, сквозная трассировка W3C Trace Context через границы сервисов, веб-панель ручного управления (Manual Intervention UI) и интеграционное тестирование инвариантов консистентности.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Теория Саги, оркестрация vs хореография и Happy Path (Упражнения 1–26)"),
        (27, "Раздел 2: Компенсационные транзакции, идемпотентность и конечные автоматы (Упражнения 27–52)"),
        (53, "Раздел 3: Outbox/Inbox, таймауты, дедлоки и распределенная консистентность (Упражнения 53–78)"),
        (79, "Раздел 4: Промышленная координация (Temporal/Cadence), Observability и интеграционные тесты (Упражнения 79–104)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 68!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы досконально изучили одну из самых сложных тем распределенных систем: паттерн Сага, построение оркестраторов и хореографии, идемпотентные компенсации, транзакционный Outbox и Inbox, а также методы достижения строгой согласованности данных в HighLoad микросервисах BigTech.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter67.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 67 Альтернативные RPC-протоколы</a>
            <a href="chapter69.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 69 Паттерны Outbox и Inbox для надежной доставки сообщений →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'68. Паттерн Saga и компенсационные транзакции ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter69_html(chapters):
    active_chapter_num = 69
    current_exercises = ch69_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
      <div class="hero-tag">Глава 69</div>
      <h1 class="hero-title">Паттерны Outbox и Inbox для надежной доставки сообщений</h1>
      <p class="hero-desc">
        Исчерпывающее инженерное руководство по проектированию надежных событийно-ориентированных систем на Go: гарантированная доставка сообщений без распределенных двухфазных транзакций (2PC). Проблема Dual Write (одновременная несогласованная запись в БД и брокер) и ее математическая неизбежность в ненадежных сетях. Паттерн Transactional Outbox на стороне Producer: единая локальная ACID-транзакция сохранения бизнес-сущности и события, DDL-схемы таблицы outbox, разделение aggregate_id и partition_key, частичные индексы WHERE sent_at IS NULL. Способы ретрансляции: Outbox Poller с SELECT FOR UPDATE SKIP LOCKED, Push-модель на базе PostgreSQL LISTEN/NOTIFY и реактивный CDC (Change Data Capture) через чтение журнала упреждающей записи WAL (библиотека pglogrepl и Debezium Event Router). Надежная публикация: экспоненциальный бэкофф (Exponential Backoff), Dead Letter Queue (DLQ) для ядовитых сообщений и Publisher Confirms в RabbitMQ с групповым подтверждением (Multiple Ack). Паттерн Transactional Inbox на стороне Consumer: гарантии At-Least-Once брокера и достижение семантики Effectively Exactly-Once через локальную транзакцию дедупликации, составные ключи UNIQUE(event_id, consumer_name), семантика ON CONFLICT DO NOTHING и подавление ошибок нарушения уникальности со своевременным подтверждением смещения (Ack / CommitOffset). Сравнение стратегий дедупликации: надежный реляционный Inbox в PostgreSQL против высокопроизводительного SET NX EX в Redis. Эволюция схем сообщений (Schema Evolution), сквозная трассировка OpenTelemetry (W3C Traceparent), цепочки микросервисов (Listen-to-Yourself), интеграция через прямой HTTP без брокера и сборка мусора (Garbage Collection / Pruning Daemon) с проверкой Watermark потребителей.
      </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Проблема Dual Write и основы Transactional Outbox (Упражнения 1–18)"),
        (19, "Раздел 2: Outbox Poller, CDC Debezium и версионирование событий (Упражнения 19–36)"),
        (37, "Раздел 3: Transactional Inbox, идемпотентное потребление и дедупликация (Упражнения 37–54)"),
        (55, "Раздел 4: Промышленная архитектура, RabbitMQ/Kafka, Observability и E2E надежность (Упражнения 55–72)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 69!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы досконально освоили фундаментальные стандарты надежности распределенных систем: искоренение Dual Write, Transactional Outbox и Inbox, чтение PostgreSQL WAL через CDC, групповые подтверждения брокеров, а также построение надежных сквозных пайплайнов с семантикой Effectively Exactly-Once.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter68.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 68 Паттерн Saga и компенсационные транзакции</a>
            <a href="chapter70.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 70 Проектирование идемпотентных API →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'69. Паттерны Outbox и Inbox для надежной доставки сообщений ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter70_html(chapters):
    active_chapter_num = 70
    current_exercises = ch70_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 70</div>
        <h1 class="hero-title">Проектирование идемпотентных API</h1>
        <p class="hero-desc">
            Полное академическое и промышленное руководство по проектированию надежных, строго идемпотентных распределенных API и микросервисов на Go: теория и международные спецификации IETF (The Idempotency-Key HTTP Header Field), RFC 7231 и RFC 7232. Механика обнаружения параллельных запросов (In-Flight Detection) с возвратом кодов 409 Conflict и заголовка Retry-After, распределенные блокировки на базе Redis SET NX EX и строчные транзакционные замки PostgreSQL (SELECT FOR UPDATE NOWAIT / pg_try_advisory_xact_lock). Криптографическая защита от подмены полезной нагрузки (Request Fingerprinting) с вычислением SHA-256 хэша тела и детекцией Payload Mismatch (код 422 Unprocessable Entity). Перехват и воспроизведение ответов через кастомные обертки http.ResponseWriter (Response Capturer) с сохранением кодов, заголовков и тел, возврат заголовка Idempotent-Replay: true. Управление жизненным циклом и дифференцированный TTL (24 часа для финансовых операций, 5 минут для безопасных методов), батчевая фоновая очистка (Batched GC Job) и секционирование таблиц (pg_partman). Идемпотентность длительных асинхронных операций со статусом Processing (202 Accepted + Polling), интерцепторы gRPC с извлечением ключа из context metadata, семантика PATCH и частичная идемпотентность, композитный скоупинг ключей по тенантам и пользователям (tenant:user:key), приоритет Rate Limiting над кэшированием для отражения DoS-атак, интеграция с Saga Orchestrator, Transactional Outbox, Transactional Inbox и построение эталонного шлюза платежей (Payment Gateway).
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Теория идемпотентности, Redis Store и Response Recorder (Упражнения 1–18)"),
        (19, "Раздел 2: TTL, Request Fingerprinting и конкурентный In-Progress Lock (Упражнения 19–37)"),
        (38, "Раздел 3: Реляционная СУБД, Stripe-like Charges и асинхронные операции (Упражнения 38–55)"),
        (56, "Раздел 4: gRPC Interceptors, ETag, Observability и End-to-End шлюз платежей (Упражнения 56–74)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 70!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили проектирование идемпотентных API на уровне архитектуры HighLoad и Tier-1 BigTech: дедупликацию запросов, защиту от гонок и подмены данных, транзакционную фиксацию в СУБД, перехват ответов и сквозную надежность в распределенных системах.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter69.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 69 Паттерны Outbox и Inbox для надежной доставки сообщений</a>
            <a href="chapter71.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #00add8;">Глава 71 Выборы лидера (Leader Election) в распределенных системах →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'70. Проектирование идемпотентных API ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter71_html(chapters):
    active_chapter_num = 71
    current_exercises = ch71_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 71</div>
        <h1 class="hero-title">Выборы лидера (Leader Election) в распределенных системах</h1>
        <p class="hero-desc">
            Фундаментальное и прикладное руководство по реализации отказоустойчивых алгоритмов выбора лидера (Leader Election) в распределенных системах на Go: координаторы etcd (v3.5+) и HashiCorp Consul. Атомарные аренды (Leases), KeepAlive heartbeat-потоки, транзакции сравнения ревизий (Txn CAS) и пакет go.etcd.io/etcd/client/v3/concurrency. Механизмы Kubernetes LeaderElector (client-go), хуки OnStartedLeading, OnStoppedLeading и OnNewLeader с fail-fast гарантией. Анализ асинхронных сетей и сетевых разделений (Network Partitions, Split-Brain), теорема о кворумах (Quorum Intersection), расчет отказоустойчивости нечетных кластеров. Предотвращение набега толпы (Thundering Herd) через детерминированные очереди CreateRevision и экспоненциальный Full Jitter backoff. Управление сессиями HashiCorp Consul (api.Session), семантика блокировок (KV Acquire / Release), Blocking Queries (WaitIndex) и параметр LockDelay. Защита хранилищ от зомби-лидеров через монотонные Fencing Tokens, глубокие проверки здоровья лидера (Deep Health Checks), graceful step down с drain активных задач и концептуальный переход к консенсусу Raft.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: etcd Leases, KeepAlive и атомарные транзакции захвата лидерства (Упражнения 1–22)"),
        (23, "Раздел 2: Пакет concurrency.Election, Kubernetes LeaderElector и Standby-режимы (Упражнения 23–45)"),
        (46, "Раздел 3: Network Partitions, Split-Brain, кворумы и разделение обязанностей лидера (Упражнения 46–67)"),
        (68, "Раздел 4: Consul vs etcd, Fencing Tokens, Health Checks и мост к протоколу Raft (Упражнения 68–90)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 71!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы досконально изучили механизмы распределенного выбора лидера в HighLoad и Cloud Native архитектурах: от низкоуровневых арен etcd и сессий Consul до защиты от сетевых разделений, кворумов, предотвращения Split-Brain с помощью Fencing Tokens и бесшовного переключения при сбоях.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter70.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 70 Проектирование идемпотентных API</a>
            <a href="chapter72.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 72 Протокол консенсуса Raft →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'71. Выборы лидера (Leader Election) в распределенных системах ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter72_html(chapters):
    active_chapter_num = 72
    current_exercises = ch72_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 72</div>
        <h1 class="hero-title">Протокол консенсуса Raft</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по алгоритму распределенного консенсуса Raft на Go: от математической спецификации Диего Онгаро до высоконагруженных промышленных реализаций (hashicorp/raft и etcd/raft). Архитектурные роли (Leader, Follower, Candidate), жизненный цикл Term и рандомизированный ElectionTimeout. Структура RPC-сообщений RequestVote и AppendEntries, инварианты Election Safety, Leader Append-Only и Log Matching Property. Репликация конечного автомата (FSM), тотальный порядок логов (Total Order), commitIndex и lastApplied. Усечение логов (Log Compaction), автоматические снапшоты (SnapshotThreshold) и потоковая передача InstallSnapshot. Расширения протокола: Pre-Vote для нейтрализации Disruptive Servers, ReadIndex и Lease Read для линеаризуемого чтения без записи на диск, Single-Server Membership Changes (AddVoter, DemoteVoter, RemoveServer). Архитектура Multi-Raft и шардирование (CockroachDB, TiKV), детерминированное тестирование консенсуса и концептуальный переход к распределенным блокировкам.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Фундамент Raft, конечные автоматы FSM и роли узлов (Упражнения 1–20)"),
        (21, "Раздел 2: Репликация логов, CommitIndex, сетевой транспорт и бутстрап (Упражнения 21–41)"),
        (42, "Раздел 3: Продвинутые оптимизации: Pre-Vote, ReadIndex, Multi-Raft и Снапшоты (Упражнения 42–62)"),
        (63, "Раздел 4: Отказоустойчивость, Chaos Testing, Fencing и сетевой перенос (Упражнения 63–83)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 72!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы досконально освоили устройство протокола Raft: от математических инвариантов консенсуса, репликации логов и конечных автоматов до создания снапшотов, Pre-Vote фазы, линейного чтения ReadIndex и построения отказоустойчивых кластеров высокой доступности.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter71.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 71 Выборы лидера (Leader Election)</a>
            <a href="chapter73.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 73 Распределенные блокировки и Fencing Tokens →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'72. Протокол консенсуса Raft ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter73_html(chapters):
    active_chapter_num = 73
    current_exercises = ch73_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 73</div>
        <h1 class="hero-title">Распределенные блокировки и Fencing Tokens</h1>
        <p class="hero-desc">
            Фундаментальное и прикладное руководство по проектированию, реализации и эксплуатации распределенных блокировок (Distributed Locks) в высоконагруженных микросервисных архитектурах на Go. Анализ базового мьютекса в Redis (SET resource_name my_random_value NX PX ttl), атомарное освобождение через Lua-скрипты и фоновые процессы автоматического продления аренды (Watchdog / KeepAlive). Критический разбор алгоритма Redlock: математическая полемика Мартина Клеппмана (Martin Kleppmann) и Сальваторе Санфилиппо (antirez), проблемы асинхронной репликации, сдвига физических часов (Clock Skew) и паузы сборщика мусора (Stop-The-World GC Pause). Полнофункциональная распределенная координация через etcd (go.etcd.io/etcd/client/v3/concurrency): создание аренды (Lease), транзакции атомарного сравнения ревизий Txn (If CreateRevision == 0) и реактивное ожидание освобождения через etcd Watch API без busy-polling нагрузки. Блокировки в HashiCorp Consul на основе сессий (Session API) и параметра ModifyIndex. Концепция и реализация Fencing Tokens (ограждающих монотонных токенов): сквозная передача токена в хранилище (PostgreSQL / S3), паттерн Guard Row в реляционной СУБД (INSERT ... ON CONFLICT DO UPDATE с инкрементом токена и проверкой в WHERE), отсечение запоздалых записей зомби-воркеров и 100% защита от катастрофы Split-Brain. Архитектурные паттерны: минимизация критической секции (Lock Minimization), иерархия блокировок (Lock Ordering / Lock Hierarchy) для предотвращения распределенных дедлоков, комбинация распределенных блокировок с ключами идемпотентности (Idempotency Keys), распределенные семафоры (Distributed Semaphores на Redis ZSET), мониторинг Lock Contention в Prometheus и построение высоконадежного распределенного диспетчера задач.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Базовые Redis Lock, Lua-скрипты, Watchdog и уязвимость асинхронной репликации (Упражнения 1–17)"),
        (18, "Раздел 2: Redlock controversy, etcd concurrency.Mutex, Consul locks и Backoff Jitter (Упражнения 18–34)"),
        (35, "Раздел 3: Fencing Tokens, защита от GC Pause, Guard Row и распределенный планировщик (Упражнения 35–51)"),
        (52, "Раздел 4: Распределенные семафоры, Lock Hierarchy, etcd Leases и финальный проект (Упражнения 52–68)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 73!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы глубоко и всесторонне освоили распределенные блокировки и Fencing Tokens: от Redis SET NX PX и Lua-скриптов до etcd concurrency, сессий Consul, Guard Row в PostgreSQL, защиты от Split-Brain и построения отказоустойчивых планировщиков корпоративного уровня.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter72.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 72 Протокол консенсуса Raft</a>
            <a href="chapter74.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #0b1120; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 74 Cache-friendly структуры данных и выравнивание памяти →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'73. Распределенные блокировки и Fencing Tokens ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter74_html(chapters):
    active_chapter_num = 74
    current_exercises = ch74_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 74</div>
        <h1 class="hero-title">Cache-friendly структуры данных и выравнивание памяти</h1>
        <p class="hero-desc">
            Исчерпывающее практическое и теоретическое руководство по микроархитектурной оптимизации структур данных в Go под современные иерархии кэш-памяти процессоров (L1, L2, L3, TLB). Анатомия 64-байтной кэш-линии ЦПУ и механика выравнивания полей структур (Memory Alignment & Padding). Устранение катастрофического феномена False Sharing (паразитного разделения строк кэша) и межъядерных инвалидаций (Cache Line Bouncing) в протоколах когерентности MESI/MOESI. Профилирование промахов кэша и метрики HITM с помощью низкоуровневой утилиты Linux perf c2c и perf stat. Data-Oriented Design (DOD): всестороннее сравнение Array of Structures (AoS), Struct of Arrays (SoA) и гибридного подхода AoSoA (Chunked Tiling) для аппаратной SIMD-векторизации (AVX2/Neon). Оптимизация многомерных массивов: физическая природа деградации Column-Major обхода, разрушение TLB и работа аппаратного потокового префетчера (Stream Prefetcher). Сравнение кэш-локальности B-деревьев против бинарных деревьев поиска (BST) и устранение задержек Pointer Chasing. Продвинутые кэш-эффективные структуры: хэш-таблицы с открытой адресацией (Open Addressing), алгоритм Robin Hood Hashing и революционная архитектура Swiss Tables (Google Abseil / Go 1.24+ swissmap). Раскладка Эйтзингера (Eytzinger / BFS layout) и кэш-независимые структуры ван Эмде Боаса (van Emde Boas layout). Hot/Cold Splitting, String Arenas, сжатие указателей (Pointer Compression до 32-bit offset) и Zero-Copy плоская бинарная сериализация (FlatBuffers / SBE). Оптимизация пауз сборщика мусора через структуры без указателей (Pointer-Free noscan spans). Учет топологии NUMA на многосокетных серверах, модель Roofline (Memory-Bound vs Compute-Bound), строгое статистическое тестирование через benchstat и проектирование высокопроизводительных сетевых сокетов в стиле gnet/evio.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Выравнивание памяти, Padding и анатомия структур (Упражнения 1–25)"),
        (26, "Раздел 2: Кэш-линии процессора, False Sharing и Data-Oriented Design (AoS vs SoA) (Упражнения 26–50)"),
        (51, "Раздел 3: Аппаратный Prefetcher, ассоциативность кэша и SIMD-выравнивание (Упражнения 51–75)"),
        (76, "Раздел 4: Cache-friendly алгоритмы, NUMA-оптимизация и профилирование perf (Упражнения 76–99)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 74!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы глубоко изучили микроархитектуру современных процессоров и принципы построения Cache-friendly систем: от выравнивания структур и устранения False Sharing до Data-Oriented Design, Swiss Tables, лейаута Эйтзингера, String Arenas, NUMA-топологии и модели Roofline.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter73.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 73 Распределенные блокировки и Fencing Tokens</a>
            <a href="chapter75.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #040d21; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 75 Lock-free структуры данных →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'74. Cache-friendly структуры данных и выравнивание памяти ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter75_html(chapters):
    active_chapter_num = 75
    current_exercises = ch75_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 75</div>
        <h1 class="hero-title">Lock-free структуры данных</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по проектированию и реализации неблокирующих (Lock-Free и Wait-Free) структур данных в Go на базе пакета sync/atomic и низкоуровневой модели памяти (Go Memory Model). Атомарные примитивы современного процессора: Compare-And-Swap (CAS), Fetch-And-Add (XADD), Atomic Load/Store и семантика Sequential Consistency. Разработка неблокирующего стека Трейбера (Treiber Stack) и структуры очереди Майкла-Скотта (Michael-Scott Queue / MS-Queue) с фиктивным головным узлом (Dummy Sentinel Node). Глубокий анализ классической проблемы ABA: механизмы разрушения структур данных при возврате узлов, решения через версионированные ссылки (Tagged Pointers), упакованные дескрипторы и сопоставление со сборщиком мусора Go. Принципы безопасного управления памятью: Epoch-Based Reclamation (EBR), Hazard Pointers и Read-Copy-Update (RCU) через atomic.Pointer[T]. Архитектура кольцевых буферов (Ring Buffers): ультрабыстрый Single-Producer Single-Consumer (SPSC) буфер без CAS, подавление паразитного разделения кэш-линий (False Sharing) через 64-байтный Cache Line Padding, локальное кэширование индексов (Cached Head/Tail) и побитовая адресация степени двойки (Power-of-2). Промышленная реализация многопоточной очереди Дмитрия Вьюкова (Vyukov Bounded MPMC Queue) с монотонными Sequence Numbers для каждого слота. Шаблон LMAX Disruptor: предварительно аллоцированные кольца, курсоры последовательностей и пакетная обработка (Batch Operations). Политики противодавления (Backpressure): Block, Drop Oldest (кольцевая перезапись) и Drop Newest. Профилирование динамики CAS-циклов: лавины повторов (CAS Retry Storms), адаптивный экспоненциальный откат (Exponential Backoff with Jitter), бенчмаркинг против sync.Mutex и финальный High-Performance Message Passing Framework.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Базовые атомики, Spinlock и Treiber Stack (Упражнения 1–19)"),
        (20, "Раздел 2: Проблема ABA, Tagged Pointers и SPSC Ring Buffer (Упражнения 20–38)"),
        (39, "Раздел 3: Memory Ordering, MS-Queue и MPMC Ring Buffer (Упражнения 39–57)"),
        (58, "Раздел 4: Продвинутые паттерны: RCU, Hazard Pointers, Backpressure и Финальный фреймворк (Упражнения 58–75)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 75!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили проектирование Lock-free структур данных: от атомиков, модели памяти Go и Treiber Stack до устранения проблемы ABA, SPSC и MPMC очередей Вьюкова, LMAX Disruptor, стратегий Backpressure и финального фреймворка передачи сообщений.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter74.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 74 Cache-friendly структуры данных и выравнивание памяти</a>
            <a href="chapter76.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #040d21; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 76 Ассемблер Go (Plan 9 Assembly) и SIMD →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'75. Lock-free структуры данных ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter76_html(chapters):
    active_chapter_num = 76
    current_exercises = ch76_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 76</div>
        <h1 class="hero-title">Ассемблер Go (Plan 9 Assembly) и SIMD</h1>
        <p class="hero-desc">
            Глубокое инженерное погружение в низкоуровневую разработку на диалекте Plan 9 Assembly и аппаратную векторизацию SIMD (SSE, AVX2, AVX-512, ARM NEON) в среде Go. Анатомия машинного кода и анализ ассемблерных листингов с помощью go build -gcflags="-S", go tool objdump и флагов компилятора SSA. Эволюция соглашений о вызовах: стек ABI0 против регистровой модели ABIInternal (Go 1.17+), ABI Wrappers и зарезервированные регистры (R14 для горутины *g). Оптимизация устранения проверок границ срезов (Bounds Check Elimination — BCE). Правила оформления ассемблерных файлов .s: псевдорегистры SB, FP, SP, фреймы $locals-args, прагмы //go:noescape и //go:nosplit, заголовочные файлы textflag.h и go_asm.h. Векторные расширения процессора: 128-битные регистры XMM и 256-битные YMM. Векторная арифметика VMOVUPS, VADDPS, VPADDD, Fused Multiply-Add (VFMADD231PS) и горизонтальная редукция через VEXTRACTF128 и VHADDPS. Обязательная очистка состояния VZEROUPPER для предотвращения штрафа перехода AVX-SSE. Branchless программирование (инструкции CMOV, битовые трюки SARQ + XORQ). Промышленная кодогенерация через avo: распределение виртуальных регистров, расчет стека и устранение человеческих ошибок. Архитектура сверхбыстрого векторного парсинга simdjson и оптимизация TLB через Huge Pages (2 МБ / 1 ГБ).
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Основы Plan 9 Assembly, ABI и соглашения о вызовах (Упражнения 1–12)"),
        (13, "Раздел 2: Векторизация SIMD (SSE, AVX2) и Fused Multiply-Add (Упражнения 13–24)"),
        (25, "Раздел 3: Инструменты генерации avo, JIT, Huge Pages и Профилирование perf (Упражнения 25–35)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 76!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы освоили Plan 9 Assembly и SIMD-векторизацию в Go: от соглашений ABI0/ABIInternal и псевдорегистров до инструкций AVX2/FMA, кодогенерации с библиотекой avo, Branchless-алгоритмов и оптимизации Huge Pages.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter75.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 75 Lock-free структуры данных</a>
            <a href="chapter77.html" style="display: inline-flex; align-items: center; gap: 6px; background: #00add8; color: #040d21; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none;">Глава 77 Высокопроизводительные сетевые фреймворки (gnet, evio) →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'76. Ассемблер Go (Plan 9 Assembly) и SIMD ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter77_html(chapters):
    active_chapter_num = 77
    current_exercises = ch77_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 77</div>
        <h1 class="hero-title">Высокопроизводительные сетевые фреймворки (gnet, evio)</h1>
        <p class="hero-desc">
            Глубокое инженерное руководство по проектированию и эксплуатации ультравысокопроизводительных сетевых сервисов на базе событийно-ориентированных движков gnet и evio в обход стандартной модели Go goroutine-per-connection. Анатомия барьера C10M и системные вызовы Linux epoll (Edge-Triggered vs Level-Triggered). Архитектурный паттерн Multi-Reactor: разделение на Main Reactor (Acceptor Loop) и Sub-Reactors (Worker Loops), жесткая привязка потоков ОС к ядрам CPU (LockOSThread, CPU Affinity) и подавление конкуренции за сокет через SO_REUSEPORT. Технологии Zero-Copy и Zero-Allocation: работа с эластичным кольцевым буфером RingBuffer, векторный ввод-вывод writev (Scatter-Gather I/O), прямая передача данных через sendfile и повторное использование памяти через sync.Pool. Проектирование бинарных протоколов с префиксом длины (Length-Prefixed Framing) и потокобезопасная разгрузка бизнес-логики в Worker Pool через неблокирующий AsyncWrite. Защита от перегрузок: реализация паттернов Backpressure, Load Shedding и TCP Flow Control. Разработка собственного сервера баз данных класса Redis с поддержкой протокола RESP под нагрузку 100 000 одновременных соединений при расходе памяти всего 15–20 МБ.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Реакторы, сокетные вызовы и основы gnet/evio (Упражнения 1–10)"),
        (11, "Раздел 2: Многопоточность, C10K бенчмарки и Worker Pools (Упражнения 11–21)"),
        (22, "Раздел 3: Продвинутые протоколы, Zero-Copy и Финальный HFT шлюз (Упражнения 22–32)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 77!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили событийно-ориентированную сетевую разработку: от системных вызовов epoll и многопоточного Multi-Reactor gnet до протоколов кадрирования, Worker Pools, Zero-Copy парсинга RESP и проектирования сверхбыстрого HFT шлюза.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter76.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 76 Ассемблер Go (Plan 9 Assembly) и SIMD</a>
            <a href="chapter78.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #0284c7;">Глава 78 Облачные хранилища, Envelope Encryption и KMS →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'77. Высокопроизводительные сетевые фреймворки (gnet, evio) ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter78_html(chapters):
    active_chapter_num = 78
    current_exercises = ch78_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 78</div>
        <h1 class="hero-title">Облачные хранилища, Envelope Encryption и KMS</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по криптографической защите данных в распределенных объектных хранилищах (AWS S3, MinIO, Ceph, Google Cloud Storage, Azure Blob). Архитектурный паттерн Envelope Encryption: разделение ключей шифрования данных (DEK) и мастер-ключей (KEK), исключение вендорных блокировок и преодоление лимита 4 КБ в облачных KMS (AWS KMS, GCP Cloud KMS, Azure Key Vault, HashiCorp Vault Transit). Механика аппаратных модулей безопасности (HSM / CloudHSM, FIPS 140-2 Level 3). Сквозной протокол S3 Multipart Upload: параллельная передача гигабайтных файлов через семафорные воркер-пулы и errgroup, вычисление аппаратных контрольных сумм CRC32C и SHA-256, отказоустойчивый Resume и гарантированная очистка брошенных частей через AbortMultipartUpload и S3 Lifecycle Rules. Безопасная временная раздача через Presigned URLs без публичного доступа к бакетам. Неизменяемые WORM хранилища (S3 Object Lock Compliance Mode), автоматическая ежегодная ротация ключей с сохранением обратной совместимости, GDPR Crypto-shredding (Право на забвение) и сквозная трассировка OpenTelemetry с контекстом W3C.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Основы S3, Envelope Encryption и интеграция с KMS (Упражнения 1–24)"),
        (25, "Раздел 2: Multipart Upload, Streaming Encryption и Presigned URLs (Упражнения 25–50)"),
        (51, "Раздел 3: Продвинутые политики KMS, ротация ключей и WORM Object Lock (Упражнения 51–72)"),
        (73, "Раздел 4: Cloud-Native архитектура, Crypto-shredding и Итоговый сервис (Упражнения 73–95)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 78!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы освоили полный стек облачной безопасности данных: от Envelope Encryption и AWS/GCP KMS до параллельного Multipart Upload, S3 Lifecycle, Presigned URLs, WORM Object Lock и паттерна Crypto-shredding.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter77.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 77 Высокопроизводительные сетевые фреймворки (gnet, evio)</a>
            <a href="chapter79.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #0284c7;">Глава 79 Интеграция с Service Mesh (Istio, Linkerd) и mTLS →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'78. Облачные хранилища, Envelope Encryption и KMS ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter79_html(chapters):
    active_chapter_num = 79
    current_exercises = ch79_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 79</div>
        <h1 class="hero-title">Интеграция с Service Mesh (Istio, Linkerd) и mTLS</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по интеграции Go-микросервисов с Service Mesh (Istio, Linkerd) и реализации распределенной архитектуры Zero Trust. Data Plane под микроскопом: механизмы перехвата сокетов через сетевые таблицы Linux iptables (цепочки PREROUTING и OUTPUT, getsockopt с SO_ORIGINAL_DST) и сокетные eBPF программы ядра. Архитектурное сравнение Envoy Sidecar (C++) и Linkerd micro-proxy (Rust): неблокирующие event loops epoll, HTTP/2 мультиплексирование, EWMA балансировка и динамическая xDS/SDS синхронизация с istiod. Тотальный взаимный TLS (mTLS) в режиме STRICT: стандарт SPIFFE/SPIRE, валидация SAN URI сертификатов SVID и автоматическая ротация ключей через Citadel/Linkerd Identity без даунтайма. L7 Traffic Management: декларативные правила VirtualService и DestinationRule, весовые канареечные релизы (Canary Deployments), маршрутизация по HTTP-заголовкам (X-Canary, X-Beta-User), Traffic Mirroring (Shadowing), Egress Gateway с TLS Origination и Multi-Cluster сетка через East-West Gateway. Отказоустойчивость: автоматические ретраи с экспоненциальным бэкоффом и Full Jitter, предотвращение Retry Amplification и штормов повторов, пассивный Circuit Breaker (Outlier Detection) с исключением сбойных подов, gRPC Client Keepalive и серверная EnforcementPolicy. Распределенный Rate Limiting через Envoy RLS gRPC, WASM-фильтры на TinyGo и сквозная трассировка OpenTelemetry с контекстами W3C (traceparent, tracestate) и B3 (Zipkin).
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура Sidecar, iptables, mTLS и проброс контекста трассировки (Упражнения 1–20)"),
        (21, "Раздел 2: Управление L7-трафиком, Egress, gRPC Keepalive и WASM фильтры (Упражнения 21–40)"),
        (41, "Раздел 3: JWT, телеметрия, архитектура Linkerd и SPIFFE авторизация (Упражнения 41–60)"),
        (61, "Раздел 4: Производительность, бенчмаркинг, Disaster Recovery и Capstone Master Service (Упражнения 61–80)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 79!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы освоили полный стек облачной интеграции с Service Mesh: от архитектуры Sidecar, iptables перехвата и Zero Trust mTLS до канареечной маршрутизации VirtualService, Outlier Detection, Envoy RLS, WASM-фильтров на TinyGo и сквозного проброса трейсов W3C/B3.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter78.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 78 Облачные хранилища, Envelope Encryption и KMS</a>
            <a href="chapter80.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #0284c7;">Глава 80 Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'79. Интеграция с Service Mesh (Istio, Linkerd) и mTLS ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter80_html(chapters):
    active_chapter_num = 80
    current_exercises = ch80_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 80</div>
        <h1 class="hero-title">Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive</h1>
        <p class="hero-desc">
            Глубокое инженерное руководство по сквозной распределенной трассировке (Distributed Tracing) и сетевой надежности gRPC в высоконагруженных Cloud-Native микросервисах. Анатомия стандартов W3C Trace Context (RFC 9421) и Zipkin B3: побайтовый разбор и валидация 55-байтного заголовка traceparent (version, trace_id, parent_id, trace_flags), управление упорядоченным списком пар tracestate и передача сквозных метаданных W3C Baggage. Мультипротокольная контекстная пропагация (OpenTelemetry Propagators) через любые архитектурные границы: HTTP/1.1 заголовки, gRPC metadata (HTTP/2 HEADERS), брокеры сообщений Apache Kafka (Record Headers) и NATS (Msg Headers). Решение фундаментальной проблемы балансировки gRPC за L4 балансировщиками (K8s Service ClusterIP, AWS NLB): залипание постоянных мультиплексированных соединений, клиентский Round Robin через Headless Service и L7 проксирование через Envoy Service Mesh. Внутреннее устройство gRPC Keepalive: активное зондирование сокетов 8-байтными HTTP/2 PING-фреймами (ClientParameters: Time, Timeout, PermitWithoutStream), мгновенное распознавание полуоткрытых сокетов (dead connections) в обход 15-минутных таймаутов Linux TCP (tcp_retries2), серверная политика защиты от DoS-атак (EnforcementPolicy: MinTime, PermitWithoutStream, штрафные страйки) и плавная ротация сокетов через MaxConnectionAge, MaxConnectionAgeGrace и кадры GOAWAY с добавлением Jitter. Искусство Cloud-Native Graceful Draining в Kubernetes: устранение ошибок 502/RST и Envoy 503 UC, синхронизация удаления из EndpointSlice и обновления правил iptables/IPVS, координация lifecycle.preStop хука, разделение LivenessProbe (только рантайм) и ReadinessProbe (503 при дренаже), а также безопасная остановка серверов (GracefulStop с жестким дедлайном Stop) и долгоживущих стримов по EOF.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: W3C Trace Context, форматы заголовков и основы gRPC Keepalive (Упражнения 1–20)"),
        (21, "Раздел 2: Kubernetes Lifecycle, Graceful Draining, PreStop и контекстная передача (Упражнения 21–38)"),
        (39, "Раздел 3: Multi-Format Propagation, Service Mesh, SPIFFE Zero-Trust и Channelz (Упражнения 39–58)"),
        (59, "Раздел 4: Rate Limiting, Cache Stampede Shield, Chaos Engineering и Capstone Service (Упражнения 59–76)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 80!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили протоколы распределенной трассировки W3C Trace Context и Zipkin B3, клиентские и серверные политики gRPC Keepalive, ликвидацию сетевых гонок в Kubernetes с помощью Graceful Draining и PreStop хуков, а также построение надежных микросервисных архитектур.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter79.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 79 Интеграция с Service Mesh (Istio, Linkerd) и mTLS</a>
            <a href="chapter81.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #0284c7;">Глава 81 Безопасность цепочки поставок (Supply Chain Security) и SBOM →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'80. Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter81_html(chapters):
    active_chapter_num = 81
    current_exercises = ch81_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 81</div>
        <h1 class="hero-title">Безопасность цепочки поставок (Supply Chain Security) и SBOM</h1>
        <p class="hero-desc">
            Фундаментальное инженерное руководство по безопасности цепочки поставок программного обеспечения (Supply Chain Security) и паспортизации артефактов (SBOM) в экосистеме Go. Анатомия защиты дерева зависимостей: криптографическая база контрольных сумм sum.golang.org (GOSUMDB), аудит go.sum, изоляция приватных модулей через GOPRIVATE и GONOSUMDB, предотвращение атак Dependency Confusion и тайпосквоттинга. Практика полного вендоринга (go mod vendor) для автономных Air-Gapped контуров, семантический версионинг (MVS) и автоматический аудит лицензионной чистоты (go-licenses, защита от вирусных GPL-лицензий). Глубокий анализ уязвимостей с учетом достижимости в графе вызовов (reachability analysis) через официальный инструмент govulncheck. Генерация машиночитаемых паспортов ПО (SBOM) в международных стандартах CycloneDX 1.5 и SPDX 2.3 утилитой Anchore Syft с соблюдением требований директивы NTIA. Криптографическое подписание контейнерных образов, бинарников и документов SBOM через Sigstore Cosign, аттестации in-toto, верификация в Kubernetes через Policy Controller и достижение стандартов герметичности сборок SLSA Level 3. Развертывание и тюнинг корпоративных прокси-серверов Athens и JFrog Artifactory, безопасная очистка кэша модулей, харденинг сборочных раннеров CI/CD и безопасное удаление конфиденциальных данных из оперативной памяти процесса.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Защита зависимостей, go.sum, GOPRIVATE и сканирование уязвимостей (Упражнения 1–34)"),
        (35, "Раздел 2: Воспроизводимые сборки, стандарты SBOM (SPDX/CycloneDX) и утилита Syft (Упражнения 35–68)"),
        (69, "Раздел 3: Подписание образов через Cosign, аттестации in-toto и SLSA Level 3 (Упражнения 69–102)"),
        (103, "Раздел 4: Корпоративные прокси (Athens/Artifactory), вендоринг и рантайм-харднинг (Упражнения 103–136)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 81!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили защиту цепочки поставок ПО, контроль контрольных сумм и изоляцию приватных репозиториев, генерацию спецификаций SBOM, подписание образов утилитой Cosign и построение надежного защищенного конвейера DevSecOps.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter80.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 80 Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive</a>
            <a href="chapter82.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #0284c7;">Глава 82 Защита сетевых сокетов и противодействие DoS-атакам →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'81. Безопасность цепочки поставок (Supply Chain Security) и SBOM ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter82_html(chapters):
    active_chapter_num = 82
    current_exercises = ch82_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 82</div>
        <h1 class="hero-title">Защита сетевых сокетов и противодействие DoS-атакам</h1>
        <p class="hero-desc">
            Глубокое практическое руководство по низкоуровневой защите сетевых сокетов, отражению DoS/DDoS-атак и тюнингу сетевого стека Linux в приложениях на Go. Анатомия асимметричных атак исчерпания ресурсов: механика Slowloris (удержание медленных соединений), Slow Read / Tarpit (медленное чтение ответов) и Header Bombing (атака гигантскими заголовками). Построение эшелонированной защиты прикладного уровня: обязательная конфигурация таймаутов http.Server (ReadHeaderTimeout, ReadTimeout, WriteTimeout, IdleTimeout), разделение лимитов для файловых загрузчиков и использование http.MaxBytesReader для предотвращения OOM. Харденинг сетевых сокетов ядра через net.ListenConfig: шардирование сокетов SO_REUSEPORT для параллелизации Accept по ядрам CPU, задержка пробуждения Go через TCP_DEFER_ACCEPT, ускорение рукопожатий TCP Fast Open (TFO) и быстрое обнаружение сетевых сбоев через TCP_USER_TIMEOUT и TCP Keep-Alive. Отражение объемных атак на уровне ядра: криптографические SYN Cookies (sysctl net.ipv4.tcp_syncookies), тюнинг somaxconn и tcp_max_syn_backlog, обход переполнения conntrack через правила NOTRACK в iptables. Ограничение скорости (Rate Limiting on Accept) и семафоры конкурентности со сбросом нагрузки (Load Shedding HTTP 503). Изоляция системных вызовов через Seccomp (блокировка ptrace и network egress), мандатный контроль доступа AppArmor, анализ профилей ядра через strace и запуск на стандартном порту 80 без прав root через Linux Capabilities (cap_net_bind_service).
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Механика DoS-атак Slowloris, тайм-ауты http.Server и защита от медленных клиентов (Упражнения 1–14)"),
        (15, "Раздел 2: Ограничение соединений (netutil, atomic), TLS-харденинг и тюнинг Keep-Alive (Упражнения 15–28)"),
        (29, "Раздел 3: Низкоуровневые оптимизации ядра: SO_REUSEPORT, SYN Cookies, TCP Fast Open и TCP_DEFER_ACCEPT (Упражнения 29–41)"),
        (42, "Раздел 4: Системная изоляция Seccomp, защита от перегрузок (Load Shedding), AppArmor и The Unbreakable Server (Упражнения 42–55)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 32px; background: #131d33; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
        <h3 style="color: #38bdf8; font-size: 20px; margin-bottom: 12px;">Поздравляем с освоением главы 82!</h3>
        <p style="color: #94a3b8; font-size: 15px; max-width: 650px; margin: 0 auto 24px auto; line-height: 1.6;">
            Вы в совершенстве освоили низкоуровневую защиту сокетов, парирование атак Slowloris и SYN Flood, тонкий тюнинг сетевых параметров ядра Linux, шардирование портов через SO_REUSEPORT и проектирование неуязвимых HighLoad-серверов на Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter81.html" style="display: inline-flex; align-items: center; gap: 6px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #334155;">← Глава 81 Безопасность цепочки поставок (Supply Chain Security) и SBOM</a>
            <a href="chapter83.html" style="display: inline-flex; align-items: center; gap: 6px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: 1px solid #0284c7;">Глава 83 Системная изоляция, Seccomp и Linux Capabilities →</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'82. Защита сетевых сокетов и противодействие DoS-атакам ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter83_html(chapters):
    active_chapter_num = 83
    current_exercises = ch83_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content">')
    
    # Hero Section
    content_parts.append(f"""
    <section class="hero-section">
        <div class="hero-tag">Глава 83 • Финал курса</div>
        <h1 class="hero-title">Системная изоляция, Seccomp и Linux Capabilities</h1>
        <p class="hero-desc">
            Фундаментальное практическое руководство по низкоуровневой системной изоляции процессов, ограничению полномочий ядра и безопасной архитектуре контейнеризации в Go. Управление системными ресурсами: аудит файловых дескрипторов (ulimit NOFILE) и отражение атак исчерпания ресурсов (EMFILE DoS). Дискретные возможности ядра (Linux Capabilities): привязка к привилегированным портам без прав root через CAP_NET_BIND_SERVICE, низкоуровневое манипулирование масками Permitted, Effective, Inheritable, Bounding и Ambient через capset и prctl, сброс избыточных прав (Drop Privileges) до непривилегированного пользователя с использованием syscall.AllThreadsSyscall. Системный файрвол Seccomp (Secure Computing Mode): построение бескомпромиссных белых списков (Zero Trust Whitelist) через libseccomp-golang и ручной байткод cBPF (unix.SockFilter) без CGO, перехват и блокировка векторов RCE (запрет execve/execveat с фатальным сигналом SIGSYS), перехват сисколлов в пространстве пользователя через seccomp_unotify в ядре Linux 5.0+. Профилирование системных вызовов Go Runtime (futex, clone3, mmap, epoll_pwait, sigaltstack) с помощью strace и генерация декларативных OCI Seccomp JSON-профилей для Docker и Kubernetes. Мандатный контроль доступа (MAC) AppArmor: ограничение файловой системы в режиме Enforce и сетевой изоляции egress. Неизменяемая инфраструктура: запуск контейнеров с Read-Only Root Filesystem и безопасной tmpfs. Изоляция файловых пространств: классический chroot против атомарного pivot_root. Управление ресурсами ядра: изоляция сетевых пространств имен (Network Namespaces) и контрольные группы cgroup v2 (memory.max, cpu.max, защита от Fork Bomb через pids.max). Запуск в Kubernetes в профиле Restricted (PodSecurityContext, drop ALL). Мониторинг безопасности ядра в реальном времени через eBPF (bpf2go, ring buffer, трассировка sys_enter_connect). Аппаратная виртуализация и песочница Google gVisor (runsc): эмуляция системных вызовов ядром Sentry на Go и предотвращение Container Escape. Реактивная защита от атак перебора с динамическим баном в iptables через Fail2Ban.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Лимиты ресурсов (ulimit), привилегия CAP_NET_BIND_SERVICE и основы Seccomp (Упражнения 1–7)"),
        (8, "Раздел 2: Профилирование сисколлов (strace), генерация OCI-профилей и отбрасывание прав (Упражнения 8–14)"),
        (15, "Раздел 3: Минимальные capabilities, профили AppArmor, изоляция chroot и cgroup v2 (Упражнения 15–21)"),
        (22, "Раздел 4: Zero Trust в Kubernetes, рантайм eBPF, песочница gVisor и интеграция с Fail2Ban (Упражнения 22–28)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer (Final chapter congratulations!)
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">🎉 Грандиозный финал • Все 83 главы пройдены!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с полным освоением всего учебника Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы преодолели грандиозный путь от базовых пакетов, синтаксиса и слайсов до сложнейших глубин рантайма Go (GMP, GC триколор, Netpoller), высоконагруженных распределенных систем (Raft, Saga, Outbox, CDC), сетевой оптимизации сокетов (SO_REUSEPORT, TCP Fast Open) и системной изоляции ядра Linux (Seccomp, Linux Capabilities, cgroups v2, eBPF и gVisor).
            <br><br>
            <strong>Все 7 071 практическое упражнение</strong> вооружили вас инженерными знаниями уровня <strong>Lead / Principal Go Engineer</strong> в ведущих технологических компаниях!
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter82.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 82 Защита сетевых сокетов и противодействие DoS-атакам</a>
            <a href="chapter84.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 84 CQRS и Event Sourcing на Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'83. Системная изоляция, Seccomp и Linux Capabilities ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter84_html(chapters):
    active_chapter_num = 84
    current_exercises = ch84_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 84 • Advanced Distributed Systems & Event-Driven Architecture</div>
        <h1 class="hero-title">CQRS и Event Sourcing на Go</h1>
        <p class="hero-desc">
            Глубокое практическое руководство по проектированию систем на основе Command Query Responsibility Segregation (CQRS) и Event Sourcing на языке Go. Архитектура доменных агрегатов и неизменяемых логов событий (Append-Only Event Store) на PostgreSQL с оптимистической блокировкой версий и защитой от конфликтов конкурентной записи. Высокопроизводительная регидрация состояния агрегатов, создание и инвалидация снимков (Snapshots) для ускорения загрузки длинных потоков событий. Построение синхронных и асинхронных проекций (Read Models), отслеживание смещений (Checkpoints), гарантии доставки At-Least-Once и идемпотентное обновление материализованных представлений в PostgreSQL и полнотекстовом поисковом движке Elasticsearch. Управление эволюцией схемы событий (Schema Evolution, Event Upcasting на лету) без деградации исторических данных. Надежная интеграция с транзакционным Outbox-паттерном, оркестрация распределенных транзакций и саг с компенсирующими транзакциями при сбоях. Комплаенс с требованиями приватности GDPR/CCPA через криптографическое уничтожение ключей (Crypto-shredding), CDC-репликация событий через Debezium, распределенная трассировка W3C/OpenTelemetry через границы команд и проекций, а также боевой аудит производительности и устойчивости систем под экстремальной нагрузкой.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Фундамент CQRS, агрегаты, регидрация и персистентность Event Store в PostgreSQL (Упражнения 1–11)"),
        (12, "Раздел 2: Проекции Read Model, чекпоинты, эволюция схем (Upcasting) и транзакционный Outbox (Упражнения 12–22)"),
        (23, "Раздел 3: Конкурентный доступ, оптимистические блокировки, партиционирование и саги с компенсациями (Упражнения 23–34)"),
        (35, "Раздел 4: GDPR/Crypto-shredding, распределенное реплицирование, Observability и BigTech Production (Упражнения 35–45)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 84 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением CQRS и Event Sourcing на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы глубоко освоили доменные агрегаты, архитектуру событийных хранилищ с защитой от гонок версий, снапшоты, асинхронные и синхронные проекции в PostgreSQL и Elasticsearch, эволюцию схем без миграций и криптографическое удаление персональных данных.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter83.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 83 Системная изоляция, Seccomp и Linux Capabilities</a>
            <a href="chapter85.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 85 Многоуровневое кэширование (L1/L2) и распределенная когерентность →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'84. CQRS и Event Sourcing на Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter85_html(chapters):
    active_chapter_num = 85
    current_exercises = ch85_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 85 • Advanced Distributed Storage, Caching & Coherence</div>
        <h1 class="hero-title">Многоуровневое кэширование (L1-L2) и распределенная когерентность</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по проектированию сверхпроизводительных систем многоуровневого кэширования (Multi-Level Caching) на языке Go. Организация иерархии памяти: локальный L1-кэш в оперативной памяти процесса (Zero-GC кольцевые буферы BigCache/FreeCache, шардированные структуры с защитой от False Sharing) и распределенный L2-кэш на базе Redis Cluster. Ликвидация эффекта набегающего стада (Cache Stampede / Thundering Herd) с помощью дедупликации вызовов sync/singleflight, отвязки контекстов и алгоритма вероятностного раннего устаревания XFetch. Защита базы данных от пробивания (Cache Penetration) и лавинного устаревания (Cache Avalanche) через фильтры Блума, кэширование Null-Object и центрированный TTL Jitter. Паттерны синхронной (Write-Through) и отложенной асинхронной (Write-Behind) записи с пакетным сбросом на диск. Обеспечение строгой согласованности кэшей (Cache Coherence) через шину Redis Pub/Sub и встроенный серверный трекинг протокола RESP3 (Client-Side Caching). Продвинутые алгоритмы вытеснения TinyLFU/W-TinyLFU, Zero-Copy бинарная сериализация, прозрачное сжатие zstd/lz4, контроль давления памяти (Memory Pressure / GOMEMLIMIT), Circuit Breaker защита от сбоев Redis и проектирование production-ready Enterprise-библиотеки кэша на чистом Go.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура L1/L2, Zero-GC структуры, Cache-Aside и ликвидация Thundering Herd (Упражнения 1–8)"),
        (9, "Раздел 2: Вероятностный XFetch, фильтры Блума, джиттер TTL и инвалидация через Pub/Sub (Упражнения 9–15)"),
        (16, "Раздел 3: Redis RESP3 Tracking, дифференциальный TTL, алгоритмы TinyLFU и Zero-Copy Protobuf (Упражнения 16–23)"),
        (24, "Раздел 4: Метрики Hit Ratio, двойная инвалидация, Circuit Breaker, MGET и Enterprise-библиотека (Упражнения 24–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 85 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением многоуровневого кэширования и когерентности на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы детально изучили архитектуру двухуровневого кэша L1/L2, алгоритмы Zero-GC, ликвидацию Thundering Herd через singleflight и XFetch, защиту от Penetration через фильтры Блума, протокол RESP3 Client-Side Tracking, сжатие пейлоадов и предотвращение рассинхронизации данных в распределенных кластерах.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter84.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 84 CQRS и Event Sourcing на Go</a>
            <a href="chapter86.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 86 Масштабируемые распределенные планировщики и очереди задач →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'85. Многоуровневое кэширование (L1-L2) и распределенная когерентность ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter86_html(chapters):
    active_chapter_num = 86
    current_exercises = ch86_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 86 • Advanced Distributed Systems & Asynchronous Task Processing</div>
        <h1 class="hero-title">Масштабируемые распределенные планировщики и очереди задач</h1>
        <p class="hero-desc">
            Комплексное инженерное руководство по проектированию и эксплуатации высокопроизводительных отказоустойчивых очередей фоновых задач и распределенных планировщиков на языке Go. Сравнительный анализ архитектур хранения: Redis Streams (Consumer Groups, XACK) и Sorted Sets (ZSet для отложенных задач) против очередей на базе PostgreSQL (библиотека River, транзакционная постановка без Dual-Write, конкурентная выборка FOR UPDATE SKIP LOCKED). Механизмы надежности: Heartbeat и обнаружение зависших воркеров, приоритизация (Strict vs Weighted Fair Queuing), планирование отложенных (Scheduled) и периодических (Cron) задач с распределенной синхронизацией. Математически выверенные политики повторов (Exponential Backoff с Full Jitter по алгоритмам AWS), изоляция ядовитых сообщений в Dead Letter Queue (DLQ), версионирование полезной нагрузки (Schema Upcasting), строгая идемпотентность и дедупликация. Управление потоком: распределенный Rate Limiting, честное планирование (Fair Scheduling) между тенантами в Multi-Tenant SaaS, пакетная обработка (Batching / Bulk Insert в ClickHouse), Graceful Shutdown без потери задач, динамическое масштабирование пулов воркеров (Autoscaling по Queue Lag), Backpressure-защита от переполнения брокеров и построение Enterprise менеджера задач на чистом Go.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Фундамент асинхронных очередей, воркер-пулы, Redis Streams/ZSet и PostgreSQL SKIP LOCKED (Упражнения 1–8)"),
        (9, "Раздел 2: Распределенный Cron, Exponential Backoff с Full Jitter, DLQ, дедупликация и автоскейлинг (Упражнения 9–15)"),
        (16, "Раздел 3: Rate Limiting, Fair Scheduling, батчинг, Graceful Shutdown и библиотеки Asynq / River (Упражнения 16–23)"),
        (24, "Раздел 4: Изоляция Poison Pill, Backpressure, профилирование утечек, бенчмарки и Enterprise-менеджер (Упражнения 24–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 86 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением распределенных планировщиков и очередей задач!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы детально освоили архитектуру очередей на Redis и PostgreSQL, конкурентную выборку SKIP LOCKED, восстановление по Heartbeat, справедливое планирование между тенантами, батчинг, библиотеки Asynq и River, а также построение надежного корпоративного менеджера фоновых задач.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter85.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 85 Многоуровневое кэширование (L1-L2) и распределенная когерентность</a>
            <a href="chapter87.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 87 Оркестрация распределенных процессов (Durable Execution) на Temporal.io →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'86. Масштабируемые распределенные планировщики и очереди задач ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter87_html(chapters):
    active_chapter_num = 87
    current_exercises = ch87_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 87 • Advanced Distributed Systems, Durable Execution & Temporal.io</div>
        <h1 class="hero-title">Оркестрация распределенных процессов (Durable Execution) на Temporal.io</h1>
        <p class="hero-desc">
            Фундаментальное руководство по парадигме долговечного исполнения (Durable Execution) и распределенной оркестрации бизнес-процессов на платформе Temporal.io на языке Go. Механика Event Sourcing и Replay детерминизма: почему локальные переменные, циклы, таймеры и стек вызовов восстанавливаются без потери состояния даже при падении серверов. Разделение зон ответственности: кластер Temporal (Frontend, History, Matching) и клиентские воркеры Go SDK. Проектирование Activities: сайд-эффекты, таймауты (StartToClose, ScheduleToStart, ScheduleToClose), экспоненциальный RetryPolicy с Full Jitter, классификация Non-Retryable ошибок и Activity Heartbeating с сохранением чекпоинтов. Управление параллелизмом: workflow.Go, детерминированные каналы, Selector и параллельные Child Workflows с Fan-Out / Fan-In семафором. Взаимодействие с внешним миром: асинхронные Сигналы (Signals), синхронные Запросы (Queries), атомарный Update API (валидация + мутация за 1 round-trip) и паттерн Human-in-the-Loop. Надежность и эволюция: распределенная Сага (Saga Pattern) с компенсациями в NewDisconnectedContext, версионирование (Workflow Versioning, GetVersion, Worker Build IDs) и Replay-тестирование в CI/CD. Продвинутые возможности: Temporal Schedule API, Nexus RPC, кастомные Search Attributes в Elasticsearch, Batch Operations, сквозное шифрование AES-256 (PayloadCodec / Codec Server), мониторинг Prometheus, Multi-Cluster репликация, паттерн Durable Poller и промышленный процессинг международных банковских переводов SWIFT/SEPA.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Парадигма Durable Execution, архитектура Temporal, воркеры и детерминизм (Упражнения 1–12)"),
        (13, "Раздел 2: Сигналы, запросы, таймеры, Human-in-the-Loop, Child Workflows и распределенная Сага (Упражнения 13–25)"),
        (26, "Раздел 3: Мокирование, OTel трассировка, сквозное шифрование, HighLoad тюнинг и Update API (Упражнения 26–37)"),
        (38, "Раздел 4: Checkpoints, Local Activities, mTLS Cloud, Fan-Out, Nexus, Chaos и SWIFT-процессинг (Упражнения 38–50)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 87 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением Durable Execution и Temporal.io!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы полностью овладели архитектурой Temporal, парадигмой долговечного исполнения, гарантиями детерминизма, распределенными сагами, сигналами, запросами, Update API, версионированием через Build ID, сквозным шифрованием и проектированием высоконадежных систем банковского уровня.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter86.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 86 Масштабируемые распределенные планировщики и очереди задач</a>
            <a href="chapter88.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 88 Потоковая обработка данных в реальном времени (Stream Processing) →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'87. Оркестрация распределенных процессов (Durable Execution) на Temporal.io ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter88_html(chapters):
    active_chapter_num = 88
    current_exercises = ch88_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 88 • Advanced Distributed Systems, Real-Time Analytics & Stream Processing</div>
        <h1 class="hero-title">Потоковая обработка данных в реальном времени (Stream Processing)</h1>
        <p class="hero-desc">
            Полное инженерное руководство по проектированию высокопроизводительных распределенных конвейеров потоковой обработки данных на языке Go. Фундаментальные основы: непрерывные бесконечные потоки (Unbounded Streams) против пакетной обработки (Batch), потоковые пайплайны на каналах Go (Fan-In / Fan-Out), решение дилеммы времени (Event Time vs Processing Time vs Ingestion Time) и отсечение сетевых задержек. Управление временем и окнами: генераторы водяных знаков (Bounded Out-Of-Orderness Watermarks), тумблинговые (Tumbling), скользящие (Sliding с Pane-квантованием) и сессионные окна (Session Windows) с динамическим слиянием интервалов. Высокопроизводительное управление состоянием: встроенные LSM-хранилища (Embedded State Stores на базе Pebble и Badger), онлайн-алгоритмы инкрементального свертывания (алгоритм Велфорда для среднего и дисперсии за O(1) памяти) и вероятностный подсчет уникальных пользователей (HyperLogLog). Сложные потоковые паттерны: соединение независимых потоков во временном окне (Stream-Stream Join), обогащение потока данными таблиц (Stream-Table Join / KTable), потоковая дедупликация, обработка запаздывающих событий (Allowed Lateness) и перенаправление в Side Outputs (Dead Letter Stream). Надежность корпоративного уровня: семантика Exactly-Once Processing (EoS), распределенные снимки состояния по алгоритму Чанди-Лэмпорта (Chandy-Lamport Barrier Checkpointing), фреймворк Goka, партиционирование по ключам, адаптивное обратное давление (Backpressure), потоковый детектор аномалий (Z-Score), оконные триггеры (Early Emission), управление State TTL, безопасный повторный прогон истории (Stream Replay), метрики лага Prometheus, lock-free кольцевой буфер LMAX Disruptor, пакетная запись в ClickHouse, Graceful Drain и сквозной боевой сервис мониторинга антифрода (Real-Time Fraud Detection).
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Фундамент потоков, конвейеры, время, водяные знаки и оконные вычисления (Упражнения 1–7)"),
        (8, "Раздел 2: Встроенное состояние, инкрементальная статистика, HLL, соединения потоков и Exactly-Once (Упражнения 8–15)"),
        (16, "Раздел 3: Чекпоинты Чанди-Лэмпорта, Goka, партиционирование, Backpressure, Z-Score и триггеры (Упражнения 16–23)"),
        (24, "Раздел 4: Stream Replay, метрики лага, Disruptor, ClickHouse Sink, Graceful Drain и Fraud Detection (Упражнения 24–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 88 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением потоковой обработки в реальном времени!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы полностью овладели архитектурой распределенной потоковой аналитики: оконными агрегациями, водяными знаками, встроенными хранилищами состояния, чекпоинтами Чанди-Лэмпорта, гарантией Exactly-Once, алгоритмами детектирования аномалий и высокоскоростными конвейерами на чистом Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter87.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 87 Оркестрация распределенных процессов (Durable Execution) на Temporal.io</a>
            <a href="chapter89.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 89 Хаос-инженерия и нагрузочное тестирование на Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'88. Потоковая обработка данных в реальном времени (Stream Processing) ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter89_html(chapters):
    active_chapter_num = 89
    current_exercises = ch89_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 89 • Enterprise Reliability Engineering, Chaos Testing & HighLoad Workloads</div>
        <h1 class="hero-title">Хаос-инженерия и нагрузочное тестирование на Go</h1>
        <p class="hero-desc">
            Полное инженерное руководство по исследованию устойчивости распределенных систем, стресс-тестированию и непрерывной хаос-инженерии на языке Go. Фундаментальные основы: формулирование гипотез Steady State, ограничение радиуса поражения (Blast Radius) и архитектура Toxiproxy. Программное управление сетевыми искажениями в автоматизированных тестах: инъекция сетевой задержки (Latency), джиттера (Jitter), ограничение полосы пропускания (Bandwidth), нарезка пакетов (Slicer), полузакрытые сокеты (Slow Close) и экстренные разрывы соединений (Reset Peer / RST). Паттерны защиты: хаос-тестирование Circuit Breaker (gobreaker) и интеграционные тесты с Testcontainers-Go. Моделирование нагрузки и математическая строгость: сравнительный анализ Closed vs Open Workload (закон Литтла, Пуассоновский процесс), феномен скоординированного пропуска (Coordinated Omission) Гила Тене и точный расчет перцентилей задержки (p50, p90, p99, p99.9) через логарифмические структуры HdrHistogram. Разработка собственного высокоскоростного открытого генератора нагрузки на чистом Go: экстремальный тюнинг пула виртуальных пользователей (VUs), переиспользование Keep-Alive сокетов в http.Transport и профили нагрузки Step-Up, Spike и многочасовой Soak Test. Архитектурная надежность корпоративного масштаба: симуляция сетевого разделения (Split-Brain / Network Partition в Raft-кворуме), прикладной middleware Chaos Monkey с таргетингом по заголовкам, изоляция каскадных сбоев через паттерн Bulkhead, эмуляция зависания дискового ввода-вывода (I/O Hang), хаос-тестирование под лимитами Linux cgroups v2 (memory.max, cpu.max, GOMEMLIMIT), устойчивость gRPC-интерцепторов к системным кодам ошибок, стресс-тестирование Transactional Outbox при падении брокера Apache Kafka, поведение распределенных блокировок Redis при крахе узла, автоматическая верификация алертов Prometheus, декларативные сценарии аварийных учений Game Day, профилирование пауз сборщика мусора (GC STW, GOGC, Mark Assist), регрессионный Quality Gate в CI/CD пайплайнах и сквозная платформа хаос-инженерии Capstone.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Принципы хаоса, Toxiproxy, сетевые токсики и Circuit Breaker (Упражнения 1–10)"),
        (11, "Раздел 2: Testcontainers, модели нагрузки, Coordinated Omission и открытый генератор (Упражнения 11–15)"),
        (16, "Раздел 3: HdrHistogram, профили Step-Up/Spike, Split-Brain, Chaos Monkey и Bulkhead (Упражнения 16–20)"),
        (21, "Раздел 4: Деградация I/O, cgroups v2, gRPC интерцепторы, Outbox и Capstone-платформа (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 89 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением хаос-инженерии и нагрузочного тестирования!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы полностью овладели методологией проактивной надежности: инъекцией сетевых сбоев Toxiproxy, открытыми пуассоновскими моделями нагрузки, устранением скоординированного пропуска, точным расчетом перцентилей HdrHistogram, изоляцией Bulkhead, стресс-тестированием рантайма Go и автоматизацией Game Day.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter88.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 88 Потоковая обработка данных в реальном времени (Stream Processing)</a>
            <a href="chapter90.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 90 Контракт-ориентированные API-шлюзы: gRPC-Gateway, gRPC-Web и OpenAPI →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'89. Хаос-инженерия и нагрузочное тестирование на Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter90_html(chapters):
    active_chapter_num = 90
    current_exercises = ch90_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 90 • Cloud-Native API Gateways, Protobuf Ecosystem & OpenAPI</div>
        <h1 class="hero-title">Контракт-ориентированные API-шлюзы: gRPC-Gateway, gRPC-Web и OpenAPI</h1>
        <p class="hero-desc">
            Фундаментальное практическое руководство по созданию современных контрактно-ориентированных (Contract-First) API-шлюзов на языке Go с использованием экосистемы Protocol Buffers v3, gRPC-Gateway v2, gRPC-Web и OpenAPI (Swagger). Архитектурная парадигма Single Source of Truth: единый контракт IDL против проблемы рассинхронизации (Contract Drift), автоматическая кодогенерация серверных интерфейсов, клиентов и схем данных. Аннотации маршрутизации google.api.http: привязка REST методов, параметров URL, query-строки и тела запроса. Мультиплексирование сетевых протоколов: запуск на раздельных портах, разделение трафика через библиотеку cmux (Connection Multiplexing по сигнатуре заголовков) и единый HTTP/2 сервер со стандартным пакетом h2c без сторонних библиотек. Трансляция ошибок и метаданных: соответствие кодов статусов gRPC и HTTP, кастомные обработчики ошибок в стандарте RFC 7807 (Problem Details), двунаправленный проброс метаданных контекста (WithIncomingHeaderMatcher, WithOutgoingHeaderMatcher) и аутентификация JWT на периметре шлюза. Тонкий тюнинг сериализации JSONPb: сохранение исходных snake_case имен полей и принудительный вывод значений по умолчанию (EmitUnpopulated). Потоковые интерфейсы: передача Server-Streaming RPC через HTTP Chunked Transfer Encoding и Server-Sent Events (SSE). Браузерная интеграция с протоколом gRPC-Web: спецификация фрейминга, 5-байтный префикс кадра, инкапсуляция HTTP/2 Trailers в завершающий фрейм тела ответа (0x80), in-process прокси improbable-eng/grpc-web и обязательная настройка CORS middleware (Access-Control-Expose-Headers для grpc-status). Декларативная валидация запросов через правила bufbuild/protovalidate на базе движка CEL. Линтинг и строгий аудит обратной совместимости контрактов с Buf CLI (buf lint, buf breaking против репозитория). Enterprise паттерны: частичное обновление ресурсов через google.protobuf.FieldMask (HTTP PATCH), полиморфные события с google.protobuf.Any, эффективная передача бинарных файлов через google.api.HttpBody без Base64 накладных расходов. Периметральная защита и Observability: алгоритм Token Bucket Rate Limiting (golang.org/x/time/rate), сквозная распределенная трассировка OpenTelemetry с W3C Trace Context (traceparent), раздельные метрики Prometheus для шлюза и бэкендов, скоординированный Graceful Shutdown обоих серверов, комплексное E2E тестирование паритета контрактов и финальный Capstone-шлюз микросервисной платформы.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Contract-First, кодогенерация grpc-gateway и аннотации REST (Упражнения 1–7)"),
        (8, "Раздел 2: Мультиплексирование cmux, HTTP/2 h2c, ошибки и метаданные (Упражнения 8–15)"),
        (16, "Раздел 3: Server-Streaming, gRPC-Web протокол, CORS и protovalidate (Упражнения 16–22)"),
        (23, "Раздел 4: Any, HttpBody, Rate Limiting, OpenTelemetry, E2E и Capstone (Упражнения 23–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 90 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением контрактных API-шлюзов!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели современным стеком контрактной разработки API: Protobuf Contract-First парадигмой, кодогенерацией gRPC-Gateway, мультиплексированием протоколов, gRPC-Web для фронтенда, декларативной валидацией protovalidate, аудитом Buf CLI и комплексной периметральной защитой.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter89.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 89 Хаос-инженерия и нагрузочное тестирование на Go</a>
            <a href="chapter91.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 91 Разработка собственных Kubernetes Operators и CRD на Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'90. Контракт-ориентированные API-шлюзы: gRPC-Gateway, gRPC-Web и OpenAPI ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter91_html(chapters):
    active_chapter_num = 91
    current_exercises = ch91_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 91 • Cloud-Native Platform Engineering & Kubernetes Internals</div>
        <h1 class="hero-title">Разработка собственных Kubernetes Operators и CRD на Go</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по созданию промышленных операторов Kubernetes (Kubernetes Operators) и расширению API платформы через Custom Resource Definitions (CRD) на языке Go. Концептуальные основы: переход от императивного управления к декларативному (Desired State vs Observed State), паттерн Operator как способ кодификации человеческой SRE-экспертизы и математическая строгость контрольного цикла (Reconciliation Loop: Observe -> Analyze -> Act). Проектирование контрактов API: строгое разделение .spec и подресурса /status, разметка Go-структур маркерами генератора Kubebuilder (+kubebuilder:validation, +kubebuilder:subresource:status, +kubebuilder:printcolumn) и генерация методов глубокого клонирования zz_generated.deepcopy.go. Анатомия фреймворка controller-runtime: разбор метода Reconcile, сигнатура Request с NamespacedName, дедупликация событий (Event Coalescing) и принцип абсолютной идемпотентности контроллера. Архитектура кэширования: внутреннее устройство Informer Cache, очереди Delta FIFO, Indexer в оперативной памяти процесса, проблема Read-After-Write Consistency и предикаты фильтрации событий (GenerationChangedPredicate). Управление жизненным циклом и целостность данных: каскадная сборка мусора через OwnerReferences, стандартизация состояний через срез условий metav1.Condition (паттерн Ready, Progressing, Degraded), перехват удаления через Finalizers и безопасная очистка внешней инфраструктуры. Продвинутые механизмы платформы: валидационные (Validating) и мутационные (Mutating Defaulting) Admission Webhooks, автоматический выпуск и ротация TLS-сертификатов с cert-manager, наблюдение за дочерними объектами через Watches/Owns и реакция на внешние шины через source.Channel. Высокая доступность и устойчивость: выборы лидера (Leader Election на Kubernetes Leases), Server-Side Apply (SSA) с управлением полями Field Management, бесконфликтная миграция версий через Conversion Webhooks (Hub & Spoke), Quorum-Aware Rolling Updates для распределенных СУБД с консенсусом, хаос-инженерия контроллеров и финальный Capstone-оператор распределенного кэширования.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Контрольный цикл, CRD Spec/Status, Kubebuilder и DeepCopy (Упражнения 1–10)"),
        (11, "Раздел 2: Event Predicates, OwnerReferences, Conditions, Finalizers и Webhooks (Упражнения 11–20)"),
        (21, "Раздел 3: Watches/Owns, Conflict Retry, envtest, Ginkgo, RBAC и Leader Election (Упражнения 21–30)"),
        (31, "Раздел 4: Conversion Webhooks, SSA, Quorum Updates, Multi-Tenancy и Capstone (Упражнения 31–45)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 91 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением разработки Kubernetes Operators на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели элитной компетенцией Cloud-Native инженерии: разработкой собственных операторов Kubernetes с использованием Kubebuilder, controller-runtime, Admission Webhooks, Server-Side Apply, Leader Election, хаос-тестирования и паттернов надежности распределенных систем.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter90.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 90 Контракт-ориентированные API-шлюзы: gRPC-Gateway, gRPC-Web и OpenAPI</a>
            <a href="chapter92.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 92 Расширяемость систем: Plugins, IPC и WebAssembly (Wazero) →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'91. Разработка собственных Kubernetes Operators и CRD на Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter92_html(chapters):
    active_chapter_num = 92
    current_exercises = ch92_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 92 • Core Systems, IPC, Security & WebAssembly Internals</div>
        <h1 class="hero-title">Расширяемость систем: Plugins, IPC и WebAssembly (Wazero)</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по созданию расширяемых архитектур корпоративных платформ на Go. Архитектурные парадигмы расширяемости: Microkernel, FFI, Shared Objects, Out-of-Process IPC и изолированные песочницы WebAssembly. Анатомия стандартного пакета plugin: динамическая линковка .so, системный вызов dlopen, экспорт символов и фундаментальные ограничения ABI компилятора Go. Внепроцессные плагины через фреймворк HashiCorp go-plugin: архитектура взаимодействия через UNIX Domain Sockets, безопасное рукопожатие HandshakeConfig с Magic Cookies, Protobuf-контракты и адаптеры gRPC, двусторонняя коммуникация через GRPCBroker и изоляция сбоев на уровне ядра ОС. WebAssembly (Wasm) для серверного Go: сравнительный анализ с контейнерами, отказ от CGO и архитектура чистого рантайма Tetrate Wazero с JIT-компиляцией для amd64 и arm64. Линейная память Wasm: экспорт функций allocate и deallocate, чтение/запись срезов байт через api.Memory, регистрация хост-функций для предоставления системных возможностей хоста и стандарт WASI Snapshot Preview 1. Системная песочница и безопасность: ограничение виртуальной памяти Wasm, защита от OOM, перехват бесконечных циклов через context.WithTimeout и учет процессорных инструкций (Gas Metering). HighLoad паттерны: пул разогретых инстансов sync.Pool, изоляция памяти при конкурентных запросах, передача бинарных Protobuf-структур, горячая перезагрузка модулей через atomic.Pointer без прерывания трафика, компиляция динамических DSL в Wasm-байткод и построение платформы Enterprise Serverless Execution Engine.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура расширяемости, стандартный пакет plugin и HashiCorp go-plugin (Упражнения 1–10)"),
        (11, "Раздел 2: Callbacks, рантайм Wazero, компиляция WASI, линейная память и хост-функции (Упражнения 11–20)"),
        (21, "Раздел 3: Песочницы, лимиты памяти, Gas Metering, пулинг, бенчмарки и Serverless (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 92 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением плагинных архитектур и WebAssembly на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели передовыми технологиями расширяемости корпоративных систем: архитектурой Out-of-Process IPC плагинов на базе HashiCorp go-plugin, бессерверным рантаймом Wazero WebAssembly на чистом Go, безопасными песочницами WASI, Gas Metering, пулингом инстансов и горячей заменой модулей без даунтайма.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter91.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 91 Разработка собственных Kubernetes Operators и CRD на Go</a>
            <a href="chapter93.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 93 Высокопроизводительные API Gateway и Reverse Proxy на чистом Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'92. Расширяемость систем: Plugins, IPC и WebAssembly (Wazero) ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter93_html(chapters):
    active_chapter_num = 93
    current_exercises = ch93_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 93 • HighLoad Networking, Reverse Proxy & Cloud Gateways</div>
        <h1 class="hero-title">Высокопроизводительные API Gateway и Reverse Proxy на чистом Go</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по созданию сверхпроизводительных и отказоустойчивых API-шлюзов (API Gateway) и обратных прокси (Reverse Proxy) на чистом Go, способных выдерживать 100 000+ RPS. Архитектурная декомпозиция: различия Forward Proxy, Reverse Proxy и полнофункционального API Gateway (BFF, Single Entry Point). Анатомия net/http/httputil.ReverseProxy: детальный разбор функций Director и Rewrite (Go 1.20+), динамическая перезапись целевых хостов, заголовков Host и нормализация путей. Безопасность периметра и RFC-стандарты: стандартизация служебных заголовков X-Forwarded-* и защита от IP Spoofing, очистка транзитных заголовков (Hop-by-Hop Headers по RFC 2616/7230), инъекция корпоративных заголовков безопасности (HSTS, nosniff, DENY) и маскирование ошибок бэкенда через ModifyResponse, кастомная классификация сбоев через ErrorHandler (504 Timeout vs 502 Refused). Сетевой тюнинг ядра и рантайма: немедленный сброс потоковых данных FlushInterval (-1 для SSE и токенов LLM), защита от DoS через http.MaxBytesReader (HTTP 413), глубокий тюнинг пулов соединений http.Transport (MaxIdleConns, MaxIdleConnsPerHost, IdleConnTimeout, ForceAttemptHTTP2), системные флаги сокетов Linux SO_REUSEPORT и SO_REUSEADDR. Алгоритмическая балансировка нагрузки: lock-free Round-Robin на atomic.Uint64, балансировка по наименьшей нагрузке Least Connections с Release Callback, кольцо консистентного хэширования с виртуальными нодами (Consistent Hashing & Sticky Sessions). Надежность и самоисцеление: активный опрос здоровья /healthz с порогами сбоев, пассивное обнаружение аномалий (Outlier Detection) с карантином, размыкатель цепи (Circuit Breaker per Route). Продвинутые возможности шлюза: префиксный роутинг со стриппингом префиксов, канареечная маршрутизация по заголовкам и кукам, прозрачное проксирование WebSockets через http.Hijacker, сквозное проксирование gRPC (h2c) с трейлерами, централизованная JWT-аутентификация с инъекцией доверенных заголовков, распределенный Sliding Window Rate Limiting, динамическое gzip-сжатие с sync.Pool, HTTP Caching на ETag (304 Not Modified), сквозная трассировка W3C Trace Context (traceparent), экспорт Prometheus-метрик, структурированный Access Log на log/slog, горячая перезагрузка маршрутов через atomic.Pointer и финальный production-ready шлюз с graceful shutdown.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Устройство ReverseProxy, заголовки, потоковая передача и тюнинг транспорта (Упражнения 1–10)"),
        (11, "Раздел 2: Алгоритмы балансировки, Health Checks, WebSockets, gRPC и JWT (Упражнения 11–20)"),
        (21, "Раздел 3: Rate Limiting, Circuit Breaker, Caching, OTel, Hot Reload и Capstone Gateway (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 93 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением сетевых API-шлюзов и Reverse Proxy на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели передовыми компетенциями сетевой HighLoad-инженерии: проектированием производительных Reverse Proxy на базе httputil, сетевым тюнингом сокетов Linux (SO_REUSEPORT, somaxconn), алгоритмической балансировкой Least Connections и Consistent Hashing, защитой периметра (JWT, Rate Limiting, Circuit Breaker), поддержкой WebSockets/gRPC и сквозной наблюдаемостью.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter92.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 92 Расширяемость систем: Plugins, IPC и WebAssembly (Wazero)</a>
            <a href="chapter94.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 94 Enterprise Release Engineering: Feature Flags, динамический конфиг и Canary Routing →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'93. Высокопроизводительные API Gateway и Reverse Proxy на чистом Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter94_html(chapters):
    active_chapter_num = 94
    current_exercises = ch94_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 94 • Enterprise Release Engineering, Dynamic Config & Canary Routing</div>
        <h1 class="hero-title">Enterprise Release Engineering: Feature Flags, динамический конфиг и Canary Routing</h1>
        <p class="hero-desc">
            Исчерпывающее инженерное руководство по современной прогрессивной доставке (Progressive Delivery), разделению деплоя и релиза (Deploy != Release), фиче-флагам (Feature Flags / Toggles) и динамической конфигурации на Go. Архитектурная философия Trunk-Based Development и классификация флагов по Мартину Фаулеру (Release, Experiment, Ops, Permission Toggles). Внедрение открытого отраслевого стандарта CNCF OpenFeature: провайдеры, клиенты, хуки жизненного цикла (Before, After, Error, Finally), контекст вычисления (Evaluation Context) и сбор Prometheus-метрик. Продвинутый таргетинг: сегментация пользователей, SemVer правила, консистентное хэширование CRC32 для процентных раскаток (Percentage Rollouts) и детерминированных A/B-тестов. Экстренное управление надежностью: аварийные рубильники (Kill Switches) с реакцией за десятки миллисекунд, локальный L1-кэш с синхронизацией через Redis Pub/Sub и безопасный оффлайн-режим (Graceful Fallback). Динамическая перезагрузка конфигурации (Hot Reload) на базе ядра Linux (inotify/fsnotify) и spf13/viper, двухфазная валидация инвариантов перед применением и сверхбыстрое lock-free чтение на atomic.Pointer (Go 1.19+). Канареечная маршрутизация на уровне HTTP Middleware, автоматический откат релизов (Auto-Rollback по 5xx rate в Prometheus), аудит изменений по принципу Four-Eyes, борьба с техническим долгом устаревших флагов с помощью AST-анализа (go/ast) и финальная комплексная корпоративная платформа релиз-инженерии на Go.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Философия флагов, OpenFeature SDK, таргетинг и Kill Switches (Упражнения 1–10)"),
        (11, "Раздел 2: Flipt, Redis Pub/Sub, Canary Middleware, AST-анализ и fsnotify Hot Reload (Упражнения 11–20)"),
        (21, "Раздел 3: Viper, atomic.Pointer, SaaS мульти-тенантность, Auto-Rollback и Capstone платформа (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 94 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением Enterprise Release Engineering на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы освоили элитные практики управления релизами и конфигурацией: открытый стандарт OpenFeature, потокобезопасные рубильники безопасности (Kill Switches), горячую перезагрузку файлов с fsnotify/viper, lock-free архитектуру конфигурации на atomic.Pointer, процентные раскатки по хэшу CRC32 и автоматический откат релизов по метрикам Prometheus.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter93.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 93 Высокопроизводительные API Gateway и Reverse Proxy на чистом Go</a>
            <a href="chapter95.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 95 Распределенная координация и хранилище метаданных etcd v3 →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'94. Enterprise Release Engineering: Feature Flags, динамический конфиг и Canary Routing ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter95_html(chapters):
    active_chapter_num = 95
    current_exercises = ch95_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 95 • Distributed Systems, Raft Consensus & Cloud Metadata</div>
        <h1 class="hero-title">Распределенная координация и хранилище метаданных etcd v3</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по распределенной координации, консенсусу Raft и надежному хранилищу метаданных на базе etcd v3 на Go. Архитектура etcd: многоверсионный контроль конкурентности (MVCC), логический счетчик глобальных ревизий (Main Revision, ModRevision, CreateRevision), встроенный B+tree движок BoltDB (bbolt) и алгоритм консенсуса Raft. Подключение через официальный SDK go.etcd.io/etcd/client/v3: пулы соединений, таймауты, взаимная mTLS-аутентификация с сертификатами X.509 и авто-синхронизация топологии кластера. Базовые операции и расширенный диапазонный поиск: Get, Put, Delete, WithPrefix(), алфавитный скан WithRange(), постраничная выгрузка курсором (Cursor-based Pagination). Механизм аренд (Leases): эфемерные ключи с TTL, двунаправленный gRPC KeepAlive стрим, построение динамического Service Discovery и клиентская балансировка вызовов Round-Robin. Потоковые подписки Watchers: реактивные уведомления в реальном времени, префиксный мониторинг каталогов параметров, надежное возобновление после разрывов сети через WithRev(lastRev+1) и самоисцеление при сжатии истории (rpctypes.ErrCompacted). Распределенные примитивы синхронизации: атомарные транзакции Compare-And-Swap (If/Then/Else Txn), программная память транзакций (Software Transactional Memory - STM), честные распределенные блокировки concurrency.NewMutex с защитой от дедлоков при сбоях (kill -9), выборы лидера (Leader Election) с методом Campaign, поддержание лидерства и добровольная отставка Resign. Эксплуатация и SRE: in-memory L1 кэш метаданных с ревизиями, периодическая компактификация (Compaction), дефрагментация узлов (Defragmentation), обработка переполнения дисковой квоты (ErrNoSpace / Alarm Disarm), распределенная FIFO-очередь задач, запуск встроенного тестового кластера (Embedded etcd) и финальный Enterprise Coordinator на Go.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Архитектура Raft, MVCC ревизии, clientv3, пагинация и Service Discovery (Упражнения 1–10)"),
        (11, "Раздел 2: Watchers, авто-восстановление, транзакции Txn, STM и Distributed Locks (Упражнения 11–20)"),
        (21, "Раздел 3: Выборы лидера, Compaction, Defragmentation, Embedded etcd и Enterprise Coordinator (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 95 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением распределенной координации на etcd v3!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели передовыми механизмами распределенных систем: протоколом консенсуса Raft, версионированием MVCC, транзакциями CAS и STM, честными распределенными блокировками, выборами лидера с Resign, реактивными подписками Watchers, эксплуатацией (Compaction/Defragmentation) и разработкой отказоустойчивых координаторов на Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter94.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 94 Enterprise Release Engineering: Feature Flags, динамический конфиг и Canary Routing</a>
            <a href="chapter96.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 96 Zero-Downtime миграции баз данных и паттерн Expand/Contract на Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'95. Распределенная координация и хранилище метаданных etcd v3 ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter96_html(chapters):
    active_chapter_num = 96
    current_exercises = ch96_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 96 • Storage, Caching & Data Consistency</div>
        <h1 class="hero-title">Zero-Downtime миграции баз данных и паттерн Expand-Contract на Go</h1>
        <p class="hero-desc">
            Фундаментальное руководство по эволюции схемы реляционных и NoSQL баз данных под высокой нагрузкой без даунтайма. Природа сбоев DDL: эксклюзивные блокировки таблиц (ACCESS EXCLUSIVE LOCK), очередь блокировок и исчерпание пула соединений. Обязательные настройки безопасности: SET lock_timeout = '2s', statement_timeout и транзакционные миграции в PostgreSQL. Жизненный цикл паттерна Expand-Contract (Parallel Run): безопасное добавление колонок (Expand), двойная запись в Go (Dual Write), фоновый потоковый перенос исторических данных (Backfill с чанкованием по первичному ключу и Keyset Pagination), адаптивный троттлинг по лагу репликации (pg_stat_replication), переключение чтения (Switch Read) и финальное сжатие схемы (Contract). Безопасные операции со схемой: CREATE INDEX CONCURRENTLY с обработкой статуса INVALID, добавление ограничений NOT VALID с последующей валидацией VALIDATE CONSTRAINT, бесшовное изменение типов колонок (int32 -> int64), View-based Abstraction с триггерами INSTEAD OF, секционирование таблиц (Declarative Partitioning), Zero-Downtime в NoSQL (On-Read Migration в MongoDB), безопасный регламент вывода таблиц из эксплуатации (_deprecated_) и промышленная утилита миграций на Go с graceful shutdown по SIGINT.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: DDL-блокировки, lock_timeout, Expand-Contract и безопасные индексы (Упражнения 1–10)"),
        (11, "Раздел 2: Dual Write, Keyset Backfill, адаптивный троттлинг, Switch Read и Contract (Упражнения 11–20)"),
        (21, "Раздел 3: CI/CD совместимость, партиционирование, NoSQL On-Read, карантин и Capstone утилита (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 96 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением Zero-Downtime миграций баз данных!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы овладели высшим пилотажем эволюции баз данных под миллионными нагрузками: паттерном Expand-Contract, неблокирующим DDL, Keyset-пагинацией бэкфилла, троттлингом по лагу репликации, теневой верификацией Shadow Writing и разработкой надежных миграционных утилит на Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter95.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 95 Распределенная координация и хранилище метаданных etcd v3</a>
            <a href="chapter97.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 97 Time-Series СУБД, сжатие Gorilla и IoT-телеметрия на Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'96. Zero-Downtime миграции баз данных и паттерн Expand-Contract на Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


def build_chapter97_html(chapters):
    active_chapter_num = 97
    current_exercises = ch97_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 97 • Storage, Caching & Data Consistency</div>
        <h1 class="hero-title">Time-Series СУБД, сжатие Gorilla и IoT-телеметрия на Go</h1>
        <p class="hero-desc">
            Фундаментальное практическое руководство по созданию сверхпроизводительных Time-Series баз данных, сжатию телеметрии и высокочастотному приему метрик на Go. Специфика временных рядов: Append-Only поток, монотонность времени, отсутствие точечных обновлений и деградация реляционных B-Tree индексов. Побитовый алгоритм сжатия Facebook Gorilla: дифференциальное кодирование временных меток Delta-of-Delta (D'=0 в 1 бит), побитовое сжатие вещественных чисел float64 через XOR (повторы в 1 бит, ведущие и замыкающие нули), реализация BitWriter и BitReader на чистом Go, декомпрессия с гарантией 100% побитовой точности и экономия памяти свыше 85-90%. Архитектура ядра TSDB: горячий буфер в памяти (Head Chunk), 2-часовая ротация, переход в Immutable статус, сброс сегментов на диск и упреждающий журнал WAL. Обратный индекс меток (Inverted Tag Index) и ускорение пересечений постингов через Roaring Bitmaps. Интеграция с TimescaleDB: гипертаблицы, квантование time_bucket, непрерывные инкрементальные агрегаты (Continuous Aggregates), политики автоматического удаления retention и гибридное колоночное сжатие чанков. Прием IoT-телеметрии по протоколу MQTT (eclipse/paho.mqtt), потоковая буферизация Batch Flusher с pgx.CopyFrom, восстановление пропусков (LOCF, Linear Interpolation), расчет производных Rate с защитой от сбросов счетчиков, прием метрик Prometheus Remote Write (Snappy + Protobuf), кольцевой буфер (Ring Buffer) оперативного кэша в RAM, лимитер High Cardinality бомб и Capstone встраиваемая Time-Series СУБД на Go.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: Специфика TSDB, сжатие Gorilla (Delta-of-Delta, XOR) и BitWriter/BitReader (Упражнения 1–10)"),
        (11, "Раздел 2: Декомпрессия, бенчмарки, архитектура чанков, Roaring Bitmaps и TimescaleDB (Упражнения 11–20)"),
        (21, "Раздел 3: Колоночное сжатие, MQTT, Batch Flusher, Gap Filling, Remote Write и Capstone TSDB (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 97 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением Time-Series СУБД и алгоритмов Gorilla!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели передовыми технологиями хранения метрик: побитовым сжатием временных рядов Gorilla, архитектурой Head/Immutable чанков, Roaring Bitmaps фильтрацией, гипертаблицами TimescaleDB, MQTT конвейерами телеметрии и созданием собственных движков TSDB на Go.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter96.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 96 Zero-Downtime миграции баз данных и паттерн Expand-Contract на Go</a>
            <a href="chapter98.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 98 Архитектурный контроль: Разработка корпоративных линтеров для golangci-lint →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'97. Time-Series СУБД, сжатие Gorilla и IoT-телеметрия на Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter98_html(chapters):
    active_chapter_num = 98
    current_exercises = ch98_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 98 • Go Internals, Compilers, Tooling & AI</div>
        <h1 class="hero-title">Архитектурный контроль: Разработка корпоративных линтеров для golangci-lint</h1>
        <p class="hero-desc">
            Инженерное руководство по созданию кастомных статических анализаторов и линтеров корпоративного уровня на Go с интеграцией в golangci-lint. Архитектура go/analysis: драйверы singlechecker/multichecker, pass-контекст analysis.Pass, AST-инспекция через inspector.Inspector и ast.Inspect. Семантический анализ типов: go/types, TypeInfo (Types, Defs, Uses, Implicits), валидация имплементации интерфейсов (types.Implements) и разрешение сигнатур функций. Автоматизированное тестирование анализаторов: analysistest.Run, тестовые фикстуры и директивы // want. Проектирование правил Clean Architecture: контроль графа зависимостей и запрет импортов доменного слоя в инфраструктуру. Валидация выравнивания структур и обнаружение struct padding для минимизации памяти. Безопасность и надежность: детектирование необработанных горутин и утечек defer, предотвращение небезопасной конкатенации SQL-запросов и выявление теневого копирования sync.Mutex. Автоматическое исправление кода (Quick Fixes): analysis.SuggestedFix, TextEdit и флаг -fix. Упаковка анализатора в плагины golangci-lint (.so и Module Plugin System), локальный запуск через Lefthook pre-commit хуки и CI/CD GitHub Actions/GitLab CI. Разработка Enterprise Linter Suite — комплексного анализатора кодовой базы.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: go/analysis, AST, семантика типов go/types и первые линтеры (Упражнения 1–10)"),
        (11, "Раздел 2: Слои Clean Architecture, горутины, выравнивание структур и автоисправления (Упражнения 11–20)"),
        (21, "Раздел 3: Плагины golangci-lint, SQL-инъекции, Lefthook, CI/CD и Enterprise Linter Suite (Упражнения 21–30)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 98 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением разработки корпоративных линтеров на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы освоили разработку продвинутых статических анализаторов на базе go/analysis и go/types: от низкоуровневой инспекции AST и проверки архитектурных инвариантов до создания плагинов для golangci-lint, автоматических SuggestedFixes и построения корпоративного пайплайна контроля качества кода.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter97.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 97 Time-Series СУБД, сжатие Gorilla и IoT-телеметрия на Go</a>
            <a href="chapter99.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 99 Интеграция с ИИ, LLM-оркестрация и векторный поиск на Go →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'98. Архитектурный контроль: Разработка корпоративных линтеров для golangci-lint ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER



def build_chapter99_html(chapters):
    active_chapter_num = 99
    current_exercises = ch99_exercises
    sidebar_html = build_sidebar(chapters, active_chapter_num, current_exercises)
    
    content_parts = []
    content_parts.append('<main class="main-content" id="top">')
    
    # Chapter Hero
    content_parts.append("""
    <section class="chapter-hero">
        <div class="hero-badge">Глава 99 • Go Internals, Compilers, Tooling & AI</div>
        <h1 class="hero-title">Интеграция с ИИ, LLM-оркестрация и векторный поиск на Go</h1>
        <p class="hero-desc">
            Исчерпывающее практическое руководство по созданию высокопроизводительных ИИ-шлюзов, RAG-платформ и оркестрации LLM на Go. Преимущества Go: обработка десятков тысяч одновременных SSE-соединений (Server-Sent Events) с субмикросекундным GMP-планировщиком и стеком горутин 2 КБ. Интеграция с OpenAI-совместимыми API (vLLM, Ollama, Triton) на чистом net/http с контролем дедлайнов context.Context. Векторные эмбеддинги (Dense Vectors): геометрия евклидовых пространств, косинусное сходство (Cosine Similarity), SIMD и Loop Unrolling. Полноценная интеграция с PostgreSQL pgvector: миграции схемы, операторы расстояния (&lt;=&gt;, &lt;-&gt;, &lt;#&gt;), индексы HNSW (m=16, ef_construction=64) и IVFFlat. Архитектура Retrieval-Augmented Generation (RAG): чанкование документов (Semantic, Overlap, Parent-Child), пакетный конвейер индексации Ingestion Pipeline с pgx.CopyFrom, гибридный поиск (Hybrid Search) с ранжированием Reciprocal Rank Fusion (RRF) и кросс-энкодеры (Cross-Encoder Re-ranking). Паттерн Function Calling (Tool Use): ToolRegistry, схемы параметров JSON Schema, параллельный вызов инструментов и ReAct-агенты (Reasoning + Acting). Семантическое кэширование в Redis, управление бюджетом токенов (Token Bucket Rate Limiting), структурированный вывод (Structured Outputs), защита от Prompt Injection (Guardrails), экспорт метрик в Prometheus и интеграция с локальными моделями Ollama.
        </p>
    </section>
    """)
    
    sections = [
        (1, "Раздел 1: HTTP API, SSE стриминг токенов, эмбеддинги и математика векторов (Упражнения 1–15)"),
        (16, "Раздел 2: Function Calling, мульти-агенты, семантический кэш, промпты и Ollama (Упражнения 16–30)"),
        (31, "Раздел 3: ReAct, мультимодальность, HyDE, Parent-Child, Reranking, Guardrails и SRE-агент (Упражнения 31–45)")
    ]
    
    current_sec_idx = 0
    for ex in current_exercises:
        num = ex['num']
        if current_sec_idx < len(sections):
            s_start, s_title = sections[current_sec_idx]
            if num >= s_start:
                content_parts.append(f"""
                <div class="section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00add8;">
                    <h2>{s_title}</h2>
                </div>
                """)
                current_sec_idx += 1
        
        content_parts.append(build_exercise_card(ex))
        
    # Chapter Footer
    content_parts.append(f"""
    <section class="chapter-footer" style="margin-top: 48px; padding: 36px; background: linear-gradient(135deg, #131d33 0%, #0f2744 100%); border: 2px solid #0284c7; border-radius: 16px; text-align: center; box-shadow: 0 10px 30px rgba(2, 132, 199, 0.2);">
        <div style="display: inline-block; padding: 8px 16px; background: #0284c7; color: white; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em;">Глава 99 завершена!</div>
        <h3 style="color: #38bdf8; font-size: 26px; margin-bottom: 16px; font-weight: 800;">Поздравляем с освоением LLM-оркестрации и векторного поиска на Go!</h3>
        <p style="color: #cbd5e1; font-size: 16px; max-width: 720px; margin: 0 auto 28px auto; line-height: 1.7;">
            Вы в совершенстве овладели передовыми технологиями искусственного интеллекта на Go: потоковой передачей токенов SSE, векторным поиском pgvector HNSW, гибридным ранжированием RRF, автономными ReAct-агентами, Function Calling и созданием надежных высокопроизводительных RAG-платформ.
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap;">
            <a href="chapter98.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155; transition: background 0.2s;">← Глава 98 Архитектурный контроль: Разработка корпоративных линтеров для golangci-lint</a>
            <a href="chapter100.html" style="display: inline-flex; align-items: center; gap: 8px; background: #0284c7; color: #ffffff; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">Глава 100 Архитектурный Capstone: Проектирование и сквозной запуск отказоустойчивой HighLoad-платформы →</a>
            <a href="index.html" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #38bdf8; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #0284c7;">🏠 Главная портала (Треки)</a>
        </div>
    </section>
    """)
    content_parts.append('</main>')
    return HTML_HEAD.replace('01. Пакеты и модули (91/91)', f'99. Интеграция с ИИ, LLM-оркестрация и векторный поиск на Go ({len(current_exercises)}/{len(current_exercises)})') + chr(10) + sidebar_html + chr(10) + chr(10).join(content_parts) + chr(10) + HTML_FOOTER


# All 100 chapters metadata
all_100_chapters = [
    (1, "Пакеты и модули", "chapter1.html", 91, True, "Модули, go.mod, SemVer, Cobra CLI, internal, vendor"),
    (2, "Компиляция, сборка и запуск", "chapter2.html", 25, True, "go build, флаги линкера, кросс-компиляция, race detector, Scratch Docker"),
    (3, "Пакет fmt и консольный ввод-вывод", "chapter3.html", 65, True, "Форматирование, сканирование, буферизация, кастомные стрингеры"),
    (4, "Базовые типы, переменные и константы", "chapter4.html", 111, True, "Числа, переполнения, iota, битовые маски, типизация, кастинг"),
    (5, "Условные конструкции", "chapter5.html", 64, True, "if/else с инициализатором, switch, type switch, fallthrough"),
    (6, "Циклы", "chapter6.html", 64, True, "for, range, итераторы, оптимизации компилятора, метки break/continue"),
    (7, "Массивы", "chapter7.html", 32, True, "Фиксированные массивы, передача по значению, память на стеке"),
    (8, "Слайсы", "chapter8.html", 74, True, "SliceHeader, len vs cap, append, подслайсирование, утечки памяти"),
    (9, "Мапы", "chapter9.html", 62, True, "hmap, bmap, эвакуация бакетов, коллизии, конкурентная запись"),
    (10, "Функции", "chapter10.html", 100, True, "Именованные возвраты, замыкания, defer хронология, рекурсия"),
    (11, "Указатели", "chapter11.html", 49, True, "Разыменование, адресная арифметика, escape analysis, стек vs куча"),
    (12, "Передача аргументов", "chapter12.html", 67, True, "Семантика передачи по значению, мутации, стоимость копирования"),
    (13, "Структуры", "chapter13.html", 71, True, "Теги json/db, выравнивание полей (padding), анонимные структуры"),
    (14, "Интерфейсы", "chapter14.html", 77, True, "iface, eface, dynamic dispatch, nil-interface ловушка, io.Reader/Writer"),
    (15, "ООП в Go", "chapter15.html", 127, True, "Композиция vs наследование, эмбеддинг, полиморфизм, SOLID на Go"),
    (16, "Дженерики", "chapter16.html", 131, True, "Параметрический полиморфизм, constraints, comparable, мономорфизация"),
    (17, "Обработка ошибок", "chapter17.html", 58, True, "errors.Is, errors.As, wrapping %w, кастомные типы ошибок"),
    (18, "Работа с файлами", "chapter18.html", 100, True, "os.File, bufio, ioutil/io, потоковое чтение, временные файлы"),
    (19, "Логирование", "chapter19.html", 84, True, "log/slog, структурированные логи, лог-уровни, JSONHandler"),
    (20, "Горутины и синхронизация", "chapter20.html", 124, True, "go routine, sync.WaitGroup, sync.Mutex, sync.RWMutex, sync.Once, atomic"),
    (21, "Каналы и select", "chapter21.html", 95, True, "Буферизованные каналы, fan-out, fan-in, pipeline, закрытие каналов"),
    (22, "Контекст", "chapter22.html", 52, True, "context.WithTimeout, WithCancel, WithValue, propagation, graceful stop"),
    (23, "Паттерны конкурентности", "chapter23.html", 132, True, "Worker Pool, Semaphore, Or-Done, ErrGroup, Singleflight, Rate Limiting"),
    (24, "Низкоуровневая сеть", "chapter24.html", 63, True, "net.TCPConn, net.UDPConn, таймауты сокетов, deadliness, буферы"),
    (25, "HTTP-клиент", "chapter25.html", 45, True, "http.Client, Transport, Keep-Alive, connection pooling, retries"),
    (26, "HTTP-сервер, REST API и Middleware", "chapter26.html", 158, True, "http.Handler, Chi/Gin/Fiber, CORS, Auth, Recovery, Rate Limiter"),
    (27, "Реляционные базы данных (SQL и PostgreSQL)", "chapter27.html", 163, True, "database/sql, jackc/pgx, connection pool, ACID, транзакции, индексы"),
    (28, "Базы данных NoSQL и кэширование (Redis)", "chapter28.html", 115, True, "go-redis, Strings, Hashes, Pub/Sub, Streams, Redis Cluster"),
    (29, "Модульное тестирование (Unit Testing) и Assertions", "chapter29.html", 96, True, "testing.T, testify/assert, табличные тесты, TestMain"),
    (30, "Мокирование и интеграционное тестирование", "chapter30.html", 107, True, "testcontainers-go, gomock, mockery, PostgreSQL/Redis в Docker"),
    (31, "Бенчмарки, фаззинг и продвинутые методы тестирования", "chapter31.html", 120, True, "testing.B, testing.F, mem/allocs profiling, фаззинг парсеров"),
    (32, "Protocol Buffers и gRPC", "chapter32.html", 189, True, "proto3, protoc-gen-go, Unary, Streaming, Interceptors, Metadata"),
    (33, "Микросервисная архитектура и паттерны", "chapter33.html", 89, True, "Service Discovery, Circuit Breaker, Service-to-Service auth"),
    (34, "GraphQL", "chapter34.html", 78, True, "graphql-go, gqlgen, Resolvers, Schema First, DataLoaders"),
    (35, "WebSockets и Real-time", "chapter35.html", 78, True, "gorilla/websocket, coder/websocket, hub/room broadcast, ping/pong"),
    (36, "RabbitMQ", "chapter36.html", 130, True, "amqp091-go, Exchanges (direct/topic/fanout), Queues, ACKs, DLQ"),
    (37, "Apache Kafka", "chapter37.html", 88, True, "segmentio/kafka-go, Consumer Groups, Partitions, Rebalance, Offsets"),
    (38, "NATS и NATS JetStream", "chapter38.html", 77, True, "nats.go, Core NATS, JetStream, At-Least-Once, Key-Value Store"),
    (39, "Метрики и мониторинг (Prometheus)", "chapter39.html", 114, True, "prometheus/client_golang, Counter, Gauge, Histogram, Summary"),
    (40, "Распределенная трассировка (OpenTelemetry)", "chapter40.html", 79, True, "OTel Go SDK, Tracers, Spans, Context Propagation, Jaeger/Otlp"),
    (41, "Профилирование и рантайм-диагностика", "chapter41.html", 24, True, "net/http/pprof, CPU, Heap, Goroutine, Block/Mutex profile"),
    (42, "Проектирование чистой архитектуры и DDD", "chapter42.html", 98, True, "Domain, UseCases, Repositories, Aggregates, Value Objects"),
    (43, "Шаблоны проектирования распределенных и enterprise-систем", "chapter43.html", 112, True, "Factory, Strategy, Adapter, Unit of Work, Specification"),
    (44, "Проектирование высоконагруженных и отказоустойчивых систем", "chapter44.html", 64, True, "Bulkhead, Sharding, Read Replicas, Backoff, Graceful Degradation"),
    (45, "Контейнеризация и Docker", "chapter45.html", 75, True, "Multi-stage Dockerfile, Scratch/Alpine, non-root, Docker Compose"),
    (46, "Автоматизация CI-CD", "chapter46.html", 57, True, "GitHub Actions, GitLab CI, линтинг, тесты, сборка и пуш образов"),
    (47, "Оркестрация в Kubernetes", "chapter47.html", 180, True, "Pods, Deployments, Services, ConfigMaps, Secrets, Ingress, HPA, Probes"),
    (48, "Планировщик GMP", "chapter48.html", 93, True, "G, M, P, Runqueues, Work Stealing, Sysmon, Preemption в Go"),
    (49, "Аллокатор кучи и управление памятью", "chapter49.html", 66, True, "TCMalloc, mcache, mcentral, mheap, size classes, span"),
    (50, "Garbage Collector и тюнинг памяти", "chapter50.html", 87, True, "Триколор марк-энд-свип, GOGC, GOMEMLIMIT, Write Barrier"),
    (51, "Работа с unsafe и низкоуровневой памятью", "chapter51.html", 85, True, "unsafe.Pointer, uintptr, string-to-bytes no-alloc, struct offset"),
    (52, "Интеграция с C-кодом через CGO", "chapter52.html", 70, True, "import \"C\", cgo types, накладные расходы CGO, call overhead"),
    (53, "Системные вызовы и взаимодействие с ОС", "chapter53.html", 75, True, "syscall, golang.org/x/sys/unix, dup2, pipe, signals, fork/exec"),
    (54, "Продвинутая рефлексия (reflect)", "chapter54.html", 114, True, "reflect.Type, reflect.Value, интроспекция полей, динамический вызов"),
    (55, "Анализ AST и статический анализ кода", "chapter55.html", 85, True, "go/parser, go/ast, ast.Walk, инспекция синтаксических деревьев"),
    (56, "Кодогенерация и шаблонизация", "chapter56.html", 77, True, "go:generate, text/template, stringer, генерация структур"),
    (57, "Симметричное и асимметричное шифрование", "chapter57.html", 100, True, "AES-GCM, ChaCha20, RSA, ECDSA, Ed25519, crypto/rand"),
    (58, "Хеширование паролей и криптографическая стойкость", "chapter58.html", 56, True, "bcrypt, Argon2id, scrypt, PBKDF2, соль, тайминг-атаки"),
    (59, "Токены аутентификации и авторизация", "chapter59.html", 66, True, "JWT (golang-jwt), PASETO, OAuth2, RBAC, Claims validation"),
    (60, "Безопасность веб-приложений и защита API", "chapter60.html", 63, True, "CSRF, XSS, SQLi защита, Secure Headers, Rate Limiting, CORS"),
    (61, "Документоориентированная база данных MongoDB", "chapter61.html", 113, True, "mongo-go-driver, BSON, Aggregation Pipelines, Indexes, Transactions"),
    (62, "Аналитическая СУБД ClickHouse", "chapter62.html", 71, True, "ClickHouse-go, MergeTree, батчинг вставок, OLAP аналитика"),
    (63, "Поисковые движки Elasticsearch и OpenSearch", "chapter63.html", 60, True, "elastic/go-elasticsearch, Full-text Search, Aggregations, Indexing"),
    (64, "Логическая репликация и Change Data Capture", "chapter64.html", 57, True, "PostgreSQL WAL, Debezium, pglogrepl, потоковая репликация событий"),
    (65, "Вебхуки и платформы обратных вызовов", "chapter65.html", 116, True, "HMAC-SHA256 подписи, идемпотентность, очереди доставки, повторы"),
    (66, "Server-Sent Events", "chapter66.html", 69, True, "text/event-stream, HTTP/1.1 и HTTP/2 стриминг, reconnect, event IDs"),
    (67, "Альтернативные RPC-протоколы", "chapter67.html", 92, True, "Twirp, JSON-RPC 2.0, Cap'n Proto, FlatBuffers, производительность"),
    (68, "Паттерн Saga и компенсационные транзакции", "chapter68.html", 104, True, "Оркестрация и хореография саг, компенсации, state machine"),
    (69, "Паттерны Outbox и Inbox для надежной доставки сообщений", "chapter69.html", 72, True, "Transactional Outbox, De-duplication Inbox, At-Least-Once"),
    (70, "Проектирование идемпотентных API", "chapter70.html", 74, True, "Idempotency-Key заголовок, Redis блокировки, кэш ответов"),
    (71, "Выборы лидера (Leader Election) в распределенных системах", "chapter71.html", 90, True, "PostgreSQL advisory locks, Redis Redlock, Consul/K8s leases"),
    (72, "Протокол консенсуса Raft", "chapter72.html", 83, True, "hashicorp/raft, Leader, Follower, Candidate, Log Replication, Quorum"),
    (73, "Распределенные блокировки и Fencing Tokens", "chapter73.html", 68, True, "Redlock, Distributed Mutex, Fencing Tokens против pause"),
    (74, "Cache-friendly структуры данных и выравнивание памяти", "chapter74.html", 99, True, "Кэш-линии L1/L2/L3, ложное разделение (false sharing), struct padding"),
    (75, "Lock-free структуры данных", "chapter75.html", 75, True, "CAS, atomic.Value, Treiber Stack, Michael-Scott Queue"),
    (76, "Ассемблер Go (Plan 9 Assembly) и SIMD", "chapter76.html", 35, True, "Plan 9 псевдорегистры (FP, SP, SB), SIMD AVX2 инструкции"),
    (77, "Высокопроизводительные сетевые фреймворки (gnet, evio)", "chapter77.html", 32, True, "Reactor паттерн, non-blocking epoll, нулевые аллокации сокетов"),
    (78, "Облачные хранилища, Envelope Encryption и KMS", "chapter78.html", 95, True, "AWS S3/MinIO, Envelope Encryption (DEK/KEK), HashiCorp Vault"),
    (79, "Интеграция с Service Mesh (Istio, Linkerd) и mTLS", "chapter79.html", 80, True, "Envoy sidecar, взаимный TLS (mTLS), Spiffe/Spire идентификация"),
    (80, "Контекст трассировки (W3C Trace Context, B3) и gRPC Keepalive", "chapter80.html", 76, True, "traceparent, tracestate, gRPC Keepalive пинги, HTTP/2 GOAWAY"),
    (81, "Безопасность цепочки поставок (Supply Chain Security) и SBOM", "chapter81.html", 136, True, "govulncheck, Syft SBOM (SPDX/CycloneDX), Cosign криптоподпись"),
    (82, "Защита сетевых сокетов и противодействие DoS-атакам", "chapter82.html", 55, True, "Slowloris, SYN flood, TCP SYN cookies, TCP keepalive, SO_REUSEPORT"),
    (83, "Системная изоляция, Seccomp и Linux Capabilities", "chapter83.html", 28, True, "seccomp bpf фильтры, libseccomp, CAP_NET_BIND_SERVICE, drop privs"),
    
    # 17 Planned Chapters (84-100)
    (84, "CQRS и Event Sourcing на Go", "chapter84.html", len(ch84_exercises), True, "Агрегаты, оптимистическая блокировка версий, Snapshots, проекции в Postgres/Elastic"),
    (85, "Многоуровневое кэширование (L1/L2) и распределенная когерентность", "chapter85.html", len(ch85_exercises), True, "In-memory TinyLFU/Ristretto, Redis RESP3 BCAST, алгоритм XFetch, Write-Behind"),
    (86, "Масштабируемые распределенные планировщики и очереди задач", "chapter86.html", len(ch86_exercises), True, "Фоновые очереди Asynq/River, SKIP LOCKED, периодические задачи, кластерный Cron"),
    (87, "Оркестрация распределенных процессов (Durable Execution) на Temporal.io", "chapter87.html", len(ch87_exercises), True, "Temporal Workflows, Activities, Replay детерминизм, Signals, Queries, Long Timers"),
    (88, "Потоковая обработка данных в реальном времени (Stream Processing)", "chapter88.html", len(ch88_exercises), True, "Tumbling/Sliding/Session окна, Watermarks, Late Data, Exactly-Once Checkpoints"),
    (89, "Хаос-инженерия и нагрузочное тестирование на Go", "chapter89.html", len(ch89_exercises), True, "Инъекция сбоев Toxiproxy, открытая модель нагрузки, HdrHistogram, p99.9 задержки"),
    (90, "Контракт-ориентированные API-шлюзы: gRPC-Gateway, gRPC-Web и OpenAPI", "chapter90.html", len(ch90_exercises), True, "Contract-First, buf, gRPC-Gateway, gRPC-Web, OpenAPI v3, protovalidate"),
    (91, "Разработка собственных Kubernetes Operators и CRD на Go", "chapter91.html", len(ch91_exercises), True, "Kubebuilder, Custom Resources, Reconcile Loop, Informers, Workqueues, Webhooks, SSA"),
    (92, "Расширяемость систем: Plugins, IPC и WebAssembly (Wazero)", "chapter92.html", len(ch92_exercises), True, "plugin.Open, HashiCorp go-plugin (gRPC IPC), Wazero Wasm песочницы, Fuel metering"),
    (93, "Высокопроизводительные API Gateway и Reverse Proxy на чистом Go", "chapter93.html", len(ch93_exercises), True, "httputil.ReverseProxy, динамическая маршрутизация, Peak-EWMA, Request Hedging"),
    (94, "Enterprise Release Engineering: Feature Flags, динамический конфиг и Canary Routing", "chapter94.html", len(ch94_exercises), True, "OpenFeature SDK, Canary rollouts, Kill Switch за 50 мс, fsnotify Hot Reload"),
    (95, "Распределенная координация и хранилище метаданных etcd v3", "chapter95.html", len(ch95_exercises), True, "clientv3 Watchers, Leases с автопродлением, атомарные транзакции Txn, Service Discovery"),
    (96, "Zero-Downtime миграции баз данных и паттерн Expand-Contract на Go", "chapter96.html", len(ch96_exercises), True, "Expand/Migrate/Contract, Shadow Writing, Backfill воркеры, защита от AccessExclusiveLock"),
    (97, "Time-Series СУБД, сжатие Gorilla и IoT-телеметрия на Go", "chapter97.html", len(ch97_exercises), True, "Прием сотен тысяч метрик/сек, Gorilla Delta-of-Delta и XOR компрессия, TimescaleDB"),
    (98, "Архитектурный контроль: Разработка корпоративных линтеров для golangci-lint", "chapter98.html", len(ch98_exercises), True, "go/analysis фреймворк, семантика типов go/types, AST-инспекция, Suggested Fixes"),
    (99, "Интеграция с ИИ, LLM-оркестрация и векторный поиск на Go", "chapter99.html", len(ch99_exercises), True, "Ollama, OpenAI SDK, SSE токены, Function Calling, pgvector, Qdrant, RAG конвейер"),
    (100, "Архитектурный Capstone: Проектирование и сквозной запуск отказоустойчивой HighLoad-платформы", "chapter100.html", 35, False, "Финальный проект: gRPC-Gateway, DDD, Event Sourcing, Temporal, L1/L2 кэш, OTel, Seccomp, AI")
]

learning_paths = [
    {
        "id": "core-go",
        "title": "Core Go & Idiomatic Engineering",
        "badge": "Junior → Middle",
        "color": "#38bdf8",
        "icon": "🔷",
        "desc": "Синтаксис, система модулей, структуры данных, полиморфизм интерфейсов, дженерики, идиоматичная обработка ошибок и файловые операции.",
        "tags": ["go.mod", "slices", "maps", "interfaces", "generics", "errors", "slog"],
        "chapters": list(range(1, 20)),
        "start_url": "chapter1.html"
    },
    {
        "id": "concurrency-network",
        "title": "High-Concurrency & Low-Latency Network",
        "badge": "Middle+ → Senior",
        "color": "#10b981",
        "icon": "⚡",
        "desc": "Многопоточность без гонок данных, каналы и select, context, низкоуровневые сокеты TCP/UDP, event-loop gnet, lock-free и DoS-защита.",
        "tags": ["goroutines", "channels", "sync", "TCP/UDP", "gnet", "lock-free", "SO_REUSEPORT"],
        "chapters": [20, 21, 22, 23, 24, 25, 26, 74, 75, 76, 77, 82],
        "start_url": "chapter20.html"
    },
    {
        "id": "storage-consistency",
        "title": "Storage, Caching & Data Consistency",
        "badge": "Middle+ → Senior+",
        "color": "#f59e0b",
        "icon": "💾",
        "desc": "Реляционные и NoSQL хранилища: пул pgx, Redis, ClickHouse, Mongo, CDC репликация, двухуровневый L1/L2 кэш с XFetch и Zero-Downtime миграции.",
        "tags": ["PostgreSQL", "pgx", "Redis", "ClickHouse", "Elasticsearch", "CDC", "XFetch"],
        "chapters": [27, 28, 61, 62, 63, 64, 85, 96, 97],
        "start_url": "chapter27.html"
    },
    {
        "id": "distributed-systems",
        "title": "Distributed Systems & Event-Driven Architecture",
        "badge": "Senior → Staff/Principal",
        "color": "#a855f7",
        "icon": "🌐",
        "desc": "Распределенные платформы: gRPC, Kafka, RabbitMQ, Saga, Outbox, консенсус Raft, etcd, CQRS/ES, очереди River/Asynq и Temporal.io.",
        "tags": ["gRPC", "Kafka", "RabbitMQ", "NATS", "Raft", "Temporal", "etcd", "CQRS"],
        "chapters": [32, 33, 34, 35, 36, 37, 38, 68, 69, 70, 71, 72, 73, 84, 86, 87, 95],
        "start_url": "chapter32.html"
    },
    {
        "id": "observability-reliability",
        "title": "Enterprise Observability & Reliability Engineering",
        "badge": "Senior → Tech Lead",
        "color": "#f43f5e",
        "icon": "📊",
        "desc": "Полный стек надежности: Testcontainers, фаззинг, метрики Prometheus, OTel трассировка, pprof профилирование, Чистая архитектура, хаос-инженерия Toxiproxy.",
        "tags": ["testcontainers", "fuzzing", "Prometheus", "OpenTelemetry", "pprof", "Toxiproxy", "OpenFeature"],
        "chapters": [29, 30, 31, 39, 40, 41, 42, 43, 44, 80, 89, 94],
        "start_url": "chapter29.html"
    },
    {
        "id": "cloud-platform",
        "title": "Cloud-Native, DevOps & Platform Security",
        "badge": "Senior → Platform Lead",
        "color": "#06b6d4",
        "icon": "🛡️",
        "desc": "Инфраструктура и безопасность: Docker, Kubernetes, K8s Operators/CRD, Service Mesh, gRPC-Gateway, Reverse Proxy, Cloud KMS, SBOM, Seccomp.",
        "tags": ["Docker", "Kubernetes", "Kubebuilder", "Service Mesh", "KMS", "SBOM", "Seccomp"],
        "chapters": [45, 46, 47, 78, 79, 81, 83, 90, 91, 93],
        "start_url": "chapter45.html"
    },
    {
        "id": "internals-ai",
        "title": "Go Internals, Compilers, Tooling & AI",
        "badge": "Staff / Principal Engineer",
        "color": "#ec4899",
        "icon": "🧠",
        "desc": "Элитный рантайм: планировщик GMP, аллокатор mcache/mheap, GC, unsafe, CGO, AST, WebAssembly Wazero, корпоративные линтеры `go/analysis`, LLM RAG и Capstone.",
        "tags": ["GMP", "Heap Allocator", "GC", "unsafe", "AST", "Wazero Wasm", "go/analysis", "Ollama/pgvector"],
        "chapters": [48, 49, 50, 51, 52, 53, 54, 55, 56, 92, 98, 99, 100],
        "start_url": "chapter48.html"
    }
]

def build_portal_html(chapters):
    # Sidebar for portal has active_chapter_num=0 (highlight portal link)
    sidebar_html = build_sidebar(chapters, active_chapter_num=0, current_exercises=[])
    
    p = []
    p.append('<main class="main-content" id="top">')
    
    # 1. Hero Section
    p.append("""
    <section style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(24, 36, 64, 0.95) 100%); border: 1px solid #1e293b; border-radius: 16px; padding: 40px; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; margin-bottom: 16px; border: 1px solid rgba(56, 189, 248, 0.3);">
            🚀 Профессиональный тренажер • 100 глав • 7 000+ практических задач • BigTech Standards
        </div>
        <h1 style="font-size: 2.6rem; font-weight: 800; color: #f8fafc; line-height: 1.25; margin-bottom: 16px;">
            Go Backend Engineering <span style="background: linear-gradient(90deg, #00ADD8, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Workout</span>
        </h1>
        <p style="font-size: 1.15rem; color: #94a3b8; max-width: 920px; line-height: 1.7; margin-bottom: 28px;">
            Интерактивный русскоязычный учебник-тренажер для бэкенд-инженеров, 
            нацеленных на позиции Middle, Senior и Staff Go Developer в ведущих технологических компаниях 
            (Яндекс, Ozon, Авито, Т-Банк, VK, Wildberries). 
            Глубокое практическое погружение в компилятор, рантайм Go (GMP, GC триколор, epoll/netpoller), 
            распределенные протоколы (Raft, Saga, Outbox, CDC), сетевую оптимизацию сокетов и системную изоляцию Linux.
        </p>
        
        <!-- Metrics Counter Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px;">
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #38bdf8;">100</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; font-weight: 500;">Глав курса (83 готовы + 17 в плане)</div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #10b981;">7 071+</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; font-weight: 500;">Задач с эталонными решениями</div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #a855f7;">7</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; font-weight: 500;">Сквозных образовательных траекторий</div>
            </div>
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 2.2rem; font-weight: 800; color: #f59e0b;">22</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; font-weight: 500;">Тематических кластера знаний</div>
            </div>
        </div>

        <!-- Quick CTA Buttons -->
        <div style="display: flex; gap: 14px; flex-wrap: wrap;">
            <a href="chapter1.html" style="display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #0284c7, #00ADD8); color: #fff; font-weight: 700; padding: 12px 24px; border-radius: 10px; text-decoration: none; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4); transition: transform 0.2s;">
                <span>🚀 Начать обучение (Глава 01)</span> →
            </a>
            <a href="#learning-paths" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155;">
                <span>🗺️ Образовательные треки</span>
            </a>
            <a href="#curriculum" style="display: inline-flex; align-items: center; gap: 8px; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 12px 22px; border-radius: 10px; text-decoration: none; border: 1px solid #334155;">
                <span>📚 Каталог 100 модулей</span>
            </a>
        </div>
    </section>
    """)
    
    # 2. Section: 7 Learning Paths
    p.append("""
    <section id="learning-paths" style="margin-bottom: 50px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; flex-wrap: wrap; gap: 12px;">
            <div>
                <h2 style="font-size: 1.8rem; font-weight: 800; color: #f8fafc;">Сквозные образовательные траектории (Learning Paths)</h2>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 4px;">Выберите специализацию под ваши карьерные цели и грейд</p>
            </div>
            <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 0.85rem; font-weight: 700; padding: 4px 12px; border-radius: 20px;">7 специализаций</span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 24px;">
    """)
    
    for lp in learning_paths:
        tags_html = "".join([f'<span style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; color: #94a3b8; font-size: 0.75rem; padding: 2px 8px; border-radius: 6px; font-family: monospace;">#{t}</span>' for t in lp["tags"]])
        
        ch_links = []
        for cnum in lp["chapters"]:
            found = next((c for c in all_100_chapters if c[0] == cnum), None)
            if found:
                if found[4]: # Ready
                    ch_links.append(f'<a href="{found[2]}" style="display: inline-block; padding: 2px 8px; background: rgba(30, 41, 59, 0.8); border: 1px solid #334155; border-radius: 6px; color: #38bdf8; text-decoration: none; font-size: 0.78rem; font-weight: 600;" title="{html.escape(found[1])}">{cnum}</a>')
                else:
                    ch_links.append(f'<span style="display: inline-block; padding: 2px 8px; background: rgba(30, 41, 59, 0.4); border: 1px dashed #475569; border-radius: 6px; color: #94a3b8; font-size: 0.78rem;" title="{html.escape(found[1])} (В плане)">{cnum}</span>')
        ch_links_html = " ".join(ch_links)
        
        p.append(f"""
        <div style="background: #131d33; border: 1px solid #1e293b; border-radius: 14px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; position: relative; transition: border-color 0.2s, transform 0.2s;">
            <div>
                <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 1.8rem;">{lp["icon"]}</span>
                    <span style="background: rgba(56, 189, 248, 0.1); color: {lp["color"]}; font-size: 0.78rem; font-weight: 700; padding: 4px 10px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.2);">{lp["badge"]}</span>
                </div>
                <h3 style="font-size: 1.25rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">{lp["title"]}</h3>
                <p style="font-size: 0.9rem; color: #94a3b8; line-height: 1.6; margin-bottom: 16px;">{lp["desc"]}</p>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 18px;">
                    {tags_html}
                </div>
            </div>
            <div>
                <div style="font-size: 0.78rem; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px;">Главы трека:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 18px;">
                    {ch_links_html}
                </div>
                <a href="{lp["start_url"]}" style="display: inline-flex; align-items: center; justify-content: center; gap: 6px; width: 100%; background: #1e293b; color: #f8fafc; font-weight: 600; padding: 10px; border-radius: 8px; text-decoration: none; border: 1px solid #334155; font-size: 0.9rem; transition: background 0.2s;">
                    <span>Перейти к треку</span> →
                </a>
            </div>
        </div>
        """)
        
    p.append("""
        </div>
    </section>
    """)

    # 3. Section: 100 Chapters Interactive Curriculum
    p.append("""
    <section id="curriculum" style="margin-bottom: 60px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; flex-wrap: wrap; gap: 16px;">
            <div>
                <h2 style="font-size: 1.8rem; font-weight: 800; color: #f8fafc;">Полный каталог курса (100 модулей)</h2>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 4px;">Интерактивная матрица всех глав от синтаксиса до Staff Capstone</p>
            </div>
            
            <!-- Quick Filter Tabs -->
            <div style="display: flex; gap: 8px; background: #0f172a; padding: 4px; border-radius: 10px; border: 1px solid #1e293b;">
                <button class="filter-btn active" data-filter="all" style="background: #1e293b; color: #38bdf8; border: none; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; cursor: pointer;">Все (100)</button>
                <button class="filter-btn" data-filter="done" style="background: transparent; color: #94a3b8; border: none; padding: 6px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer;">✅ Готово (83)</button>
                <button class="filter-btn" data-filter="plan" style="background: transparent; color: #94a3b8; border: none; padding: 6px 14px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; cursor: pointer;">📋 В плане (17)</button>
            </div>
        </div>
        
        <!-- Live Search Bar -->
        <div style="position: relative; margin-bottom: 24px;">
            <input type="text" id="curriculum-search" placeholder="Быстрый поиск темы, ключевого слова или номера главы..." style="width: 100%; background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 14px 20px 14px 44px; color: #f8fafc; font-size: 1rem; outline: none; transition: border-color 0.2s;" autocomplete="off">
            <span style="position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #64748b; font-size: 1.1rem;">🔍</span>
        </div>

        <!-- Curriculum Grid -->
        <div id="curriculum-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
    """)
    
    for num, title, fname, ex_count, is_ready, keywords in all_100_chapters:
        status_attr = "done" if is_ready else "plan"
        card_class = "curriculum-card"
        
        if is_ready:
            badge_html = f'<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; font-weight: 700; font-size: 0.78rem; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3);">✅ Готово ({ex_count}/{ex_count})</span>'
            link_start = f'<a href="{fname}" style="text-decoration: none; color: inherit; display: flex; flex-direction: column; justify-content: space-between; height: 100%;">'
            link_end = '</a>'
            card_border = "#1e293b"
            card_cursor = "pointer"
        else:
            badge_html = f'<span style="background: rgba(168, 85, 247, 0.15); color: #c084fc; font-weight: 700; font-size: 0.78rem; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(168, 85, 247, 0.3);">📋 В плане (~{ex_count} упр.)</span>'
            link_start = '<div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; opacity: 0.85;">'
            link_end = '</div>'
            card_border = "#2a2238"
            card_cursor = "default"

        p.append(f"""
        <div class="{card_class}" data-num="{num}" data-title="{html.escape(title.lower())}" data-status="{status_attr}" style="background: #131d33; border: 1px solid {card_border}; border-radius: 12px; padding: 20px; cursor: {card_cursor}; transition: border-color 0.2s, transform 0.15s; position: relative;">
            {link_start}
                <div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; gap: 8px;">
                        <span style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; font-weight: 800; font-size: 0.85rem; padding: 3px 8px; border-radius: 6px; font-family: monospace;">#{num:02d}</span>
                        {badge_html}
                    </div>
                    <h4 style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-bottom: 6px; line-height: 1.35;">{html.escape(title)}</h4>
                    <p style="font-size: 0.82rem; color: #94a3b8; line-height: 1.5; margin-bottom: 12px;">{html.escape(keywords)}</p>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; pt: 8px; border-top: 1px solid #1e293b; margin-top: 8px; padding-top: 8px;">
                    <span style="font-size: 0.78rem; color: #64748b;">{'Открыть главу →' if is_ready else 'Дорожная карта'}</span>
                    <span style="font-size: 0.78rem; color: #38bdf8; font-weight: 600;">{ex_count} упражнений</span>
                </div>
            {link_end}
        </div>
        """)
        
    p.append("""
        </div>
    </section>
    """)

    # 4. Filter and Search Client-Side Script
    p.append("""
    <script>
        // curriculum-toggle-filter-client-script
        document.addEventListener('DOMContentLoaded', () => {
            const searchInput = document.getElementById('curriculum-search');
            const filterBtns = document.querySelectorAll('.filter-btn');
            const cards = document.querySelectorAll('.curriculum-card');
            
            let activeFilter = 'all';
            
            function applyFilters() {
                const query = (searchInput ? searchInput.value.toLowerCase().trim() : '');
                
                cards.forEach(card => {
                    const title = card.getAttribute('data-title') || '';
                    const num = card.getAttribute('data-num') || '';
                    const status = card.getAttribute('data-status') || '';
                    
                    const matchesSearch = !query || title.includes(query) || num.includes(query);
                    const matchesFilter = (activeFilter === 'all') || (activeFilter === status);
                    
                    if (matchesSearch && matchesFilter) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
            
            if (searchInput) {
                searchInput.addEventListener('input', applyFilters);
            }
            
            filterBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    filterBtns.forEach(b => {
                        b.style.background = 'transparent';
                        b.style.color = '#94a3b8';
                        b.style.fontWeight = '600';
                    });
                    btn.style.background = '#1e293b';
                    btn.style.color = '#38bdf8';
                    btn.style.fontWeight = '700';
                    
                    activeFilter = btn.getAttribute('data-filter');
                    applyFilters();
                });
            });
        });
    </script>
    """)

    p.append('</main>')
    
    title_replaced_head = HTML_HEAD.replace('01. Пакеты и модули (91/91)', 'Главная — Портал курса и Образовательные треки (100 модулей)')
    return title_replaced_head + '\n' + sidebar_html + '\n' + '\n'.join(p) + '\n' + HTML_FOOTER


if __name__ == '__main__':
    chapters = get_all_chapters()
    
    pages = [
        ('index.html', build_portal_html),
        ('chapter1.html', build_chapter1_html),
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
        ('chapter53.html', build_chapter53_html),
        ('chapter54.html', build_chapter54_html),
        ('chapter55.html', build_chapter55_html),
        ('chapter56.html', build_chapter56_html),
        ('chapter57.html', build_chapter57_html),
        ('chapter58.html', build_chapter58_html),
        ('chapter59.html', build_chapter59_html),
        ('chapter60.html', build_chapter60_html),
        ('chapter61.html', build_chapter61_html),
        ('chapter62.html', build_chapter62_html),
        ('chapter63.html', build_chapter63_html),
        ('chapter64.html', build_chapter64_html),
        ('chapter65.html', build_chapter65_html),
        ('chapter66.html', build_chapter66_html),
        ('chapter67.html', build_chapter67_html),
        ('chapter68.html', build_chapter68_html),
        ('chapter69.html', build_chapter69_html),
        ('chapter70.html', build_chapter70_html),
        ('chapter71.html', build_chapter71_html),
        ('chapter72.html', build_chapter72_html),
        ('chapter73.html', build_chapter73_html),
        ('chapter74.html', build_chapter74_html),
        ('chapter75.html', build_chapter75_html),
        ('chapter76.html', build_chapter76_html),
        ('chapter77.html', build_chapter77_html),
        ('chapter78.html', build_chapter78_html),
        ('chapter79.html', build_chapter79_html),
        ('chapter80.html', build_chapter80_html),
        ('chapter81.html', build_chapter81_html),
        ('chapter82.html', build_chapter82_html),
        ('chapter83.html', build_chapter83_html),
        ('chapter84.html', build_chapter84_html),
        ('chapter85.html', build_chapter85_html),
        ('chapter86.html', build_chapter86_html),
        ('chapter87.html', build_chapter87_html),
        ('chapter88.html', build_chapter88_html),
        ('chapter89.html', build_chapter89_html),
        ('chapter90.html', build_chapter90_html),
        ('chapter91.html', build_chapter91_html),
        ('chapter92.html', build_chapter92_html),
        ('chapter93.html', build_chapter93_html),
        ('chapter94.html', build_chapter94_html),
        ('chapter95.html', build_chapter95_html),
        ('chapter96.html', build_chapter96_html),
        ('chapter97.html', build_chapter97_html),
        ('chapter98.html', build_chapter98_html),
        ('chapter99.html', build_chapter99_html),
    ]
    
    for filename, builder_fn in pages:
        path = os.path.join('/home/ut/work/go-workout', filename)
        content = builder_fn(chapters)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Written {path} ({os.path.getsize(path)} bytes)")


