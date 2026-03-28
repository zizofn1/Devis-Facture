import sys
import subprocess

try:
    import fitz
except ImportError:
    print('PyMuPDF not installed, installing...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyMuPDF'])
    import fitz

def check_pdf(filename):
    print(f'--- {filename} ---')
    doc = fitz.open(filename)
    page_height = doc[0].rect.height
    print(f'Page height: {page_height}')
    for page_num in range(len(doc)):
        page = doc[page_num]
        texts = page.get_text('dict')['blocks']
        print(f'Page {page_num + 1}:')
        for block in texts:
            if 'lines' in block:
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        if 'Cachet et Signature' in text or 'Conditions' in text:
                            print(f'   "{text}" at Y-bbox: {span["bbox"][1]:.2f} - {span["bbox"][3]:.2f}')

try:
    check_pdf('test_devis_final.pdf')
except Exception as e:
    print('error', e)

try:
    check_pdf('test_2pages.pdf')
except Exception as e:
    print('error', e)
