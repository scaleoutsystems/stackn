FROM python:3.8 as pythonbuild1
RUN pip install Flask

RUN mkdir /app
RUN mkdir /app/work

FROM pythonbuild1

COPY . /app
WORKDIR /app



ENTRYPOINT ["python"]
CMD ["serve.py"]
