#!/usr/bin/env python3
"""Build report/MAIN_REPORT.md from the task reports, then export MAIN_REPORT, AI_CRITIQUE and AI_AUDIT_REPORT to PDF.

Usage: python3 scripts/build_report.py [--md-only]
PDF: pandoc (md -> self-contained HTML, Mermaid rendered by mermaid.js) -> google-chrome headless print-to-pdf.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / 'report'


def section(path, title, link_fix=None):
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'\A# .*\n', '', text)                       # drop the file's own H1
    text = re.sub(r'^(#{1,5}) ', r'#\1 ', text, flags=re.M)   # shift headings one level down
    if link_fix:
        text = link_fix(text)
    return f'# {title}\n\n{text.strip()}\n'


def build_md():
    skill_fix = lambda t: re.sub(r'\]\((?!https?:)', '](../skill/', t)
    parts = [
        '# HW05 – Performance Testing: Báo cáo chính\n\n'
        'Sinh viên **23120190** · Flow 1 (login → products → product detail → cart → checkout → my-orders) · '
        'Repo: https://github.com/tzin1401/testing-hw05\n\n'
        '| Phần | Nội dung |\n|---|---|\n'
        '| 1 | Task 1 – Load / Stress / Spike / Soak |\n| 2 | Bug report |\n| 3 | Task 2 – Phân tích AI và misinterpretation hunt |\n'
        '| 4 | Task 3 – Continuous Performance Testing |\n| 5 | Agent Skill |\n| 6 | AI Critique |\n\n'
        'Video demo: Load https://youtu.be/gI2pvrCkcQg · Stress https://youtu.be/1ZFqomMaMFU · '
        'Spike https://youtu.be/qH1VOzb8fZU · Soak https://youtu.be/ADsnkwwEeRE · '
        'Agent Skill https://youtu.be/1NvKtbFaqGs\n\n'
        'AI Audit Report: [AI_AUDIT_REPORT.md](AI_AUDIT_REPORT.md) · Toàn văn log: [AI_LOG.md](AI_LOG.md)\n',
        section(R / 'TASK1_REPORT.md', '1. Task 1 – Kiểm thử hiệu năng') + '\n### Bảng thông số phần cứng\n\n'
        + re.search(r'(\| Hạng mục.*?)\n\n', (R / '05_hardware.md').read_text(encoding='utf-8'), re.S).group(1) + '\n',
        section(R / '09_bugs.md', '2. Bug report'),
        section(R / 'TASK2_REPORT.md', '3. Task 2 – Phân tích AI'),
        section(R / 'TASK3_REPORT.md', '4. Task 3 – Continuous Performance Testing'),
        section(ROOT / 'skill' / 'README.md', '5. Agent Skill', skill_fix),
        section(R / 'AI_CRITIQUE.md', '6. AI Critique'),
    ]
    out = R / 'MAIN_REPORT.md'
    out.write_text('\n\n'.join(parts), encoding='utf-8')
    print('wrote', out.relative_to(ROOT))


CSS = '''<style>
body{font-family:"Noto Sans","DejaVu Sans",sans-serif;font-size:10.5pt;line-height:1.45;max-width:none;margin:0;padding:0 4mm;color:#111}
h1{font-size:17pt;border-bottom:2px solid #333;padding-bottom:3px;margin-top:22px}h2{font-size:13.5pt;margin-top:18px}h3{font-size:11.5pt}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:9pt;page-break-inside:auto}th,td{border:1px solid #999;padding:3px 5px;vertical-align:top}
th{background:#eee}tr{page-break-inside:avoid}code{font-size:8.8pt;background:#f3f3f3;padding:0 2px;word-break:break-all}
pre{background:#f6f6f6;padding:6px;font-size:8.3pt;white-space:pre-wrap;word-break:break-all}img{max-width:100%;max-height:120mm}
blockquote{border-left:3px solid #bbb;margin-left:0;padding-left:8px;color:#333}
</style>'''
MERMAID = '''<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>document.querySelectorAll('pre.mermaid').forEach(p=>{const d=document.createElement('div');d.className='mermaid';d.textContent=p.textContent;p.replaceWith(d)});
mermaid.initialize({startOnLoad:false});mermaid.run().then(()=>{document.title+=' ';});</script>'''


def pdf(md_paths, out_pdf, title):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'head.html').write_text(CSS)
        (tmp / 'foot.html').write_text(MERMAID)
        html = R / ('.' + out_pdf.stem + '.tmp.html')  # inside report/ so relative image paths resolve
        try:
            subprocess.run(['pandoc', *map(str, md_paths), '-f', 'gfm', '-s', '--metadata', f'title={title}',
                            '-H', str(tmp / 'head.html'), '-A', str(tmp / 'foot.html'), '-o', str(html)], check=True)
            subprocess.run(['google-chrome', '--headless=new', '--no-sandbox', '--disable-gpu',
                            '--virtual-time-budget=15000', '--no-pdf-header-footer',
                            f'--user-data-dir={tmp / "chrome"}',
                            f'--print-to-pdf={out_pdf}', html.as_uri()],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            html.unlink(missing_ok=True)
    print('wrote', out_pdf.relative_to(ROOT))


if __name__ == '__main__':
    build_md()
    if '--md-only' not in sys.argv:
        pdf([R / 'MAIN_REPORT.md'], R / 'MAIN_REPORT.pdf', 'HW05 – 23120190 – Main report')
        pdf([R / 'AI_CRITIQUE.md'], R / 'AI_CRITIQUE.pdf', 'HW05 – 23120190 – AI Critique')
        pdf([R / 'AI_AUDIT_REPORT.md', R / 'AI_LOG.md'], R / 'AI_AUDIT_REPORT.pdf', 'HW05 – 23120190 – AI Audit Report')
