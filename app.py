import uvicorn
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType


from altcha import (
    ChallengeOptions,
    create_challenge,
    verify_solution,
    verify_server_signature,
    verify_fields_hash,
)

load_dotenv()
ALTCHA_HMAC_KEY = os.environ['ALTCHA_HMAC_KEY']
MAIL_CONF = ConnectionConfig(
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_FROM=os.getenv('MAIL_FROM'),
    MAIL_PORT=int(os.getenv('MAIL_PORT')),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_FROM_NAME=os.getenv('MAIN_FROM_NAME'),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='./templates'
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def healthcheck():
    return {"status": "working"}


@app.get("/{code}/mail")
def redirect_mail(code: str):
    client = get_client(code)
    if (client == None):
        raise HTTPException(status_code=404, detail="Not Found")
    return RedirectResponse("mailto:" + client['mail'])


@app.get("/{code}/altcha")
def get_altcha(code: str):
    client = get_client(code)
    if (client == None):
        raise HTTPException(status_code=404, detail="Not Found")
    try:
        challenge = create_challenge(
            ChallengeOptions(
                hmac_key=ALTCHA_HMAC_KEY + code,
                max_number=50000,
            )
        )
        return challenge.__dict__
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create challenge: {str(e)}")


@app.post("/{code}/submit")
async def post_submit(code: str, request: Request):
    client = get_client(code)
    if (client == None):
        raise HTTPException(status_code=404, detail="Not Found")
    form = dict(jsonable_encoder(await request.form()))
    
    payload = form.pop("altcha", None)
    
    if not payload:
        raise HTTPException(status_code=400, detail="Classified as spam")

    try:
        verified, err = verify_solution(payload, ALTCHA_HMAC_KEY + code, True)
        if not verified:
            raise HTTPException(status_code=400, detail="Classified as spam")

        form.pop('_agreed', None)
        returnurl = form.pop('_returnurl', client['form']['return_url'])
        subject = form.pop('_subject', client['form']['subject'])
        reply = form.pop('_reply', None)

        if reply:
            reply = [form.get(reply)]

        params = dict()
        params['subject'] = subject
        params['name'] = client['name']
        params['values'] = form

        message = MessageSchema(
            subject=subject,
            recipients=client['form']['receivers'],
            template_body=params,
            subtype=MessageType.html,
            reply_to=reply
        )

        fm = FastMail(MAIL_CONF)
        await fm.send_message(message, template_name='submit.html')
        return RedirectResponse(returnurl)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Classified as spam")


def get_client(code: str):
    with open('storage/clients.json', encoding="utf-8") as json_file:
        clients = json.load(json_file)
        return next(iter(list(filter(lambda c: c['client'] == code, clients))), None)
        
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)