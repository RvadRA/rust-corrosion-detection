# Данные проекта: обнаружение ржавчины и коррозии

Датасет-карта для ТЗ 1 (ПАО «ЧКПЗ»). Здесь описано, какие открытые данные скачаны,
как они лежат на диске, что в них реально размечено и чего не хватает.

## 1. Состав

| Набор | Файл | Объём | Разметка | Лицензия |
|---|---|---|---|---|
| Corrosion in Industrial Complexes in Ostrava | `raw/ostrava.zip` | 105 изображений 2048×2048 + 105 масок, сплит 75/15/15 | Бинарные пиксельные маски коррозии | CC BY 4.0 |
| Corrosion Condition State (Virginia Tech) | `raw/vt_corrosion.zip` | 440 изображений (оригинал + 512×512) + 440 масок + 440 LabelMe JSON | 3 класса: fair / poor / severe | CC0 |
| Corroded Pipelines (Petrobras) | `raw/Corrosion_Pipelines.zip` | 110 изображений, 709 instance-масок | COCO, 1 класс `corrosão` | CC BY 4.0 |
| Собственная съёмка (план) | — | 300 кадров нормы + 20–50 деталей с дефектами | Полигоны + ignore-зоны | Внутренняя |

Итого открытых данных: **655 изображений** (105 + 440 + 110), 709 instance-масок
в pipelines и 440 масок VT.

## 2. Источники и лицензии

| Набор | DOI / ссылка | Авторы, год |
|---|---|---|
| Ostrava | https://doi.org/10.5281/zenodo.11235637 | Corrosion in Industrial Complexes in Ostrava, 2024 |
| Virginia Tech | https://doi.org/10.7294/16624663.v2 | Bianchi, Hebdon, 2021 |
| Corroded Pipelines | https://doi.org/10.6084/m9.figshare.30019591.v2 | Petrobras / Corroded Pipelines, 2025 |

Лицензии разрешают учебное и исследовательское использование при указании авторов.
Для коммерческого внедрения условия лицензий нужно проверить отдельно.

## 3. Контрольные суммы

| Файл | Размер, байт | SHA-256 |
|---|---|---|
| `Corrosion_Pipelines.zip` | 11 009 354 | `3ce05636b67932d6be86df3fb643cc5ab95b84e8d717c165502aae7343072803` |
| `ostrava.zip` | 384 363 293 | `874a60cd8e9e92476c2314bd6acfcac7dc0f64eb797ea220a091a96681de50c5` |
| `vt_corrosion.zip` | 333 388 620 | `45f0ec8b26f1c09d707f3010af359a28e0985d385d2bf6d98b5d4dd308e9dbe5` |

MD5 `ostrava.zip` совпадает с опубликованным на Zenodo: `e30f1f62eb85018c2faee44909e69a06`.

## 4. Структура на диске

```
dataset/raw/
├── Corrosion_Pipelines.zip
├── ostrava.zip
├── vt_corrosion.zip
├── pipelines/
│   └── job_100_dataset_2025_04_09_17_18_29_coco 1.0/
│       ├── annotations/instances_default.json
│       └── images/
├── ostrava/
│   └── corrosion-in-industrial-complexes-in-ostrava/
│       ├── train/{images,masks}       # 75 + 75
│       ├── validation/{images,masks}  # 15 + 15
│       └── test/{images,masks}        # 15 + 15
└── vt/
    └── Corrosion Condition State Classification/
        ├── original/{Train,Test}/{images,masks,json}  # 396 + 44
        └── 512x512/{Train,Test}/{images_512,mask_512} # 396 + 44
```

Сырые данные и веса не коммитятся: `dataset/raw/` и `dataset/processed/` в `.gitignore`.
Скрипт скачивания и проверки — `src/ml/download_data.py`.

## 5. Что реально размечено

- **Ostrava**: 105 изображений, у каждого есть маска; класс один — «коррозия».
  Сплит авторов: train 75, validation 15, test 15.
- **Virginia Tech**: 440 изображений. В релизе фактически три класса, `good` нет:
  fair — 432 изображения, poor — 337, severe — 104 (одно изображение может содержать
  несколько состояний). Всего 4113 полигонов. Сплит: train 396, test 44.
- **Pipelines**: 110 изображений, 709 instance-масок, одна категория `corrosão`.

## 6. Ограничения и план

1. **Нет класса «норма»**. Все три открытых набора содержат только дефекты. Чистую
   поверхность и сложные негативы (блики, масло, СОЖ, царапины) нужно снимать
   самостоятельно или вырезать чистые области из открытых кадров.
2. **Доменный сдвиг**. Мосты, трубы и промышленные конструкции — не цилиндры после
   обработки. Нужна собственная съёмка 20–50 деталей и тест на отложенном домене.
3. **Разметка степени**. В Ostrava и pipelines маски бинарные, степень «лёгкая/глубокая»
   не размечена. Нужна ручная переразметка по правилам ТЗ.
4. **Мелкие пятна**. Целевой объект от 5 мм при 0,2 мм/пикс — около 25 пикселей;
   на таких объектах recall падает, поэтому нужны crop'ы и copy-paste.

Целевые сплиты после пересборки: train — 300 изображений на класс (`norm`,
`rust_light`, `rust_deep`), val — 100 на класс, test — 200 (100/50/50), как в ТЗ.

## 7. Воспроизведение

```bash
python src/ml/download_data.py --dest dataset/raw
python src/ml/download_data.py --dest dataset/raw --check-only
```

Скрипт проверяет SHA-256, распаковывает архивы и печатает фактическое число
изображений и масок. Если файл уже скачан и контрольная сумма совпала, повторная
загрузка не выполняется (для принудительной — флаг `--force`).
