FROM python:3.11-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*
COPY app ./app
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh