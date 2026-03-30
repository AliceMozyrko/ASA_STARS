import os
import json

data_path = "labs" 

phonemes = set()

for root, _, files in os.walk(data_path):
    for file in files:
        if file.endswith(".lab"):
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    
                    if len(parts) == 3:
                        phoneme = parts[2].strip()
                        
                        if phoneme != "":
                            phonemes.add(phoneme)

phoneme_list = sorted(list(phonemes))

phoneme_dict = {p: i for i, p in enumerate(phoneme_list)}

with open("phoneme_set.json", "w", encoding="utf-8") as f:
    json.dump(phoneme_dict, f, ensure_ascii=False, indent=2)

print("Кількість фонем:", len(phoneme_dict))
