FROM python:3.12-alpine
WORKDIR /app
COPY app.py /app/app.py
RUN addgroup -S -g 10001 app && adduser -S -D -u 10001 -G app app
USER 10001:10001
EXPOSE 8000
CMD ["python", "-u", "/app/app.py"]
