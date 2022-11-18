MOUNTS="\
--device /dev/snd \
--device /dev/bus/usb \
--volume /etc/timezone:/etc/timezone:ro \
--volume /etc/localtime:/etc/localtime:ro"
sudo xhost +si:localuser:root
sudo docker run --runtime nvidia -it --rm \
	--network host \
	$MOUNTS \
	vlab
	
