"""
split_segments.py

Нарізає wav+lab файли на фрагменти по ~30 секунд по межах синтагм (AP/pɑu).
Оновлює metadata_processed.json з новими фрагментами.

Використання:
  python split_segments.py \
    --wav_dir wavs/ \
    --lab_dir labs/ \
    --output_wav_dir data/segments/wavs/ \
    --output_lab_dir data/segments/labs/ \
    --output_meta data/processed/ukrainian/metadata_processed.json \
    --speaker ukrainian_speaker \
    --max_dur 30.0
"""

import json
import os
import argparse
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path

SILENCE_TOKENS = {"pɑu", "AP"}


def parse_lab(lab_path):
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


def find_split_points(lab_entries, max_dur=30.0):
    """
    Знаходить точки розбиття по межах синтагм (AP/pɑu),
    намагаючись тримати фрагменти близько до max_dur секунд.
    """
    total_dur = lab_entries[-1][1]
    split_points = [0.0]
    last_split = 0.0

    for i, (start, end, ph) in enumerate(lab_entries):
        if ph in SILENCE_TOKENS:
            current_dur = end - last_split
            if current_dur >= max_dur:
                split_points.append(end)
                last_split = end

    if split_points[-1] < total_dur:
        split_points.append(total_dur)

    return split_points


def lab_to_item(item_name, wav_fn, lab_entries, speaker):
    """Конвертує lab_entries у запис metadata."""
    ph_list = []
    ph_durs = []
    ph2words = []
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


def process_dataset(wav_dir, lab_dir, output_wav_dir, output_lab_dir, output_meta, speaker, max_dur):
    wav_dir = Path(wav_dir)
    lab_dir = Path(lab_dir)
    os.makedirs(output_wav_dir, exist_ok=True)
    os.makedirs(output_lab_dir, exist_ok=True)

    lab_files = sorted(lab_dir.glob("*.lab"))
    items = []
    skipped = []
    total_segments = 0

    for lab_path in lab_files:
        item_name = lab_path.stem
        wav_path = wav_dir / f"{item_name}.wav"

        if not wav_path.exists():
            skipped.append(f"{item_name}: wav не знайдено")
            continue

        try:
            lab_entries = parse_lab(str(lab_path))
            if not lab_entries:
                skipped.append(f"{item_name}: порожній lab файл")
                continue

            # Завантажуємо аудіо
            wav, sr = librosa.load(str(wav_path), sr=24000, mono=True)

            # Знаходимо точки розбиття
            split_points = find_split_points(lab_entries, max_dur=max_dur)

            # Нарізаємо
            for seg_idx in range(len(split_points) - 1):
                seg_start = split_points[seg_idx]
                seg_end = split_points[seg_idx + 1]
                seg_dur = seg_end - seg_start

                if seg_dur < 1.0:
                    continue

                seg_name = f"{item_name}_seg{seg_idx:03d}"

                # Фрагмент wav
                start_sample = int(seg_start * sr)
                end_sample = int(seg_end * sr)
                seg_wav = wav[start_sample:end_sample]
                seg_wav_path = os.path.join(output_wav_dir, f"{seg_name}.wav")
                sf.write(seg_wav_path, seg_wav, sr)

                # Фрагмент lab (зсуваємо час до 0)
                seg_lab_entries = [
                    (round(s - seg_start, 6), round(e - seg_start, 6), ph)
                    for s, e, ph in lab_entries
                    if s >= seg_start - 0.001 and e <= seg_end + 0.001
                ]

                if not seg_lab_entries:
                    continue

                # Обрізаємо межі
                seg_lab_entries[0] = (0.0, seg_lab_entries[0][1], seg_lab_entries[0][2])
                seg_lab_entries[-1] = (seg_lab_entries[-1][0], round(seg_end - seg_start, 6), seg_lab_entries[-1][2])

                seg_lab_path = os.path.join(output_lab_dir, f"{seg_name}.lab")
                with open(seg_lab_path, "w", encoding="utf-8") as f:
                    for s, e, ph in seg_lab_entries:
                        f.write(f"{s}\t{e}\t{ph}\n")

                # Запис metadata
                item = lab_to_item(seg_name, seg_wav_path, seg_lab_entries, speaker)
                items.append(item)
                total_segments += 1

            print(f"✅ {item_name}: {len(split_points)-1} фрагментів ({lab_entries[-1][1]:.1f}s)")

        except Exception as e:
            skipped.append(f"{item_name}: {e}")
            import traceback
            traceback.print_exc()

    # Зберігаємо metadata
    os.makedirs(os.path.dirname(output_meta), exist_ok=True)
    with open(output_meta, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\n📊 Всього фрагментів: {total_segments}")
    print(f"📄 Збережено: {output_meta}")

    if skipped:
        print(f"\n⚠️  Пропущено ({len(skipped)}):")
        for s in skipped:
            print(f"   {s}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wav_dir",        default="wavs/")
    parser.add_argument("--lab_dir",        default="labs/")
    parser.add_argument("--output_wav_dir", default="data/segments/wavs/")
    parser.add_argument("--output_lab_dir", default="data/segments/labs/")
    parser.add_argument("--output_meta",    default="data/processed/ukrainian/metadata_processed.json")
    parser.add_argument("--speaker",        default="ukrainian_speaker")
    parser.add_argument("--max_dur",        type=float, default=30.0)
    args = parser.parse_args()

    process_dataset(
        wav_dir=args.wav_dir,
        lab_dir=args.lab_dir,
        output_wav_dir=args.output_wav_dir,
        output_lab_dir=args.output_lab_dir,
        output_meta=args.output_meta,
        speaker=args.speaker,
        max_dur=args.max_dur,
    )