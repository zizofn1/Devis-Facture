import re

with open('pdf_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of the second block
start_idx = 0
for i in range(10, len(lines)):
    if 'PDF_GENERATOR.PY — Génération du PDF' in lines[i] and 'import os' in lines[i+3]:
        start_idx = i - 1
        break

if start_idx == 0:
    print('Error: Could not find second block boundary.')
    exit(1)

new_lines = lines[start_idx:]
content = ''.join(new_lines)

# Fix 1: Add leading to doc_title
content = re.sub(
    r'(\"doc_title\": ps\(\"DocTitle\",\n\s*fontName=\"Helvetica-Bold\", fontSize=20,\n\s*textColor=colors\.HexColor\(C\[\"dark\"\]\),\n\s*spaceAfter=)2(\),)',
    r'\g<1>15, leading=26\g<2>',
    content
)

# Fix 2: Inject BottomAnchor
anchor_code = '''
class BottomAnchor(Flowable):
    \"\"\"Ancre le composant cible (ex: conditions/signatures) en bas de la page.\"\"\"
    def __init__(self, target):
        Flowable.__init__(self)
        self.target = target
    def wrap(self, availWidth, availHeight):
        w, h = self.target.wrap(availWidth, availHeight)
        self.w, self.h = w, h
        if h > availHeight: return availWidth, h
        self._consumed = max(h, availHeight)
        return availWidth, self._consumed
    def draw(self):
        self.target.drawOn(self.canv, 0, 0)

'''

# Insert BottomAnchor after CONTENT_H = ...
content = content.replace(
    'CONTENT_H = PAGE_H - MARGIN_T - MARGIN_B\n',
    'CONTENT_H = PAGE_H - MARGIN_T - MARGIN_B\n\n' + anchor_code
)

# Fix 3: Use BottomAnchor in _section_footer_block
content = content.replace(
    'return [KeepTogether(inner)]',
    'return [BottomAnchor(KeepTogether(inner))]'
)

# Fix: missing Flowable in import
content = content.replace(
    'Paragraph, Spacer, HRFlowable, KeepTogether',
    'Flowable, Paragraph, Spacer, HRFlowable, KeepTogether'
)

with open('pdf_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('pdf_generator.py cleaned and updated.')
