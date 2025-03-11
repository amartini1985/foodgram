# Описание проекта:

Веб-приложение на Python с использованием Django.

## Используемый стек технологий:
- Python 3.9
- Django
- Django REST Framework

## Порядок развертывания проекта:
1) Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:amartini1985/api_yamdb.git
```

```
cd api_final_yatube
```

2) Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

3) Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

4) Запустить проект:

```
python3 manage.py runserver
```
5) Заполнить базу данных: 

```
python3 manage.py load_csv_data
```

6) Пример запросов:
Получение списка произведений:

Запрос:

GET /api/v1/titles/

Структура ответа:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "name": "string",
      "year": 0,
      "rating": 0,
      "description": "string",
      "genre": [
        {
          "name": "string",
          "slug": "^-$"
        }
      ],
      "category": {
        "name": "string",
        "slug": "^-$"
      }
    }
  ]
}
```

## Cпецификация проекта
Спецификация будет доступна по адресу: http://127.0.0.1:8000/redoc/

## Авторы проекта:
[Andrey Martyanov/amartini1985](https://github.com/amartini1985)

Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

