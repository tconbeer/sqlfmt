FROM python:3-slim

COPY dist/*.whl .
RUN pip install $(find . -name "*.whl")
RUN mkdir format

CMD sqlfmt ./format