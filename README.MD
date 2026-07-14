# GeoCOCO

GeoCOCO — сервис оркестрации пайплайна подготовки/сборки датасета с единым контрактом запуска как из API, так и из CLI.  
Ключевая идея: вход задаётся через `JobSpec`, результат возвращается как `JobResult`, что делает интерфейсы консистентными между web-слоем и командной строкой.

## Архитектура

Проект разделён на несколько слоёв:

- `src/geococo`
  - `core` — базовая доменная/внутренняя логика (концептуальный слой).
  - `api` — публичный фасад (`src/geococo/api/pipeline.py`), предоставляет `run_pipeline(...)`.
  - `services` — orchestration/use-case слой, где выполняется прикладной сценарий (например, `build_dataset`).
- `apps/web`
  - FastAPI-приложение (`apps/web/geococo_web/main.py`) с endpoint-ами `/health` и `/run`.

Поток вызова в текущем MVP:

1. Клиент (HTTP или CLI) формирует `JobSpec`.
2. Публичный API (`run_pipeline`) принимает спецификацию и делегирует в сервисный слой.
3. Сервисный слой возвращает `JobResult`.

## Требования к окружению

- Python 3.10+
- Для web-части требуются `fastapi` и `uvicorn`.
- Пакет `geococo` должен быть доступен в окружении (например, через editable install или при `PYTHONPATH=src`).
- Для GIS-части в зависимости от используемых модулей могут потребоваться системные зависимости (GDAL/GEOS/PROJ).

## Быстрый старт

Ниже безопасные примеры запуска. Точные команды установки зависимостей/окружения зависят от вашего менеджера пакетов и структуры окружения.

### 1) Запуск web-сервиса (FastAPI)

Пример запуска через Uvicorn:

```bash
uvicorn geococo_web.main:app --app-dir apps/web --reload
```

Если пакет `geococo` не резолвится, убедитесь, что `src` добавлен в `PYTHONPATH` или проект установлен в editable-режиме.

После запуска:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Проверка статуса: `GET http://127.0.0.1:8000/health`

### 2) Запуск через CLI

CLI-энтрипоинт находится в `src/geococo/cli.py`.

Пример вызова:

```bash
python -m geococo.cli --config path/to/config.yaml --param key=value --param mode=test
```

CLI собирает параметры в `JobSpec`, вызывает `run_pipeline(...)` и печатает `JobResult` в JSON.

## API

### `GET /health`

Проверка доступности сервиса.

Пример ответа:

```json
{
  "status": "ok"
}
```

### `POST /run`

Запуск пайплайна.

Пример запроса:

```json
{
  "config_path": "configs/sample.yaml",
  "params": {
    "key": "value"
  }
}
```

Пример ответа (структура `JobResult`):

```json
{
  "status": "success",
  "message": "Pipeline completed",
  "outputs": {},
  "metadata": {}
}
```

Значения `status`/`message` определяются сервисным слоем в зависимости от результата выполнения.

## Модели

Контракты описаны в `src/geococo/models.py`:

- `JobSpec`
  - `config_path: str | None` — путь к конфигурации пайплайна.
  - `params: dict[str, Any]` — произвольные параметры запуска.

- `JobResult`
  - `status: str` — итоговый статус выполнения.
  - `message: str` — человекочитаемое сообщение.
  - `outputs: dict[str, Any]` — полезные результаты/артефакты.
  - `metadata: dict[str, Any]` — служебные метаданные выполнения.

## Планы

Планируется расширение интеграции с QGIS: подготовка и экспорт результатов пайплайна в форматах/процессах, удобных для геопространственных сценариев и визуализации в QGIS.
