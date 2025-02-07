from dimits import Dimits # type: ignore
from time import sleep
import tqdm # type: ignore


dt = Dimits("en_US-hfc_male-medium")

with open("assets/audio/audio_lines") as file:
    lines = file.readlines()
    
pbar = tqdm.tqdm(lines)
for indx, i in enumerate(pbar):
    pbar.set_description(f"Processong Line {indx + 1}")
    dt.text_2_audio_file(f"{i}..", f"{i}".replace(" ", "_").strip(), "./assets/audio/")
    
    for _ in range(10000000):
        continue