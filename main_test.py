import sys, os
print('executable:', sys.executable)
print('_MEIPASS:', getattr(sys, '_MEIPASS', 'NOT DEFINED'))
print('frozen:', getattr(sys, 'frozen', False))
