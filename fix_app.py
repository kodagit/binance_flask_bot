with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# simple_chart.html'i index.html ile değiştir
content = content.replace('simple_chart.html', 'index.html')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('app.py güncellendi.')
