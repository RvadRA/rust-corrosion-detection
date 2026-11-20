# Система обнаружения ржавчины и коррозии

Проектная работа по курсу **«Современные методы DevOps»** (ЮУрГУ, ВШЭКН).
Проект: **ТЗ 1. Система обнаружения ржавчины и коррозии** — автоматический контроль цилиндров на линии ПАО «ЧКПЗ».

## Автор

**Райимжонов Абдусамад Тулкинович** — индивидуальная работа: аналитика / PM, ML / CV, backend, frontend, DevOps.

## Задача

Цель ТЗ: находить на боковой поверхности и кромках цилиндра ржавчину, измерять её площадь и выдавать вердикт `НОРМА` / `ВНИМАНИЕ` / `БРАК` / `ОШИБКА СИСТЕМЫ` для линии.

**Что фактически реализовано в прототипе:** U-Net выполняет только бинарную сегментацию «ржавчина / фон». Классификатор степени «лёгкая / глубокая» не обучен, поэтому система не определяет глубину коррозии. Вердикт по площади — это бизнес-правило поверх бинарной маски, а не оценка степени.

Требования ТЗ, которые пока не подтверждены прототипом:

- Лёгкая ржавчина ≤ 20 мм² → «Внимание».
- Глубокая коррозия или площадь > 20 мм² → «Брак»; ветка «глубокая коррозия» не реализована без классификатора степени.
- Обнаружение пятен от 5 мм ≥ 98%, погрешность площади ≤ ±15%, точность степени ≥ 95% — целевые метрики, не достигнуты.

## Стек

- **ML / CV:** Python 3.11, PyTorch (CPU-инференс U-Net M4), NumPy, SciPy, Pillow
- **Backend:** FastAPI, PostgreSQL 16 (архив проверок, автоматическая ротация 30 дней), выгрузка CSV с UTF-8 BOM
- **Frontend:** React, Tailwind CSS, Vite, Lucide Icons (интерфейс оператора: снимок с масками, вердикт, площадь, журнал, просмотр оригиналов)
- **Инфраструктура:** Docker, Docker Compose (multi-stage сборка, непривилегированные пользователи, healthchecks), GitHub Actions
- **Веб-сервер фронтенда:** Nginx (reverse proxy для API и медиа)

## Архитектура сервисов и порты

| Сервис | Порт | Назначение | Доступ |
|---|---|---|---|
| `frontend` | `3000` | Веб-интерфейс оператора (React + Tailwind в Nginx) | Внешний (`http://localhost:3000`) |
| `backend` | `8000` | REST API (FastAPI, CRUD, бизнес-логика вердиктов, валидация, ротация, CSV) | Внешний (`http://localhost:8000`) |
| `ml` | `8001` (expose) | Сервис нейросетевого инференса U-Net (PyTorch CPU, multipart) | **Только внутри docker-сети** (снаружи закрыт) |
| `db` | `5432` (expose) | СУБД PostgreSQL 16 (хранение архива проверок) | **Только внутри docker-сети** (снаружи закрыт) |

## Веса модели и чистый запуск

- Чекпоинт U-Net: `dataset/processed/kt3/unet.pt` (размер ~7.45 МБ, SHA-256: `3900ef9023e22c5580666c37d9c4c5194a1f63fe057104bfad73f34a47dbdaa0`).
- Архитектура: `UNet(channels=(16, 32, 64, 128), bottleneck=256)`, вход 256×256 RGB.
- Веса **не хранятся в git** (занесены в `.gitignore` и `.dockerignore`).
- Для запуска на чистом компьютере предусмотрен скрипт автоматической верификации и скачивания весов:

```bash
python scripts/fetch_weights.py
```

Скрипт проверяет контрольную сумму SHA-256 и скачивает чекпоинт в `dataset/processed/kt3/unet.pt`. В контейнер `ml` веса пробрасываются через read-only volume: `./dataset/processed/kt3/unet.pt:/models/unet.pt:ro`.

---

## Быстрый старт (КТ 4: Прототип)

### 1. Подготовка конфигурации и весов

```bash
# Windows (PowerShell)
Copy-Item .env.example .env
python scripts/fetch_weights.py

# Linux / macOS / Bash
cp .env.example .env
python scripts/fetch_weights.py
```

Параметры в `.env`:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL` — реквизиты БД.
- `ML_SERVICE_URL=http://ml:8001` — адрес ML-сервиса внутри docker сети.
- `DATA_DIR=/app/data` — путь к volume с загрузками и масками.
- `RETENTION_DAYS=30` — срок хранения архива проверок и файлов (дней).
- `MAX_UPLOAD_SIZE_MB=32` — максимальный размер загружаемого файла.
- `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` — разрешённые источники.
- `MM_PER_PX=` — масштаб камеры (мм на пиксель). Если пуст, калибровка считается невыполненной.

### 2. Запуск контейнеров

```bash
docker compose up --build -d
```

### 3. Проверка статуса контейнеров

```bash
docker compose ps
```

Все сервисы (`corrosion_db`, `corrosion_ml`, `corrosion_backend`, `corrosion_frontend`) должны перейти в состояние `healthy`.

### 4. Проверка работоспособности (Healthcheck)

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "db": "connected",
  "ml": "ready",
  "retention_days": 30,
  "timestamp": "..."
}
```

### 5. Остановка сервисов

```bash
# Остановка контейнеров
docker compose stop

# Полная остановка с удалением контейнеров и сетей
docker compose down

# С удалением томов данных (если требуется полный сброс БД)
docker compose down -v
```

---

## Проведение контроля деталей

### Backup-видео демо

[Скачать backup-видео демонстрации](docs/kt5/demo_backup.mp4)

### Через веб-интерфейс (UI)
1. Откройте в браузере: **`http://localhost:3000`**
2. В блоке «Контроль детали» перетащите или выберите снимок цилиндра (поддерживаются JPG, PNG, WEBP до 32 МБ).
3. Нажмите **«Запустить инспекцию»**.
4. Просмотрите вердикт (`НОРМА` / `ВНИМАНИЕ` / `БРАК` / `ОШИБКА СИСТЕМЫ`), площадь поражения, уверенность модели и переключайте вид (Overlay / Маска / Исходный снимок). При клике на записи истории отображаются их фактические исходные снимки.
5. Результат автоматически добавится в архив проверок справа.
6. Нажмите **«Выгрузить CSV»** для скачивания отчета с кодировкой UTF-8 BOM.

### Через curl (API)

Отправка изображения на контроль:
```bash
curl -F "file=@dataset/raw/ostrava/corrosion-in-industrial-complexes-in-ostrava/test/images/01.jpg" http://localhost:8000/api/v1/inspect
```

Проверка валидации невалидного файла (возвращает 415/400):
```bash
curl -F "file=@README.md" http://localhost:8000/api/v1/inspect
```

Получение последних результатов:
```bash
curl http://localhost:8000/api/v1/results
```

Выгрузка журнала проверок в формате CSV:
```bash
curl -o results.csv http://localhost:8000/api/v1/results.csv
```

---

## Версии окружения и отличия от КТ 3

- **Эксперименты КТ 3:** проводились на Python 3.14.2 / PyTorch 2.15.0 на хосте разработчика (исследование алгоритмов, подбор гиперпараметров).
- **Docker-контейнеры КТ 4:** зафиксированы стабильные LTS-образы Debian Bookworm — **Python 3.11-slim** и **PyTorch 2.3.1+cpu**. Это обеспечивает минимальный размер образов (без тяжёлых CUDA-зависимостей), гарантированную повторяемость сборки и воспроизводимость на любом сервере.
- Архитектура UNet и сериализованный `state_dict` чекпоинта полностью совместимы между версиями: результаты инференса на тестовом снимке `01.jpg` совпадают бит-в-бит (`area_px = 619904`, `confidence = 0.7307`).

---

## Тесты и CI

- Backend: unit-тесты вердиктов и калибровки, API-тесты на SQLite с замоканным ML-сервисом. Тесты реального инференса U-Net не входят в CI, чтобы не скачивать веса и PyTorch.
- Frontend: CI проверяет установку зависимостей и production-сборку Vite.
- Workflow: `.github/workflows/ci.yml` запускается на `push` и `pull_request`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r src/backend/requirements.txt -r src/backend/requirements-test.txt
pytest

cd src/frontend
npm ci
npm run build
```

---

## Известные ограничения этапа КТ 4

1. **Целевые метрики ТЗ ещё не достигнуты:**
   - В КТ 3 обучена baseline-модель U-Net M4 (точные значения из `docs/kt3/results/unet.json`):
     - **Test (79 снимков):** F1 micro = 0.6285, Mean Dice = 0.5849, Mean IoU = 0.4515, Precision = 0.5991, Recall = 0.6609, Mean Area Rel Error = 1.2219.
     - **Validation (35 снимков):** Mean Dice = 0.7192, F1 = 0.7644, Mean IoU = 0.5865; лучшая эпоха — 8 (val_dice = 0.7183, loss = 1.0031).
   - Цели ТЗ (Recall ≥ 98% для дефектов от 5 мм и погрешность площади ≤ ±15%) на текущем открытом датасете не достигнуты из-за отсутствия собственных снимков цилиндров ЧКПЗ и негативных примеров (масло, СОЖ, блики).
2. **Степень поражения («лёгкая / глубокая»):**
   - На этапе КТ 4 сегментируется бинарная маска коррозии; классификатор глубины поражения не обучен из-за отсутствия послойной разметки.
3. **Калибровка масштаба (MM_PER_PX):**
   - `MM_PER_PX` — масштаб **исходного** снимка (мм на пиксель). `area_px` считается по маске, возвращённой к размеру исходника, а не по входу U-Net 256×256; `area_mm2 = area_px × MM_PER_PX²`.
   - Расчёт площади в мм² выполняется только при наличии калибровки камеры (`MM_PER_PX`). Без калибровки возвращается `area_mm2 = null` и `calibrated = false`, а вердикт сопровождается предупреждающим сообщением о необходимости калибровки и о том, что вердикт не является приёмочным.
4. **Интеграция с ПЛК:**
   - В этапе КТ 4 реализован программный стек (ML + API + DB + UI). Эмулятор ПЛК и дискретный обмен сигналами вынесены в отдельный этап.

---

## Структура репозитория

```text
├── docker/
│   ├── backend.Dockerfile # Multi-stage Dockerfile бэкенда
│   ├── frontend.Dockerfile# Multi-stage Dockerfile фронтенда
│   ├── ml.Dockerfile      # Multi-stage Dockerfile сервиса ML-инференса
│   └── nginx.conf         # Конфигурация Nginx для фронтенда и reverse-proxy
├── docker-compose.yml     # Оркестрация сервисов db, ml, backend, frontend
├── .github/
│   └── workflows/
│       └── ci.yml         # CI: backend pytest + frontend build
├── scripts/
│   └── fetch_weights.py   # Скачивание и верификация SHA-256 весов unet.pt
├── tests/                 # Unit/API-тесты backend и калибровки
├── .dockerignore          # Исключения сборки Docker
├── .env.example           # Шаблон переменных окружения
├── pytest.ini             # Конфигурация pytest
├── docs/
│   ├── kt1/               # КТ 1: документ, схемы
│   ├── kt2/               # КТ 2: обзор, датасет, метрики
│   ├── kt3/               # КТ 3: эксперименты M1-M4
│   ├── kt4/               # КТ 4: прототип
│   └── kt5/               # КТ 5: защита
├── src/
│   ├── backend/
│   │   ├── main.py        # Основное приложение FastAPI (порт 8000, httpx async)
│   │   ├── db.py          # Сессии SQLAlchemy, без слабых дефолтов, с backfill
│   │   ├── models.py      # Модель Inspection (с upload_path и message)
│   │   ├── schemas.py     # Pydantic схемы ответов (с original_url)
│   │   ├── requirements.txt
│   │   └── requirements-test.txt
│   ├── frontend/
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   ├── tailwind.config.js
│   │   ├── vite.config.js
│   │   ├── src/
│   │   │   ├── App.jsx    # Панель оператора (React + Tailwind)
│   │   │   ├── index.css
│   │   │   └── main.jsx
│   │   └── index.html
│   └── ml/
│       ├── inference.py   # Ядро инференса U-Net, постобработка, расчет площадей
│       ├── calibration.py # Resize маски к исходнику и пересчёт площади в мм²
│       ├── service.py     # FastAPI сервис инференса (порт 8001 expose, временные файлы)
│       ├── requirements.txt
│       └── kt3/           # Эксперименты КТ 3
├── dataset/               # Данные (не коммитятся в git)
└── README.md
```
