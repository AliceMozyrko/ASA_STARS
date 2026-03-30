import os
import json

audio_folder = "wavs"
labs_folder = "labs"

lab_files = [f for f in os.listdir(labs_folder) if f.endswith(".lab")]
lab_files.sort()  

metadata = []

for lab_file in lab_files:
    lab_path = os.path.join(labs_folder, lab_file)
    with open(lab_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        phonemes = content.split()  

    audio_filename = lab_file.replace(".lab", ".wav")
    audio_path = os.path.join(audio_folder, audio_filename)

    metadata.append({
        "filename": audio_filename,
        "audio_filepath": audio_path,
        "phonemes": phonemes
    })

os.makedirs("json_splits", exist_ok=True)
with open("json_splits/metadata_all.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
