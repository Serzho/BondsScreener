# BondsScreener

Программа выгрузки, фильтрации, подсчета доходности облигаций и вывода в табличном виде, доступных для покупки в России.

* License - CC BY-NC-ND 4.0
* Table service - Google Sheets
* Broker api - Tinkoff

## Начало работы
1. Установка библиотек
```
$ pip install -r requirements.txt
```
2. Получение токена брокера (рекомендуется получить токен без возможности выставления заявок):  
https://www.tinkoff.ru/invest/settings/ 
3. Настройка google sheets:  
https://habr.com/ru/articles/483302/
4. Конфигурирование cfg.py:  
**TOKEN** - токен от google sheets в текстовом формате  
**EMAIL** - список почтовых адресов, для которых будет выдан доступ к таблице  
**TABLE_TOKEN_FILE** - путь к файлу токена от брокера  
**BOND_COMMISSION** - коммиссия при покупке облигации  
**CURRENCY_COMMISSION** - коммиссия при покупке валют  
**UNARY_REQUEST_LIMIT** - лимит запросов к api брокера в минуту    
**MAX_REQUEST_ATTEMPTS** - максимальное количество попыток получения одного запроса  
**LOGGING_LEVEL** - уровень логирования  
**START_TYPE** - режим запуска  
5. Запуск
```
python ./BondsScreener.py 
```
6. По ссылке из вывода в консоль находится таблица (без удаления таблицы эта ссылка остается постоянной)

## 
## t.me/serzho_christ
