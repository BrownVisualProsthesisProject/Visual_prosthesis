FROM nvcr.io/nvidia/l4t-base:r32.7.1
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="America/New_York"
RUN ls ./

RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      python3.8 python3.8-dev python3-pip \
      # dev
      libopenmpi-dev libomp-dev libopenblas-dev libblas-dev \
      libeigen3-dev python3-tk libssl-dev zlib1g-dev gcc g++ make nano \
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
      libopenal-dev \
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
RUN python3.8 -m pip install scikit-image==0.17.2
RUN ls -a -h
RUN git clone -b luxonis https://github.com/BrownVisualProsthesisProject/Visual_prosthesis
WORKDIR Visual_prosthesis
RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install -r requirements_jetson.txt
RUN python3.8 -m pip uninstall opencv-python-headless opencv-python opencv-contrib-python -y
RUN python3.8 -m pip install opencv-python opencv-contrib-python
RUN python3.8 -m  pip install protobuf==3.20.3 --upgrade
RUN python3.8 -m pip install pygame gtts ultralytics fuzzywuzzy
RUN git clone https://github.com/mallorbc/whisper_mic && cd whisper_mic && \
    python3.8 -m pip install -r requirements.txt && cd ..


RUN cp ./Docker/asound.conf /etc

RUN apt-get update && apt-get install -y wget build-essential cmake pkg-config libjpeg-dev libtiff5-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran git

ADD docker_dependencies.sh .
RUN ./docker_dependencies.sh

ADD ./depthai ./depthai

RUN ls
RUN python3.8 ./depthai/install_requirements.py

RUN apt-get update && \
	apt-get install cmake build-essential libopencv-dev python3-pyaudio -y && \
	apt remove --purge --auto-remove cmake -y && \
	apt update && \
	apt install -y software-properties-common lsb-release && \
	apt clean all && \
	wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | gpg --dearmor - | tee /etc/apt/trusted.gpg.d/kitware.gpg >/dev/null && \
	apt-add-repository "deb https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" && \
	apt update && \
	apt install kitware-archive-keyring && \
	rm /etc/apt/trusted.gpg.d/kitware.gpg && \
	apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 42D5A192B819C5DA && \
	apt update && apt install cmake -y

RUN apt-get install libopenblas-base libopenmpi-dev 

RUN git clone --recursive -b v0.11.0 https://github.com/pytorch/audio torchaudio && \
    cd torchaudio && \
    sed -i 's#  URL https://zlib.net/zlib-1.2.11.tar.gz#  URL https://zlib.net/fossils/zlib-1.2.11.tar.gz#g' third_party/zlib/CMakeLists.txt || echo "failed to patch torchaudio/third_party/zlib/CMakeLists.txt" && \
    python3.8 setup.py install && \
    cd ../ && \
    rm -rf torchaudio
