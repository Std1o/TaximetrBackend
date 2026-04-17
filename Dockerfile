FROM python:3.9

WORKDIR /code

RUN mkdir -p /code/taximetr/images

COPY ./requirements.txt /code/

RUN pip install -r requirements.txt

COPY ./taximetr /code/taximetr

# Добавляем src в PYTHONPATH
ENV PYTHONPATH=/code/taximetr

# Запускаем как модуль
CMD ["python", "-m", "taximetr"]
