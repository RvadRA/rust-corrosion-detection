"""Аудит усреднения F1/Dice/IoU по сохранённым строкам M1–M4."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "kt3" / "results"


def load_rows():
    methods = {}
    thr = json.loads((OUT / "thresholds.json").read_text(encoding="utf-8"))
    for name in ("M1 HSV-порог", "M2 Lab-порог"):
        methods[name] = (thr["methods"][name]["rows"], thr["methods"][name]["test"]["all"])
    for name, fname in (("M3 RandomForest", "rf.json"), ("M4 U-Net", "unet.json")):
        d = json.loads((OUT / fname).read_text(encoding="utf-8"))
        methods[name] = (d["rows"], d["test"]["all"])
    return methods


def recalc(rows):
    tp = sum(int(r["tp"]) for r in rows)
    fp = sum(int(r["fp"]) for r in rows)
    fn = sum(int(r["fn"]) for r in rows)
    denom = 2 * tp + fp + fn
    return {
        "n": len(rows),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision_micro": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
        "recall_micro": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
        "f1_micro": round(2 * tp / denom, 4) if denom else 1.0,
        "dice_micro": round(2 * tp / denom, 4) if denom else 1.0,
        "iou_micro": round(tp / (tp + fp + fn), 4) if (tp + fp + fn) else 1.0,
        "dice_macro": round(float(np.mean([r["dice"] for r in rows])), 4),
        "iou_macro": round(float(np.mean([r["iou"] for r in rows])), 4),
        "area_rel_error_macro": round(float(np.mean([r["area_rel_error"] for r in rows])), 4),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    audit = {
        "source": "src/ml/kt3/audit_metrics.py",
        "note": "F1/Precision/Recall — micro (по пикселям); Dice/IoU — macro (среднее по изображениям). "
                "benchmark.py качество не считает, только FPS/RSS.",
        "methods": {},
    }
    mismatches = []
    for name, (rows, reported) in load_rows().items():
        calc = recalc(rows)
        checks = {}
        for old, new in (("precision", "precision_micro"), ("recall", "recall_micro"),
                         ("f1", "f1_micro"), ("mean_dice", "dice_macro"),
                         ("mean_iou", "iou_macro"), ("mean_area_rel_error", "area_rel_error_macro")):
            before = reported.get(old)
            after = calc[new]
            checks[old] = {"reported": before, "recomputed": after,
                           "delta": round(abs(float(before) - float(after)), 4) if before is not None else None}
            if before is not None and abs(float(before) - float(after)) > 1e-3:
                mismatches.append(f"{name}:{old}")
        calc["reported"] = {k: reported[k] for k in reported if k != "n"}
        calc["checks"] = checks
        audit["methods"][name] = calc

    audit["status"] = "ok" if not mismatches else "mismatch"
    audit["mismatches"] = mismatches
    (OUT / "metrics_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, m in audit["methods"].items():
        print(name, "F1micro", m["f1_micro"], "DiceMacro", m["dice_macro"],
              "IoUmacro", m["iou_macro"], "IoUmicro", m["iou_micro"],
              "area", m["area_rel_error_macro"])
    print("status", audit["status"], mismatches)
    print("saved", OUT / "metrics_audit.json")


if __name__ == "__main__":
    main()
