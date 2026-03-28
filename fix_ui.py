import re
import os

ui_path = 'ui.py'
with open(ui_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the broken line in ui.py (around line 600)
# 'config.DOC_TYPES["facture"][        help_menu.add_command...'
broken_str = 'config.DOC_TYPES["facture"][        help_menu.add_command'
if broken_str in text:
    text = text.replace(broken_str, 'config.DOC_TYPES["facture"]["conditions"] = c_fac\n\n        help_menu.add_command')

# Let's also make sure 'self.config(menu=menubar)Les calculs' is fixed
b2 = 'self.config(menu=menubar)Les calculs (Total, TVA, TTC) se font tous seuls !\\n'
if b2 in text:
    text = text.replace(b2, 'self.config(menu=menubar)\n')

b3 = 'config.DOC_TYPES["facture"]['
if b3 in text and ']' not in text[text.find(b3):text.find(b3)+40]:
    text = text.replace(b3, 'config.DOC_TYPES["facture"]["conditions"] = c_fac')

with open(ui_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Fix applied")
