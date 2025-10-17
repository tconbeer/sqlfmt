FROM python:3-slim

COPY dist/*.whl .
RUN pip install $(find . -name "*.whl")[jinjafmt]
RUN rm *.whl

RUN mkdir /src
WORKDIR /src

CMD ["sqlfmt", "."]
