FROM python:3.11

LABEL maintainer="Braden Baird <bradenbdev@gmail.com>"

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

COPY main.py example_config.py image_api.py search_page.py drawers.py series_utils.py LICENSE README.md ./

CMD python3 main.py