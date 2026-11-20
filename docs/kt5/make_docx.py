"""Генерация документа КТ 5 «Защита»."""

import hashlib
import importlib.util
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
KT4_PATH = os.path.join(BASE, "..", "kt4", "make_docx.py")
DOC_PATH = os.path.join(BASE, "КТ 5. Защита.docx")
PDF_PATH = os.path.join(BASE, "КТ 5. Защита.pdf")
HASH_PATH = DOC_PATH + ".sha256"
FIG_TOBE = os.path.join(BASE, "..", "kt1", "tobe.png")
FIG_MODELS = os.path.join(BASE, "figures", "models_f1.png")
HEADING_COLOR = (0x1F, 0x38, 0x64)


def load_kt4():
    spec = importlib.util.spec_from_file_location("kt4_docx", KT4_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DOC_PATH = DOC_PATH
    module.PDF_PATH = PDF_PATH
    module.HASH_PATH = HASH_PATH
    return module


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def has_user_edits():
    if not os.path.exists(DOC_PATH):
        return False
    if not os.path.exists(HASH_PATH):
        return True
    expected = open(HASH_PATH, encoding="utf-8").read().strip().split()[0]
    return sha256(DOC_PATH) != expected


def build():
    kt4 = load_kt4()
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = kt4.FONT
    st.font.size = Pt(14)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), kt4.FONT)
    st.paragraph_format.first_line_indent = Cm(0)
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.space_after = Pt(0)
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, Cm(2))
    kt4.add_page_number(section)

    doc.core_properties.title = "КТ 5. Защита"
    doc.core_properties.subject = "ТЗ 1. Система обнаружения ржавчины и коррозии"
    doc.core_properties.author = "Райимжонов Абдусамад Тулкинович"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.line_spacing = 1.0
    title.paragraph_format.space_after = Pt(2)
    r = title.add_run("КТ 5. Защита")
    kt4.style_run(r, 18, bold=True)
    r.font.color.rgb = RGBColor(*HEADING_COLOR)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.first_line_indent = Cm(0)
    sub.paragraph_format.line_spacing = 1.0
    sub.paragraph_format.space_after = Pt(10)
    kt4.style_run(sub.add_run("ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"), 14,
                  italic=True)

    kt4.table(doc, ["Поле", "Значение"], [
        ["Проект (ТЗ)", "ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"],
        ["Дата защиты", "19.11.2026"],
        ["Капитан", "Райимжонов Абдусамад Тулкинович"],
        ["Участники", "Индивидуальная работа. Все этапы проекта выполняются самостоятельно"],
        ["Репозиторий", "https://github.com/RvadRA/rust-corrosion-detection"],
    ], widths=[4.2, 12.8])

    kt4.heading(doc, "1. Задача и бизнес-процесс")
    kt4.para(doc, "Проблема. После обработки цилиндр осматривает оператор ОТК: вручную, по сменам "
                  "и при разном освещении. Мелкие пятна от 5 мм пропускаются, площадь не измеряется, "
                  "фото и результат не сохраняются. Из-за этого нельзя проверить порог 20 мм², "
                  "подтвердить спор с поставщиком и стабильно уложиться в такт линии. Повторный "
                  "осмотр мастером добавляет субъективности и времени.")
    kt4.para(doc, "Что заменяет система. Ручной визуальный осмотр и повторный осмотр мастером. "
                  "Камера снимает боковую поверхность и кромки, ML-сервис находит ржавчину, считает "
                  "площадь и формирует вердикт. Оператор видит снимок с выделенными дефектами, а ПЛК "
                  "получает сигнал Норма / Внимание / Брак / Ошибка системы.")
    kt4.subheading(doc, "Как будет устроен процесс")
    kt4.numbered_list(doc, [
        "Деталь останавливается на позиции контроля; камера делает 4–8 кадров за оборот или 3–4 камеры "
        "снимают по кругу.",
        "U-Net строит маску ржавчины; система считает площадь в пикселях, при калибровке — в мм².",
        "По правилу ТЗ формируется вердикт: нет ржавчины — НОРМА; только лёгкая и ≤ 20 мм² — "
        "ВНИМАНИЕ; глубокая или > 20 мм² — БРАК.",
        "Результат сохраняется в архив на 30 дней, выгружается в CSV, сигнал уходит в ПЛК по OPC UA "
        "или Profinet.",
        "Инженер настраивает пороги без правки кода, оператор разбирает спорные случаи, технолог "
        "смотрит статистику.",
    ])
    kt4.para(doc, "Границы прототипа. В КТ 4 реализован программный стек: ML + API + PostgreSQL + "
                  "интерфейс + Docker. Камера, освещение, механика, ПЛК и линия не входят в прототип: "
                  "для них подготовлены требования и план интеграции.")
    kt4.picture(doc, FIG_TOBE, "Рис. 1. Бизнес-процесс «как будет»: система заменяет ручной осмотр, "
                              "а решение уходит в ПЛК и архив.", width=14.0)

    kt4.heading(doc, "2. Что сравнили")
    kt4.para(doc, "Сравнение M1–M4 выполнено на одном замороженном test из КТ 3: 79 изображений, "
                  "256×256, бинарные маски «ржавчина / фон». Ostrava — 15, Virginia Tech — 44, "
                  "Pipelines — 20. Пороги и early stopping настраивались только на val, VT в "
                  "validation отсутствует.")
    kt4.table(doc, ["Метод", "F1 micro", "Dice macro", "IoU macro", "Ошибка площади", "VT F1",
                    "FPS (CPU)"], [
        ["M1. HSV-порог", "0,551", "0,533", "0,405", "172 %", "0,496", "201,5"],
        ["M2. Lab-порог", "0,564", "0,534", "0,406", "125 %", "0,513", "105,2"],
        ["M3. RandomForest цвет + текстура", "0,623", "0,582", "0,450", "120 %", "0,567", "10,6"],
        ["M4. U-Net", "0,629", "0,585", "0,452", "122 %", "0,612", "17,6"],
    ], widths=[4.8, 2.0, 2.0, 2.0, 2.2, 1.8, 1.9], font_size=10)
    kt4.picture(doc, FIG_MODELS, "Рис. 2. M4 U-Net даёт лучший F1 micro и более ровное качество "
                                "на трёх источниках.", width=15.2)
    kt4.para(doc, "Почему для прототипа выбрана M4 U-Net. У неё лучший F1 micro (0,629) и Dice/IoU "
                  "macro (0,585 / 0,452). M3 RandomForest отстаёт всего на 0,005 F1, но заметно хуже "
                  "на Virginia Tech (0,567 против 0,612). U-Net лучше держит границы и площадь, не "
                  "зависит от AGPL-лицензии YOLO и работает на CPU. M3 оставлен как интерпретируемый "
                  "baseline, M1/M2 HSV/Lab — как быстрый fallback.")
    kt4.para(doc, "Дополнительная проверка на публичной VT-выборке. Отдельно собраны 200 пар "
                  "Virginia Tech (44 официальных test + 156 train), DOI 10.7294/16624663.v2, CC0. "
                  "На 44 test при 512×512 U-Net дал F1 micro 0,6129, IoU micro 0,4418, Dice macro "
                  "0,5364, IoU macro 0,4051, ошибку площади 1,0013. Это совпадает с VT-результатом "
                  "КТ 3. Выборка не является приёмкой: VT — мосты и состояние конструкций, а не "
                  "гильзы ЧКПЗ; 156 train-кадров пересекаются с обучением КТ 3, поэтому F1 0,6483 "
                  "на них и 0,6415 на всех 200 — leakage, а не честная оценка.")

    kt4.heading(doc, "3. Результат против критериев приёмки")
    kt4.table(doc, ["Критерий из ТЗ", "Требование", "Результат", "Выполнено"], [
        ["Recall пятен от 5 мм", "≥ 98 %", "15,6 % (spot-level, IoU ≥ 0,5)", "нет"],
        ["Погрешность площади", "≤ ±15 %", "122 % (M4)", "нет"],
        ["Правильная степень «лёгкая / глубокая»", "≥ 95 %",
         "не оценивалась: нет разметки степени", "нет"],
        ["Тест на 200 деталях (100 / 50 / 50)", "200 реальных деталей",
         "79 изображений, реальных деталей 0", "нет"],
        ["Пропуск брака", "≤ 2 %", "не оценивался", "нет"],
        ["Ложная отбраковка", "≤ 3 %", "не оценивалась", "нет"],
        ["Время проверки", "не больше такта линии", "17,6 FPS на CPU; такт не задан",
         "не проверено"],
        ["Вердикты", "«Норма», «Внимание», «Брак», «Ошибка системы»",
         "НОРМА / ВНИМАНИЕ / БРАК; сбой ML → HTTP 503", "частично"],
        ["Архив", "≥ 30 дней", "retention 30 дней; тест на записи 31 день", "да"],
        ["Выгрузка в CSV", "есть", "HTTP 200, UTF-8 BOM, разделитель ;", "да"],
        ["Настройка порогов инженером", "без правки кода",
         "MM_PER_PX через .env; UI/API настройки нет", "частично"],
        ["Правило вердикта", "0 / 20 мм² / глубокая",
         "0 — норма; ≤ 20 — внимание; > 20 — брак; без калибровки — внимание", "частично"],
        ["Интеграция с ПЛК", "Profinet или OPC UA", "не реализована", "нет"],
    ], widths=[5.0, 3.6, 5.4, 2.8], font_size=10)
    kt4.para(doc, "Итог. Приёмка не пройдена. По ключевым критериям качества — recall пятен, площадь, "
                  "степень, вердикт и 200 деталей — результат ниже требований ТЗ. Это диагностический "
                  "уровень F1 ≈ 0,63, а не промышленная точность. Причины: доменный сдвиг (мосты и "
                  "трубы вместо цилиндров), отсутствие чистых кадров и hard negatives, downsample до "
                  "256 px, обучение на CPU 12 эпох без предобученного энкодера.")
    kt4.subheading(doc, "Что уже работает как инженерный прототип")
    for text in [
        "Путь «вход → результат» без ручных шагов: загрузка, инспекция, overlay, запись в журнал.",
        "Все 4 контейнера healthy; /health показывает db=connected, ml=ready, retention 30 дней.",
        "Валидация файлов: .md → 415, повреждённый JPEG → 400, лимит 32 МБ.",
        "CSV с UTF-8 BOM и разделителем ; — все медиа URL отдают 200.",
        "ML down → 503 с понятным сообщением; после старта ML → снова ready.",
        "Retention проверен на синтетически состаренной записи: 404 и удаление upload/mask/overlay.",
        "MM_PER_PX=0,1 → area_mm2=6199,04, calibrated=true, вердикт БРАК.",
        "Чистый старт подтверждён: Release v1.0.0-kt3, fetch_weights.py, SHA-256, "
        "docker compose up --build.",
    ]:
        kt4.bullet(doc, text, size=12)

    kt4.heading(doc, "4. Демонстрация")
    kt4.para(doc, "Демо — 5–6 минут, чтобы осталось время на вопросы. Показываем не «красивую "
                  "картинку», а полный путь и отказные сценарии.")
    kt4.table(doc, ["Сценарий", "Что показываем", "Ожидаемый результат", "Статус"], [
        ["docker compose ps + /health", "4 контейнера, БД и ML",
         "4/4 healthy; db=connected, ml=ready", "да"],
        ["Загрузка 01.jpg через UI", "Результат, overlay, журнал",
         "ВНИМАНИЕ, area_px=619904, confidence=0,7307, area_mm2=null", "да"],
        ["MM_PER_PX=0,1", "Калиброванная площадь и вердикт",
         "area_mm2=6199,04, calibrated=true, БРАК", "да"],
        ["GET /api/v1/results.csv", "Выгрузка журнала", "200, UTF-8 BOM, ; , 4 строки", "да"],
        ["ML down", "Отказ ML-сервиса",
         "503 с понятным сообщением; после старта ML → healthy", "да"],
        ["Retention 30 дней", "Состаренная запись", "404; upload/mask/overlay удалены", "да"],
        ["Чистый старт", "Release + веса + compose",
         "SHA-256 совпал; 4 контейнера healthy", "да"],
    ], widths=[4.2, 4.3, 6.2, 1.9], font_size=10)
    kt4.subheading(doc, "Порядок показа")
    kt4.numbered_list(doc, [
        "docker compose ps и curl http://localhost:8000/health — фиксируем, что стенд живой.",
        "В UI загружаем 01.jpg; показываем overlay, вердикт, площадь, уверенность и запись в журнале.",
        "Открываем CSV; показываем BOM и разделитель.",
        "В терминале останавливаем ML, повторяем инспекцию → 503; поднимаем ML → healthy.",
        "Показываем retention на состаренной записи или заранее сделанный скриншот.",
        "Возвращаемся к выводу: прототип технически работает, качество модели — нет.",
    ])
    kt4.para(doc, "Запасное видео. Видео будет записано и положено в docs/kt5/demo_backup.mp4; "
                  "ссылка будет добавлена в README и этот отчёт. Пока запасной вариант — "
                  "docs/kt4/figures/ui_screenshot.png, таблица сценариев выше и этот отчёт. Если "
                  "Docker не поднимается на защите, показываем видео и скриншоты, а не тратим время "
                  "на починку.")

    kt4.heading(doc, "5. Рекомендация заказчику")
    kt4.labeled(doc, "Что внедрять.", "U-Net M4 как baseline для пилота, а не как готовую "
                 "промышленную модель. Рядом оставить HSV/Lab fallback и RandomForest M3 для сравнения "
                 "и объяснимости. YOLOv8-seg не внедрять без коммерческой лицензии: AGPL-3.0 требует "
                 "раскрытия кода сетевого сервиса. SegFormer-B0 не внедрять до проверки лицензии весов "
                 "NVIDIA. Для степени «лёгкая / глубокая» нужна отдельная голова и разметка.")
    kt4.subheading(doc, "Какое железо нужно")
    kt4.table(doc, ["Компонент", "Рекомендация"], [
        ["Камера", "Цветная 5 МП, глобальный затвор, GigE; ≤ 0,2 мм/пиксель"],
        ["Съёмка", "4–8 кадров за оборот на роликах или 3–4 камеры по кругу"],
        ["Свет", "5000–6500 К, CRI ≥ 90, рассеянный купол, защита от бликов"],
        ["Защита", "IP65 для камер и света, защита от пыли, СОЖ и вибрации"],
        ["Вычисления", "Edge-сервер или ПК с CPU; для линии — GPU/ускоритель; 16 ГБ RAM"],
        ["Хранение", "30 дней архива, резервное копирование media"],
        ["Интеграция", "OPC UA или Profinet, триггер камеры, сигналы вердикта"],
    ], widths=[3.8, 13.2], font_size=11)
    kt4.subheading(doc, "Что доработать перед внедрением")
    kt4.numbered_list(doc, [
        "Снять 300 чистых кадров и 20–50 реальных деталей с дефектами; добавить блики, масло, СОЖ и "
        "царапины как hard negatives.",
        "Обучить модель на нативном разрешении или crop'ах 512–1024 px, взять предобученный энкодер, "
        "GPU, больше эпох и TTA.",
        "Добавить голову степени, калибровку мм/пиксель по эталону и проверку на 200 деталях "
        "(100 / 50 / 50).",
        "Реализовать настройку порогов в UI/API, а не только через .env.",
        "Интегрировать камеру, свет и ПЛК; проверить такт линии и поведение при сбое.",
        "Добавить аутентификацию, TLS, резервное копирование и минимальный мониторинг.",
    ])
    kt4.para(doc, "Рекомендация. Не внедрять в линию до приёмки. Запускать пилот на 20–50 деталях "
                  "параллельно с оператором, собирать ошибки и только после стабильного recall и "
                  "площади расширять на 200 деталей. Текущий результат полезен как основа и как честный "
                  "baseline, но не как замена ОТК.")

    kt4.heading(doc, "6. Вклад участников")
    kt4.table(doc, ["Участник", "Что сделал за проект"], [
        ["Райимжонов Абдусамад Тулкинович",
         "Анализ ТЗ и вопросы заказчику; бизнес-процессы «как есть» / «как будет»; обзор 11 источников; "
         "подготовка данных Ostrava / VT / Pipelines; M1–M4, U-Net, метрики и аудит; публичная "
         "VT-выборка; FastAPI, PostgreSQL, React, Docker Compose; отчёты КТ 1–5 и презентация. "
         "Внешних участников нет — индивидуальная работа."],
    ], widths=[5.0, 12.0], font_size=11)

    kt4.heading(doc, "7. Презентация (10 минут)")
    kt4.table(doc, ["№", "Слайд", "Время"], [
        ["1", "Задача и команда", "1,0 мин"],
        ["2", "Бизнес-процесс «как есть» и «как будет»", "1,5 мин"],
        ["3", "Данные и методы", "1,5 мин"],
        ["4", "Сравнение моделей", "1,5 мин"],
        ["5", "Прототип и живое демо", "2,5 мин"],
        ["6", "Результаты против критериев приёмки", "1,0 мин"],
        ["7", "Рекомендация заказчику", "0,5 мин"],
        ["8", "Вывод и вопросы", "0,5 мин"],
    ], widths=[1.4, 12.4, 3.2], font_size=11)
    kt4.para(doc, "Файл презентации: docs/kt5/КТ 5. Презентация.pptx. Главная мысль: прототип "
                  "технически работает, но модель не прошла приёмку; внедрять можно только пилотом "
                  "после сбора своих данных.", align="left", indent=False)

    kt4.heading(doc, "Чек-лист сдачи", page_break=True)
    checklist = [
        ("Сдано всё из раздела «Что сдать» своего ТЗ — отчёт и презентация готовы, видео и коммит "
         "остаются.", False),
        ("Итоговый отчёт и презентация в репозитории — файлы созданы локально, но ещё не "
         "закоммичены.", False),
        ("Код запускается по README — подтверждено 19.11.2026: 4 контейнера healthy, health, CSV, "
         "медиа.", True),
        ("Демо проверено, есть запасное видео — демо проверено, видео ещё не записано.", False),
        ("Каждый участник готов ответить на вопросы по своей части — индивидуальная работа, материал "
         "в отчёте.", True),
    ]
    for text, done in checklist:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        kt4.style_run(p.add_run(("☒ " if done else "☐ ") + text), 12)

    kt4.heading(doc, "Приложение. Короткие ответы на вопросы")
    qa = [
        ("Почему recall 15,6 %, а не 98 %?",
         "Пятна 5 мм при downsample до 256 px теряют пиксели; модели обучены на мостах и трубах, а не "
         "на цилиндрах; нет чистых кадров и hard negatives. Нужны нативное разрешение, свои данные и "
         "приёмочный тест."),
        ("Почему F1 0,63 — это плохо?",
         "F1 pixel-level завышен крупными пятнами. На уровне пятен recall ещё ниже. Для ТЗ важен именно "
         "recall пятен от 5 мм и площадь, а не средний F1 по пикселям."),
        ("Почему U-Net, а не YOLO?",
         "U-Net дал лучший F1 и более ровный результат на трёх источниках; YOLO не запускался и требует "
         "AGPL-лицензию. YOLO остаётся кандидатом на edge-инференс после проверки."),
        ("Почему VT не в validation?",
         "В validation 35 изображений, VT там нет; пороги и early stopping на VT не настраивались. "
         "VT — только test. Публичная VT200 подтвердила результат, но не заменила приёмку."),
        ("Почему в журнале 4 записи, а не 200?",
         "Это демонстрационные записи прототипа. Приёмочный тест на 200 реальных деталях не "
         "проводился — нет данных заказчика."),
        ("Можно ли внедрять?",
         "Нет. Только пилот на 20–50 деталях параллельно с оператором, после сбора данных и повторной "
         "приёмки."),
    ]
    for q, a in qa:
        kt4.bullet(doc, a, size=12, bold_prefix=q + " ")

    if has_user_edits() and "--force" not in sys.argv:
        fallback = DOC_PATH.replace(".docx", " (new).docx")
        doc.save(fallback)
        print(f"ВНИМАНИЕ: в {DOC_PATH} есть правки пользователя.")
        print(f"Сохранено в новый файл: {fallback}")
        print("Проверьте его и запустите с --force только после подтверждения.")
        return

    tmp = DOC_PATH + ".tmp.docx"
    doc.save(tmp)
    try:
        os.replace(tmp, DOC_PATH)
        with open(HASH_PATH, "w", encoding="utf-8") as f:
            f.write(sha256(DOC_PATH) + "\n")
        print(f"saved: {DOC_PATH}")
    except PermissionError:
        fallback = DOC_PATH.replace(".docx", " v2.docx")
        os.replace(tmp, fallback)
        print(f"file is open, saved: {fallback}")


def export_pdf():
    import win32com.client

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(os.path.abspath(DOC_PATH), ReadOnly=False)
        doc.ExportAsFixedFormat(
            OutputFileName=os.path.abspath(PDF_PATH),
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0,
            Range=0,
            Item=0,
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=1,
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False,
        )
        print(f"exported: {PDF_PATH}")
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()


if __name__ == "__main__":
    build()
    if "--pdf" in sys.argv:
        export_pdf()
