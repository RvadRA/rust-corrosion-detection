"""Генерация документа КТ 3 «Эксперименты»."""

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
BASE = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE, "КТ 3. Эксперименты.docx")
HASH_PATH = DOC_PATH + ".sha256"
FIG_GOOD = os.path.join(BASE, "figures", "examples_good.png")
FIG_BAD = os.path.join(BASE, "figures", "examples_bad.png")


def style_run(run, size=14, bold=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)


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


def heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    style_run(run, 14, bold=True)
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
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
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
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


def no_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def table(doc, headers, rows, widths, font_size=12):
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

    doc.core_properties.title = "КТ 3. Эксперименты"
    doc.core_properties.subject = "ТЗ 1. Система обнаружения ржавчины и коррозии"
    doc.core_properties.author = "Райимжонов Абдусамад Тулкинович"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.line_spacing = 1.0
    title.paragraph_format.space_after = Pt(2)
    r = title.add_run("КТ 3. Эксперименты")
    style_run(r, 18, bold=True)
    r.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.first_line_indent = Cm(0)
    sub.paragraph_format.line_spacing = 1.0
    sub.paragraph_format.space_after = Pt(10)
    style_run(sub.add_run("ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"), 14, italic=True)

    table(doc, ["Поле", "Значение"], [
        ["Проект (ТЗ)", "ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"],
        ["Дата сдачи", "18.11.2026"],
        ["Капитан", "Райимжонов Абдусамад Тулкинович"],
        ["Участники", "Индивидуальная работа. Все этапы проекта выполняются самостоятельно"],
        ["Репозиторий", "https://github.com/RvadRA/rust-corrosion-detection"],
    ], widths=[4.2, 12.8])

    heading(doc, "1. Железо")
    table(doc, ["Компонент", "Значение"], [
        ["Видеокарта", "NVIDIA GeForce RTX 3060 Laptop GPU"],
        ["VRAM, ГБ", "6"],
        ["RAM, ГБ", "16"],
        ["Процессор", "AMD Ryzen 7 5800H"],
        ["ОС, версии библиотек", "Windows 11; Python 3.14.2; NumPy 2.5.4; scikit-learn 1.9.1; "
                                 "SciPy 1.18.1; PyTorch 2.15.0+cpu"],
    ], widths=[4.5, 12.5])
    para(doc, "Эксперименты запущены на CPU: установлен PyTorch CPU-only, видеокарта не использовалась. "
              "Это сделано для воспроизводимости на машине без CUDA; VRAM в таблице равна 0. Для обучения "
              "на GPU нужен PyTorch CUDA и отдельный прогон.")

    heading(doc, "2. Условия эксперимента")
    subheading(doc, "2.1. Тестовые данные")
    table(doc, ["Выборка", "Всего", "Ostrava", "Virginia Tech", "Pipelines"], [
        ["Train", "541", "75", "396", "70"],
        ["Val", "35", "15", "0", "20"],
        ["Test", "79", "15", "44", "20"],
    ], widths=[3.8, 3.0, 3.0, 3.6, 3.6])
    para(doc, "Все методы проверены на одном и том же test: 79 изображений, 256×256, бинарные маски "
              "«ржавчина / фон». Ostrava и VT используют авторские split; pipelines разделены 70/20/20 "
              "по seed 42. Пересечений по изображениям между train/val/test нет, test заморожен до "
              "обучения. Класса «норма» и разметки степени «лёгкая/глубокая» в открытых данных нет, "
              "поэтому оценивалась только бинарная сегментация.")
    labeled(doc, "Ограничение validation.", "В validation всего 35 изображений: Ostrava 15 и Pipelines 20. "
            "Virginia Tech в validation отсутствует полностью. Поэтому пороги HSV/Lab, порог RandomForest "
            "и выбор лучшей эпохи U-Net настраивались без VT, а все метрики VT — только на test. Это не "
            "позволяет считать VT-результат независимой валидацией гиперпараметров.")

    subheading(doc, "2.2. Обозначения методов")
    table(doc, ["Код", "Метод"], [
        ["M1", "HSV-порог"],
        ["M2", "Lab-порог"],
        ["M3", "RandomForest цвет+текстура"],
        ["M4", "U-Net"],
    ], widths=[3.0, 14.0])
    para(doc, "Фактически выполненные методы перенумерованы в M1–M4. E0–E7 — это первоначальный план "
              "экспериментов из КТ 2; обозначения E0–E7 сохраняются за планом и не переиспользуются для "
              "фактических прогонов.")

    subheading(doc, "2.3. Настройки")
    for text in [
        "Seed 42, вход 256×256, маски — nearest-neighbor, изображения — bilinear.",
        "Пороги HSV/Lab и порог вероятности подбирались только на val (35 изображений), затем один раз "
        "применялись к test.",
        "HSV: hue 0,00–0,10 и 0,92–1,00; S ≥ 0,20; V ≥ 0,15; V ≤ 1,00.",
        "Lab: a ≥ 5; b ≥ 0; L ≤ 100.",
        "RandomForest: 80 деревьев, глубина 16, min_samples_leaf 5, по 1500 положительных и 1500 "
        "отрицательных пикселей с изображения; признаки RGB, HSV, Lab, локальные средние 9×9, локальное "
        "СКО, градиент, red excess; порог 0,65; морфология 3×3 и удаление компонент < 24 px.",
        "U-Net: 1,94 млн параметров, каналы 16–32–64–128, bottleneck 256; 12 эпох, batch 8, AdamW, "
        "lr 1e-3, BCE + Dice, аугментация поворотами и отражениями; лучшая эпоха 8; порог 0,50; та же "
        "морфология.",
        "Метрики: pixel precision, recall, F1, Dice, IoU, относительная ошибка площади. FPS — обработка "
        "test на CPU, без учёта загрузки модели.",
    ]:
        bullet(doc, text)

    subheading(doc, "2.4. Скрипт для повтора")
    for text in [
        "python src/ml/kt3/prepare_data.py",
        "python src/ml/kt3/run_thresholds.py",
        "python src/ml/kt3/run_rf.py",
        "python src/ml/kt3/run_unet.py --epochs 12",
        "python src/ml/kt3/benchmark.py",
        "python src/ml/kt3/run_spots.py",
        "python src/ml/kt3/audit_metrics.py",
        "python src/ml/kt3/make_examples.py",
        "python docs/kt3/make_docx.py",
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        style_run(p.add_run(text), 12)

    heading(doc, "3. Результаты сравнения")
    table(doc, ["Модель / метод", "Precision (micro)", "Recall (micro)", "F1 (micro)", "Dice / IoU (macro)", "FPS", "VRAM / RAM, ГБ"], [
        ["M1. HSV-порог", "0,468", "0,668", "0,551", "0,533 / 0,405", "201,5", "0 / 0,31"],
        ["M2. Lab-порог", "0,523", "0,614", "0,564", "0,534 / 0,406", "105,2", "0 / 0,31"],
        ["M3. RandomForest цвет+текстура", "0,589", "0,662", "0,623", "0,582 / 0,450", "10,6", "0 / 0,51"],
        ["M4. U-Net", "0,599", "0,661", "0,629", "0,585 / 0,452", "17,6", "0 / 0,69"],
    ], widths=[3.8, 2.3, 2.2, 2.0, 3.2, 1.5, 2.0])
    table(doc, ["Модель / метод", "F1 all (micro)", "Ошибка площади", "Ostrava F1 (micro)", "VT F1 (micro)", "Pipelines F1 (micro)"], [
        ["M1. HSV-порог", "0,551", "172%", "0,628", "0,496", "0,634"],
        ["M2. Lab-порог", "0,564", "125%", "0,638", "0,513", "0,620"],
        ["M3. RandomForest", "0,623", "120%", "0,749", "0,567", "0,624"],
        ["M4. U-Net", "0,629", "122%", "0,663", "0,612", "0,629"],
    ], widths=[4.0, 2.5, 2.8, 2.5, 2.5, 2.7])
    table(doc, ["Метрика ТЗ", "Цель", "Факт", "Вывод"], [
        ["Recall пятен от 5 мм", "≥ 98%", "15,6% (spot-level, IoU ≥ 0,5)", "Не достигнуто; нужен тест в нативном разрешении"],
        ["Ошибка площади", "≤ 15%", "120–172% (M3–M4: 120–122%)", "Не достигнуто; мелкие маски и доменный сдвиг"],
        ["Точность степени", "≥ 95%", "не оценивалась", "В открытых данных нет меток «лёгкая/глубокая»"],
        ["Точность вердикта", "≥ 95%", "не оценивалась", "Нет трёхклассовой разметки и калибровки мм/пиксель"],
        ["Тест на 200 деталях", "100/50/50", "79 изображений", "Приёмочный тест не проводился"],
    ], widths=[5.0, 3.0, 4.0, 5.0])
    para(doc, "Аудит метрик.", bold=True, indent=False, before=2, after=0)
    para(doc, "benchmark.py не считает F1/Dice/IoU: он измеряет только FPS и RSS. Качество считается в "
              "common.summarize(). Precision, Recall и F1 — micro-усреднение по пикселям: "
              "F1 = 2TP / (2TP + FP + FN). Dice и IoU — macro-среднее по 79 изображениям: сначала Dice/IoU "
              "каждого кадра, затем среднее. F1 micro численно совпадает с Dice micro, но в таблице стоит "
              "Dice macro, поэтому F1 ≠ Dice — это разные способы усреднения, а не ошибка. Для M1: "
              "F1 micro 0,5505, Dice macro 0,5334, IoU macro 0,4052, IoU micro 0,3798. Пересчёт по "
              "сохранённым tp/fp/fn выполнен в audit_metrics.py, результат — metrics_audit.json, "
              "расхождений с сохранёнными значениями нет (status: ok).")
    para(doc, "Лучший результат по F1 (micro) и Dice/IoU (macro) — M4 U-Net: F1 0,629, Dice 0,585, "
              "IoU 0,452. M3 RandomForest отстаёт на 0,005 F1 (micro), но заметно лучше на Ostrava "
              "(0,749 против 0,663) и хуже на VT (0,567 против 0,612). U-Net более сбалансирован по "
              "источникам, поэтому выбран для прототипа. Пороговые методы проигрывают по точности, но "
              "дают интерпретируемый fallback и работают на порядки быстрее.")
    para(doc, "Ошибка площади 120–122% у M3–M4 — средняя относительная ошибка по изображениям; она "
              "сильно завышена кадрами с маленькими масками, где несколько лишних пикселей дают сотни "
              "процентов. У M1–M2 ошибка выше — 172% и 125% соответственно. Для приёмки нужна площадь "
              "по детали и калибровка мм/пиксель, а не средняя по кадрам.")
    para(doc, "На уровне пятен (IoU ≥ 0,5, компоненты ≥ 24 px) M4 даёт recall 15,6% и precision 12,4%; "
              "у M3 recall 19,8% при precision 8,1%, у M1/M2 — 18,0–19,8% при precision 6,8–7,1%. "
              "Pixel F1 не равен обнаружению пятен: крупные пятна дают много пикселей и завышают общую картину.")
    para(doc, "Целевые 98% recall и ±15% площади на этом прогоне не достигнуты. Причины: открытые "
              "датасеты сняты на мостах и трубах, а не на цилиндрах; нет класса «норма» и hard negatives; "
              "5-мм пятно при downsample до 256 px теряет пиксели; U-Net обучен на CPU всего 12 эпох без "
              "предобученного энкодера. Это промежуточный результат, а не приёмочный.")

    heading(doc, "4. Примеры")
    subheading(doc, "4.1. Удачные примеры")
    picture(doc, FIG_GOOD, "Рис. 1. Удачные примеры U-Net: исходник, эталон, предсказание и карта ошибок")
    for text in [
        "Ostrava / 02, Dice 0,93. Крупное пятно с ярким оранжево-коричневым цветом и чёткой границей; "
        "ошибки только по краям шелушения.",
        "VT / 36, Dice 0,93. Ржавая труба на зелёном фоне; модель уверенно отделяет трубу от фона, "
        "слегка теряет дальний тонкий конец.",
        "Ostrava / 01, Dice 0,90. Вертикальная ржавая полоса на бетоне; граница размыта, но площадь и "
        "положение переданы верно.",
    ]:
        bullet(doc, text)

    subheading(doc, "4.2. Неудачные примеры")
    picture(doc, FIG_BAD, "Рис. 2. Неудачные примеры U-Net: зелёный — TP, красный — FP, синий — FN")
    for text in [
        "VT / 11, Dice 0,00. Эталон — тонкая ржавая полоса по верхней балке и небольшое пятно на выступе. "
        "Модель размечает широкое пятно на бетоне: цвет бетона близок к ржавчине, тонкие структуры теряются.",
        "VT / 21, Dice 0,00. Маленькое пятно на белой балке (78 px в маске). После downsample до 256 px "
        "объект становится меньше эффективного рецептивного поля и пропускается.",
        "VT / 19, Dice 0,11. Эталон — тонкая ржавая линия по фланцу. Модель переразмечает тёмную "
        "влажную/ржавую нижнюю зону и кабель, путая тень и тёмный металл с коррозией.",
    ]:
        bullet(doc, text)

    heading(doc, "5. Промежуточные выводы")
    labeled(doc, "Лучший вариант.", "M4 U-Net (1,94 млн параметров) — лучший F1 (micro) и Dice/IoU "
            "(macro), более ровное качество на трёх источниках. Для прототипа берём U-Net; M3 RandomForest "
            "оставляем как интерпретируемый baseline, M1/M2 HSV/Lab — как быстрый fallback.")
    labeled(doc, "Целевые метрики ТЗ не достигнуты.", "98% recall пятен и ±15% площади требуют нативного "
            "разрешения, собственной съёмки цилиндров, разметки степени и калибровки мм/пиксель. На "
            "открытых данных получен только диагностический уровень F1 ≈ 0,63.")
    para(doc, "Что улучшить к прототипу:", bold=True, indent=False, before=2, after=0)
    for text in [
        "Снять 300 чистых кадров и 20–50 деталей, добавить блики и царапины.",
        "Обучать на нативном разрешении или на crop'ах 512–1024 px, а не на 256 px.",
        "Взять предобученный энкодер (ResNet-34/EfficientNet-B0), больше эпох и GPU; добавить TTA.",
        "Добавить голову степени «лёгкая/глубокая» и калибровку площади по эталону.",
        "Проверить YOLOv8-seg, SegFormer-B0 и PatchCore на том же test; сейчас они не запускались.",
        "Сделать cross-dataset тест и приёмочный тест на 200 реальных деталях (100/50/50).",
    ]:
        numbered(doc, text)

    heading(doc, "Чек-лист сдачи")
    checklist = [
        ("M1–M4 запущены на одних и тех же данных", True),
        ("Таблица сравнения заполнена полностью", True),
        ("Метрики посчитаны кодом из репозитория", True),
        ("Описано железо", True),
        ("Выбран лучший вариант для прототипа", True),
        ("YOLOv8-seg, SegFormer-B0 и PatchCore не запущены — следующий этап", False),
        ("Приёмочные 98% / ±15% / 200 деталей не проверены — нужны свои данные", False),
        ("VT отсутствует в validation — ограничение сохраняется", False),
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


if __name__ == "__main__":
    build()
