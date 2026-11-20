"""Генерация заполненного документа КТ 2 (.docx)."""

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
DOC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "КТ 2. Анализ и данные.docx")
HASH_PATH = DOC_PATH + ".sha256"

SOURCES = [
    ("1", "Medeiros et al., 2010. Texture and Color Features for Nondestructive Corrosion Detection",
     "Классические признаки HSI + GLCM + FLDA для коррозии на резервуарах и трубопроводах",
     "Интерпретируемо, не нужна обучающая выборка, работает на CPU",
     "Ручные пороги, чувствительность к свету, только бинарная детекция"),
    ("2", "Review: Segmentation of rust defects on painted steel, 2021",
     "Обзор HSV/Lab, кластеризации, SVM и нейросетей для сегментации ржавчины",
     "Систематизирует классические и ML-подходы, много ссылок",
     "Фокус на окрашенной стали, а не на чистом металле"),
    ("3", "Nash et al., 2022. Deep learning corrosion detection with confidence",
     "HRNetV2 для пиксельной сегментации + байесовская оценка неопределённости, 225 изображений",
     "Маски и «уверенность» по пикселям, честная оценка ошибок",
     "Датасет закрыт, домен — промышленные сооружения"),
    ("4", "Ameli et al., 2024. Steel Bridge Corrosion Segmentation, Mask R-CNN and YOLOv8",
     "Открытый датасет 514 изображений мостов, сравнение Mask R-CNN и YOLOv8",
     "Открытые данные и маски, учёт степени коррозии",
     "Мосты и окрашенные конструкции, не цилиндры"),
    ("5", "Fondevik et al., 2020. Image Segmentation of Corrosion Damages",
     "608 изображений с instance-масками, Mask R-CNN и PSPNet, двухступенчатая аугментация",
     "Индустриальный домен, instance-маски, анализ аугментации",
     "mIoU 77,5% у Mask R-CNN, съёмка с дрона"),
    ("6", "Bianchi, Hebdon, 2021. Corrosion Condition State Dataset (Virginia Tech)",
     "440 изображений мостов, 4 состояния (в релизе размечены 3), DeepLabV3+, F1 86,67%",
     "CC0, градации состояния, пиксельная разметка",
     "512×512, мосты, размытые границы"),
    ("7", "Chen et al., 2025. Corrosion-Grade Recognition with Improved YOLOv8",
     "YOLOv8 для 5 стадий коррозии, 2880 изображений после солевого тумана, mAP 96,3%",
     "Градации коррозии, внимание, разные условия света",
     "Классификация, а не площадь; синтетические фоны"),
    ("8", "Tolentino et al., 2026. Surface Corrosion in Steel Hand Tools Using YOLOv8",
     "YOLOv8s-seg на 7000 изображений, развёртывание на Raspberry Pi 5",
     "Реальный edge-кейс, честно показаны ограничения",
     "Recall мелких пятен 17,4% — риск для ТЗ (5 мм)"),
    ("9", "Yan et al., 2025. SegFormer with edge feature extraction",
     "SegFormer + модуль краёв и прогрессивный декодер, 3,6 млн параметров, 96,5% на трубах",
     "Малые области и границы, лёгкая модель",
     "Свой датасет, нужна высокая детализация"),
    ("10", "Guo et al., 2025. Corrosion Segmentation with Improved TransU-Net",
     "TransU-Net + слияние HSV/Lab и текстурных признаков, mIoU 75,42%",
     "Использует цвет и текстуру, устойчив к сложному фону",
     "Тяжёлая модель (108 млн параметров), ниже FPS"),
    ("11", "Roth et al., 2021. Towards Total Recall in Industrial Anomaly Detection",
     "PatchCore: unsupervised-аномалия по «нормальным» изображениям, AUROC 99,6% на MVTec AD",
     "Не нужны примеры дефектов, ловит неизвестные отклонения, Apache-2.0",
     "Не даёт площадь и степень, нужен чистый «нормальный» набор"),
]

LINKS = [
    "https://link.springer.com/article/10.1155/2010/817473",
    "https://www.sciencedirect.com/science/article/abs/pii/S0926580520310955",
    "https://www.nature.com/articles/s41529-022-00232-6",
    "https://www.mdpi.com/2412-3811/9/1/3",
    "https://doi.org/10.1109/ictai50040.2020.00125",
    "https://doi.org/10.7294/16624663.v2",
    "https://www.mdpi.com/1424-8220/25/8/2630",
    "https://www.mdpi.com/2673-4591/134/1/56",
    "https://www.nature.com/articles/s41598-025-92531-6",
    "https://www.mdpi.com/2079-9292/14/23/4688",
    "https://arxiv.org/abs/2106.08265",
]


def style_run(run, size=14, bold=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(14)
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
         before=0, after=0, spacing=1.5, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = spacing
    p.paragraph_format.first_line_indent = Cm(1.25)
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
    style_run(run, 12, bold=True)
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    return p


def bullet(doc, text, size=14, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_prefix:
        r = p.add_run(bold_prefix)
        style_run(r, size, bold=True)
    r = p.add_run(text)
    style_run(r, size)
    return p


def numbered(doc, text, size=14):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    style_run(r, size)
    return p


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def no_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def table(doc, headers, rows, widths=None, font_size=9, header_fill="D9E2F3"):
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
        run = p.add_run(h)
        style_run(run, font_size, bold=True)
        shade_cell(cell, header_fill)
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
            run = p.add_run(str(value))
            style_run(run, font_size)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(12)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
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
    run.font.size = Pt(10)
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

    doc.core_properties.title = "КТ 2. Анализ и данные"
    doc.core_properties.subject = "ТЗ 1. Система обнаружения ржавчины и коррозии"
    doc.core_properties.author = "Райимжонов Абдусамад Тулкинович"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.line_spacing = 1.0
    title.paragraph_format.space_after = Pt(2)
    r = title.add_run("КТ 2. Анализ и данные")
    style_run(r, 18, bold=True)
    r.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.first_line_indent = Cm(0)
    sub.paragraph_format.line_spacing = 1.0
    sub.paragraph_format.space_after = Pt(10)
    r = sub.add_run("ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)")
    style_run(r, 13, italic=True)

    table(
        doc,
        ["Поле", "Значение"],
        [
            ["Проект (ТЗ)", "ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"],
            ["Дата сдачи", "18.11.2026"],
            ["Капитан", "Райимжонов Абдусамад Тулкинович"],
            ["Участники", "Индивидуальная работа (согласовать с преподавателем)"],
            ["Репозиторий", "https://github.com/RvadRA/rust-corrosion-detection"],
        ],
        widths=[4.2, 12.8],
        font_size=11,
    )

    heading(doc, "1. Обзор источников")
    para(doc, "Источники отбирали по четырём критериям: пиксельная разметка или пригодность метода "
              "для маски, коррозия/ржавчина на металле, воспроизводимость результата и открытая "
              "лицензия. Работы только с классификацией включали, если они дают признаки или "
              "архитектуру для сегментации.", size=11, indent=False)
    para(doc, "Отобраны 11 работ: классические признаки, сегментация коррозии на мостах и трубах, "
              "лёгкие edge-модели и unsupervised-детекция аномалий. Для каждой указано, что берём "
              "и чего не хватает для ТЗ.", size=11, indent=False)
    table(
        doc,
        ["№", "Источник", "Что предлагает", "Плюсы", "Минусы"],
        SOURCES,
        widths=[1.1, 4.1, 4.5, 3.7, 3.6],
        font_size=8,
    )
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("Ссылки:")
    style_run(r, 10.5, bold=True)
    for i, link in enumerate(LINKS, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)
        style_run(p.add_run(f"[{i}] {link}"), 9)

    para(doc, "Вывод из обзора.", bold=True, before=0, after=0)
    para(doc, "Для задачи ТЗ нужна не просто детекция, а пиксельная сегментация: только по маске можно "
              "посчитать площадь в мм² и применить порог 20 мм². Классические HSV/Lab + текстура дают "
              "интерпретируемый baseline, но зависят от света и бликов. YOLO-seg быстрая и даёт "
              "instance-маски, однако на мелких пятнах recall падает (17,4% у Tolentino et al.). "
              "U-Net и SegFormer точнее по границам и площади, но требуют больше ресурсов. PatchCore "
              "полезен как страхующая проверка «норма/аномалия», но не определяет степень. Открытых "
              "датасетов с ржавчиной на цилиндрических деталях нет — это разрыв, который закрываем "
              "переносом с мостов и труб и собственной разметкой.")

    heading(doc, "2. Кандидаты для сравнения")
    table(
        doc,
        ["Модель / метод", "Почему выбран", "Требования к железу", "Лицензия"],
        [
            ["Классика: HSV/Lab + LBP/GLCM + морфология + калибровка площади",
             "Baseline из ТЗ: цвет и текстура ржавчины, интерпретируемые пороги, работает без обучения; "
             "нужен для проверки, что нейросеть реально лучше",
             "CPU, < 1 ГБ RAM, реальное время",
             "OpenCV Apache-2.0, scikit-image BSD-3"],
            ["YOLOv8s-seg (Ultralytics)",
             "Instance-сегментация в реальном времени, маски пятен и рамки, простая интеграция и экспорт; "
             "подтверждён на коррозии (Ameli 2024, Tolentino 2026)",
             "Обучение 640 px, batch 4, AMP — влезает в 6 ГБ; инференс < 1,5 ГБ VRAM",
             "AGPL-3.0 (для внедрения у заказчика нужна коммерческая лицензия)"],
            ["U-Net с энкодером ResNet-34 / EfficientNet-B0 (smp)",
             "Пиксельная сегментация с точными границами и площадью, устойчива к дисбалансу классов, "
             "лёгкая и быстрая; в Ostrava U-Net++ дал F1 0,933",
             "512 px, batch 8, AMP — 4–6 ГБ VRAM",
             "MIT (smp), веса ImageNet"],
            ["SegFormer-B0 (NVIDIA)",
             "Transformer-энкодер даёт глобальный контекст и лучше держит неровные границы; 3,7 млн "
             "параметров, лидер по mIoU в обзорах коррозии (Guo 2025, Yan 2025)",
             "512 px, batch 4–8, AMP — 4–6 ГБ VRAM",
             "Код Apache-2.0, веса NVIDIA «other» (ограничение для коммерции)"],
            ["PatchCore (Amazon)",
             "Unsupervised-аномалия: учится только на «норме», ловит неизвестные дефекты и блики/масло "
             "как аномалии; страховка от пропуска брака",
             "512 px, признаки ResNet-18/50; CPU/GPU, 2–8 ГБ RAM",
             "Apache-2.0"],
        ],
        widths=[3.3, 6.8, 3.4, 3.5],
        font_size=8.5,
    )
    para(doc, "Mask R-CNN в сравнение не берём: тяжелее и медленнее при близком качестве instance-масок; "
              "для 6 ГБ VRAM и такта линии он проигрывает YOLO-seg и U-Net.", size=11, italic=True)
    para(doc, "Лицензии перед пилотом: YOLOv8-seg — AGPL-3.0, при сетевом использовании нужно открывать "
              "код сервиса; веса SegFormer-B0 — лицензия NVIDIA «other» с ограничением коммерческого "
              "применения. Для внедрения готовим замену на U-Net (MIT) или покупаем коммерческую "
              "лицензию; PatchCore (Apache-2.0) остаётся страховочной проверкой.", size=11)

    heading(doc, "3. Данные")

    subheading(doc, "3.1. Источники данных")
    table(
        doc,
        ["Набор и источник", "Объём", "Классы и случаи", "Разметка", "Лицензия"],
        [
            ["Corrosion in Industrial Complexes in Ostrava (Zenodo, DOI 10.5281/zenodo.11235637)",
             "105 изображений, 2048×2048, сплит 75/15/15",
             "Бинарная коррозия на промышленных конструкциях", "Пиксельные маски", "CC BY 4.0"],
            ["Corrosion Condition State, Virginia Tech (Figshare, DOI 10.7294/16624663.v2)",
             "440 изображений, оригинал + 512×512; 432 fair / 337 poor / 104 severe (с перекрытием), "
             "чистых good нет", "3 фактических состояния: fair / poor / severe",
             "Пиксельные маски, LabelMe", "CC0"],
            ["Corroded Pipelines, Petrobras (Figshare, DOI 10.6084/m9.figshare.30019591.v2)",
             "110 изображений, 709 instance-масок", "Коррозия внутренней поверхности труб, 1 класс",
             "COCO instance-маски", "CC BY 4.0"],
            ["Собственная съёмка (линия ПАО «ЧКПЗ» или чистые детали; по согласованию)",
             "300 изображений нормы + 20–50 деталей с дефектами",
             "Норма, лёгкая, глубокая; блики, масло, СОЖ", "CVAT, полигоны + ignore-зоны", "Внутренняя"],
        ],
        widths=[4.0, 3.7, 3.7, 3.0, 2.6],
        font_size=8,
    )
    para(doc, "Итого открытых данных: 655 изображений, из них 709 instance-масок в pipelines. Все лицензии "
              "проверены и допускают учебное использование; исходные файлы хранятся в dataset/raw/, в git "
              "не коммитятся. Контрольные суммы и структура описаны в dataset/README.md.", size=11)
    labeled(doc, "Важная находка.", "В открытых наборах нет класса «чистая поверхность»: VT содержит "
            "только кадры с коррозией (fair/poor/severe), Ostrava и pipelines — тоже только дефекты. "
            "Поэтому norm и сложные негативы (блики, масло, СОЖ) нужно собирать самостоятельно или "
            "вырезать чистые области из открытых кадров. Это усиливает риск доменного сдвига и делает "
            "съёмку чистых деталей обязательным шагом, а не опцией.")

    subheading(doc, "3.2. Целевые классы и пересборка разметки")
    table(
        doc,
        ["Целевой класс", "Что входит", "Откуда берём"],
        [
            ["norm", "Чистая обработанная поверхность без ржавчины",
             "Собственная съёмка чистых деталей (300 кадров), чистые области Ostrava/pipelines, "
             "промышленные фоны без дефектов"],
            ["rust_light", "Лёгкая ржавчина: матовая поверхность, шелушение, поверхностное окисление без выраженных глубоких ямок",
             "VT fair, маски Ostrava и pipelines после ручной проверки"],
            ["rust_deep", "Глубокая коррозия: тёмные участки, рыхлый слой, выраженные ямки и повреждение металла",
             "VT poor/severe, маски Ostrava и pipelines после ручной проверки"],
            ["ignore", "Блики, масло, СОЖ, царапины, краска, фон, размытые границы",
             "Размечаем отдельно и исключаем из FP"],
        ],
        widths=[2.2, 7.0, 7.8],
        font_size=9,
    )
    para(doc, "Состояния VT (good/fair/poor/severe; фактически в релизе размечены только fair/poor/severe) — "
              "это состояние конструкции по AASHTO/BIRM, а не строго «лёгкая/глубокая ржавчина». Поэтому "
              "используем их как слабые метки, а спорные кадры переразмечаем вручную по правилам ТЗ. "
              "Бинарные маски Ostrava и pipelines тоже требуют ручной оценки степени. Площадь — отдельное "
              "условие вердикта: лёгкая и ≤ 20 мм² → ВНИМАНИЕ, глубокая или > 20 мм² → БРАК.")

    subheading(doc, "3.3. Объём и сплиты")
    t33 = table(
        doc,
        ["Выборка", "Состав", "Цель"],
        [
            ["Train (план)", "300 изображений на класс (norm, rust_light, rust_deep)",
             "≥ 900 изображений после ре-разметки; аугментация — только после сплита"],
            ["Val (план)", "100 изображений на класс", "Подбор порогов и early stopping"],
            ["Test (план)", "200 изображений: 100 норма, 50 лёгкая, 50 глубокая",
             "Экспериментальная проверка; приёмка по ТЗ — отдельно, на 200 реальных деталях"],
        ],
        widths=[2.5, 6.2, 8.3],
        font_size=9,
    )
    for row in t33.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    labeled(doc, "Плановый состав.", "Train, Val и Test — планируемые, а не уже собранные. Аугментацию "
            "и copy-paste выполняем только после разделения исходных кадров, иначе похожие изображения "
            "попадут в train и test и завысят метрики. 200 тестовых изображений — экспериментальная "
            "выборка; 200 реальных деталей — отдельная приёмочная проверка по ТЗ.")
    labeled(doc, "Текущий разрыв.", "Открытые наборы дают 655 изображений, но norm в них отсутствует "
            "полностью, а после пересборки классов не хватает до 300 на класс. Закрываем так: "
            "(1) собственная съёмка 300 чистых кадров и 20–50 деталей с дефектами, (2) ре-разметка и "
            "crop'ы крупных изображений Ostrava/VT, (3) аугментация и copy-paste мелких пятен. Сплит "
            "делаем по источнику и условию съёмки, чтобы кадры одной детали или серии не попали "
            "одновременно в train и test.")

    subheading(doc, "3.4. Разметка")
    for text in [
        "Инструмент: CVAT (или Label Studio), формат экспорта — COCO instance segmentation + маски.",
        "Полигоны по внешней границе пятна; для глубокой коррозии — вся зона поражения, включая ямки.",
        "Минимальный объект: пятно 5 мм при 0,2 мм/пикс ≈ 25 пикселей в диаметре; всё меньше — в ignore.",
        "Двойная разметка 10% кадров, расхождение проверяет капитан; целевое согласие ≥ 0,8 "
        "(Cohen's kappa).",
        "Гайдлайн: что считать лёгкой/глубокой, как обводить блики и масло, что делать на границе детали.",
        "Люди в кадр не попадают, согласие на съёмку не требуется; персональные данные не собираем.",
    ]:
        bullet(doc, text)

    subheading(doc, "3.5. Аугментация и сложные негативы")
    for text in [
        "Геометрия: отражения, повороты на 90°/180°, небольшой сдвиг и перспектива.",
        "Фото: яркость, контраст, гамма, размытие, шум, имитация блика и капель СОЖ.",
        "Цвет: оттенок не двигаем больше ±5°, чтобы не превратить чистый металл в «ржавчину» и наоборот.",
        "Copy-paste мелких пятен для роста recall на объектах 5 мм; балансировка классов.",
        "Hard negatives: чистая сталь с бликами, масляные пятна, следы СОЖ, царапины, цвета побежалости, "
        "краска.",
    ]:
        bullet(doc, text)

    subheading(doc, "3.6. Порядок сбора и разметки")
    for text in [
        "Скачать архивы и проверить SHA-256 скриптом src/ml/download_data.py.",
        "Привести маски Ostrava и VT к COCO; бинарные маски pipelines сохранить как instance-маски.",
        "Переразметить степень: fair → rust_light, poor/severe → rust_deep; спорные зоны — в ignore.",
        "Снять 300 чистых кадров и 20–50 деталей с дефектами, добавить hard negatives (блики, масло, СОЖ).",
        "Заморозить test (200 кадров) до обучения; split — по источнику и детали, seed 42.",
        "Проверить согласие разметки на 10% кадров, целевое Cohen's kappa ≥ 0,8.",
    ]:
        numbered(doc, text)

    heading(doc, "4. Метрики")
    table(
        doc,
        ["Метрика", "Как считаем", "Целевое значение из ТЗ"],
        [
            ["Recall пятен (spot-level)", "TP при IoU с разметкой ≥ 0,5; TP / (TP + FN), отдельно для "
                                          "пятен от 5 мм", "≥ 98%"],
            ["Precision / F1 пятен", "TP / (TP + FP), гармоническое среднее",
             "Справочно, контролируем ложные срабатывания"],
            ["Ошибка площади", "MAPE суммарной площади по детали: |S_pred − S_gt| / S_gt", "≤ 15%"],
            ["Точность степени", "Доля пятен/деталей с верной меткой лёгкая/глубокая", "≥ 95%"],
            ["Точность вердикта", "Доля деталей с верным НОРМА/ВНИМАНИЕ/БРАК", "≥ 95% (цель проекта)"],
            ["Пропуск брака", "Брак, ушедший как норма или внимание / все бракованные детали", "≤ 2%"],
            ["Ложная отбраковка", "Годные, отправленные в брак / все годные", "≤ 3%"],
            ["Dice / IoU (mIoU)", "Пиксельное совпадение масок, диагностическая метрика",
             "Справочно, ориентир mIoU ≥ 0,7"],
            ["Скорость", "Латентность на деталь и FPS при batch=1; замер на CPU и GPU",
             "Уложиться в такт линии (уточняется)"],
            ["Ресурсы", "Пик VRAM и RAM при обучении и инференсе", "VRAM ≤ 6 ГБ, RAM ≤ 16 ГБ"],
            ["Устойчивость", "Recall на подвыборке с бликами/маслом/СОЖ",
             "Падение ≤ 5% к основной выборке"],
        ],
        widths=[4.0, 7.6, 5.4],
        font_size=8.5,
    )

    subheading(doc, "4.1. Как метрики связаны с вердиктом")
    table(
        doc,
        ["Метрика", "На что влияет", "Приоритет"],
        [
            ["Пропуск брака ≤ 2%", "Глубокая ржавчина не должна попасть в НОРМА или ВНИМАНИЕ; "
                                   "задаёт верхнюю границу порога", "Критичный"],
            ["Ложная отбраковка ≤ 3%", "Лёгкая ржавчина с площадью ≤ 20 мм² не должна уходить в БРАК; "
                                       "балансирует пропуск", "Критичный"],
            ["Ошибка площади ≤ 15%", "Правило 20 мм² работает только при калибровке мм/пиксель "
                                     "и точной маске", "Высокий"],
            ["Точность степени ≥ 95%", "От неё зависит выбор НОРМА / ВНИМАНИЕ / БРАК", "Высокий"],
            ["Recall пятен ≥ 98%", "Пятна от 5 мм — минимальный объект ТЗ; мелкие пятна самые сложные",
             "Критичный"],
            ["Латентность", "Если инференс дольше такта, вердикт не успевает к линии", "Высокий"],
        ],
        widths=[4.2, 8.8, 4.0],
        font_size=9,
    )
    para(doc, "Метрики считаем на двух уровнях: пятно (spot-level) и деталь (verdict-level). Для приёмки "
              "главными считаем пропуск брака, ложную отбраковку и точность вердикта; Dice/IoU оставляем "
              "диагностикой, чтобы не оптимизировать модель под пиксели в ущерб бизнес-правилам.", size=11)

    heading(doc, "5. План экспериментов")
    table(
        doc,
        ["Этап и что делаем", "Модели", "Данные", "Результат", "Ответственный", "Срок"],
        [
            ["E0. Собрать пайплайн данных и метрик, зафиксировать сплиты и seed", "—",
             "655 открытых изображений", "Воспроизводимый датасет и скрипт метрик", "Райимжонов А. Т.", "4"],
            ["E1. Baseline по цвету и текстуре, подбор порогов HSV/Lab", "HSV/Lab + LBP/GLCM",
             "Train/val/test", "Таблица метрик baseline", "Райимжонов А. Т.", "4"],
            ["E2. Instance-сегментация, сравнение размеров", "YOLOv8n-seg, YOLOv8s-seg", "640 px, AMP",
             "Точность, FPS, VRAM", "Райимжонов А. Т.", "4–5"],
            ["E3. Семантическая сегментация", "U-Net (ResNet-34), SegFormer-B0", "512 px, AMP",
             "Точность площади и границ", "Райимжонов А. Т.", "5"],
            ["E4. Unsupervised-аномалия на «норме»", "PatchCore", "Только norm + тест",
             "AUROC, recall аномалий", "Райимжонов А. Т.", "5"],
            ["E5. Абляции: HSV vs Lab vs оба, LBP, маска бликов, голова степени", "Лучшие 2 модели",
             "Тот же сплит", "Вклад каждого блока", "Райимжонов А. Т.", "5"],
            ["E6. Проверка доменного сдвига: обучение на открытых, тест на отложенных «своих»/другом "
             "датасете", "Лучшая модель", "Cross-dataset",
             "Падение метрик и вывод о дообучении", "Райимжонов А. Т.", "5"],
            ["E7. Ускорение: PyTorch vs ONNX Runtime, FP16/INT8", "Лучшая модель", "Тест",
             "Латентность и FPS", "Райимжонов А. Т.", "5"],
        ],
        widths=[3.5, 2.6, 2.7, 2.7, 3.5, 2.0],
        font_size=8,
    )

    subheading(doc, "5.1. Железо и условия")
    t_hw = table(
        doc,
        ["Компонент", "Значение"],
        [
            ["GPU", "NVIDIA RTX 3060 Laptop, 6 ГБ VRAM"],
            ["RAM", "16 ГБ"],
            ["CPU", "AMD Ryzen 7 5800H"],
            ["ОС и стек", "Windows 11, Python 3.11, PyTorch 2.x, CUDA 12.x"],
            ["Резерв", "Google Colab (T4 16 ГБ) для тяжёлых прогонов"],
        ],
        widths=[4.0, 13.0],
        font_size=10,
    )
    for row in t_hw.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    para(doc, "Условия: одинаковый сплит и seed 42, 3 прогона на конфигурацию (mean ± std), AMP, early "
              "stopping по val loss, фиксированные входы 640 px (YOLO) и 512 px (U-Net/SegFormer), один "
              "и тот же тест для всех моделей. Скрипты и конфиги — в src/ml/, результаты — в docs/kt3/.",
         size=11)

    subheading(doc, "5.2. Критерий выбора модели для прототипа")
    para(doc, "Модель проходит в КТ 4, если одновременно: recall пятен ≥ 98%, ошибка площади ≤ 15%, "
              "точность степени ≥ 95%, латентность укладывается в такт линии, VRAM ≤ 6 ГБ и лицензия "
              "допускает использование у заказчика. При равенстве выбираем более быструю и простую в "
              "калибровке; AGPL-модель (YOLO) оставляем как исследовательский вариант, а для внедрения "
              "готовим замену на U-Net/PatchCore или коммерческую лицензию.")

    heading(doc, "6. Риски данных и экспериментов")
    table(
        doc,
        ["Риск", "Что делаем"],
        [
            ["Мало данных, сильный дисбаланс классов",
             "Ре-разметка, crop'ы, copy-paste мелких пятен, oversampling, Dice/focal loss"],
            ["Доменный сдвиг: мосты и трубы вместо цилиндров",
             "Своя съёмка 20–50 деталей, hard negatives, тест на отложенном домене, дообучение"],
            ["Субъективная граница «лёгкая/глубокая»",
             "Гайдлайн, двойная разметка 10%, калибровка с технологом, kappa ≥ 0,8"],
            ["Лицензии AGPL-3.0 (YOLO) и NVIDIA (SegFormer)",
             "Для прототипа допустимо, для внедрения — U-Net/PatchCore или коммерческая лицензия"],
            ["6 ГБ VRAM", "Лёгкие модели, AMP, 512–640 px, batch 2–4, gradient accumulation, Colab"],
            ["Нет 200 реальных деталей для приёмки",
             "Сейчас тест на открытых данных, финальная приёмка — на пилоте у заказчика"],
        ],
        widths=[6.4, 10.6],
        font_size=9.5,
    )

    heading(doc, "7. Артефакты и воспроизводимость")
    t_art = table(
        doc,
        ["Артефакт", "Где", "Статус"],
        [
            ["Датасет-карта, структура, контрольные суммы", "dataset/README.md", "готово"],
            ["Скрипт скачивания и проверки SHA-256", "src/ml/download_data.py", "готово"],
            ["Сырые данные (655 изображений)", "dataset/raw/", "скачано, в git не коммитится"],
            ["Сплиты и seed 42", "docs/kt3/splits.json", "появится в КТ 3"],
            ["Конфиги обучения", "src/ml/configs/", "появится в КТ 3"],
            ["Метрики и логи прогонов", "docs/kt3/", "появится в КТ 3"],
            ["Окружение", "requirements.txt, Dockerfile", "requirements — КТ 3, Docker — КТ 4"],
        ],
        widths=[6.2, 6.2, 4.6],
        font_size=9,
    )
    for row in t_art.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    para(doc, "Воспроизводимость: Python 3.11, PyTorch 2.x, CUDA 12.x, seed 42, фиксированные входы "
              "640/512 px, один test для всех моделей. Данные и веса в git не хранятся, скачиваются "
              "скриптом и проверяются по SHA-256.", size=11)

    heading(doc, "8. Критерий готовности к КТ 3")
    for text in [
        "Датасет и test-сплит заморожены, разметка версионируется.",
        "Пересечений Train/Val/Test по деталям и источникам нет.",
        "Baseline E1 воспроизводится одной командой, метрики — автоматически.",
        "Ограничения: нет norm, доменный сдвиг, лицензии YOLO/SegFormer.",
    ]:
        bullet(doc, text)

    h = heading(doc, "Чек-лист сдачи")
    h.paragraph_format.space_before = Pt(6)
    for text, done in [
        ("Обзор статей: ≥ 3 кандидатов с обоснованием", True),
        ("Датасет собран: 3 открытых набора, 655 изображений, лицензии проверены", True),
        ("Метрики и целевые значения записаны", True),
        ("Датасет-карта, структура и контрольные суммы: dataset/README.md", True),
        ("Довести разметку до 300 изображений на класс", False),
        ("Согласовать с заказчиком съёмку 20–50 деталей", False),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        r = p.add_run(("☒ " if done else "☐ ") + text)
        style_run(r, 12)

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
