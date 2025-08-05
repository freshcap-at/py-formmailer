
FROM python:3.13

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./app.py /code/app.py
COPY ./templates/submit.html /code/templates/submit.html
COPY ./assets/altcha.js /code/assets/altcha.js
COPY ./storage/clients.json /code/storage/clients.json

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
EXPOSE 3001
VOLUME ["/code/storage"]

CMD ["fastapi", "run", "app.py", "--port", "3001"]