
pip install --upgrade setuptools
sudo apt-get install portaudio19-dev
apt install curl
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

primero rust
despues tranformers
depsues env con sys pack

git clone https://github.com/mallorbc/whisper_mic && cd whisper_mic
pip install -r requirements.txt
pip install scikit-image==0.17.2
pynput == 1.7.6
pygame == 2.5.1
pyzmq == 25.1.1
rapidfuzz-3.2.0
onnxruntime-1.15.1
numpy 1.23.5
#yolo
psutil
ultralytics


sudo wget -qO- https://docs.luxonis.com/install_dependencies.sh | bash
git clone https://github.com/luxonis/depthai
python3.8 ./depthai/install_requirements.py