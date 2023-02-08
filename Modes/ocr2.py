"""OCR module with Tesseract."""

# Third party modules
import cv2
from PIL import Image
import tesserocr
import numpy as np
import cv2
from imutils.object_detection import non_max_suppression

# Local modules
from Video_stream_sub import VideoStreamSubscriber

import numpy as np

BINARY_THREHOLD = 180
def image_smoothening(img):
    ret1, th1 = cv2.threshold(img, BINARY_THREHOLD, 255, cv2.THRESH_BINARY)
    ret2, th2 = cv2.threshold(th1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3

def remove_noise_and_smooth(img):
    #img = cv2.imread(file_name, 0)
	img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	filtered = cv2.adaptiveThreshold(img.astype(np.uint8), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 41, 3)
	kernel = np.ones((1, 1), np.uint8)
	opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
	closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
	ocr_image = image_smoothening(img)
	ocr_image = cv2.bitwise_or(img, closing)
	return ocr_image

def skew_correction(img):

    # Skew correction
    coords = np.column_stack(np.where(img > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def SetCVImage(self, image, color='BGR'):
    """ Sets an OpenCV-style image for recognition.

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
    height, width   = image.shape[:2]
    bytes_per_line  = bytes_per_pixel * width

    if bytes_per_pixel != 1 and color != 'RGB':
        # non-RGB color image -> convert to RGB
        image = cv2.cvtColor(image, getattr(cv2, f'COLOR_{color}2RGB'))
    elif bytes_per_pixel == 1 and image.dtype == bool:
        # binary image -> convert to bitstream
        image = np.packbits(image, axis=1)
        bytes_per_line  = image.shape[1]
        width = bytes_per_line * 8
        bytes_per_pixel = 0
    # else image already RGB or grayscale

    self.SetImageBytes(image.tobytes(), width, height,
                        bytes_per_pixel, bytes_per_line)

if __name__ == "__main__":
    # Pytesseract configuration.
    custom_config = r"--oem 3 --psm 6"

    east = cv2.dnn.readNet("./Modes/frozen_east_text_detection.pb")

    hostname = "127.0.0.1"  # Use to receive from localhost
    # hostname = "192.168.86.38"  # Use to receive from other computer
    port = 5557
    config = ("-l eng --oem 1 --psm 6")
    # Initialize frame receiver.
    imagehub = VideoStreamSubscriber(hostname, port)

    while True:
        # Grab new frame.
        host_name, frame = imagehub.recv_image()
        frame = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)
        #frame = remove_noise_and_smooth(frame)
        frame = cv2.resize(frame, (640, 640))
        blob = cv2.dnn.blobFromImage(frame, 1.0, (640, 640),
            (123.68, 116.78, 103.94), swapRB=True, crop=False)

        east.setInput(blob)
        (scores, geometry) = east.forward(["feature_fusion/Conv_7/Sigmoid","feature_fusion/concat_3"])

        (numRows, numCols) = scores.shape[2:4]
        rects = []
        confidences = []

        for y in range(0, numRows):
            scoresData = scores[0, 0, y]
            xData0 = geometry[0, 0, y]
            xData1 = geometry[0, 1, y]
            xData2 = geometry[0, 2, y]
            xData3 = geometry[0, 3, y]
            anglesData = geometry[0, 4, y]

            for x in range(0, numCols):
                if scoresData[x] < 0.5:
                    continue

                (offsetX, offsetY) = (x * 4.0, y * 4.0)

                angle = anglesData[x]
                cos = np.cos(angle)
                sin = np.sin(angle)

                h = xData0[x] + xData2[x]
                w = xData1[x] + xData3[x]

                endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                startX = int(endX - w)
                startY = int(endY - h)

                rects.append((startX, startY, endX, endY))
                confidences.append(scoresData[x])
        
        # Apply non-maxima suppression to the bounding boxes
        boxes = non_max_suppression(np.array(rects), probs=confidences)

        # loop over the bounding boxes
        for (startX, startY, endX, endY) in boxes:
            # draw the bounding box on the image
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

        # show the output image
        cv2.imshow("Text Detection", frame)
        frame = Image.fromarray(frame)
        
        if cv2.waitKey(1) == ord("q"):
            text = tesserocr.image_to_text(frame)
            
            print("Detection: " + text)




