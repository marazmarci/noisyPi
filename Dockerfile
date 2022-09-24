FROM python:latest
RUN apt-get update -y && \
    apt-get install -y sox alsa-utils
WORKDIR /usr/app/src
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY noisyPi.py config.py ./
CMD ["python3", "noisyPi.py"]
# docker image build -t marazmarci/noisypi .
# docker run --device="/dev/snd:/dev/snd" --name=noisypi --restart=unless-stopped marazmarci/noisypi