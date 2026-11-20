"""Генерация блок-схем «как есть» и «как будет» для КТ 1."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Patch

plt.rcParams["font.family"] = "DejaVu Sans"

ROLES = {
    "line": ("Линия / ПЛК", "#DCE9F7", "#2F5597"),
    "oper": ("Оператор ОТК", "#E2F0D9", "#548235"),
    "tech": ("Технолог / инженер", "#FFF2CC", "#BF9000"),
    "cam": ("Камера и свет", "#E4DFEC", "#673AB7"),
    "cv": ("Система CV", "#E1F5FE", "#0277BD"),
    "note": ("Проблема / результат", "#FBE5D6", "#C55A11"),
    "start": ("Начало / конец", "#E7E6E6", "#595959"),
}


def box(ax, cx, cy, w, h, text, role, fs=9, bold=False):
    fill, edge = ROLES[role][1], ROLES[role][2]
    p = FancyBboxPatch(
        (cx - w / 2, cy - h / 2),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=1.4,
        facecolor=fill,
        edgecolor=edge,
        zorder=2,
    )
    ax.add_patch(p)
    ax.text(
        cx,
        cy,
        text,
        ha="center",
        va="center",
        fontsize=fs,
        fontweight="bold" if bold else "normal",
        color="#1a1a1a",
        zorder=3,
    )
    return (cx, cy, w, h)


def diamond(ax, cx, cy, w, h, text, role, fs=9):
    fill, edge = ROLES[role][1], ROLES[role][2]
    pts = [(cx - w / 2, cy), (cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fill, edgecolor=edge, linewidth=1.4, zorder=2))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, zorder=3)
    return (cx, cy, w, h)


def arrow(ax, p1, p2, label=None, lx=0.2, ly=0.2, via=None, color="#333333"):
    style = dict(arrowstyle="-|>", lw=1.5, color=color, shrinkA=0, shrinkB=0)
    if via is None:
        ax.annotate("", xy=p2, xytext=p1, arrowprops=style, zorder=1)
        if label:
            ax.text((p1[0] + p2[0]) / 2 + lx, (p1[1] + p2[1]) / 2 + ly, label,
                    fontsize=8.5, color="#C00000", ha="center", va="center", zorder=4)
    else:
        ax.plot([p1[0], via[0]], [p1[1], via[1]], color=color, lw=1.5, zorder=1)
        ax.annotate("", xy=p2, xytext=via, arrowprops=style, zorder=1)
        if label:
            ax.text(via[0] + lx, (via[1] + p2[1]) / 2 + ly, label,
                    fontsize=8.5, color="#C00000", ha="center", va="center", zorder=4)


def legend(ax, y):
    handles = [Patch(facecolor=f, edgecolor=e, label=n) for n, f, e in ROLES.values()]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=4, frameon=False, fontsize=8.5)


def draw_asis(path):
    W, H = 14.2, 16.0
    fig, ax = plt.subplots(figsize=(11, 11.6))
    ax.set_xlim(0, W)
    ax.set_ylim(-1.6, H)
    ax.axis("off")
    ax.set_title("Бизнес-процесс «как есть»: визуальный контроль ржавчины", fontsize=13, fontweight="bold", pad=8)

    s = box(ax, 6.75, 14.5, 5.8, 0.95, "Деталь выходит с линии\nпосле обработки", "start", bold=True)
    b2 = box(ax, 6.75, 12.85, 6.3, 1.25, "Оператор ОТК вручную осматривает\nбоковую поверхность и кромки", "oper")
    d1 = diamond(ax, 6.75, 11.05, 3.9, 1.6, "Пятна или\nсомнения есть?", "oper")
    b4 = box(ax, 12.0, 9.0, 3.2, 1.35, "Деталь годна =\nНОРМА → следующая\nоперация", "oper", fs=8.5)
    b5 = box(ax, 6.75, 9.0, 6.0, 1.25, "Мастер / технолог\nсмотрит повторно и решает", "tech")
    d2 = diamond(ax, 6.75, 7.0, 4.0, 1.6, "Ремонтопригодна?", "tech")
    b7 = box(ax, 2.1, 5.1, 4.0, 1.0, "Возврат на шлифовку", "line")
    b8 = box(ax, 6.75, 5.1, 4.2, 1.0, "Брак → изолятор брака", "line")
    res = box(ax, 6.6, 3.2, 9.6, 1.15, "Результат: запись в бумажный журнал (если успели),\nфото и площадь пятна не сохраняются", "oper")
    prob = box(ax, 6.75, 1.0, 11.4, 2.1,
               "Проблемы: субъективность и усталость оператора; мелкие пятна от 5 мм пропускаются;\n"
               "площадь не измеряется; нет архива, прослеживаемости и выгрузки; ложная отбраковка\n"
               "и споры с поставщиком ничем не подтверждены", "note", fs=9)

    arrow(ax, (s[0], s[1] - s[3] / 2), (b2[0], b2[1] + b2[3] / 2))
    arrow(ax, (b2[0], b2[1] - b2[3] / 2), (d1[0], d1[1] + d1[3] / 2))
    arrow(ax, (d1[0] + d1[2] / 2, d1[1]), (b4[0], b4[1] + b4[3] / 2), "нет", lx=0.35, ly=0.0, via=(12.0, 11.05))
    arrow(ax, (d1[0], d1[1] - d1[3] / 2), (b5[0], b5[1] + b5[3] / 2), "да", lx=0.35, ly=0.0)
    arrow(ax, (b5[0], b5[1] - b5[3] / 2), (d2[0], d2[1] + d2[3] / 2))
    arrow(ax, (d2[0] - d2[2] / 2, d2[1]), (b7[0], b7[1] + b7[3] / 2), "да", lx=0.0, ly=0.2, via=(2.1, 7.0))
    arrow(ax, (d2[0], d2[1] - d2[3] / 2), (b8[0], b8[1] + b8[3] / 2), "нет", lx=0.3, ly=0.0)
    arrow(ax, (b4[0], b4[1] - b4[3] / 2), (res[0] + res[2] / 2, res[1]), via=(12.0, 3.2))
    arrow(ax, (b7[0], b7[1] - b7[3] / 2), (res[0] - res[2] / 2, res[1]), via=(2.1, 3.2))
    arrow(ax, (b8[0], b8[1] - b8[3] / 2), (res[0], res[1] + res[3] / 2))
    arrow(ax, (res[0], res[1] - res[3] / 2), (prob[0], prob[1] + prob[3] / 2))

    legend(ax, 1.03)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_tobe(path):
    W, H = 15.0, 19.0
    fig, ax = plt.subplots(figsize=(12, 14.2))
    ax.set_xlim(0, W)
    ax.set_ylim(-1.4, H)
    ax.axis("off")
    ax.set_title("Бизнес-процесс «как будет»: автоматический контроль ржавчины", fontsize=13, fontweight="bold", pad=8)

    s = box(ax, 7.5, 18.0, 6.6, 0.9, "Деталь на позиции контроля\n(датчик присутствия)", "start", bold=True)
    b2 = box(ax, 7.5, 16.4, 6.8, 1.05, "ПЛК: старт проверки,\nвращение детали на роликах", "line")
    b3 = box(ax, 7.5, 14.7, 7.8, 1.2, "Камера и свет: 4–8 кадров за оборот, белый\n5000–6500 К, CRI ≥ 90, купол против бликов", "cam")
    b4 = box(ax, 7.5, 12.95, 8.4, 1.3, "Система CV: HSV/Lab, сегментация ржавчины,\nфильтрация бликов, масла и следов СОЖ", "cv")
    b5 = box(ax, 7.5, 11.2, 8.2, 1.25, "Площадь всех пятен в мм² по калибровке +\nстепень: лёгкая / глубокая", "cv")
    d = diamond(ax, 7.5, 9.35, 3.6, 1.6, "Правило\nвердикта", "cv")
    b7 = box(ax, 2.55, 7.4, 4.0, 1.05, "НОРМА\nржавчины нет", "line")
    b8 = box(ax, 7.5, 7.4, 4.6, 1.05, "ВНИМАНИЕ\nлёгкая ≤ 20 мм²", "line")
    b9 = box(ax, 12.35, 7.4, 4.8, 1.05, "БРАК\nглубокая или > 20 мм²", "line")
    b10 = box(ax, 7.5, 5.5, 9.4, 1.25, "Вердикт в ПЛК (Profinet / OPC UA) и в архив на 30 дней:\nснимок с масками, площадь, степень, выгрузка в CSV", "line")
    b11 = box(ax, 7.5, 3.75, 9.8, 1.25, "Оператор видит снимок с выделенными дефектами,\nвердикт и площадь; подтверждает или отправляет на шлифовку / в брак", "oper")
    b12 = box(ax, 7.5, 2.0, 8.8, 1.15, "Инженер настраивает пороги и параметры без правки кода;\nконтроль дрейфа цвета по эталону ColorChecker", "tech")
    err = box(ax, 13.45, 10.6, 2.8, 0.95, "Сбой / нет кадра →\n«Ошибка системы»", "note", fs=8.5)

    arrow(ax, (s[0], s[1] - s[3] / 2), (b2[0], b2[1] + b2[3] / 2))
    arrow(ax, (b2[0], b2[1] - b2[3] / 2), (b3[0], b3[1] + b3[3] / 2))
    arrow(ax, (b3[0], b3[1] - b3[3] / 2), (b4[0], b4[1] + b4[3] / 2))
    arrow(ax, (b4[0], b4[1] - b4[3] / 2), (b5[0], b5[1] + b5[3] / 2))
    arrow(ax, (b5[0], b5[1] - b5[3] / 2), (d[0], d[1] + d[3] / 2))
    arrow(ax, (d[0] - d[2] / 2, d[1]), (b7[0], b7[1] + b7[3] / 2), "нет", lx=0.15, ly=0.15, via=(2.55, 9.35))
    arrow(ax, (d[0], d[1] - d[3] / 2), (b8[0], b8[1] + b8[3] / 2), "лёгкая", lx=0.35, ly=0.0)
    arrow(ax, (d[0] + d[2] / 2, d[1]), (b9[0], b9[1] + b9[3] / 2), "глубокая", lx=-0.1, ly=0.15, via=(12.35, 9.35))
    arrow(ax, (b7[0], b7[1] - b7[3] / 2), (b10[0] - b10[2] / 2, b10[1]), via=(2.55, 5.5))
    arrow(ax, (b8[0], b8[1] - b8[3] / 2), (b10[0], b10[1] + b10[3] / 2))
    arrow(ax, (b9[0], b9[1] - b9[3] / 2), (b10[0] + b10[2] / 2, b10[1]), via=(12.35, 5.5))
    arrow(ax, (b10[0], b10[1] - b10[3] / 2), (b11[0], b11[1] + b11[3] / 2))
    arrow(ax, (b11[0], b11[1] - b11[3] / 2), (b12[0], b12[1] + b12[3] / 2))
    ax.plot([b3[0] + b3[2] / 2, err[0], err[0]], [b3[1], b3[1], err[1] + err[3] / 2], color="#C55A11", lw=1.3, ls="--")
    ax.annotate("", xy=(err[0], err[1] + err[3] / 2), xytext=(err[0], err[1] + err[3] / 2 + 0.3),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#C55A11"))

    legend(ax, 1.04)
    fig.text(0.5, 0.012,
             "Система заменяет ручной визуальный осмотр: оператор получает готовый вердикт, "
             "снимок с масками и измеренную площадь.",
             ha="center", fontsize=9, style="italic")
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    draw_asis("asis.png")
    draw_tobe("tobe.png")
    print("saved asis.png, tobe.png")
