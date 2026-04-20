import base64
from PIL import Image, ImageDraw

img = Image.new('RGB', (300, 300), color = 'white')
d = ImageDraw.Draw(img)
d.text((10,10), "Test Receipt\nAmount: 120.00\nDate: 2026-04-14", fill=(0,0,0))
img.save('test_receipt.jpg')

with open('test_bank.csv', 'w') as f:
    f.write("Transaction Date,Transaction Details,Withdrawals,Deposits\n")
    f.write("2026-04-10,Amazon Shopping,500.00,\n")
    f.write("2026-04-11,Salary Credit,,50000.00\n")
