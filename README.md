# 2026-VK-EDU-Web-13-Shpakova-D

# AskPupkin

Проект вопросов и ответов (аналог StackOverflow), разрабатываемый в рамках курса по Web-разработке VK Education.

## Описание проекта

AskPupkin — это платформа, где пользователи могут задавать вопросы по программированию, отвечать на них, ставить оценки и искать нужную информацию по тегам. На текущем этапе реализована **read-only версия сайта** (просмотр данных из БД без авторизации и обработки форм).

## Стек технологий

- **Backend:** Python 3.12, Django 6
- **База данных:** PostgreSQL 17
- **Frontend:** HTML5, CSS3, Bootstrap 5
- **Контейнеризация:** Docker, Docker Compose
- **Отладка:** django-debug-toolbar

## Реализованный функционал

- Модели: Question, Answer, Tag, Profile, QuestionLike, AnswerLike с правильными связями (`ForeignKey`, `ManyToMany`, `OneToOne`) и ограничениями БД (`unique_together`).
- Кастомный `QuestionManager` с методами `new()`, `hot()`, `by_tag()`, `with_related()` и оптимизацией N+1 через `select_related` / `prefetch_related` / `annotate(Count)`.
- Локализованная админ-панель Django с `list_display`, `search_fields`, `list_filter`, Inline для профилей и ответов, `raw_id_fields` для производительности.
- Management command `fill_db <ratio>` для генерации тестовых данных через Faker и `bulk_create`.
- Постраничный вывод вопросов и ответов с обработкой 404 и пустых состояний.
- Конфигурация через `.env` файлы (раздельно для локального и docker-окружения).

## Доступные страницы

После запуска сервера:

- `http://127.0.0.1:8000/` — главная (новые вопросы)
- `http://127.0.0.1:8000/hot/` — популярные вопросы
- `http://127.0.0.1:8000/tag/<name>/` — вопросы по тегу
- `http://127.0.0.1:8000/question/<id>/` — страница вопроса со списком ответов
- `http://127.0.0.1:8000/ask/` — форма создания вопроса (без обработки)
- `http://127.0.0.1:8000/login/`, `/signup/`, `/profile/` — формы авторизации и профиля (без обработки)
- `http://127.0.0.1:8000/admin/` — админ-панель (требует суперпользователя)
- `http://127.0.0.1:8000/__debug__/` — django-debug-toolbar (только при DEBUG=True)

## Конфигурация окружения

В корне проекта используются три `.env`-файла:

- **`.env.example`** — шаблон со всеми переменными (без секретов), коммитится в репозиторий.
- **`.env.local`** — для локального запуска Django (`DB_HOST=localhost`). Игнорируется git.
- **`.env.docker`** — для запуска через docker-compose (`DB_HOST=db`). Игнорируется git.

При локальном запуске Django сначала ищет `.env.local`, потом `.env`. В docker-окружении используется `.env.docker` через `env_file` в `docker-compose.yml`.

## Запуск проекта

### 1. Клонирование

```bash
git clone https://github.com/GrayMouse9/2026-VK-EDU-Web-13-Shpakova-D.git
cd 2026-VK-EDU-Web-13-Shpakova-D
```

### 2. Подготовить переменные окружения

```bash
cp .env.example .env.local
cp .env.example .env.docker
```

В `.env.local` оставь `DB_HOST=localhost`. В `.env.docker` поменяй на `DB_HOST=db`.

### Вариант A. Локальный запуск (Django + Postgres в Docker)

```bash
# Поднять только базу
docker compose up -d db

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Применить миграции и создать суперпользователя
python manage.py migrate
python manage.py createsuperuser

# Заполнить базу тестовыми данными
python manage.py fill_db 5

# Запустить сервер
python manage.py runserver
```

### Вариант B. Полный запуск через Docker Compose

```bash
docker compose up --build

# В отдельном терминале — миграции и заполнение базы
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py fill_db 5
```

После любого из вариантов открой в браузере `http://127.0.0.1:8000/`.

## Структура проекта

```
.
├── application/          # Настройки Django проекта
├── core/                 # Приложение пользователей (Profile, login/signup/profile views)
├── questions/            # Приложение вопросов (Question, Answer, Tag, лайки)
│   ├── management/
│   │   └── commands/
│   │       └── fill_db.py    # Команда заполнения БД через Faker
│   ├── admin.py
│   ├── models.py
│   └── views.py
├── templates/            # Общие шаблоны (base.html, inc/)
├── static/               # Статика (Bootstrap, картинки)
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── manage.py
```

## Полезные команды

- `python manage.py fill_db <ratio>` — наполнить БД, где ratio — коэффициент (5 → ~50 вопросов, 10000 → ~100k вопросов).
- `python manage.py migrate` — применить миграции к БД.
- `python manage.py createsuperuser` — создать суперпользователя для админки.
- `docker compose down -v` — остановить контейнеры и **удалить данные БД**.
- `docker compose logs -f db` — смотреть логи Postgres в реальном времени.
