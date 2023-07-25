FROM python:3.11-alpine

WORKDIR /due

COPY requirements.lock /due
COPY pyproject.toml /due
COPY src/ /due/src

RUN python -m pip install --no-cache-dir --upgrade pip

RUN sed '/-e/d' requirements.lock > requirements.txt
RUN sed -i 's/requires = \["hatchling"\]/requires = \["setuptools", "setuptools-scm"\]/; s/build-backend = "hatchling.build"/build-backend = "setuptools.build_meta"/' pyproject.toml
RUN sed -i '/\[tool\.hatch\.metadata\]/d; /allow-direct-references = true/d' pyproject.toml

RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

RUN pip install .

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "due", "run", "--host=0.0.0.0"]
