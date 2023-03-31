import telebot
import datetime
from bs4 import BeautifulSoup
import requests
import time
from threading import Thread


class Proshop:
    class Product:
        def __init__(self, soup):
            try:
                self.name = soup.find('h2').text.strip().rstrip()
                self.link = soup.find('h2').find_previous('a').get('href')
            except AttributeError:
                raise AttributeError

        def __str__(self):
            return f"{self.name}\n\nNew item detected:\n\n{Proshop.url_main}{self.link}"

    # url = 'https://www.proshop.pl/?c=dron-helikopter~laptop~smartwatch-zegarek-i-opaska-sportowa~tablet~telefon-komorkowy&pre=0&s=Demo&o=1152'
    url = 'https://www.proshop.de/?c=drohnen~handys-smartphones~ipad-tablet~laptops~smartwatches-pulsuhren-sportuhren-schrittzaehler&pre=0&s=Demo&o=1152'
    url_main = 'https://www.proshop.de'
    bot = telebot.TeleBot("5130003121:AAHz6AJbDxYGb2pKojhXmlEvuV6GywZzS_I")
    me = 408972919
    he = 305092919
    users = (me, he)

    def __init__(self):
        self.products = []
        self.previous_products = []
        self.last_time_check = None
        self.max_pages = None
        self.s = requests.Session()

    def get_page(self, url, first=False):
        ua = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        # proxy = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
        while True:
            try:
                req = self.s.get(url, headers={'User-Agent': ua}, allow_redirects=True, timeout=5)
                products = BeautifulSoup(req.content, 'lxml').find(id='products').find_all('li')
                for product in products:
                    self.products.append(Proshop.Product(product))
                if first:
                    self.max_pages = int(BeautifulSoup(req.text, 'lxml').find('ul', class_="pagination").find_all('li')[-2].text)
                return True
            except requests.exceptions.ConnectionError as e:
                print(e)
                time.sleep(1)
            except requests.exceptions.Timeout as e:
                print(e)
                time.sleep(1)
            except AttributeError:
                print('Attribute error')
                time.sleep(1)
            except NameError:
                Proshop.bot.send_message(Proshop.me, 'Name error')
                time.sleep(1)

    def __scrap(self):
        self.products = []
        threads = []
        self.get_page(Proshop.url, first=True)
        for num in range(2, self.max_pages + 1):
            url = f"{Proshop.url}&pn={num}"
            threads.append(Thread(target=self.get_page, args=(url,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return self.products

    def execute(self):
        t1 = datetime.datetime.now()
        if not self.previous_products:
            self.previous_products = self.__scrap().copy()
            """while len(list(map(lambda p: p.name, self.products))) != len(set(map(lambda p: p.name, self.products))):
                time.sleep(3)
                self.previous_products = self.__scrap().copy()"""
        else:
            self.__scrap()
            """while len(list(map(lambda p: p.name, self.products))) != len(set(map(lambda p: p.name, self.products))):
                time.sleep(3)
                self.__scrap()"""
            mp = set(map(lambda p: p.name, self.previous_products))
            for product in self.products:
                if product.name not in mp:
                    Proshop.send(product)
            self.previous_products = self.products.copy()
        time.sleep(2)
        self.last_time_check = datetime.datetime.now()
        print(self.last_time_check - t1)

    @staticmethod
    def send(product: Product):
        for user in Proshop.users:
            while True:
                try:
                    Proshop.bot.send_message(user, product.__str__())
                    break
                except Exception as e:
                    print(e)
                    time.sleep(1)

    def run_bot(self):
        @Proshop.bot.message_handler(commands=['status', 'list'])
        def commands(m):
            if m.text == '/status':
                Proshop.bot.send_message(m.from_user.id, f'Products quantity at {self.last_time_check} is {len(self.previous_products)}')
            elif m.text == '/list':
                r = ''
                if self.previous_products:
                    with open('log.txt', 'w') as file:
                        for num, product in enumerate(self.previous_products, start=1):
                            r += f"{num}) {product.name} {product.link}\n"
                        file.write(r)
                file = open('log.txt', 'r')
                Proshop.bot.send_document(m.from_user.id, file, visible_file_name=f"List at {self.last_time_check}.txt")
                file.close()

        @Proshop.bot.message_handler(func=lambda m: m.from_user.id == Proshop.he)
        def messaging(m):
            Proshop.bot.send_message(Proshop.me, m.text)

        while True:
            try:
                Proshop.bot.polling()
            except requests.exceptions.ConnectionError:
                time.sleep(1)
            except requests.exceptions.ReadTimeout:
                time.sleep(1)
            except telebot.ExceptionHandler:
                time.sleep(1)


session = Proshop()
Thread(target=session.run_bot).start()
try:
    session.bot.send_message(session.me, 'Started!')
    while True:
        session.execute()
finally:
    session.bot.send_message(session.me, 'Stopped!')
    exit()
