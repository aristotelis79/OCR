# syntax=docker/dockerfile:1

FROM python:3
 
RUN apt-get update && apt-get install -y \
libgl1 libgl1-mesa-glx ffmpeg libsm6 libxext6 libsm6 libfontconfig1 libxrender1 python3-opencv \
libtesseract-dev libleptonica-dev pkg-config tesseract-ocr tesseract-ocr-grc tesseract-ocr-ell \
&& \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

ARG BARD1PSID
ENV BARD1PSID=$BARD1PSID
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 5678
EXPOSE 8000

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt --no-cache-dir

COPY . /app

ENTRYPOINT ["python3"]

CMD ["manage.py", "runserver", "0.0.0.0:8000"]