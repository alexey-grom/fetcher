fetcher
=============

Описание
-------------

fetcher - фреймворк для быстрой разработки пауков, сливающих контент и (или) взаимодействующих с сайтами посредством специфичных запросов.

Список возможностей:
* полная реализация http-протокола, за счет использования библиотеки curl в качестве транспорта
* хранение списка задач в оперативной памяти или MongoDB
* обработка групп задач
* сохранение ответов сервера в оперативную память, файл или автоматический выбор лучшего варианта
* подавление ошибок и нестандартных ситуаций и возможность пользовательской обработки ошибок
* кеширование ответов сервера в файлы, MongoDB или MySQL
* расширения для удобного взаимодействия с lxml и v8
* расширение для взаимодействиями с формами
* структурный парсинг упрощающий извлечение структурированных но многочисленных данных на страницах

Фреймворк исключительно экспериментальный, не предназначен для широкого использования, покрытие тестами нулевое, обратной совместимости между версиями нет и не будет никогда.


Общая архитектура
-------------

Архитектура, в целом, скопирована с фреймворка для парсинга сайтов [Grab](http://grablib.org/) ([репозиторий](https://bitbucket.org/lorien/grab)), с приоритетом на рациональное расходование оперативной памяти и разработку исключительно пауков, без синхронного интерфейса. <br /> <br />
Каждый паук является наследником класса MultiFetcher, который содержит очередь задач, расширение для реализации кэша и диспетчер http-запросов. <br /> <br />
В зависимости от настроек, очередь задач независима от своего местонахождения и может хранить задачи как в базе данных, так и в оперативной памяти. То же относится и к расширению для реализации кэширования, за исключением того, что кэш может хранится, кроме БД, еще в файлах на жестком диске. <br /> <br />
Вся полезная работа пауков реализуется посредством создания задач (класс Task), содержащих, как обязательные компоненты, хэндлер задачи, класс запроса и класс ответа сервера. Кроме того, задача может содержать пользовательские атрибуты. <br /> <br />
В классе запроса (Request) хранятся, как то следует из названия, все атрибуты будущего запроса: url, метод, User-Agent, Referer и т.д. Кроме того, хранятся настройки для сохранения ответа сервера: т.к. ответ сервера может быть большим или необходимым только для сохранения в файл, изначальное скачивание ответа в файл может быть более предпочтительным, чем скачивание в оперативную память. <br /> <br />
После выполнения каждой задачи, вызывается её обработчик, определяемый по хэндлеру задачи. Если по хэндлеру не найден обработчик - задача отправляется в коллектор. <br /> <br />
Задачи можно создать тремя путями: созданием отдельного генератора задач, генерируя задачи из обработчиков задач и добавляя задачи непосредственно в очередь задач текущего паука. <br /> <br />


Кэширование
-------------

Фреймворк предоставляет готовые бекэнды для кэширования ответов сервера в mongo, БД подключаемую через SQLAlchemy или файлы на жестком диске. Кэширование актуально на больших объемах данных чтобы не перезакачивать одно и то же по нескольку раз.<br />

Для включения кэширования в конструктор класса MultiFetcher необходимо передать имя бекэнда:

    spider = MultiFetcher(
        cache_backend='file', # или 'mongo', или 'sqla'
        cache_path='/tmp/spider-cache/'
    )

Кроме того, каждый бекэнд требует дополнительные параметры для инициализации.
Дополнительные параметры:
* `file`: `cache_path` - путь куда будут сохранятся ответы сервера. по-умолчанию '/tmp/fetcher-cache'
* `mongo`: `cache_database` - имя БД. по-умолчанию 'FetcherCache'
* `sqla`: `cache_uri` - URI для подключения к БД

Если есть необходимость написать свой бекэнд для хранения ответов сервера, это можно сделать через наследование класса `fetcher.cache.BaseCacheBackend` и передачу этого класса в параметре `cache_backend` при инициализации `MultiFetcher`. <br />

    spider = MultiFetcher(
        cache_backend=YourCacheBackendClassName
    )

Кэшированием управляет расширение `fetcher.cache.CacheExtension` и оно может быть выключенным, либо работать в двух режимах: простое сохранение ответа и браузерное кэширование. <br />
Браузерное кеширование, в отличии от простого сохранения ответов на все запросы, кэширует только те ответы, которые допустимо (простые GET-запросы) и ориентируется на http-заголоки с указаниями от сервера. <br />
Режим кэширования можно установить при создании класса `MultiFetcher` передав ему параметр `cache_type` с одим из следующих значений:
* `CACHE_NONE` - кэширование отключено
* `CACHE_RESPONSE` - простое сохранение тела ответов сервера, по-умолчанию
* `CACHE_TRUE` - браузерное кэширование


Очередь задач
-------------

Т.к. задач может быть очень много (от десятков тысяч и более) и не предствляется возможным создавать их через генератор задач по мере необходимости, то хранить их в оперативной памяти нерационально. Существуют три типа очередей, со своими недостатками и достоинствами. <br />

Для того чтобы настроить фреймворк на работу с тем или иным типом очереди, либо для того чтобы передаться особые параметры для инициализации очереди, необходимо при создании класса `MultiFetcher` передать ему параметр `queue` с одним из следующих значений:

* `memory` - очередь, хранящаяся в оперативной памяти. самый быстрый, но затратный вариант. по-умолчанию выбран именно он. можно включить компрессию задач через дополнительный параметр `queue_compress=True`

* `mongo` - очередь, хранящаяся в MongoDB. задачи подвергаются компрессии, для более экономного хранения. используется БД с именем переданным через парметр`queue_database` (по-умолчанию FetcherQueues) и коллекция с именем переданным черезе параметр `queue_name` (по-умолчанию создается коллекция с первым не занятым именем). Если имя коллекции при создании передано небыло, то по завершении работы созданная коллекция удаляется из БД.

* `sqla` - очередь, хранящаяся в реляционной БД, подключенной через SQLAlchemy. задачи подвергаются компрессии, для более экономного хранения. БД подлючается по URI переданному через парметр `queue_uri`, если его нет - то создается таблица в оперативной памяти на движке SQLite.

Примеры управления созданием очередей:

    # очередь задач в оперативной памяти без компрессии задач
    spider = MultiFetcher(
        queue='memory'
    )

    # очередь задач в оперативной памяти с компрессией задач
    spider = MultiFetcher(
        queue='memory',
        queue_compress=True
    )

    # очередь задач в mysql
    spider = MultiFetcher(
        queue='sqla',
        queue_uri='mysql://логин:пароль/имя_бд
    )


Списки прокси
-------------

Интерфейс для работы со списками прокси находится в `fetcher.utils.proxy_list`. `ProxyList` - класс предоставляющий функции для работы с прокси. <br />
Перед началом работы необходимо загрузить список прокси. Это можно сделать одинаковым способом из трех различных источников:

    # загрузка списка прокси из файла
    ProxyList.append_proxies(open('/tmp/proxylist.txt', 'r'))

    # загрузка списка прокси из текстовой строки
    ProxyList.append_proxies('1.1.1.1:80\n2.2.2.2:8080')

    # загрузка списка прокси из списка
    ProxyList.append_proxies(['1.1.1.1:80', '2.2.2.2:8080'])

Во время работы и создания или конфигурирования задачи, получение нового прокси осуществляется так:

    # установка свежей прокси для новой задачи
    Task(**ProxyList.get_proxy())

    # установка свежей прокси для старой задачи
    task.clone(**ProxyList.get_proxy())

    # копирование старой задачи и установка свежей прокси
    task.clone(**ProxyList.get_proxy())

При этом ничего не мешает помимо прокси конфигурировать остальные параметры задачи. <br /> <br />
При попытке получить свежую прокси, выбирается та, которая еще не использовалась, либо та, которые использовалась раньше всех и соотвественно отдохнула дольше всех. <br /> <br />
Минимальное количество времени, которое прокси должны отдыхать, устанавливается в параметре `ProxyList.PROXY_SLEEP_TIME` и по-умолчанию равно 60 секундам. <br /> <br />
Если доступные прокси закончились и нет ни одной отдохнувшей минимальное время, то с этого момента для прокси будет возвращаться пустое значение, равносильное отключению использования прокси, о чем будет выведено соответствующее сообщение в лог.



Список просмотренных URL
-------------

Часто схема сайтов такова, что существует масса перекрестных ссылок между страницами. Если не предусматривать наличие дублирования ссылок, то бывают ситуации когда создается несколько задач для одного URL. Частично эту проблему можно решить использованием кэша, чтобы хотя бы не скачивать один URL несколько раз. Тем не менее, это половинчатое решение. <br /> <br />
Кроме того, каждый раз создавать механизм проверки URL на факт его выполненности не очень удобно. <br /> <br />
Как раз для этого и предназначен интерфейс для работы со списками просмотренных URL, который находится в `fetcher.utils.looked_urls`. Работа осуществляется через класс `LookedUrls`. <br /> <br />
Этот интерфейс имеет два статических метода:

* `LookedUrls.clear_all()` - удаление информации обо всех просмотренных URL
* `LookedUrls.is_exists(url)` - проверяет наличие url в списке просмотренных. если его там нет - добавляет.



Работа с формами
-------------

Для работы с элементами формы lxml предоставляет прекрасный API, который позволяет работать как с отдельными элементами, так и с группами, объедененными общим именем, как это делается с checkbox, radio. Так же есть возможность работать с множественным выбором значений в select. <br />

Эта функция предназначена именно для получения такого интерфейса для взаимодействия с нужным элементом текущей формы.<br />

Если элемент формы логически обособлен, то через интерфейс напрямую осуществляется работа с его значением. А если имени name соответствует группа элементов, то интерфейс дает возможность выбрать одно или несколько значений сразу для всей группы. Кроме того могут быть специфичные атрибуты для разных видов элементов формы. <br />

В общих чертах, работы с формами осуществляется в следующем порядке:
- Выбор нужной формы через метод задачи `select_form`
- Получение интерфейса к нужным элементам формы через метод `get_control` и взаимодействие с ним для определения возможных значений элемента и установки нужных
- Конфигурирование задачи для выполнения http-запроса через вызов `submit` на основе данных заполненных в форму

>Интерфейсы, которые функция может вернуть, соответствуют логическому смыслу элемента: <br />
>
>>`TextareaElement` - взаимодействие с `<textarea>`.
>>
>>>* `value` - Получение и установка значения.
>>
>>`SelectElement` - взаимодействие с `<select>`.
>>
>>>* `value` - если `<select>` может содержать только одно значение, то напрямую получает и устанавливает значение через это свойство. если `<select>` может содержать множество значений, то это свойство устанавливает возвращает экземпляр класса `MultipleSelectOptions` для работы с множеством значений.
>>>* `value_options` - список всех возможных значений для `<select>` содержащихся в <option> элементах.
>>>* `multiple` - если True, то `<select>` позволяет выбрать несколько значений.
>>
>>`MultipleSelectOptions` - работа с группой значений элемента `<select>`, который позволяет выбирать несколько значений.
>>
>>>* `options` - итератор всех возможных значений
>>>* `add` - добавить выбранное значение
>>>* `remove` - убать значение из списка выбранных
>>
>>`RadioGroup` - взаимодействие с группой переключателей `<input type=radio>`. работая с группой и устанавливая значение, `lxml` автоматически снимает выбор с другого текущего переключателя, т.к. включенным должен оставаться только один переключатель.
>>
>>>* `value` - установить/получаить текущее выбранное значение группы.
>>>* `value_options` - список всех возможных значений для этой группы.
>>
>>`CheckboxGroup` - взаимодействие с группой флажков `<input type=checkbox>`.
>>
>>>* `value` - возвращает экземпляр класса `CheckboxValues` для работы с множеством значений группы флажков.
>>
>>возможность получить набор возможных значений для `CheckboxValues` добавлена в `lxml`, но когда будет в ходу эта версия неизвестно, так что сейчас получить список возможных значений для группы флажков можно через метод задачи - `checkbox_group_values`.<br /><br />
>>
>>`CheckboxValues` - установка/удалчение флажков в группе.
>>
>>>* `add` - добавляет значение в качестве установленного в группу
>>>* `remove` - удаляет значение из группы
>>
>>`InputElement` - взаимодействие с одиночным элементом ввода
>>
>>>* `value` - значение
>>>* `type` - тип
>>>* `checkable` - True, если элемент можно "переключить": `type in ['checkbox', 'radio']`
>>>* `checked` - True, если элемент включен. для `checkable` элементов
