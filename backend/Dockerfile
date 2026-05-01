

FROM python:3.11-slim

# working directory inside the container
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

# Run the agent
CMD ["sh", "-c", "python seed_database.py && python main.py"]