"""Генерация презентации КТ 5 «Защита»."""

import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = os.path.dirname(os.path.abspath(__file__))
PPTX_PATH = os.path.join(BASE, "КТ 5. Презентация.pptx")
PDF_PATH = os.path.join(BASE, "КТ 5. Презентация.pdf")
FIG_TOBE = os.path.join(BASE, "..", "kt1", "tobe.png")
FIG_ARCH = os.path.join(BASE, "..", "kt4", "figures", "architecture.png")
FIG_UI = os.path.join(BASE, "..", "kt4", "figures", "ui_screenshot.png")
FIG_MODELS = os.path.join(BASE, "figures", "models_f1.png")

FONT = "Arial"
NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x75, 0xB6)
LIGHT = RGBColor(0xD9, 0xE2, 0xF3)
PALE = RGBColor(0xF2, 0xF5, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0x1F, 0x1F, 0x1F)
GRAY = RGBColor(0x59, 0x59, 0x59)
RED = RGBColor(0xC0, 0x00, 0x00)
ORANGE = RGBColor(0xBF, 0x8F, 0x00)
GREEN = RGBColor(0x37, 0x6E, 0x37)


def set_background(slide, color=WHITE):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, x, y, w, h, color, line=None, shape=MSO_SHAPE.RECTANGLE):
    rect = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    rect.fill.solid()
    rect.fill.fore_color.rgb = color
    if line is None:
        rect.line.fill.background()
    else:
        rect.line.color.rgb = line
    rect.line.width = Pt(0.75)
    return rect


def add_text(slide, text, x, y, w, h, size=18, color=TEXT, bold=False, italic=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return box


def add_bullets(slide, items, x, y, w, h, size=15, color=TEXT, spacing=8):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(spacing)
        p.line_spacing = 1.1
        if isinstance(item, tuple):
            text, bold = item
        else:
            text, bold = item, False
        run = p.add_run()
        run.text = "•  " + text
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return box


def add_slide_title(slide, title, subtitle=None):
    add_rect(slide, 0, 0, 13.333, 0.12, NAVY)
    add_text(slide, "КТ 5 · ЗАЩИТА", 0.55, 0.28, 3.5, 0.3, size=10, color=BLUE, bold=True)
    add_text(slide, title, 0.55, 0.58, 12.2, 0.65, size=30, color=NAVY, bold=True)
    if subtitle:
        add_text(slide, subtitle, 0.58, 1.2, 12.1, 0.4, size=14, color=GRAY, italic=True)
    add_rect(slide, 0.55, 1.32, 12.2, 0.02, LIGHT)


def add_footer(slide, number):
    add_rect(slide, 0.55, 7.05, 12.2, 0.01, LIGHT)
    add_text(slide, "ТЗ 1 · Система обнаружения ржавчины и коррозии · Райимжонов А. Т.",
             0.55, 7.12, 10.6, 0.25, size=8, color=GRAY)
    add_text(slide, str(number), 12.55, 7.12, 0.35, 0.25, size=9, color=GRAY,
             align=PP_ALIGN.RIGHT)


def add_table(slide, data, x, y, w, h, col_widths=None, font_size=12, header_size=12,
              status_col=None):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(h))
    table = shape.table
    if col_widths:
        total = sum(col_widths)
        for i, width in enumerate(col_widths):
            table.columns[i].width = Inches(w * width / total)
    for r_idx, row in enumerate(data):
        for c_idx, value in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = ""
            cell.margin_left = Inches(0.07)
            cell.margin_right = Inches(0.07)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(value)
            run.font.name = FONT
            run.font.size = Pt(header_size if r_idx == 0 else font_size)
            run.font.bold = r_idx == 0
            run.font.color.rgb = WHITE if r_idx == 0 else TEXT
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = NAVY
            elif status_col is not None and c_idx == status_col:
                v = str(value).lower()
                if v == "да":
                    cell.fill.fore_color.rgb = RGBColor(0xE2, 0xEF, 0xDA)
                    run.font.color.rgb = GREEN
                elif v == "нет":
                    cell.fill.fore_color.rgb = RGBColor(0xFB, 0xE5, 0xD6)
                    run.font.color.rgb = RED
                else:
                    cell.fill.fore_color.rgb = RGBColor(0xFF, 0xF2, 0xCC)
                    run.font.color.rgb = ORANGE
                run.font.bold = True
            elif r_idx % 2 == 0:
                cell.fill.fore_color.rgb = PALE
            else:
                cell.fill.fore_color.rgb = WHITE
    return table


def add_picture(slide, path, x, y, w=None, h=None):
    if w is not None and h is not None:
        return slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    if w is not None:
        return slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    return slide.shapes.add_picture(path, Inches(x), Inches(y), height=Inches(h))


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    slide = prs.slides.add_slide(blank)
    set_background(slide, NAVY)
    add_rect(slide, 0, 0, 0.22, 7.5, BLUE)
    add_text(slide, "КТ 5. ЗАЩИТА", 0.9, 1.15, 11.6, 0.5, size=16, color=LIGHT, bold=True)
    add_text(slide, "Система обнаружения\nржавчины и коррозии", 0.9, 1.75, 11.4, 1.7,
             size=40, color=WHITE, bold=True)
    add_text(slide, "ТЗ 1 · ПАО «ЧКПЗ» · прототип U-Net + FastAPI + PostgreSQL + React + Docker",
             0.95, 3.65, 11.2, 0.45, size=16, color=LIGHT)
    add_rect(slide, 0.95, 4.35, 5.7, 0.03, BLUE)
    add_text(slide, "Райимжонов Абдусамад Тулкинович", 0.95, 4.6, 7.8, 0.35, size=18,
             color=WHITE, bold=True)
    add_text(slide, "Индивидуальная работа · 2026", 0.95, 5.0, 7.8, 0.3, size=13, color=LIGHT)
    add_text(slide, "github.com/RvadRA/rust-corrosion-detection", 0.95, 5.45, 8.5, 0.3,
             size=13, color=LIGHT)
    add_text(slide, "19.11.2026", 10.6, 6.75, 2.0, 0.3, size=12, color=LIGHT,
             align=PP_ALIGN.RIGHT)
    add_notes(slide, "Здравствуйте. Это защита КТ 5 по ТЗ 1: система обнаружения ржавчины "
                     "и коррозии для ПАО ЧКПЗ. Работа индивидуальная. Покажу задачу, что "
                     "сравнили, что реально работает, где не прошли приёмку и что делать дальше.")

    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_slide_title(slide, "Задача и бизнес-процесс", "Ручной осмотр ОТК → автоматический контроль")
    add_bullets(slide, [
        ("Сейчас: оператор ОТК смотрит вручную, по сменам и при разном свете.", False),
        ("Мелкие пятна от 5 мм пропускаются; площадь, фото и архив не сохраняются.", False),
        ("Система: камера → U-Net → площадь и вердикт → ПЛК и архив.", True),
        ("Правило ТЗ: 0 — норма; ≤ 20 мм² — внимание; > 20 мм² или глубокая — брак.", False),
        ("Прототип покрывает ML + API + БД + UI + Docker; камера и ПЛК — граница проекта.", False),
    ], 0.55, 1.55, 6.55, 4.8, size=16, spacing=12)
    add_rect(slide, 0.55, 5.95, 6.35, 0.75, PALE, line=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Что заменяем: ручной осмотр и повторный осмотр мастером.",
             0.75, 6.12, 5.95, 0.4, size=13, color=NAVY, bold=True)
    add_picture(slide, FIG_TOBE, 7.55, 1.5, h=5.25)
    add_text(slide, "Схема «как будет» из КТ 1", 8.2, 6.85, 4.4, 0.25, size=9, color=GRAY,
             italic=True, align=PP_ALIGN.CENTER)
    add_footer(slide, 2)
    add_notes(slide, "Проблема не в том, что ржавчину нельзя увидеть, а в том, что осмотр "
                     "субъективен и не оставляет данных. Система заменяет ручной шаг: камера, "
                     "сегментация, площадь, вердикт, архив и сигнал в ПЛК. Прототип — это "
                     "программная часть; камеру и ПЛК описываем как следующий этап.")

    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_slide_title(slide, "Что сделано: прототип", "Путь «вход → результат» без ручных шагов")
    add_picture(slide, FIG_ARCH, 0.55, 1.55, w=8.15)
    add_bullets(slide, [
        ("4 сервиса: frontend, backend, ML, PostgreSQL.", False),
        ("U-Net 1,94 млн параметров, инференс на CPU.", False),
        ("FastAPI + PostgreSQL + React + Docker Compose.", False),
        ("Веса — GitHub Release, SHA-256 проверен.", False),
        ("CSV, retention 30 дней, ML down → 503.", False),
        ("Чистый старт: 4 контейнера healthy.", True),
    ], 9.0, 1.55, 3.8, 4.9, size=13, spacing=10)
    add_rect(slide, 0.55, 6.25, 12.2, 0.55, PALE, line=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Проверено: health, загрузка 01.jpg, overlay, журнал, CSV, медиа, отказ ML, "
                    "retention, калибровка MM_PER_PX.", 0.75, 6.38, 11.8, 0.3, size=11,
             color=NAVY)
    add_footer(slide, 3)
    add_notes(slide, "Архитектура проста: фронт, backend, ML и база. ML изолирован, backend "
                     "считает вердикт и хранит архив. Всё поднимается docker compose. Важно: "
                     "проверен не только счастливый путь, но и отказ ML, retention и калибровка.")

    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_slide_title(slide, "Что сравнили", "Один test из КТ 3: 79 изображений, 256×256, CPU")
    add_table(slide, [
        ["Метод", "F1", "Dice", "IoU", "Площадь", "VT F1"],
        ["M1 HSV", "0,551", "0,533", "0,405", "172 %", "0,496"],
        ["M2 Lab", "0,564", "0,534", "0,406", "125 %", "0,513"],
        ["M3 RF", "0,623", "0,582", "0,450", "120 %", "0,567"],
        ["M4 U-Net", "0,629", "0,585", "0,452", "122 %", "0,612"],
    ], 0.55, 1.55, 5.9, 3.3, col_widths=[1.5, 0.8, 0.8, 0.8, 1.0, 0.9], font_size=12)
    add_picture(slide, FIG_MODELS, 6.7, 1.55, w=6.05)
    add_rect(slide, 0.55, 5.05, 5.95, 1.3, PALE, line=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Почему U-Net", 0.75, 5.18, 5.55, 0.3, size=14, color=NAVY, bold=True)
    add_text(slide, "Лучший F1 и более ровный результат на трёх источниках. "
                    "M3 отстаёт на 0,005, но хуже на VT. YOLO не запускался и требует AGPL.",
             0.75, 5.48, 5.55, 0.75, size=11, color=TEXT)
    add_text(slide, "VT200: 44 test, 512×512, F1 0,6129. 156 train-кадров — leakage, "
                    "это не приёмка и не замена тесту на 200 деталях.",
             6.7, 4.75, 6.05, 0.75, size=10, color=GRAY, italic=True)
    add_footer(slide, 4)
    add_notes(slide, "Сравнивали четыре метода на одном test. U-Net выиграл по F1 и Dice/IoU. "
                     "RandomForest близко, но хуже на Virginia Tech. HSV и Lab оставлены как "
                     "быстрый fallback. Отдельно перепроверили публичную VT-выборку: F1 0,6129, "
                     "но 156 train-кадров пересекаются с обучением — это leakage, не приёмка.")

    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_slide_title(slide, "Результат против критериев приёмки", "Ключевые критерии ТЗ")
    add_table(slide, [
        ["Критерий", "Требование", "Результат", "Статус"],
        ["Recall пятен от 5 мм", "≥ 98 %", "15,6 %", "нет"],
        ["Ошибка площади", "≤ ±15 %", "122 %", "нет"],
        ["Степень «лёгкая / глубокая»", "≥ 95 %", "не оценивалась", "нет"],
        ["Тест на 200 деталях", "100 / 50 / 50", "79 изображений, 0 деталей", "нет"],
        ["Вердикты", "4 типа", "3 типа; сбой ML → 503", "частично"],
        ["Архив 30 дней / CSV", "есть", "проверено", "да"],
        ["ПЛК", "OPC UA / Profinet", "не реализован", "нет"],
    ], 0.55, 1.55, 12.2, 3.7, col_widths=[4.2, 3.2, 3.5, 1.9], font_size=12,
        status_col=3)
    add_rect(slide, 0.55, 5.55, 12.2, 1.15, RGBColor(0xFB, 0xE5, 0xD6), line=RED,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Приёмка не пройдена.", 0.78, 5.7, 11.7, 0.35, size=18, color=RED, bold=True)
    add_text(slide, "F1 ≈ 0,63 — диагностический уровень, не промышленная точность. "
                    "Причины: доменный сдвиг, нет чистых кадров и hard negatives, 256 px, "
                    "12 эпох на CPU, нет головы степени и калибровки.", 0.78, 6.05, 11.7, 0.55,
             size=11, color=TEXT)
    add_footer(slide, 5)
    add_notes(slide, "Здесь главный честный слайд. По трём ключевым критериям — recall, "
                     "площадь, степень — мы не прошли. 200 деталей не проверяли. Что работает: "
                     "архив, CSV, вердикты, инженерные проверки. Но это не приёмка качества, "
                     "а готовность прототипа.")

    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_slide_title(slide, "Демонстрация", "Полный путь и отказные сценарии · 5–6 минут")
    add_picture(slide, FIG_UI, 0.55, 1.45, w=5.6)
    add_text(slide, "Интерфейс оператора: вердикт, overlay, площадь, журнал",
             0.55, 6.55, 5.6, 0.3, size=9, color=GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_bullets(slide, [
        ("4/4 healthy; health: db=connected, ml=ready.", False),
        ("01.jpg → ВНИМАНИЕ, 619 904 px, confidence 0,7307.", False),
        ("MM_PER_PX=0,1 → БРАК, 6199,04 мм².", True),
        ("CSV → 200, UTF-8 BOM, 4 строки.", False),
        ("ML down → 503; после старта ML → healthy.", False),
        ("Retention 31 день → 404, файлы удалены.", False),
        ("Fallback: backup-видео и скриншоты.", False),
    ], 6.85, 1.55, 6.0, 4.9, size=13, spacing=10)
    add_rect(slide, 6.85, 6.05, 5.9, 0.55, PALE, line=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Если Docker не поднимется — показываем видео, а не чиним стенд на защите.",
             7.05, 6.18, 5.5, 0.3, size=10, color=GRAY, italic=True)
    add_footer(slide, 6)
    add_notes(slide, "Демо короткое: health, загрузка, результат, CSV, отказ ML и retention. "
                     "Отдельно показываю калибровку: при 0,1 мм/пиксель площадь 6199 мм² и "
                     "вердикт БРАК. Если стенд не поднимется, есть скриншоты и backup-видео.")

    slide = prs.slides.add_slide(blank)
    set_background(slide)
    add_slide_title(slide, "Ограничения и рекомендация", "Что мешает приёмке и что делать")
    add_rect(slide, 0.55, 1.5, 5.95, 0.45, RGBColor(0xFB, 0xE5, 0xD6))
    add_text(slide, "Почему это не приёмка", 0.75, 1.57, 5.55, 0.3, size=15, color=RED, bold=True)
    add_bullets(slide, [
        "Доменный сдвиг: мосты и трубы, а не гильзы ЧКПЗ.",
        "Нет чистых кадров, бликов, масла и СОЖ как hard negatives.",
        "Вход 256 px теряет пятна 5 мм.",
        "12 эпох на CPU, без предобученного энкодера.",
        "Нет головы степени и калибровки мм/пиксель.",
        "Нет 200 реальных деталей для приёмки.",
    ], 0.55, 2.1, 5.95, 3.8, size=12, spacing=9)
    add_rect(slide, 6.8, 1.5, 5.95, 0.45, RGBColor(0xE2, 0xEF, 0xDA))
    add_text(slide, "Что делать дальше", 7.0, 1.57, 5.55, 0.3, size=15, color=GREEN, bold=True)
    add_bullets(slide, [
        "Свои данные: 300 чистых + 20–50 дефектных деталей.",
        "Нативное разрешение или crop 512–1024 px.",
        "Предобученный энкодер, GPU, больше эпох, TTA.",
        "Голова степени и калибровка по эталону.",
        "Камера, свет, ПЛК; такт линии и обработка сбоя.",
        "Аутентификация, TLS, backup, мониторинг.",
    ], 6.8, 2.1, 5.95, 3.8, size=12, spacing=9)
    add_rect(slide, 0.55, 5.05, 12.2, 0.7, PALE, line=LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Критерий перехода к пилоту: стабильный recall на своих 20–50 деталях и "
                    "площадь ≤ 15 % после калибровки.", 0.78, 5.2, 11.7, 0.4, size=12,
             color=GRAY, italic=True)
    add_rect(slide, 0.55, 6.05, 12.2, 0.7, RED, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(slide, "Внедрять только пилотом на 20–50 деталях, не в линию до приёмки.",
             0.75, 6.2, 11.8, 0.4, size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide, 7)
    add_notes(slide, "Ограничения системные: данные, разрешение, степень и калибровка. Поэтому "
                     "рекомендация не внедрение, а пилот на 20–50 деталях параллельно с "
                     "оператором. В линию — только после сбора своих данных и повторной приёмки.")

    slide = prs.slides.add_slide(blank)
    set_background(slide, NAVY)
    add_rect(slide, 0, 0, 0.22, 7.5, BLUE)
    add_text(slide, "ВЫВОД", 0.9, 1.15, 3.0, 0.4, size=14, color=LIGHT, bold=True)
    add_text(slide, "Прототип работает.\nМодель приёмку не прошла.", 0.9, 1.65, 11.6, 1.6,
             size=36, color=WHITE, bold=True)
    add_text(slide, "F1 0,629 · recall пятен 15,6 % · ошибка площади 122 % · 200 деталей не проверены",
             0.95, 3.45, 11.6, 0.5, size=17, color=LIGHT)
    add_text(slide, "Дальше: свои данные, нативное разрешение, голова степени, калибровка и пилот.\n"
                    "Спасибо. Вопросы.", 0.95, 4.35, 11.6, 1.0, size=22, color=WHITE, bold=True)
    add_text(slide, "github.com/RvadRA/rust-corrosion-detection", 0.95, 6.55, 8.0, 0.3,
             size=12, color=LIGHT)
    add_text(slide, "19.11.2026", 10.8, 6.55, 1.8, 0.3, size=12, color=LIGHT,
             align=PP_ALIGN.RIGHT)
    add_notes(slide, "Главная мысль: инженерно прототип работает, но качество модели не "
                     "дотягивает до ТЗ. Это не провал, а честный baseline и понятный план: "
                     "свои данные, разрешение, степень, калибровка и пилот. Спасибо, готов "
                     "ответить на вопросы.")

    prs.core_properties.title = "КТ 5. Защита"
    prs.core_properties.subject = "ТЗ 1. Система обнаружения ржавчины и коррозии"
    prs.core_properties.author = "Райимжонов Абдусамад Тулкинович"
    prs.save(PPTX_PATH)
    print(f"saved: {PPTX_PATH}")


def export_pdf():
    import win32com.client

    power = win32com.client.DispatchEx("PowerPoint.Application")
    power.Visible = 1
    presentation = None
    try:
        presentation = power.Presentations.Open(os.path.abspath(PPTX_PATH), WithWindow=False)
        presentation.SaveAs(os.path.abspath(PDF_PATH), 32)
        print(f"exported: {PDF_PATH}")
    finally:
        if presentation is not None:
            presentation.Close()
        power.Quit()


if __name__ == "__main__":
    build()
    if "--pdf" in sys.argv:
        try:
            export_pdf()
        except Exception as exc:
            print(f"PDF export skipped: {exc}")
