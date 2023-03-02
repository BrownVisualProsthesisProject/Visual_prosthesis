"""OCR mode with EasyOCR."""

# Third party modules
import cv2
import easyocr
import numpy as np

# Local modules
from Video_stream_sub import VideoStreamSubscriber

BINARY_THREHOLD = 180

def sharpen(gray_frame):

    blur = cv2.GaussianBlur(gray_frame, (0,0), 3)
    unsharp_mask = cv2.addWeighted(gray_frame, 1.5, blur, -0.5, 0)
    
    return unsharp_mask

def sharpen2(gray_frame):
    blur = cv2.medianBlur(gray_frame, 3)
    # Apply an unsharp mask to sharpen the image
    unsharp_masked = cv2.addWeighted(gray_frame, 1.5, blur, -0.5, 0)
    return unsharp_masked

def binarize(frame):
    
    binary_frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)
    binary_frame = cv2.bitwise_not(binary_frame)
    bilateral_filtered = cv2.bilateralFilter(binary_frame, 9, 75, 75)
    return binary_frame


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
    reader = easyocr.Reader(["ch_tra", "en"])

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
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        unsharp_mask = sharpen(gray_frame)
        binary_frame = binarize(unsharp_mask)

        # show the output image
        cv2.imshow("Text Detection", binary_frame)
        # frame = Image.fromarray(frame)

        if cv2.waitKey(1) == ord("q"):
            result = reader.readtext(gray_frame, paragraph=True)

            print("Detection:")
            print(result)
