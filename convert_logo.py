from PIL import Image
import os

img = Image.open('logo.png')
# Save as ICO with common sizes
img.save('logo.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Logo.ico updated successfully from logo.png")
