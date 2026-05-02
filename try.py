import json
import os
import argparse
from pathlib import Path


# Мітки пауз / меж синтагм
SILENCE_TOKENS = {"pɑu", "AP"}


def parse_lab(lab_path: str) -> list[tuple[float, float, str]]:
    entries = []
    with open(lab_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            start, end, ph = float(parts[0]), float(parts[1]), parts[2]
            entries.append((start, end, ph))
    return entries


def lab_to_item(
    item_name: str,
    wav_fn: str,
    lab_entries: list[tuple[float, float, str]],
    speaker: str,
) -> dict:

    ph_list = []
    ph_durs = []
    ph2words = []

    # Групуємо фонеми у синтагми.
    # Кожна нова синтагма починається після silence токена.
    # Silence токени включаємо у поточну синтагму.
    word_groups = []      
    current_group = []

    pending_silences = []

    for start, end, ph in lab_entries:
        if ph in SILENCE_TOKENS:
            if current_group:
                current_group.append((start, end, ph))
                word_groups.append(current_group)
                current_group = []
            else:
                pending_silences.append((start, end, ph))
        else:
            if not current_group:
                current_group.extend(pending_silences)
                pending_silences = []
            current_group.append((start, end, ph))

    if current_group:
        current_group.extend(pending_silences)
        word_groups.append(current_group)
    elif pending_silences:
        word_groups.append(pending_silences)

    word_list = []
    word_durs = []

    for word_idx, group in enumerate(word_groups):
        group_start = group[0][0]
        group_end = group[-1][1]
        word_dur = round(group_end - group_start, 6)

        word_str = "_".join(ph for _, _, ph in group if ph not in SILENCE_TOKENS)
        if not word_str:
            word_str = "SP"

        word_list.append(word_str)
        word_durs.append(word_dur)

        for start, end, ph in group:
            ph_list.append(ph)
            ph_durs.append(round(end - start, 6))
            ph2words.append(word_idx + 1)  

    pitches = [0] * len(ph_list)

    return {
        "item_name": item_name,
        "wav_fn": wav_fn,
        "ph": ph_list,
        "ph_durs": ph_durs,
        "ph2words": ph2words,
        "word": word_list,
        "word_durs": word_durs,
        "pitches": pitches,
        "singer": speaker,
        "lang": "uk",
    }

def process_dataset(wav_dir: str, lab_dir: str, output_path: str, speaker: str):
    wav_dir = Path(wav_dir)
    lab_dir = Path(lab_dir)

    lab_files = sorted(lab_dir.glob("*.lab"))
    if not lab_files:
        print(f"❌ Не знайдено .lab файлів у {lab_dir}")
        return

    items = []
    skipped = []

    for lab_path in lab_files:
        item_name = lab_path.stem
        wav_path = wav_dir / f"{item_name}.wav"

        if not wav_path.exists():
            skipped.append(f"{item_name}: wav не знайдено ({wav_path})")
            continue

        try:
            lab_entries = parse_lab(str(lab_path))
            if not lab_entries:
                skipped.append(f"{item_name}: порожній lab файл")
                continue

            item = lab_to_item(
                item_name=item_name,
                wav_fn=str(wav_path),
                lab_entries=lab_entries,
                speaker=speaker,
            )
            items.append(item)

        except Exception as e:
            skipped.append(f"{item_name}: {e}")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"✅ Оброблено: {len(items)} файлів")
    print(f"📄 Збережено: {output_path}")

    if skipped:
        print(f"\n⚠️  Пропущено ({len(skipped)}):")
        for s in skipped:
            print(f"   {s}")

    if items:
        avg_ph = sum(len(i["ph"]) for i in items) / len(items)
        avg_words = sum(len(i["word"]) for i in items) / len(items)
        print(f"\n📊 Статистика:")
        print(f"   Середня к-сть фонем: {avg_ph:.1f}")
        print(f"   Середня к-сть синтагм: {avg_words:.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Підготовка metadata_processed.json для STARS (українська)")
    parser.add_argument("--wav_dir",  default="wavs/",  help="Папка з WAV файлами")
    parser.add_argument("--lab_dir",  default="labs/",  help="Папка з LAB файлами")
    parser.add_argument("--output",   default="data/processed/ukrainian/metadata_processed.json",
                        help="Шлях до вихідного metadata_processed.json")
    parser.add_argument("--speaker",  default="ukrainian_speaker", help="Ім'я спікера")
    args = parser.parse_args()

    process_dataset(
        wav_dir=args.wav_dir,
        lab_dir=args.lab_dir,
        output_path=args.output,
        speaker=args.speaker,
    )