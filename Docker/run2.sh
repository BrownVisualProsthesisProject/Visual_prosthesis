sudo docker run \
-it \
--network host \
--runtime nvidia \
--privileged \
--device=/dev/snd \
-v /dev/snd:/dev/snd:ro \
--device=/dev/bus/usb \
-v /dev/bus/usb:/dev/bus/usb:ro \
-e DISPLAY=:0 \
--device=/dev/video0 \
-v /lib/udev:/lib/udev:ro \
-v /lib/modules:/lib/modules:ro \
-v /etc/asound.conf:/etc/asound.conf:ro \
-v /home/paradisolab/Visual_prosthesis:/home \
vlab
