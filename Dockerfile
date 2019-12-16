FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
COPY ./db.sqlite3 .
COPY ./iris_example.ipynb /code/
COPY ./pyspark_local_example.ipynb /code/
EXPOSE 5000
CMD python /code/manage.py runserver 0.0.0.0:5000
