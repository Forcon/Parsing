import shelve
import sqlite3
from urllib.request import urlopen

from bs4 import BeautifulSoup

SQL_Connect = sqlite3.connect('Samizdat.db')
cursor = SQL_Connect.cursor()
# import time
# start = time.time()

URL = 'http://samlib.ru/'
baze_adress = []  # Все списки данных по автору по сайту

# ---------- Получение списка со страницы автора + SQL --------
def in_avtor(url_adress):
    html = urlopen(url_adress).read().decode('cp1251')

    baze_parsing = {} # Список по странице
    key_str = [
        'URL',
        'ФИО',
        'Название',
        'Aдpeс',
        'WWW',
        'Родился',
        'Живет',
        'Обновлялось',
        'Объем',
        'Рейтинг',
        'Посетителей',
        'Friend',
        'Страна',
        'Город',
        'Кол_во',
        'Кол_Оценок',
        'Friend_on',
        'Friend_off'
        ]

    baze_parsing['URL'] = url_adress
    try:
        bs = BeautifulSoup(html, "html.parser").h3.text
        baze_parsing['ФИО'] = bs.split(':\n')[0]
        baze_parsing['Название'] = bs.split(':\n')[1]
    except(IndexError, AttributeError):
        baze_parsing['ФИО'] = ''
        baze_parsing['Название'] = ''

    try:
        start_txt = BeautifulSoup(html, "html.parser").li.text
    except(AttributeError):
        start_txt = ('\n')

    mas = [] # Массив значений полученных с сайта
    for elem in str(start_txt).split('\n'): # Чистим массив от лишних знаков
        if '\r' or ' ' or '\t' in elem:
            mas.append(elem.strip('\r, ,\t'))
        else:
            mas.append(elem)

    # Посмотреть другую логику (через ключи)
    for key in key_str[3:]:
         if key in " ".join(mas):
             for el in mas:
                 if key in el:
                     try:
                         baze_parsing[key] = el.split(': ')[1]
                     except IndexError:
                         baze_parsing[key] = ''
                     break
         else:
             baze_parsing[key] = ''

    # ------------ Убираем знаки, сбивающие запись в SQL -------------
    if "'" or "?" in str(baze_parsing):
        for key in key_str[:]:
             if "'" in baze_parsing[key]: # Убираем знаки '
                 baze_parsing[key] = baze_parsing[key].replace("'", "_")
             if "?" in baze_parsing[key]: # Убираем знаки '
                 baze_parsing[key] = baze_parsing[key].replace("?", "_")

    # ------------- Обработка строк для загрузки в базу -------------
    if baze_parsing['Живет'] != '' or ',' in baze_parsing['Живет']:
        baze_parsing['Страна'] = baze_parsing['Живет'].split(',')[0]
        baze_parsing['Город'] = baze_parsing['Живет'].split(',')[1]
    baze_parsing['Родился'] = '-'.join(baze_parsing['Родился'].split('/')[::-1])
    baze_parsing['Обновлялось'] = '-'.join(baze_parsing['Обновлялось'].split('/')[::-1])
    if '/' in baze_parsing['Объем']:
        baze_parsing['Кол_во'] = baze_parsing['Объем'].split('/')[1]
        baze_parsing['Объем'] = baze_parsing['Объем'].split('k/')[0]
    if '*' in baze_parsing['Рейтинг']:
        baze_parsing['Кол_Оценок'] = baze_parsing['Рейтинг'].split('*')[1]
        baze_parsing['Рейтинг'] = baze_parsing['Рейтинг'].split('*')[0]
    if '/' in baze_parsing['Friend']:
        baze_parsing['Friend_on'] = baze_parsing['Friend'].split('/')[0]
        baze_parsing['Friend_off'] = baze_parsing['Friend'].split('/')[1]
    elif baze_parsing['Friend'] != '':
        baze_parsing['Friend_on'] = baze_parsing['Friend']

    try:
        cursor.execute("""INSERT INTO 'Samizdat' (
            'URL', 'ФИО', 'Название', 'Aдpeс', 'WWW', 'Родился', 'Обновлялось', 'Объем', 'Рейтинг',
            'Посетителей', 'Страна',  'Город', 'Кол_во', 'Кол_Оценок', 'Friend_on', 'Friend_off') 
            VALUES (
            '{URL:s}', '{ФИО:s}', '{Название:s}', '{Aдpeс:s}', '{WWW:s}', '{Родился:s}', '{Обновлялось:s}', '{Объем:s}', '{Рейтинг:s}', 
            '{Посетителей:s}', '{Страна:s}', '{Город:s}', '{Кол_во:s}','{Кол_Оценок:s}', '{Friend_on:s}', '{Friend_off:s}'
            )""".format(**baze_parsing))

        SQL_Connect.commit() # Применение изменений к базе данных
    except sqlite3.Error as e:
        print(e, '---------->', baze_parsing['ФИО'], baze_parsing['URL'])
        try:
            cursor.execute("INSERT INTO 'URL_Error' ('URL') VALUES ('{:s}')".format(baze_parsing['URL']))
            SQL_Connect.commit()  # Применение изменений к базе данных
        except:
            print(e,'--------------------->', baze_parsing['URL'], '<------------------')
    return baze_parsing['ФИО']

# ------ Получение списка url для обработки адресов ------
def url_adres():
    cursor.execute("SELECT Адреса FROM Адреса_страниц")  # Адрес из SQL
    for el in cursor:
        letter('http://samlib.ru' + el[0])
        break

    # adresa.append()
    # for el in adresa:
    #     cursor.execute("SELECT URL FROM Samizdat WHERE URL LIKE '%{:}%'".format(el))
    #     if len(cursor.fetchall()) == 0:
    #         k = str(el).split('http://samlib.ru')[1]
    #         cursor.execute("DELETE FROM Адреса_страниц WHERE (Адреса = ?)", (k,))
    #         SQL_Connect.commit()  # Применение изменений к базе данных
    #
    # return None

# ------ Получение адресов со страницы с буквой ------
def letter(url):
    url_letter = urlopen(url)
    html = url_letter.read().decode('cp1251')
    adresa = []

    # Простой адрес
    adresa_txt = BeautifulSoup(html, "html.parser").find('table').findAllNext('dl')
    sql_comp([adresa.append(str(el.a).split('"')[1]) for el in adresa_txt])


def sql_comp(mas_url):
    cursor.execute("SELECT URL FROM Samizdat WHERE URL LIKE '%{:}%'".format(mas_url[-3]))
    if len(cursor.fetchall()) == 0:
        k = mas_url.split('http://samlib.ru')[1]
        cursor.execute("DELETE FROM Адреса_страниц WHERE (Адреса = ?)", (k,))
        SQL_Connect.commit()  # Применение изменений к базе данных
        url_adres()
    else:
        return mas_url

# ------ Функция берет адреса и передает их на парсинг ------
def adress_letter(mas_adr, start_fio):
    for i, adress in enumerate(mas_adr[start_fio:]):
        url = 'http://samlib.ru' + adress
        fio = in_avtor(url)
        print('{0:.2%} -> Обработано {1:>6d} из {2:>6d} : {3:s}'.format((i / (len(mas_adr)- start_fio)), i +1, len(mas_adr) - start_fio, fio))
    return i + 1


def mail():
    kol_znach = 0
    letter_baze = url_adres()
    kol_znach += adress_letter(letter(letter_baze), 0) # Последнее значение - это с какого из списка значений начинать
    return kol_znach

# --------- Запуск программы ----------
k = mail()
print("\nУф... {0:d} страниц обработано, работа закончена!".format(k))
cursor.close()
SQL_Connect.close()

# print_rez('b')
# print(baze_adress)  # Выведение финальных результатов парсинга
# print("\nTime: %.03f s" % (time.time() - start))

# cursor.execute("INSERT INTO 'Города' ('Город') VALUES ('{:s}')".format(baze_parsing['Живет'])
# cursor.execute("INSERT INTO 'Samizdat' ('ФИО', 'Название', 'Aдpeс') VALUES ('{ФИО:s}', '{Название:s}', '{Aдpeс:s}')".format(**baze_parsing))
# cursor.execute("INSERT INTO 'Samizdat' ('ФИО', 'Название', 'Aдpeс') VALUES ('{0:s}', '{1:s}', '{2:s}')".format(baze_parsing['ФИО'], baze_parsing['Название'], baze_parsing['Aдpeс']))
# cursor.execute("INSERT INTO 'Samizdat' ('ФИО', 'Название', 'Aдpeс') VALUES ('{0:s}', '{1:s}', '{2:s}')".format(baze_parsing['ФИО'], baze_parsing['Название'], baze_parsing['Aдpeс']))

# cursor.executemany("INSERT INTO Samizdat (ФИО) VALUES (ФИО = ?)", baze_parsing['ФИО'])
# cursor.executemany("INSERT INTO Samizdat (Название) VALUES 'Название = ?", baze_parsing['Название'])
# cursor.executemany("INSERT INTO Samizdat (Aдpeс) VALUES (дpeс = ?", baze_parsing['Aдpeс'])
# for el in key_str[1:]:
#     if el != 'Живет' and el != 'Friend':
#         cursor_sql.execute("INSERT INTO 'Samizdat' ('{0:s}') VALUES ('{1:s}')".format(el, baze_parsing[el]))
#
# #attrs['href']
# # in_avtor('http://samlib.ru/a/azik_n/')

# ------ Функция записывает результат в файл как базу ------
# def write_baze(letter):
#     f = shelve.open("baze_rez.dat", "c")  # Консервация базы
#     f[letter] = baze_adress
#     f.close()
#     # print(baze_adress)
#     baze_adress.clear()

# --------- Распечатка результатов ---------
# def print_rez(letter):
#     f = shelve.open("baze_rez.dat", "r")
#     for i, adress in enumerate(f[letter]):
#         print("{0:s} --> {1:s}".format(adress['ФИО'], adress['Aдpeс']))
#     f.close()