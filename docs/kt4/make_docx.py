"""Генерация документа КТ 4 «Прототип»."""

import hashlib
import os
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
MONO = "Consolas"
BASE = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE, "КТ 4. Прототип.docx")
PDF_PATH = os.path.join(BASE, "КТ 4. Прототип.pdf")
HASH_PATH = DOC_PATH + ".sha256"
FIG_ARCH = os.path.join(BASE, "figures", "architecture.png")
FIG_UI = os.path.join(BASE, "figures", "ui_screenshot.png")
HEADING_COLOR = (0x1F, 0x38, 0x64)


def style_run(run, size=14, bold=False, italic=False, font=FONT):
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), font)


def para(doc, text="", size=14, bold=False, italic=False, align="justify", indent=True,
         before=0, after=0, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.first_line_indent = Cm(1.25 if indent else 0)
    p.alignment = {
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
    }[align]
    run = p.add_run(text)
    style_run(run, size, bold, italic)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p


def labeled(doc, label, text, size=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.keep_together = True
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(p.add_run(label + " "), size, bold=True)
    style_run(p.add_run(text), size)
    return p


def numbered_list(doc, items, size=14):
    for i, text in enumerate(items, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.keep_together = True
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        style_run(p.add_run(f"{i}. "), size, bold=False)
        style_run(p.add_run(text), size)


def heading(doc, text, page_break=False):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    if page_break:
        p.paragraph_format.page_break_before = True
    run = p.add_run(text)
    style_run(run, 14, bold=True)
    run.font.color.rgb = RGBColor(*HEADING_COLOR)
    return p


def subheading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    style_run(run, 14, bold=True)
    run.font.color.rgb = RGBColor(*HEADING_COLOR)
    return p


def bullet(doc, text, size=14, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_prefix:
        style_run(p.add_run(bold_prefix), size, bold=True)
    style_run(p.add_run(text), size)
    return p


def numbered(doc, text, size=14):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(p.add_run(text), size)
    return p


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def shade_paragraph(p, fill="F2F2F2"):
    p_pr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def no_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def table(doc, headers, rows, widths, font_size=11):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    hdr = t.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_after = Pt(0)
        style_run(p.add_run(h), font_size, bold=True)
        shade_cell(cell, "D9E2F3")
    no_split(hdr)
    hdr._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for row in rows:
        cells = t.add_row().cells
        no_split(t.rows[-1])
        for i, value in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            style_run(p.add_run(str(value)), font_size)
    for ri, row in enumerate(t.rows):
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                if ri < len(t.rows) - 1:
                    p.paragraph_format.keep_with_next = True
    tbl_pr = t._tbl.tblPr
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(int(sum(widths) * 567)))
    jc = tbl_pr.find(qn("w:jc"))
    if jc is not None:
        jc.addprevious(tbl_w)
    else:
        tbl_pr.append(tbl_w)
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", 20), ("left", 80), ("bottom", 20), ("right", 80)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    t._tbl.tblPr.append(mar)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def code_block(doc, lines):
    for text in lines:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.right_indent = Cm(0.5)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        shade_paragraph(p, "F2F2F2")
        style_run(p.add_run(text), 10.5, font=MONO)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    style_run(run, 10)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    for el in (fld_begin, instr, fld_sep, fld_end):
        run._r.append(el)


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


def picture(doc, path, caption, width=16.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent = Cm(0)
    c.paragraph_format.space_after = Pt(4)
    style_run(c.add_run(caption), 14, italic=True)


def build():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(14)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
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
    add_page_number(section)

    doc.core_properties.title = "КТ 4. Прототип"
    doc.core_properties.subject = "ТЗ 1. Система обнаружения ржавчины и коррозии"
    doc.core_properties.author = "Райимжонов Абдусамад Тулкинович"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.line_spacing = 1.0
    title.paragraph_format.space_after = Pt(2)
    r = title.add_run("КТ 4. Прототип")
    style_run(r, 18, bold=True)
    r.font.color.rgb = RGBColor(*HEADING_COLOR)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.first_line_indent = Cm(0)
    sub.paragraph_format.line_spacing = 1.0
    sub.paragraph_format.space_after = Pt(10)
    style_run(sub.add_run("ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"), 14, italic=True)

    table(doc, ["Поле", "Значение"], [
        ["Проект (ТЗ)", "ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"],
        ["Дата сдачи", "19.11.2026"],
        ["Капитан", "Райимжонов Абдусамад Тулкинович"],
        ["Участники", "Индивидуальная работа. Все этапы проекта выполняются самостоятельно"],
        ["Репозиторий", "https://github.com/RvadRA/rust-corrosion-detection"],
    ], widths=[4.2, 12.8])

    heading(doc, "1. Выбранное решение")
    bullet(doc, "U-Net M4 для бинарной сегментации ржавчины + FastAPI + PostgreSQL + React. "
                "Модель работает на CPU, вход 256×256 RGB, порог 0,5, морфологическая постобработка "
                "и удаление компонент меньше 24 px.",
           bold_prefix="Модель / связка методов: ")
    bullet(doc, "в КТ 3 U-Net M4 показала лучший F1 micro (0,6285) и Dice/IoU macro "
                "(0,5849 / 0,4515). RandomForest M3 отстал всего на 0,005 F1, но заметно хуже "
                "на Virginia Tech (0,567 против 0,612) и менее устойчив к доменному сдвигу. "
                "U-Net даёт более ровное качество на Ostrava, Virginia Tech и Pipelines, поэтому "
                "выбрана для прототипа. HSV/Lab оставлены как быстрый интерпретируемый fallback. "
                "Подробности — в docs/kt3/kt3.md и docs/kt3/results/unet.json.",
           bold_prefix="Почему именно она: ")
    table(doc, ["Часть", "Технология", "Кто делал"], [
        ["Данные и модель", "Python 3.11, PyTorch 2.3.1+cpu, NumPy, SciPy, Pillow, U-Net M4",
         "Райимжонов А. Т."],
        ["Backend", "FastAPI, SQLAlchemy, PostgreSQL 16, httpx, Pillow", "Райимжонов А. Т."],
        ["Frontend", "React, Vite, Tailwind CSS, Lucide Icons, Nginx", "Райимжонов А. Т."],
        ["Инфраструктура", "Docker, Docker Compose, multi-stage, healthchecks", "Райимжонов А. Т."],
        ["Исследование", "M1–M4, метрики, аудит, подготовка данных", "Райимжонов А. Т."],
    ], widths=[4.2, 8.6, 4.2], font_size=11)

    heading(doc, "2. Устройство прототипа")
    picture(doc, FIG_ARCH, "Рис. 1. Архитектура прототипа КТ 4", width=16.0)
    subheading(doc, "2.1. Путь «вход → результат»")
    numbered_list(doc, [
        "Оператор загружает снимок цилиндра через браузер (http://localhost:3000) или отправляет его "
        "в POST /api/v1/inspect.",
        "Backend принимает файл потоково, проверяет расширение, размер до 32 МБ и целостность "
        "изображения через Pillow. Исходник сохраняется в uploads/{inspection_id}_{filename}.",
        "Backend вызывает ML-сервис по внутреннему адресу http://ml:8001/inspect, передавая "
        "inspection_id и, если задан, mm_per_px. ML-сервис обрабатывает исходник через временный "
        "файл и сразу удаляет его, чтобы не создавать дубликаты.",
        "U-Net возвращает маску, overlay, area_px, confidence и признак калибровки calibrated. "
        "Маска и overlay сохраняются в общие volume-каталоги masks/ и overlays/ под ID инспекции.",
        "Backend рассчитывает вердикт: площадь 0 px — НОРМА; MM_PER_PX не задан — ВНИМАНИЕ, "
        "area_mm2 = null, calibrated = false; площадь ≤ 20 мм² — ВНИМАНИЕ; площадь > 20 мм² — БРАК.",
        "Запись сохраняется в PostgreSQL. Интерфейс показывает overlay, маску или исходник, вердикт, "
        "площадь, уверенность и журнал проверок; CSV выгружается с UTF-8 BOM для Excel.",
        "Retention-задача при старте и каждые 12 часов удаляет записи и связанные файлы старше 30 дней.",
    ])

    subheading(doc, "2.2. Основные компоненты")
    table(doc, ["Компонент", "Назначение"], [
        ["frontend", "Панель оператора: загрузка, результат, история, переключение overlay/mask/original, CSV, индикатор health"],
        ["backend", "REST API, валидация, бизнес-логика вердиктов, PostgreSQL, CSV, раздача /media, retention"],
        ["ml", "Изолированный сервис инференса U-Net, multipart, временные файлы, маска и overlay"],
        ["db", "PostgreSQL 16, таблица inspections, хранение метаданных и путей к файлам"],
        ["app_data", "Общий volume: uploads/, masks/, overlays/"],
    ], widths=[3.2, 13.8], font_size=11)

    subheading(doc, "2.3. API прототипа")
    table(doc, ["Метод", "Путь", "Назначение"], [
        ["GET", "/health", "Статус backend, БД и ML"],
        ["POST", "/api/v1/inspect", "Загрузка снимка и запуск инспекции"],
        ["GET", "/api/v1/results", "Журнал проверок с пагинацией"],
        ["GET", "/api/v1/results/{id}", "Одна запись по ID"],
        ["GET", "/api/v1/results.csv", "Выгрузка журнала в CSV (UTF-8 BOM, разделитель ;)"],
        ["GET", "/media/...", "Исходники, маски и overlay"],
    ], widths=[1.8, 6.0, 9.2], font_size=11)

    heading(doc, "3. Как запустить")
    para(doc, "Требования: Docker Desktop или Docker Engine с Compose, Git, Python 3.10+ для скрипта "
              "загрузки весов, 4 ГБ свободной RAM. GPU не требуется: инференс идёт на CPU. Проверено "
              "на Windows 11 и Docker Desktop.")
    code_block(doc, [
        "git clone https://github.com/RvadRA/rust-corrosion-detection.git",
        "cd rust-corrosion-detection",
        "",
        "cp .env.example .env",
        "",
        "python scripts/fetch_weights.py",
        "",
        "docker compose up --build -d",
        "docker compose ps",
        "curl http://localhost:8000/health",
    ])
    para(doc, "Для Windows PowerShell вместо cp используется Copy-Item .env.example .env.")
    para(doc, "Ожидаемый health: status = ok, db = connected, ml = ready, retention_days = 30.")
    para(doc, "Адреса: интерфейс оператора — http://localhost:3000; OpenAPI/Swagger — "
              "http://localhost:8000/docs; проверка API — http://localhost:8000/health.")
    para(doc, "Остановка: docker compose stop; полная остановка — docker compose down; удаление томов — "
              "docker compose down -v.")
    para(doc, "Подробная инструкция: README.md в корне репозитория.")

    heading(doc, "3.1. Docker-образы")
    para(doc, "Прототип сдаётся в Docker и должен подниматься одной командой на чистом компьютере.")
    code_block(doc, [
        "git clone https://github.com/RvadRA/rust-corrosion-detection.git",
        "cd rust-corrosion-detection",
        "cp .env.example .env",
        "python scripts/fetch_weights.py",
        "docker compose up --build",
    ])
    para(doc, "Выполнение требований к образам:", bold=True, indent=False, after=0)
    for text in [
        "На каждый сервис свой Dockerfile, все сервисы описаны в docker-compose.yml.",
        "Версии зафиксированы: python:3.11-slim-bookworm, postgres:16-alpine, node:20-alpine3.20, "
        "nginx:1.27.0-alpine; Python-зависимости — в requirements.txt, frontend — в package-lock.json.",
        "Есть .dockerignore; ML, backend и frontend собираются в multi-stage.",
        "Веса не лежат в git: скачиваются scripts/fetch_weights.py и подключаются томом "
        "./dataset/processed/kt3/unet.pt:/models/unet.pt:ro; путь задаётся через MODEL_PATH.",
        "Настройки — через переменные окружения, есть .env.example; .env и веса исключены из git.",
        "GPU не нужна: используется CPU-only PyTorch. CUDA-режим не требуется и не описан как обязательный.",
        "Приложение запускается не от root: appuser в ML/backend, nginx во frontend; логи — в stdout; "
        "у всех сервисов есть healthcheck.",
        "В README описаны требования, запуск, остановка, адреса и порты.",
    ]:
        bullet(doc, text, size=12)

    table(doc, ["Сервис", "Dockerfile", "Базовый образ", "Порт", "GPU", "Размер, ГБ"], [
        ["ML / CV", "docker/ml.Dockerfile", "python:3.11-slim-bookworm", "8001, внутри", "нет", "1,74"],
        ["Backend", "docker/backend.Dockerfile", "python:3.11-slim-bookworm", "8000, внешний", "нет", "0,38"],
        ["Frontend", "docker/frontend.Dockerfile", "node:20-alpine3.20 → nginx:1.27.0-alpine",
         "3000, внешний", "нет", "0,07"],
        ["PostgreSQL", "официальный образ", "postgres:16-alpine", "5432, внутри", "нет", "0,42"],
    ], widths=[3.0, 4.3, 4.9, 2.5, 1.2, 1.6], font_size=10)
    para(doc, "Фактическое состояние локального запуска: все четыре контейнера — healthy; "
              "corrosion_frontend доступен на 3000, corrosion_backend — на 8000, corrosion_ml и "
              "corrosion_db — только внутри docker-сети.")
    para(doc, "Чистый старт подтверждён: GitHub Release v1.0.0-kt3 доступен (HTTP 302), "
              "scripts/fetch_weights.py в пустом каталоге завершился с кодом 0, SHA-256 совпал, "
              "docker compose up --build поднял четыре контейнера в состоянии healthy.",
         size=12, italic=True, indent=False, before=2, after=0)

    heading(doc, "4. Демо-сценарии")
    para(doc, "Проверенные сценарии и фактические результаты:")
    table(doc, ["Сценарий", "Ожидаемый результат", "Фактический результат", "Пройден"], [
        ["Загрузка 01.jpg через UI", "Карточка результата, overlay, запись в журнале",
         "HTTP 200; area_px = 619904, confidence = 0.7307, area_mm2 = null, calibrated = false, "
         "вердикт ВНИМАНИЕ; запись появилась в журнале", "да"],
        ["POST /api/v1/inspect с 01.jpg", "JSON с полями маски и overlay",
         "200; те же area_px и confidence; original_url, mask_url, overlay_url отдаются", "да"],
        ["Невалидный файл README.md", "HTTP 415",
         "HTTP 415, сообщение о неподдерживаемом формате", "да"],
        ["Повреждённый JPEG", "HTTP 400",
         "HTTP 400, сообщение о повреждённом изображении", "да"],
        ["Медиа для всех записей журнала", "original_url, mask_url, overlay_url → 200",
         "4 записи; все три URL для каждой записи → 200", "да"],
        ["GET /api/v1/results.csv", "200, UTF-8 BOM, разделитель ;",
         "200, 538 байт, BOM присутствует, заголовки и строки корректны", "да"],
        ["ML-сервис недоступен", "HTTP 503, понятная ошибка",
         "503; ML-сервис недоступен, после старта ml → healthy", "да"],
        ["Retention 30 дней", "Старые записи и файлы удаляются",
         "Тестовая запись состарена на 31 день; после restart backend → 404, upload/mask/overlay удалены",
         "да"],
        ["MM_PER_PX задан", "area_mm2 рассчитана, вердикт по порогу 20 мм²",
         "При MM_PER_PX=0,1: area_mm2 = 6199,04, calibrated = true, вердикт БРАК", "да"],
        ["Чистый запуск на другой машине", "docker compose up --build → 4 healthy",
         "Release v1.0.0-kt3 доступен, fetch_weights.py скачал веса с совпавшим SHA-256, "
         "4 контейнера healthy", "да"],
    ], widths=[4.0, 4.4, 6.4, 2.2], font_size=10)
    para(doc, "Проверки ML down, retention и MM_PER_PX выполнены 19.11.2026; retention — на "
              "синтетически состаренной тестовой записи. После проверок в БД остались 4 валидные записи.",
         before=2, after=0)
    para(doc, "Сценарий с UI технически пройден; вердикт не является приёмочным, так как MM_PER_PX "
              "не задан.", size=12, italic=True, indent=False, before=2, after=0)
    picture(doc, FIG_UI, "Рис. 2. Интерфейс оператора: загрузка, вердикт, overlay и журнал проверок",
            width=15.0)
    para(doc, "На скриншоте: загрузка снимка, вердикт ВНИМАНИЕ, overlay с красной маской, площадь "
              "в пикселях, уверенность 73,1 % и журнал проверок. Так как MM_PER_PX не задан, площадь "
              "в мм² не рассчитывается, а вердикт сопровождается предупреждением и не является "
              "приёмочным.")

    heading(doc, "5. Метрики на прототипе")
    para(doc, "Качество модели ниже — это метрики U-Net M4 на замороженном test из КТ 3 "
              "(79 изображений). Это тот же чекпоинт, который используется в прототипе. Это не "
              "приёмочный тест на 200 деталях.")
    table(doc, ["Метрика", "Цель из ТЗ", "Факт"], [
        ["Recall пятен от 5 мм (spot-level, IoU ≥ 0,5)", "≥ 98 %", "15,6 % — не достигнуто"],
        ["Ошибка площади", "≤ 15 %", "122 % — не достигнуто"],
        ["Точность степени «лёгкая / глубокая»", "≥ 95 %", "Не оценивалась: нет разметки степени"],
        ["Точность вердикта", "≥ 95 %", "Не оценивалась: нет трёхклассовой разметки и калибровки"],
        ["Приёмочный тест на 200 деталях (100 / 50 / 50)", "100 / 50 / 50",
         "Не проводился: test — 79 изображений"],
        ["Pixel F1 micro (диагностическая)", "Не задана в ТЗ", "0,6285"],
        ["Pixel Precision / Recall (micro)", "Не заданы в ТЗ", "0,5991 / 0,6609"],
        ["Mean Dice / IoU (macro)", "Не заданы в ТЗ", "0,5849 / 0,4515"],
        ["Скорость инференса на CPU", "Не задана в ТЗ", "17,6 FPS (КТ 3, test)"],
    ], widths=[6.2, 3.0, 7.8], font_size=11)
    subheading(doc, "5.1. Инженерные проверки прототипа")
    table(doc, ["Проверка", "Ожидание", "Факт", "Статус"], [
        ["docker compose ps", "4 сервиса healthy", "4/4 healthy", "да"],
        ["GET /health", "status = ok, БД и ML доступны",
         "db = connected, ml = ready, retention 30 дней", "да"],
        ["UI «вход → результат»", "Результат без ручных шагов",
         "Загрузка, инспекция, overlay и запись в журнале", "да"],
        ["Валидация расширения", "415", "415", "да"],
        ["Валидация повреждённого изображения", "400", "400", "да"],
        ["CSV", "200 + UTF-8 BOM", "200, BOM есть", "да"],
        ["Медиа всех записей", "200", "4 записи, все URL 200", "да"],
        ["Чистый запуск по README", "4 healthy на чужой машине",
         "fetch_weights.py — код 0, SHA-256 OK; 4 контейнера healthy", "да"],
        ["ML down", "503", "503; после старта ml → healthy", "да"],
        ["Retention", "Удаление старше 30 дней",
         "Тестовая запись 31 день: 404, upload/mask/overlay удалены", "да"],
        ["MM_PER_PX", "area_mm2 и calibrated",
         "0,1 мм/px: 6199,04 мм², calibrated = true, БРАК", "да"],
    ], widths=[4.4, 4.2, 6.2, 2.2], font_size=10)
    para(doc, "Вывод по метрикам.", bold=True, indent=False, before=2, after=0)
    para(doc, "Прототип технически проходит путь «вход → результат», но целевые метрики ТЗ не "
              "достигнуты. F1 около 0,63 — диагностический уровень, а не приёмочный. Основные причины: "
              "доменный сдвиг открытых датасетов, отсутствие собственных снимков цилиндров ЧКПЗ, "
              "отсутствие чистых негативных кадров, downsample до 256 px и обучение U-Net на CPU "
              "всего 12 эпох.")

    heading(doc, "6. Известные ограничения")
    numbered_list(doc, [
        "Качество сегментации недостаточно для приёмки. Recall пятен 15,6 % при цели ≥ 98 %, "
        "ошибка площади 122 % при цели ≤ 15 %. Модель обучена на открытых данных (Ostrava, "
        "Virginia Tech, Pipelines), а не на цилиндрах ЧКПЗ.",
        "Нет классификатора степени и трёхклассового вердикта. Разметка «лёгкая / глубокая» "
        "отсутствует, поэтому БРАК по степени и точность вердикта ≥ 95 % не проверены.",
        "Нет автоматической калибровки мм/пиксель. Механизм MM_PER_PX проверен: при 0,1 мм/px "
        "площадь 6199,04 мм², calibrated = true, вердикт БРАК. Но значение задаётся вручную по "
        "эталону; при пустом MM_PER_PX возвращается area_mm2 = null, calibrated = false, а вердикт "
        "ВНИМАНИЕ является предупреждением, а не приёмочным решением.",
        "Нет интеграции с ПЛК, камерой и линией. Реализован программный стек ML + API + БД + UI; "
        "триггер камеры, освещение, дискретный обмен с ПЛК и эмулятор линии вынесены за рамки КТ 4.",
        "Ограничение validation КТ 3. В validation 35 изображений, Virginia Tech отсутствует; "
        "пороги и early stopping на VT не настраивались. VT-результат не является независимой "
        "валидацией гиперпараметров.",
        "Низкое нативное разрешение. Вход 256×256 теряет мелкие пятна; для 5-мм дефектов нужны "
        "crop'ы 512–1024 px или нативное разрешение.",
        "Retention проверен на синтетически состаренной записи. Запись с created_at 31 день назад "
        "и её три файла удалены при старте backend; на реальном 30-дневном архиве это ещё не наблюдалось.",
        "Один узел и локальный volume. Нет очереди, репликации, горизонтального масштабирования "
        "и резервного копирования; при потере app_data пропадут медиафайлы.",
        "Безопасность базовая. Нет аутентификации, TLS и rate limiting; прототип рассчитан на "
        "локальный запуск, а не на открытый интернет.",
        "Наблюдаемость ограничена. Логи пишутся в stdout, но нет метрик, трассировки, алертов "
        "и дашбордов.",
        "Не запущены альтернативы. YOLOv8-seg, SegFormer-B0 и PatchCore не проверены на том же "
        "test; это следующий этап исследования.",
    ])
    para(doc, "Что сделать до защиты:", bold=True, indent=False, before=4, after=0)
    numbered_list(doc, [
        "Снять 300 чистых кадров и 20–50 реальных деталей, добавить блики, царапины, масло и СОЖ "
        "как hard negatives.",
        "Обучить модель на нативном разрешении или crop'ах 512–1024 px, взять предобученный энкодер, "
        "добавить GPU и TTA.",
        "Добавить голову степени и калибровку MM_PER_PX по эталону.",
        "Провести приёмочный тест на 200 деталях (100 / 50 / 50) и cross-dataset тест.",
        "Проверить retention на реальном 30-дневном архиве и калибровку на эталонной детали.",
        "Добавить эмулятор ПЛК, резервное копирование, аутентификацию и минимальный мониторинг.",
    ])

    heading(doc, "Чек-лист сдачи")
    checklist = [
        ("Прототип проходит путь «вход → результат» без ручных шагов", True),
        ("Поднимается командой docker compose up --build на чужом компьютере по README — "
         "чистый старт подтверждён", True),
        ("Все демо-сценарии проверены — ML down, retention и MM_PER_PX проверены", True),
        ("Метрики сравнены с целями из ТЗ — сравнены; цели по recall и площади не достигнуты", True),
        ("Docker-образы соответствуют требованиям из п. 3.1", True),
        ("В репозитории нет весов, паролей и персональных данных — .env и unet.pt исключены из git",
         True),
    ]
    for text, done in checklist:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        style_run(p.add_run(("☒ " if done else "☐ ") + text), 12)

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
