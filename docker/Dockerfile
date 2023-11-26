FROM python:3.11.6-slim-bookworm AS runtime

WORKDIR /app

RUN pip install --upgrade pip

# Install poetry
RUN pip install poetry
RUN poetry --version

# Create layer with dependencies installed before copying the rest of the code.
COPY pyproject.toml poetry.lock /app/

# Do not create virtualenv when we are running in container ('poetry install' command will create a virtualenv if not disabled)
RUN poetry config virtualenvs.create false
# Install dependencies.
RUN poetry install --only main

# Copy only the files we need for running the app (remember to add unnessesary files to .dockerignore)
COPY ./main.py .
COPY ./src ./src

ENTRYPOINT poetry run python main.py