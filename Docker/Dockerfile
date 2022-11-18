FROM nvcr.io/nvidia/l4t-base:r32.7.1

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="America/New_York"

RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      python3.8 python3.8-dev python3-pip \
      libopenmpi-dev libomp-dev libopenblas-dev libblas-dev libeigen3-dev python3-tk libssl-dev zlib1g-dev gcc g++ make\
      # zmq 
      libzmq3-dev \
      # tesseract
      tesseract-ocr \
      libtesseract-dev \
      libleptonica-dev \
################################################################
## install some audio stuff
################################################################
      alsa-base \
            libasound2-dev \
            alsa-utils \
            portaudio19-dev \
		  libsndfile1 \
		  unzip \
		espeak \
		ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install --upgrade setuptools gdown wheel

# pytorch 1.11.0
RUN gdown https://drive.google.com/uc?id=1hs9HM0XJ2LPFghcn7ZMOs5qu5HexPXwM
RUN python3.8 -m pip install torch-*.whl

# torchvision 0.12.0
RUN gdown https://drive.google.com/uc?id=1m0d8ruUY8RvCP9eVjZw4Nc8LAwM8yuGV
RUN python3.8 -m pip install torchvision-*.whl

RUN git clone -b jchang_fasterZQM https://github.com/BrownVisualProsthesisProject/Visual_prosthesis
WORKDIR Visual_prosthesis
#RUN git pull
#RUN python3.8 -m pip install -r requirements_jetson.txt

