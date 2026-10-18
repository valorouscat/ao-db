# ao-db — база знаний по Albion Online

Локальная база с поиском и аналитикой по игровым данным из [ao-data/ao-bin-dumps](https://github.com/ao-data/ao-bin-dumps)
плюс живые цены рынка из [Albion Online Data Project](https://www.albion-online-data.com/). Работает тремя способами:
**MCP-сервер** для Claude и других MCP-клиентов, **CLI** `./ao` и **Python-библиотека** `aodb`.

- 12.5k предметов со всеми зачарованиями, 30k строк рецептов, 9k спеллов, 5.5k мобов, 22k строк лута, 1.4k зон
- 40k игровых строк на 15 языках, 40k записей из всех 120 файлов дампа (полнотекстовый поиск)
- Поиск на любом языке игры, понимает префиксы тира: `8.3 палаш`, `T6 bow`
- Без зависимостей: нужны только Python ≥ 3.9 и git

## Быстрый старт
```sh
git clone https://github.com/valorouscat/ao-db && cd ao-db
./setup.sh                 # клонирует ao-bin-dumps и собирает ao.db (~15 с + время клонирования)
./ao search хранитель земли
./ao item 6.1 палаш
```
Обновить данные после патча игры: снова запустить `./setup.sh`.

## MCP
В репозитории есть `.mcp.json`, поэтому Claude Code подключает сервер `albion` автоматически, когда открыт этот проект.
Для другого проекта или клиента:
```sh
claude mcp add albion -- sh -c 'cd /path/to/ao-db && exec python3 -m aodb.mcp_server'
```
Сервер написан на stdio JSON-RPC без зависимостей, открывает базу только на чтение и возвращает компактный markdown.
Переменные окружения: `AO_DB` (путь к базе), `AO_LANG=ru` (русские названия в подписях), `AO_MCP_MAX_CHARS`.

## Инструменты
Одинаковые для MCP (`mcp__albion__<name>`) и CLI (`./ao <name>`, `./ao <name> -h`).

| инструмент | что делает |
|---|---|
| `search` | общий поиск: предметы, спеллы, мобы, зоны, игровые тексты, все сырые файлы |
| `item` | карточка: статы, item value, рецепты, апгрейд, спеллы, где используется, откуда падает |
| `variants` | все тиры и зачарования семейства предметов |
| `list_items`, `categories` | фильтр по категории, тиру, слоту, зачарованию |
| `compare` | сравнение статов |
| `recipe` | дерево крафта до сырья с учётом процента возврата ресурсов |
| `usedin`, `drops`, `loot` | обратные рецепты, источники дропа, раскрытие лут-листов |
| `mob`, `spell`, `zone` | мобы, способности (с подставленными числами), зоны |
| `loc` | любой игровой текст на 15 языках |
| `files`, `doc`, `sql`, `schema` | доступ к любым сырым данным и SQL только на чтение |
| `price`, `history`, `best_city` | живые цены, история, лучший город и флип |
| `craft_profit` | прибыль крафта: материалы с возвратом, налог станка, налоги рынка, маржа |
| `html` | HTML-карточки предметов с иконками |
| `info` | версия данных и статистика |

Иконки: `https://render.albiononline.com/v1/item/<ID>.png?quality=1..5&size=N`, спеллы: `.../v1/spell/<ID>.png`.

## Примеры
```sh
./ao recipe 8.3 claymore avalon --qty 2 --return-rate 15.2
./ao craft-profit "T4 bag" --city Martlock --sell-city Caerleon --focus
./ao best-city T6_MAIN_SWORD --server west
./ao list-items --cat weapons --sub bow --tier 8 --sort ip
./ao sql "select id, name_ru, json_extract(json,'$.\"@attackdamage\"') dmg from items where sub1='dagger' and tier=8 and enchant=0"
./ao doc hellgate --keys-only
```

## Устройство
```
aodb/build.py       индексатор: JSON дампа → SQLite + FTS5 (атомарная замена ao.db)
aodb/core.py        запросы к базе, каждая функция возвращает markdown
aodb/market.py      цены AODP (кэш 5 мин, повтор при 429), калькулятор крафта
aodb/tools.py       единый реестр инструментов, из него генерируются CLI и MCP
aodb/cli.py         CLI `ao`
aodb/mcp_server.py  MCP-сервер
tests/              смоук-тесты (`python3 -m unittest discover tests`, AO_NET=1 включает тесты рынка)
scripts/session-start.sh  хук Claude Code: собирает базу в новой облачной сессии
```
Схема базы: `./ao schema`. В колонках `json` лежат исходные записи целиком (атрибуты с префиксом `@`).

## Оговорки
- Числа в описаниях спеллов — базовые значения из `spells.xml`, до масштабирования по item power.
- `chance` в лут-листах — веса из игровых файлов, а не проценты.
- Цены рынка собираются игроками и могут устаревать; смотрите колонку age. Завышенные одиночные лоты калькулятор заменяет средней ценой за 7 дней.
