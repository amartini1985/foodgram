# Описание проекта:

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Используемый стек технологий:
- Python 3.9
- Django
- Django REST Framework
- Docker

## Порядок развертывания проекта через docker:
1) Клонировать репозиторий и перейти в папку проекта:

```
git git@github.com:amartini1985/foodgram.git
```

```
cd foodgram
```

2) Сборка проекта:

```
docker compose up --build
```

3) Выполнить миграции:

```
docker compose exec backend python manage.py migrate
```

4) Заполнить базу данных: 

```
docker compose exec backend python manage.py load_csv_data
```

## Порядок развертывания проекта для работы с backend:
1) Клонировать репозиторий и перейти в него в командной строке:

```
git git@github.com:amartini1985/foodgram.git
```

```
cd /foodgram/backend
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

4) Выполнить миграции:

```
python3 manage.py migrate
```

5) Запустить проект:

```
python3 manage.py runserver
```
6) Заполнить базу данных: 

```
python3 manage.py load_csv_data
```

## Адрес проекта
Проект доступен по адресу: https://foodgramm.ddnsking.com/

## Cпецификация проекта
Спецификация проекта доступна по адресу: https://foodgramm.ddnsking.com/api/docs/

## Админ зона проекта 
Админ зона проекта доступна по адресу: https://foodgramm.ddnsking.com/admin/

## Авторы проекта:
[Andrey Martyanov/amartini1985](https://github.com/amartini1985)

