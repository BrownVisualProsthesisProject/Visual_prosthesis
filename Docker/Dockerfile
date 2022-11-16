FROM nvcr.io/nvidia/l4t-base:r32.7.1

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
      git \
      python3.8 python3.8-dev python3-pip \
      libopenmpi-dev libomp-dev libopenblas-dev libblas-dev libeigen3-dev python3-tk \
      # zmq 
      libzmq3-dev \
      # tesseract
      tesseract-ocr \
      libtesseract-dev \
      libleptonica-dev \
      # text-to-speech
      ffmpeg \
      espeak \
      alsa-utils \
      libalut-dev \
      libaudio-dev \
      libopenal-dev \ 
      libasound2-dev \
      alsa-oss \
      pulseaudio

RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install setuptools gdown

# pytorch 1.11.0
RUN gdown https://drive.google.com/uc?id=1hs9HM0XJ2LPFghcn7ZMOs5qu5HexPXwM
RUN python3.8 -m pip install torch-*.whl

# torchvision 0.12.0
RUN gdown https://drive.google.com/uc?id=1m0d8ruUY8RvCP9eVjZw4Nc8LAwM8yuGV
RUN python3.8 -m pip install torchvision-*.whl

RUN git clone -b jchang_fasterZQM https://github.com/BrownVisualProsthesisProject/Visual_prosthesis
WORKDIR Visual_prosthesis
RUN python3.8 -m pip install -r requirements_jetson.txt
