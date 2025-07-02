from bs4 import BeautifulSoup

with open('debug_google_тенге_дирхам.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')
    
# Поиск всех элементов с числовыми значениями
numbers = soup.find_all(text=lambda text: text and any(char.isdigit() for char in text))
print("Найдены числа:", numbers)