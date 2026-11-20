"""Генерация заполненного документа КТ 1 (.docx)."""

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
DOC_PATH = "КТ 1. Старт и бизнес-процессы.docx"


def style_run(run, size=12, bold=False, italic=False):
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


def para(doc, text="", size=12, bold=False, italic=False, align="justify", indent=True,
         before=0, after=4, spacing=1.15, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = spacing
    if indent:
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


def heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    style_run(run, 14, bold=True)
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    return p


def subheading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    style_run(run, 12, bold=True)
    run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    return p


def bullet(doc, text, size=12, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_prefix:
        r = p.add_run(bold_prefix)
        style_run(r, size, bold=True)
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
    cant = OxmlElement("w:cantSplit")
    tr_pr.append(cant)


def table(doc, headers, rows, widths=None, font_size=9.5, header_fill="D9E2F3"):
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
        p.paragraph_format.space_after = Pt(1)
        run = p.add_run(h)
        style_run(run, font_size, bold=True)
        shade_cell(cell, header_fill)
    no_split(hdr)
    tr_pr = hdr._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:tblHeader"))
    for row in rows:
        cells = t.add_row().cells
        no_split(t.rows[-1])
        for i, value in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            run = p.add_run(str(value))
            style_run(run, font_size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def picture(doc, path, caption, width_cm=16.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    run = cap.add_run(caption)
    style_run(run, 11, italic=True)


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


def build():
    doc = Document()

    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, Cm(2))
    add_page_number(section)

    doc.core_properties.title = "КТ 1. Старт и бизнес-процессы"
    doc.core_properties.subject = "ТЗ 1. Система обнаружения ржавчины и коррозии"
    doc.core_properties.author = "Команда проекта"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(2)
    r = title.add_run("КТ 1. Старт и бизнес-процессы")
    style_run(r, 18, bold=True)
    r.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_after = Pt(10)
    r = sub.add_run("ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)")
    style_run(r, 13, italic=True)

    table(
        doc,
        ["Поле", "Значение"],
        [
            ["Проект (ТЗ)", "ТЗ 1. Система обнаружения ржавчины и коррозии (ПАО «ЧКПЗ»)"],
            ["Дата сдачи", "[уточнить в Moodle] (в шаблоне указано 14.10.2026)"],
            ["Капитан", "[ФИО капитана]"],
            ["Участники", "[ФИО 1], [ФИО 2], [ФИО 3]"],
            ["Репозиторий", "[ссылка на Git-репозиторий]"],
        ],
        widths=[4.2, 12.8],
        font_size=11,
    )

    heading(doc, "1. Команда и роли")
    table(
        doc,
        ["Участник", "Роль", "За что отвечает"],
        [
            ["[ФИО капитана]", "Капитан, аналитик / PM",
             "ТЗ и вопросы заказчику, бизнес-процессы, план-график, приёмка, отчёт и статья, коммуникация с заказчиком"],
            ["[ФИО 2]", "ML / CV-инженер",
             "Обзор источников, датасет и разметка, обучение и сравнение моделей, метрики, инференс-сервис"],
            ["[ФИО 3]", "Backend / Frontend / DevOps",
             "API и архив результатов, интерфейс оператора, Docker и docker compose, эмулятор ПЛК, CI, README"],
        ],
        widths=[3.2, 4.3, 9.5],
        font_size=10,
    )
    para(doc, "Роли распределены так, чтобы у каждого был самостоятельный блок работы и один общий "
              "интеграционный этап (КТ 4). Капитан дополнительно ведёт репозиторий и следит за сроками.")

    heading(doc, "2. Понимание задачи")

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("Цель проекта своими словами. ")
    style_run(r, 12, bold=True)
    r = p.add_run("Автоматически находить ржавчину на всей боковой поверхности и кромках цилиндра после "
                  "обработки, измерять её площадь, отличать лёгкую ржавчину от глубокой коррозии и выдавать "
                  "вердикт прямо на линию — без ручного визуального осмотра.")
    style_run(r, 12)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("Что на входе. ")
    style_run(r, 12, bold=True)
    r = p.add_run("Цветные снимки цилиндра: камера 5 МП с глобальным затвором, 4–8 кадров за оборот при "
                  "вращении детали на роликах (или 3–4 камеры по кругу). Разрешение не хуже 0,2 мм/пиксель, "
                  "белый свет 5000–6500 К, CRI ≥ 90, рассеянный купол против бликов.")
    style_run(r, 12)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Что на выходе:")
    style_run(r, 12, bold=True)
    for text in [
        "вердикт НОРМА / ВНИМАНИЕ / БРАК / ОШИБКА СИСТЕМЫ;",
        "снимок детали с выделенными пятнами ржавчины;",
        "суммарная площадь ржавчины в мм² и степень каждого пятна (лёгкая / глубокая);",
        "запись в архив (снимок + результат, хранение ≥ 30 дней, выгрузка в CSV);",
        "сигналы в ПЛК по Profinet или OPC UA.",
    ]:
        bullet(doc, text, size=11.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("Критерии приёмки из ТЗ:")
    style_run(r, 12, bold=True)
    table(
        doc,
        ["Критерий", "Требование"],
        [
            ["Обнаружение пятен от 5 мм", "recall ≥ 98%"],
            ["Погрешность площади", "≤ ±15%"],
            ["Правильная степень (лёгкая / глубокая)", "≥ 95%"],
            ["Тестовая выборка", "200 деталей: 100 норма, 50 лёгкая ржавчина, 50 глубокая"],
            ["Пропуск брака", "≤ 2%"],
            ["Ложная отбраковка", "≤ 3%"],
            ["Время проверки", "не больше такта линии"],
            ["Вердикты", "«Норма», «Внимание», «Брак», «Ошибка системы»"],
            ["Архив", "≥ 30 дней, выгрузка в CSV"],
            ["Настройка порогов", "инженером, без правки кода"],
            ["Правило вердикта", "нет ржавчины → норма; только лёгкая и ≤ 20 мм² → внимание; "
                                 "глубокая или > 20 мм² → брак"],
        ],
        widths=[6.2, 10.8],
        font_size=10,
    )

    heading(doc, "3. Разбор ТЗ и вопросы к заказчику")
    para(doc, "Заказчик: НТЦ ПАО «ЧКПЗ», отдел компьютерного зрения. Основание — «Список кейсов», "
              "утв. Подберезко Д. С.", size=11, indent=False)

    subheading(doc, "3.1. Что уже определено в ТЗ (не спрашиваем)")
    table(
        doc,
        ["Тема", "Что сказано в ТЗ"],
        [
            ["Зона контроля", "Вся боковая поверхность и кромки цилиндра"],
            ["Время проверки", "Не больше такта линии"],
            ["Вердикты и интеграция", "«Норма», «Внимание», «Брак», «Ошибка системы»; сигналы в ПЛК "
                                      "по Profinet или OPC UA"],
            ["Классы ржавчины", "Лёгкая (шелушится, матовая) и глубокая (ямки в металле)"],
            ["Признаки", "Цвет HSV/Lab, текстура (дисперсия, LBP), площадь по калибровке, степень"],
            ["Ложные срабатывания", "Блики, масло и следы СОЖ не должны считаться ржавчиной"],
            ["Правило вердикта", "Нет ржавчины → норма; только лёгкая и ≤ 20 мм² → внимание; "
                                 "глубокая или > 20 мм² → брак"],
            ["Оборудование (предварительно)", "Цветная камера 5 МП, глобальный затвор, GigE; ≤ 0,2 мм/пикс; "
                                              "свет 5000–6500 К, CRI ≥ 90; вращение на роликах 4–8 кадров "
                                              "или 3–4 камеры; ColorChecker"],
            ["Интерфейс оператора", "Снимок с выделенными дефектами, вердикт, измеренные размеры"],
            ["Архив", "Снимки и результаты ≥ 30 дней, выгрузка в CSV"],
            ["Настройки", "Пороги и параметры меняет инженер без правки кода"],
            ["Приёмка", "Пятна от 5 мм — ≥ 98%, площадь ±15%, степень ≥ 95%, "
                        "200 деталей (100/50/50), пропуск брака ≤ 2%, ложная отбраковка ≤ 3%"],
            ["Защита оборудования", "IP65 для камер и света, защита от пыли, СОЖ и вибрации"],
        ],
        widths=[4.3, 12.7],
        font_size=9,
    )
    para(doc, "Эти требования берём как есть и переносим в КТ 2–4, дублировать их в вопросах не нужно.",
         size=11, italic=True)

    subheading(doc, "3.2. Открытые вопросы")
    para(doc, "Диаметр/длина/материал, такт линии и вращение детали прямо отмечены в ТЗ как открытые. "
              "Остальные вопросы — подтверждение неоднозначных мест и границ проекта.", size=11)
    questions = [
        ("1", "Диаметр, длина и материал цилиндра?",
         "Расчёт оптики, числа камер и кадров на оборот (открытый вопрос ТЗ)"),
        ("2", "Такт линии, сек/деталь?",
         "Бюджет времени на съёмку и инференс (открытый вопрос ТЗ)"),
        ("3", "Можно ли вращать деталь на позиции контроля на роликах?",
         "Выбор схемы: 1 камера + вращение или 3–4 камеры по кругу (открытый вопрос ТЗ)"),
        ("4", "Подтвердить: «лёгкая ржавчина, но суммарно > 20 мм²» — это брак?",
         "В ТЗ сочетание не описано, принято как брак — нужно подтверждение"),
        ("5", "Какой протокол ПЛК использовать: Profinet или OPC UA?",
         "В ТЗ допущены оба, для прототипа и эмулятора нужен один"),
        ("6", "Что делать при сбое: пропускать деталь, останавливать линию или звать оператора?",
         "В ТЗ есть только сигнал «Ошибка системы», поведение линии не задано"),
        ("7", "Предоставит ли заказчик 200 деталей для приёмки (100/50/50) и эталонные образцы?",
         "Состав теста задан, но не сказано, кто даёт детали"),
        ("8", "Будет ли доступ к линии для съёмки, монтажа и опытной эксплуатации?",
         "Своих снимков нет, от этого зависит сбор данных и пусконаладка"),
        ("9", "Кто отвечает за механику установки, IP65, защиту от вибрации и СОЖ?",
         "Границы проекта: мы делаем ПО или установку целиком"),
        ("10", "«Пропуск брака ≤ 2%» и «ложная отбраковка ≤ 3%» считаются по деталям или по пятнам?",
         "Однозначные метрики для КТ 2–3 и приёмки"),
    ]
    table(
        doc,
        ["№", "Вопрос", "Зачем нужен ответ", "Ответ заказчика"],
        [[n, q, why, "[заполнить]"] for n, q, why in questions],
        widths=[0.9, 8.0, 5.0, 3.1],
        font_size=8.5,
    )

    heading(doc, "4. Бизнес-процесс «как есть»")
    picture(doc, "asis.png", "Рисунок 1 — Бизнес-процесс «как есть»: ручной визуальный контроль")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Участники: ")
    style_run(r, 12, bold=True)
    r = p.add_run("оператор ОТК, мастер / технолог, линия и склад (изолятор брака). Системы нет — всё "
                  "держится на людях и бумажном журнале.")
    style_run(r, 12)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Шаги:")
    style_run(r, 12, bold=True)
    for text in [
        "Деталь выходит с линии после обработки.",
        "Оператор ОТК вручную осматривает боковую поверхность и кромки.",
        "Если пятна или сомнения есть — мастер / технолог смотрит повторно.",
        "Решение: норма → следующая операция; ремонтопригодна → возврат на шлифовку; "
        "неремонтопригодна → изолятор брака.",
        "Результат, если успели, записывается в бумажный журнал; фото и площадь не сохраняются.",
    ]:
        pn = doc.add_paragraph(style="List Number")
        pn.paragraph_format.space_after = Pt(1)
        pn.paragraph_format.line_spacing = 1.1
        style_run(pn.add_run(text), 11.5)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Проблемы:")
    style_run(r, 12, bold=True)
    for text in [
        "Субъективность и усталость оператора: результат зависит от смены, освещения и опыта.",
        "Мелкие пятна от 5 мм пропускаются, площадь не измеряется — порог 20 мм² проверить нечем.",
        "Нет архива, фото и прослеживаемости: ложную отбраковку и спор с поставщиком нечем подтвердить.",
        "Время осмотра нестабильно и не привязано к такту линии.",
    ]:
        bullet(doc, text, size=11.5)

    heading(doc, "5. Бизнес-процесс «как будет»")
    picture(doc, "tobe.png", "Рисунок 2 — Бизнес-процесс «как будет»: автоматический контроль ржавчины")
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("Какой ручной шаг заменяет система. ")
    style_run(r, 12, bold=True)
    r = p.add_run("Полностью заменяется ручной визуальный осмотр оператора и повторный осмотр мастером: "
                  "система сама снимает деталь, находит ржавчину, измеряет площадь, определяет степень и "
                  "формирует вердикт.")
    style_run(r, 12)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Кто получает результат и что с ним делает:")
    style_run(r, 12, bold=True)
    for prefix, text in [
        ("ПЛК линии ", "получает сигнал Норма / Внимание / Брак / Ошибка системы и передаёт деталь на "
                       "следующую операцию, на шлифовку или в изолятор брака."),
        ("Оператор ", "видит на экране снимок с выделенными дефектами, вердикт и площадь; подтверждает "
                      "спорные случаи и принимает решение по деталям «Внимание»."),
        ("Инженер / технолог ", "настраивает пороги и параметры без правки кода, контролирует дрейф цвета "
                                "по эталону и разбирает спорные снимки."),
        ("Архив ", "хранит снимки и результаты ≥ 30 дней; технолог и служба качества выгружают CSV для "
                   "разбора и отчётности."),
    ]:
        bullet(doc, text, size=11.5, bold_prefix=prefix)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Ожидаемый эффект:")
    style_run(r, 12, bold=True)
    for text in [
        "Время проверки одной детали укладывается в такт линии, проверка не зависит от смены и усталости.",
        "Стабильное обнаружение пятен от 5 мм (recall ≥ 98%) и измеренная площадь вместо «на глаз».",
        "Меньше ложной отбраковки за счёт фильтрации бликов, масла и СОЖ.",
        "Появляются архив, прослеживаемость и объективные данные для разбора брака.",
    ]:
        bullet(doc, text, size=11.5)

    heading(doc, "6. План-график")
    para(doc, "Даты ориентировочные (отсчёт от 17.11.2026) — скорректировать под дедлайны в Moodle.",
         size=11, italic=True)
    table(
        doc,
        ["Этап", "Ответственный", "Срок", "КТ"],
        [
            ["Разбор ТЗ, вопросы заказчику, схемы «как есть» / «как будет», репозиторий",
             "[ФИО капитана]", "Неделя 1: 17–23.11.2026", "КТ 1"],
            ["Обзор статей и готовых решений, выбор 3+ кандидатов", "[ФИО 2]",
             "Недели 2–3: 24.11–07.12.2026", "КТ 2"],
            ["Сбор и разметка датасета, метрики", "[ФИО 2], [ФИО 3]",
             "Недели 2–3: 24.11–07.12.2026", "КТ 2"],
            ["Обучение и сравнение моделей на одном железе", "[ФИО 2]",
             "Недели 4–5: 08–21.12.2026", "КТ 3"],
            ["Разбор ошибок, выбор лучшей модели", "[ФИО 2], [ФИО капитана]",
             "Неделя 5: 15–21.12.2026", "КТ 3"],
            ["Backend, архив, CSV, интерфейс оператора", "[ФИО 3]",
             "Недели 6–7: 22.12.2026–04.01.2027", "КТ 4"],
            ["Docker-образы, docker compose up --build, демо-сценарии", "[ФИО 3], [ФИО 2]",
             "Недели 6–7: 22.12.2026–04.01.2027", "КТ 4"],
            ["Итоговый отчёт, презентация, живое демо", "Все", "Неделя 8: 05–11.01.2027", "КТ 5"],
            ["Тема и тезисы статьи", "[ФИО капитана]", "Неделя 2: 24–30.11.2026", "Статья"],
            ["Статья, проверка в «Думейте»", "[ФИО капитана], все", "Недели 5–8", "Статья"],
        ],
        widths=[7.4, 3.6, 4.2, 1.8],
        font_size=8.5,
    )

    heading(doc, "7. Риски")
    table(
        doc,
        ["Риск", "Что сделаем"],
        [
            ["Нет собственных снимков цилиндров, только открытые датасеты",
             "Подбираем открытые наборы коррозии + аугментация; параллельно договариваемся о съёмке на линии. "
             "План Б — few-shot дообучение на 20–50 своих кадрах"],
            ["Доменный сдвиг: ржавчина на цилиндрах не похожа на открытые фото",
             "Смешиваем открытые данные со своими, проверяем на отложенной «своей» выборке, оставляем "
             "классический HSV/Lab-метод как baseline"],
            ["RTX 3060 Laptop, 6 ГБ VRAM",
             "Лёгкие модели (YOLOv8n/s-seg, SegFormer-B0), вход 512–640 px, AMP, batch 2–4; при нехватке — "
             "обучение в Colab, инференс на CPU"],
            ["Блики, масло, СОЖ дают ложную ржавчину",
             "Купол / поляризация, маска бликов, отдельный класс «не дефект», проверка на реальных кадрах"],
            ["Нет доступа к ПЛК и линии",
             "Эмулятор ПЛК (OPC UA / Modbus), офлайн-демо на видео и папке снимков; интеграция описывается "
             "в отчёте"],
            ["Разметка субъективна (граница лёгкая / глубокая)",
             "Гайдлайн разметки, двойная разметка части кадров, калибровка с технологом, метрика согласия"],
            ["Сроки: сессия и Новый год",
             "MVP делаем раньше (КТ 3), резерв — неделя перед защитой, демо-видео записываем заранее"],
            ["Требование 0% ИИ в статье",
             "Пишем текст сами, ИИ используем только для поиска источников и вычитки; проверяем в «Думейте» "
             "до сдачи"],
        ],
        widths=[6.4, 10.6],
        font_size=9,
    )

    heading(doc, "8. Допущения и границы проекта")
    table(
        doc,
        ["Допущение", "Как влияет на работу"],
        [
            ["Своих снимков цилиндров пока нет",
             "До получения доступа к линии используем открытые датасеты коррозии и аугментацию; "
             "приёмка на 200 реальных деталях — этап опытной эксплуатации"],
            ["Прототип работает офлайн: папка снимков или видео",
             "ПЛК эмулируем по OPC UA; реальный ПЛК подключаем на этапе интеграции"],
            ["Разрешение съёмки ≤ 0,2 мм/пикс и калибровочная мишень доступны",
             "Без калибровки площадь в мм² и порог 20 мм² не гарантируются"],
            ["Механику, свет, IP65, монтаж и пусконаладку не изготавливаем",
             "Это граница с заказчиком (вопрос 9), в проекте — только ПО и схема установки"],
            ["«Лёгкая ржавчина > 20 мм² = брак» принимаем по ТЗ как рабочее правило",
             "Действует до подтверждения заказчиком (вопрос 4)"],
        ],
        widths=[7.4, 9.6],
        font_size=9.5,
    )

    heading(doc, "9. Исходные материалы")
    for text in [
        "filesfromcourse/ТЗ на системы техзрения ржавчина, недообработка, заусенцы.pdf — "
        "раздел «ТЗ 1. Система обнаружения ржавчины и коррозии».",
        "filesfromcourse/КТ 1. Старт и бизнес-процессы.docx — шаблон задания.",
        "filesfromcourse/Методичка как писать статьи по ИИ.pdf, Как писать тезисы статьи.pdf — "
        "для этапа статьи.",
    ]:
        bullet(doc, text, size=11.5)

    heading(doc, "Чек-лист сдачи")
    for text, done in [
        ("У каждого участника есть роль и задачи", True),
        ("Схемы «как есть» и «как будет» готовы", True),
        ("Понятно, какой ручной шаг заменяет система", True),
        ("План покрывает все пункты ТЗ", True),
        ("Репозиторий создан, есть README", True),
        ("Заполнить ФИО, ссылку на репозиторий и ответы заказчика", False),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        r = p.add_run(("☒ " if done else "☐ ") + text)
        style_run(r, 12)

    doc.save(DOC_PATH)
    print(f"saved: {DOC_PATH}")


if __name__ == "__main__":
    build()
