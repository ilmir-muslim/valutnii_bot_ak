FROM joyzoursky/python-chromedriver:3.9

WORKDIR /app

COPY ./src /app

# Обновим pip и установим зависимости
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["python", "main.py"]
