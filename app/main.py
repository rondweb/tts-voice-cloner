import os
import shutil
import urllib.parse
import uuid
from datetime import datetime

import torch
from dotenv import load_dotenv
from fastapi import (Depends, FastAPI, File, Form, HTTPException, UploadFile,
                     status)
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from keycloak import KeycloakOpenID
from TTS.api import TTS

import uvicorn
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request


load_dotenv()

app = FastAPI()

# Initialize KeycloakOpenID client
keycloak_openid = KeycloakOpenID(
    server_url=os.getenv("KEYCLOAK_SERVER_URL"),
    client_id="tts-voice-clone",
    realm_name="microsaas",
    client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET_KEY"),  # Ensure this is correct
)

# OAuth2 scheme
oauth_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{os.getenv('KEYCLOAK_SERVER_URL')}{os.getenv('KEYCLOAK_AUTH_URL')}",
    tokenUrl=f"{os.getenv('KEYCLOAK_SERVER_URL')}{os.getenv('KEYCLOAK_TOKEN_URL')}",
)


def clear_path(folder="/tmp"):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def generate_audio(
    text: str = Form(...),
    wav_file: UploadFile = File(...),
    language: str = Form(...),
):
    os.environ["COQUI_TOS_AGREED"] = "1"
    print(datetime.now())

    clear_path()

    # Save the uploaded file temporarily
    temp_wav_path = f"/tmp/{wav_file.filename}"
    with open(temp_wav_path, "wb") as temp_wav:
        content = await wav_file.read()
        temp_wav.write(content)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Init TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    output_filename = f"{uuid.uuid4()}.wav"
    output = f"/tmp/{output_filename}"

    # Generate audio file
    tts.tts_to_file(
        text=text, file_path=output, speaker_wav=temp_wav_path, language=language
    )

    # Remove temporary file
    os.remove(temp_wav_path)

    return FileResponse(path=output, filename=f"{output}.wav", media_type="audio/wav")


@app.get("/login")
async def login():
    redirect_uri = urllib.parse.quote(os.getenv("REDIRECT_URI"), safe="")
    authorization_url = f"{os.getenv('KEYCLOAK_SERVER_URL')}{os.getenv('OPENID_AUTH')}?client_id={keycloak_openid.client_id}&response_type=code&scope=openid%20profile&redirect_uri={redirect_uri}"
    return RedirectResponse(url=authorization_url)


@app.get("/auth/callback")
async def auth_callback(code: str):
    redirect_uri = os.getenv(
        "REDIRECT_URI"
    )  # Ensure this matches the Keycloak configuration
    try:
        token = keycloak_openid.token(
            grant_type="authorization_code", code=code, redirect_uri=redirect_uri
        )
        return token
    except Exception as e:
        print(f"Error obtaining token: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code or client credentials",
        )


@app.get("/protected")
async def protected_route(token: str = Depends(oauth_scheme)):
    try:
        user_info = keycloak_openid.decode_token(token)
        if "PRODUCT_FREEMIUM" not in user_info.get("realm_access", {}).get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the required role",
            )
        return {
            "message": f"Hello, {user_info['preferred_username']}!",
            "user_info": user_info,
        }
    except Exception as e:
        print(f"Error decoding token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@app.get("/protected2")
async def protected_route2(token: str = Depends(oauth_scheme)):
    try:
        user_info = keycloak_openid.decode_token(token)
        if "PRODUCT_PROFESSIONAL" not in user_info.get("realm_access", {}).get(
            "roles", []
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the required role",
            )
        return {
            "message": f"Hello, {user_info['preferred_username']}!",
            "user_info": user_info,
        }
    except Exception as e:
        print(f"Error decoding token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
