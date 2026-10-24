import yt_dlp
from pydub import AudioSegment
import os


#download directory
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_youtube_video(url : str) -> str :
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts ={
        "format":"bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
            "key": "FFmpegExtractAudio",
            "preferredcodec" : "wav",
            "preferredquality": "192"
            }
        ],
        "quiet":True, #supress download progess so user cant see backgrond video download

    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename =  ydl.prepare_filename(info).replace(".webm", ".wav").replace(".mp4", ".wav")

    return filename





def convert_to_wav(input_path:str)->str:
    "convert any audio format to wav format using pydub"
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #channel = set to mono audio, frame_rate = set to 16 KHz
    audio.export(output_path, format = "wav")
    return output_path





def chunk_audio(wav_path:str, chunk_minutes: int=10)->list:
    audio= AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks =[]

    for i, start in enumerate ( range(0, len(audio), chunk_ms)):
        chunk =audio[start: start+chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks


def process_input(source:str)->list:
    if source.startswith("https://") or source.startswith("http://"):
        print("detected youtube URL, Downloading Audio")
        wav_path = download_youtube_video(source)
    else:
        print("detected local storage, converting to wav")
        wav_path = convert_to_wav(source)

    print("chunking audio")
    chunks = chunk_audio(wav_path)
    print(f"audio ready - {len(chunks)} chunk(s) created")
    return chunks