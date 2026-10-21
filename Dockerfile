FROM python:3.12-slim

WORKDIR /app

COPY login_mod1.py .

EXPOSE 8000

CMD ["python", "-u", "login_mod1.py"]
