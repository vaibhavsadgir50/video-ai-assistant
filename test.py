import os
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.extractor import splits
from dotenv import load_dotenv
load_dotenv()



print("key loaded: ", os.getenv("SARVAM_API_KEY"))
print("CWS", os.getcwd())

source= "https://www.youtube.com/watch?v=_Q-e_nczWqM"
language = "english"
chunks= process_input(source)
transcript=transcribe_all(chunks, language=language)
print("======Transcription=====")
print(transcript[:200]+"....")




print("\n" + "=" * 60)
print(splits(transcript))