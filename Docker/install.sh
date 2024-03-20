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

RUN python3.8 -m pip install scikit-image==0.17.2
RUN ls
RUN git clone -b new_clock https://github.com/BrownVisualProsthesisProject/Visual_prosthesis
WORKDIR Visual_prosthesis
RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install -r requirements_jetson.txt
RUN python3.8 -m pip uninstall opencv-python-headless opencv-python opencv-contrib-python -y
RUN python3.8 -m pip install opencv-python opencv-contrib-python pygame gtts ultralytics rapidfuzz onnxruntime
RUN python3.8 -m  pip install protobuf==3.20.3 --upgrade
RUN git clone https://github.com/mallorbc/whisper_mic && cd whisper_mic && \
    python3.8 -m pip install -r requirements.txt && cd ..


RUN cp ./Docker/asound.conf /etc

RUN git clone https://github.com/luxonis/depthai
RUN ./depthai/docker_dependencies.sh

RUN python3.8 ./depthai/install_requirements.py
RUN python3.8 -m pip install Jetson.GPIO==2.0.16
RUN cp ./Docker/99-gpio.rules /etc/udev/rules.d/ 


WORKDIR /home

#RUN apt-get update && \
#	apt-get install cmake build-essential libopencv-dev python3-pyaudio -y && \
#	apt remove --purge --auto-remove cmake -y && \
#	apt update && \
#	apt install -y software-properties-common lsb-release && \
#	apt clean all && \
#	wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | gpg --dearmor - | tee /etc/apt/trusted.gpg.d/kitware.gpg >/dev/null && \
#	apt-add-repository "deb https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" && \
#	apt update && \
#	apt install kitware-archive-keyring && \
#	rm /etc/apt/trusted.gpg.d/kitware.gpg && \
#	apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 42D5A192B819C5DA && \
#	apt update && apt install cmake -y


