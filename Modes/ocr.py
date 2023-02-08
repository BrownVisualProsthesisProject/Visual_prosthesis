"""OCR module with Tesseract."""

# Third party modules
import cv2
import numpy as np
import tesserocr
from PIL import Image

# Local modules
from Video_stream_sub import VideoStreamSubscriber

BINARY_THREHOLD = 180


def image_smoothening(img):
    """Blur image for smoothing."""
    ret1, th1 = cv2.threshold(img, BINARY_THREHOLD, 255, cv2.THRESH_BINARY)
    ret2, th2 = cv2.threshold(th1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3


def remove_noise_and_smooth(img):
    """Remove noise from image."""
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    filtered = cv2.adaptiveThreshold(
        img.astype(np.uint8), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 41, 3
    )
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    ocr_image = image_smoothening(img)
    ocr_image = cv2.bitwise_or(img, closing)
    return ocr_image


def SetCVImage(self, image, color="BGR"):
    """Sets an OpenCV-style image for recognition.

    'image' is a numpy ndarray in color, grayscale, or binary (boolean)
        format.
    'color' is a string representing the current color of the image,
        for conversion using OpenCV into an RGB array image. By default
        color images in OpenCV use BGR, but any valid channel
        specification can be used (e.g. 'BGRA', 'XYZ', 'YCrCb', 'HSV', 'HLS',
        'Lab', 'Luv', 'BayerBG', 'BayerGB', 'BayerRG', 'BayerGR').
        Conversion only occurs if the third dimension of the array is
        not 1, else 'color' is ignored.

    """
    bytes_per_pixel = image.shape[2] if len(image.shape) == 3 else 1
    height, width = image.shape[:2]
    bytes_per_line = bytes_per_pixel * width

    if bytes_per_pixel != 1 and color != "RGB":
        # non-RGB color image -> convert to RGB
        image = cv2.cvtColor(image, getattr(cv2, f"COLOR_{color}2RGB"))
    elif bytes_per_pixel == 1 and image.dtype == bool:
        # binary image -> convert to bitstream
        image = np.packbits(image, axis=1)
        bytes_per_line = image.shape[1]
        width = bytes_per_line * 8
        bytes_per_pixel = 0
    # else image already RGB or grayscale

    self.SetImageBytes(image.tobytes(), width, height, bytes_per_pixel, bytes_per_line)


if __name__ == "__main__":
    # Pytesseract configuration.
    custom_config = r"--oem 3 --psm 6"

    hostname = "127.0.0.1"  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5557
    config = "-l eng --oem 1 --psm 6"
    # Initialize frame receiver.
    imagehub = VideoStreamSubscriber(hostname, port)

    while True:
        # Grab new frame.
        host_name, frame = imagehub.recv_image()
        frame = cv2.imdecode(np.frombuffer(frame, dtype="uint8"), -1)
        frame = remove_noise_and_smooth(frame)

        cv2.imshow("processed frame", frame)
        frame = Image.fromarray(frame)

        if cv2.waitKey(1) == ord("q"):
            text = tesserocr.image_to_text(frame)

            print("Detection: " + text)
