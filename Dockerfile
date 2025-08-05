
FROM python:3.13

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./app.py /code/app.py
COPY ./templates/submit.html /code/templates/submit.html
COPY ./assets/altcha.js /code/assets/altcha.js
COPY ./storage/clients.json /code/storage/clients.json

ENV ALTCHA_HMAC_KEY=$ALTCHA_HMAC_KEY
ENV MAIL_USERNAME=$MAIL_USERNAME
ENV MAIL_PASSWORD=$MAIL_PASSWORD
ENV MAIL_FROM=$MAIL_FROM
ENV MAIL_PORT=$MAIL_PORT
ENV MAIL_SERVER=$MAIL_SERVER
ENV MAIL_FROM_NAME=$MAIL_FROM_NAME

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
EXPOSE 3001
VOLUME /code/storage

CMD ["fastapi", "run", "app.py", "--port", "3001"]
