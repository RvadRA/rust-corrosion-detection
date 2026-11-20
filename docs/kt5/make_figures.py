"""Иллюстрации для КТ 5."""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

models = ["M1\nHSV", "M2\nLab", "M3\nRF", "M4\nU-Net"]
f1 = [0.551, 0.564, 0.623, 0.629]
colors = ["#A6A6A6", "#A6A6A6", "#A6A6A6", "#1F3864"]

fig, ax = plt.subplots(figsize=(8.6, 4.4), dpi=200)
bars = ax.bar(models, f1, color=colors, width=0.58)
ax.set_ylim(0.45, 0.66)
ax.set_ylabel("F1 micro", fontsize=11)
ax.set_title("F1 micro на test 79: M4 U-Net выбрана для прототипа", fontsize=12, pad=12)
ax.grid(axis="y", color="#E0E0E0", linewidth=0.8)
ax.set_axisbelow(True)
for bar, value in zip(bars, f1):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.004, f"{value:.3f}",
            ha="center", va="bottom", fontsize=10, fontweight="bold", color="#1F1F1F")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "models_f1.png"), bbox_inches="tight", facecolor="white")
plt.close(fig)
print(os.path.join(FIG, "models_f1.png"))
