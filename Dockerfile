FROM python:3.11

LABEL maintainer="Braden Baird <bradenbdev@gmail.com>"

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

COPY main.py ./
ADD src/dubarr ./src/dubarr

CMD python3 main.py