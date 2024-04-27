import cv2
import threading
import depthai as dai

class WebcamDisplayThread(threading.Thread):
    def __init__(self, window_name):
        super().__init__()
        self.window_name = window_name
        # Create pipeline
        pipeline = dai.Pipeline()
        # This might improve reducing the latency on some systems
        pipeline.setXLinkChunkSize(0)

        # Define source and output
        camRgb = pipeline.create(dai.node.ColorCamera)
        camRgb.setFps(30)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)

        controlIn = pipeline.create(dai.node.XLinkIn)
        controlIn.setStreamName('control')
        controlIn.out.link(camRgb.inputControl)

        xout = pipeline.create(dai.node.XLinkOut)
        xout.setStreamName("out")
        camRgb.isp.link(xout.input)
        camRgb.setIspScale(1,2)

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            cv2.imshow(self.window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

def main():
    window_name = 'Webcam Feed'

    # Create and start the display thread
    display_thread = WebcamDisplayThread(window_name)
    display_thread.start()

if __name__ == "__main__":
    main()
