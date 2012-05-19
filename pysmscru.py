# -*- coding: utf-8 -*-
# Code based on SMSC.RU API (www.smsc.ru) версия 1.5 (22.10.2011) http://smsc.ru/api/python/
# Refactored and packaged by Sergey Lavrinenko <s@lavr.me>
# TODO:
#  - unittests

import sys
if sys.version_info < (2, 6):
    raise "Only supports Python 2.6+"

from datetime import datetime
from time import sleep
import smtplib

from urllib2 import urlopen, quote

import logging 
log = logging.getLogger(__name__)

def ifs(cond, val1, val2):
    if cond:
        return val1
    return val2


class SMSC(object):

    # Класс для взаимодействия с сервером smsc.ru
    
    def __init__(self, login, password, 
                 use_post=False, 
                 use_https=False, 
                 charset='utf-8', 
                 debug=False, 
                 translit=False,
                 sender=None,
                 query=None, 
                 smtp=None,
                 timeout=2,
                 retries=3,
                 retry_pause=1):

        self.login = login
        self.password = password
        self.use_post = int(use_post)
        self.use_https = int(use_https)
        self.charset = charset
        self.debug = debug
        self.translit = int(translit)
        self.smtp = smtp  # smtp is { 'server': 'send.smsc.ru',  'login':'<smtp login>', 'password':'<smtp password>',  'from': 'sender@company.com'  }
        self.default_sender = sender
        self.default_query = query
        self.http_timeout = int(timeout)
        self.retries = int(retries or 1)
        self.retry_pause = int(retry_pause)

    def send_sms(self, phones, message, translit=0, time="", id=0, format=0, sender=None, query=None):
        # Метод отправки SMS
        #
        # обязательные параметры:
        #
        # phones - список телефонов через запятую или точку с запятой
        # message - отправляемое сообщение 
        #
        # необязательные параметры:
        #
        # translit - переводить или нет в транслит (1,2 или 0)
        # time - необходимое время доставки в виде строки (DDMMYYhhmm, h1-h2, 0ts, +m)
        # id - идентификатор сообщения. Представляет собой 32-битное число в диапазоне от 1 до 2147483647.
        # format - формат сообщения (0 - обычное sms, 1 - flash-sms, 2 - wap-push, 3 - hlr, 4 - bin, 5 - bin-hex, 6 - ping-sms)
        # sender - имя отправителя (Sender ID). Для отключения Sender ID по умолчанию необходимо в качестве имени
        # передать пустую строку или точку.
        # query - строка дополнительных параметров, добавляемая в URL-запрос ("valid=01:00&maxsms=3")
        #
        # возвращает массив (<id>, <количество sms>, <стоимость>, <баланс>) в случае успешной отправки
        # либо массив (<id>, -<код ошибки>) в случае ошибки

        formats = ["flash=1", "push=1", "hlr=1", "bin=1", "bin=2", "ping=1"]
        
        if sender is None:
            sender = self.default_sender or False
            
        if query is None:
            query = self.default_query or ""
        
        if isinstance(phones, (list, tuple)): 
            phones = ";".join(phones)

        m = self._smsc_send_cmd("send", "cost=3&phones=" + quote(phones) + "&mes=" + quote(message) + \
                    "&translit=" + str(translit) + "&id=" + str(id) + ifs(format > 0, "&" + formats[format-1], "") + \
                    ifs(sender == False, "", "&sender=" + quote(str(sender))) + "&charset=" + self.charset + \
                    ifs(time, "&time=" + quote(time), "") + ifs(query, "&" + query, ""))

        # (id, cnt, cost, balance) или (id, -error)

        if m[1] > "0":
            log.debug("Сообщение отправлено успешно. ID: %s, всего SMS: %s, стоимость: %s руб., баланс: %s руб.", m[0], m[1], m[2], m[3])
        else:
            log.error("Ошибка № %s, ID: %s",  m[1][1:],  m[0])

        return m


    # SMTP версия метода отправки SMS

    def send_sms_mail(self, phones, message, translit=0, time="", id=0, format=0, sender=""):
        
        if not self.smtp: log.error('SMTP paramaters not set')
        
        server = smtplib.SMTP(self.smtp['server'])

        if self.debug:
            server.set_debuglevel(1)

        if self.smtp('login'):
            server.login(self.smtp('login'), self.smtp('password')) 

        server.sendmail(self.smtp('from'), "send@send.smsc.ru", "Content-Type: text/plain; charset=" + self.charset + "\n\n" + \
                            self.login + ":" + self.password + ":" + str(id) + ":" + time + ":" + str(translit) + "," + \
                            str(format) + "," + sender + ":" + phones + ":" + message)
        server.quit()


    # Метод получения стоимости SMS
    #
    # обязательные параметры:
    #
    # phones - список телефонов через запятую или точку с запятой
    # message - отправляемое сообщение 
    #
    # необязательные параметры:
    #
    # translit - переводить или нет в транслит (1,2 или 0)
    # format - формат сообщения (0 - обычное sms, 1 - flash-sms, 2 - wap-push, 3 - hlr, 4 - bin, 5 - bin-hex, 6 - ping-sms)
    # sender - имя отправителя (Sender ID)
    # query - строка дополнительных параметров, добавляемая в URL-запрос ("list=79999999999:Ваш пароль: 123\n78888888888:Ваш пароль: 456")
    #
    # возвращает массив (<стоимость>, <количество sms>) либо массив (0, -<код ошибки>) в случае ошибки

    def get_sms_cost(self, phones, message, translit=0, format=0, sender=False, query=""):
        
        formats = ["flash=1", "push=1", "hlr=1", "bin=1", "bin=2", "ping=1"]
            
        if query is None:
            query = self.default_query or ""

        if isinstance(phones, (list, tuple)): 
            phones = ";".join(phones)

        m = self._smsc_send_cmd("send", "cost=1&phones=" + quote(phones) + "&mes=" + quote(message) + \
                    ifs(sender == False, "", "&sender=" + quote(str(sender))) + "&charset=" + self.charset + \
                    "&translit=" + str(translit) + ifs(format > 0, "&" + formats[format-1], "") + ifs(query, "&" + query, ""))

        # (cost, cnt) или (0, -error)

        if m[1] > "0":
            log.debug("Стоимость рассылки: %s  руб. Всего SMS: %s", m[0],  m[1])
        else:
            log.error("Ошибка № %s", m[1][1:])

        return m

    def get_status(self, id, phone):
        # Метод проверки статуса отправленного SMS или HLR-запроса
        #
        # id - ID cообщения
        # phone - номер телефона
        #
        # возвращает массив:
        # для отправленного SMS (<статус>, <время изменения>, <код ошибки sms>)
        # для HLR-запроса (<статус>, <время изменения>, <код ошибки sms>, <код страны регистрации>, <код оператора абонента>,
        # <название страны регистрации>, <название оператора абонента>, <название роуминговой страны>, <название роумингового оператора>,
        # <код IMSI SIM-карты>, <номер сервис-центра>)
        # либо массив (0, -<код ошибки>) в случае ошибки
    
        m = self._smsc_send_cmd("status", "phone=" + quote(phone) + "&id=" + str(id))

        # (status, time, err) или (0, -error)

        if m[1] >= "0":
            if self.debug:
                tm = ""
                if m[1] > "0":
                    tm = str(datetime.fromtimestamp(int(m[1])))
                else:
                    tm = "null"
                self.debug("Статус SMS = %s, время изменения статуса - %s  ",  m[0], tm )
        else:
            log.error("Ошибка № %s", m[1][1:])
        return m

    def get_balance(self):
        # Метод получения баланса
        #
        # без параметров
        #
        # возвращает баланс в виде строки или False в случае ошибки

        m = self._smsc_send_cmd("balance") # (balance) или (0, -error)

        if len(m) < 2:
            log.debug("Сумма на счете: %s руб.", m[0])
        else:
            log.error("Ошибка № %s", m[1][1:])

        return ifs(len(m) > 1, False, m[0])


    def _smsc_send_cmd(self, cmd, arg=""):
        # ВНУТРЕННИЕ МЕТОДЫ
        # Метод вызова запроса. Формирует URL и делает 3 попытки чтения
        url = ifs(self.use_https, "https", "http") + "://smsc.ru/sys/" + cmd + ".php"
        arg = "login=" + quote(self.login) + "&psw=" + quote(self.password) + "&fmt=1&" + arg

        i = 0
        ret = ""
        
        if self.use_post or len(arg) > 2000:
            post_data = arg.encode(self.charset)
        else:
            url = url + "?" + arg
            post_data = None

        log.debug("URL: %s", url)
        log.debug("DATA: %s", post_data)
        
        while ret == "" and i < self.retries:
            if i > 0:
                log.debug('Error while conecting smsc.ru HTTP API, retry %s of %s after pause', i, self.retries, self.retry_pause)
                sleep(self.retry_pause)

            data = urlopen(url, post_data, timeout=self.http_timeout) # Python 2.6 required
            ret = str(data.read())
            i += 1

        if ret == "":
            log.error("Ошибка чтения: %s", url)
            ret = "," # фиктивный ответ

        return ret.split(",")

