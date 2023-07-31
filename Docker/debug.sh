MOUNTS="\
--device /dev/snd \
--device /dev/bus/usb \
--device /dev/video0:/dev/video0:mrw \
--volume /etc/timezone:/etc/timezone:ro \
--volume /etc/localtime:/etc/localtime:ro"

sudo systemctl restart docker
sudo xhost +si:localuser:root

sudo docker run \
       -it \
       --rm \
       --privileged \
       --runtime nvidia \
       --network host \
       -e DISPLAY=$DISPLAY \
       -e LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1 \
       -v /tmp/.X11-unix/:/tmp/.X11-unix \
       -v /home/paradisolab/Visual_prosthesis:/home \
       -v /dev:/dev \
       -v /dev/bus/usb:/dev/bus/usb \
       -v /sys:/sys \
       -e JETSON_MODEL_NAME=[JETSON_XAVIER] \
       --group-add $(cut -d: -f3 < <(getent group gpio)) \
       --device-cgroup-rule='c 189:* rmw' \
       $MOUNTS \
       vlab
