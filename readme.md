fetcher
=============

![](https://github.com/alexey-grom/fetcher/fetcher/frontend/flask_frontend/static/img/spider.png)

Описание
-------------

fetcher - библиотека для быстрой разработки пауков, сливающих контент и (или) взаимодействующих с сайтами по средствам специфичных запросов.

Список возможностей:
* полная реализация http-протокола, за счет использования библиотеки curl в качестве транспорта
* хранение списка задач в оперативной памяти или MongoDB
* сохранение ответов сервера в оперативную память, файл или автоматический выбор лучшего варианта
* подавление ошибок и нестандартных ситуаций и возможность пользовательской обработки ошибок
* кеширование ответов сервера в MongoDB или MySQL
* frontend на Flask с админкой для управления пауком и просмотра моделей
* расширения для удобного взаимодействия с lxml и v8
* расширение для взаимодействиями с формами
* структурный парсинг упрощающий извлечение структурированных но многочисленных данных на страницах

