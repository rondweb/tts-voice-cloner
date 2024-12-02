from fastapi import FastAPI, Form, UploadFile, File
from datetime import datetime
from fastapi.responses import FileResponse
from TTS.api import TTS
import os, shutil
import uuid

app = FastAPI()


def clear_path(folder = '/tmp'):
    
    for filename in os.listdir(folder):
        
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

@app.post("/")
async def generate_audio(text: str = Form(...), wav_file: UploadFile = File(...), language: str = Form(...)):
    
    print(datetime.now())
    
    clear_path()
    
    # Salvar o arquivo upload temporariamente
    temp_wav_path = f"/tmp/{wav_file.filename}"
    with open(temp_wav_path, "wb") as temp_wav:
        content = await wav_file.read()
        temp_wav.write(content)

    # Init TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")  # Alterar para "cpu" se "device" não estiver definido
    output_filename = f"{uuid.uuid4()}.wav" 
    output = f"/tmp/{output_filename}"
    
    # Generate audio file
    tts.tts_to_file(text=text, file_path=output, speaker_wav=temp_wav_path, language=language)
    
    # Remover arquivo temporário
    os.remove(temp_wav_path)
        
    return FileResponse(path=output, filename=f"{output}.wav", media_type="audio/wav")
    
