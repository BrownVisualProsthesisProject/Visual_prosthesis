"""OCR module with Tesseract."""

# Third party modules
import cv2
from PIL import Image
import tesserocr

from transform import four_point_transform
import cv2
import numpy as np
import imutils
import argparse
from skimage.filters import threshold_local
import math

# Local modules
from Video_stream_sub import VideoStreamSubscriber

import numpy as np

def thresholding(img):
    dilated_img = cv2.dilate(img, np.ones((5,5), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - cv2.absdiff(img, bg_img)
    norm_img = diff_img.copy()  # Needed for 3.x compatibility
    cv2.normalize(diff_img, norm_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    _, thr_img = cv2.threshold(norm_img, 230, 0, cv2.THRESH_TRUNC)
    cv2.normalize(thr_img, thr_img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    return thr_img

def angle(x1,y1,x2,y2,x3,y3):
    if x2==x1:
        if x3==x2:
            ang=0
        else:
            m2 = (y3 - y2) / (x3 - x2)
            if m2==0:
                ang = 1.57
            else:
                ang = math.atan(1/m2)
    elif x2 == x3:
        if x1==x2:
            ang=0
        else:
            m1 = (y2 - y1) / (x2 - x1)
            if m1==0:
                ang = 1.57
            else:
                ang = math.atan(-1/m1)
    else:
        m1 = (y2-y1)/(x2-x1)
        m2 = (y3-y2)/(x3-x2)
        # print(m1,m2)
        if (m1*m2) != -1:
            m = (m1-m2)/(1+(m1*m2))
            ang = math.atan(m)
        else:
            ang = 1.57
    if ang<0:
        ang = ang+3.14

    return ang

def document_scanner(original_image,heights):
    global original
    original = original_image.copy()
    for height in heights:

        ratio = original_image.shape[0] /height
        original_image = imutils.resize(original_image, height=height)
        gray = cv2.cvtColor(original_image , cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray,(5,5),0)
        # gray = cv2.adaptiveThreshold(gray , 255 , cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,10,0)
        # _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        gray = thresholding(original_image)
        cv2.imshow('Gray2',gray)

        print('Height',height)
        threshold = [0,50,100]
        for i in threshold:
            edged = cv2.Canny(original_image,i,i+50)
            print('{}  {}'.format(i,i+50))
        # print(gray.shape)
        # print(img.shape)
        #     print(edged.shape)

        # cv2.imshow('Gray' , gray)
            cv2.imshow('Edged' , edged)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

            cnts = cv2.findContours(edged.copy() , cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
            check =False

            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)

                if len(approx) == 4:
                    screenCnt = approx
                    check = True
                    break
            if check:
                a1 = angle(screenCnt[0][0][0],screenCnt[0][0][1],screenCnt[1][0][0],screenCnt[1][0][1],screenCnt[2][0][0],screenCnt[2][0][1])
                a2 = angle(screenCnt[1][0][0],screenCnt[1][0][1],screenCnt[2][0][0],screenCnt[2][0][1],screenCnt[3][0][0],screenCnt[3][0][1])
                a3 = angle(screenCnt[2][0][0],screenCnt[2][0][1],screenCnt[3][0][0],screenCnt[3][0][1],screenCnt[0][0][0],screenCnt[0][0][1])
                a4 = angle(screenCnt[3][0][0],screenCnt[3][0][1],screenCnt[0][0][0],screenCnt[0][0][1],screenCnt[1][0][0],screenCnt[1][0][1])
                print('{},{},{},{}'.format(a1,a2,a3,a4))

                if a1<1.918 and a1>1.222 and a2<1.918 and a2>1.222 and a3<1.918 and a3>1.222 and a4<1.918 and a4>1.222:
                        print("STEP 2: Find contours of paper")
                        cv2.drawContours(original_image, [screenCnt], -1, (0, 255, 0), 2)
                        cv2.imshow("Outline", original_image)
                        
            else:
                continue

    if a1<1.918 and a1>1.222 and a2<1.918 and a2>1.222 and a3<1.918 and a3>1.222 and a4<1.918 and a4>1.222:

        warped = four_point_transform(original, screenCnt.reshape(4, 2) *ratio)
        warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            # _,warped = cv2.threshold(warped , 0 , 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        cv2.imshow('YOY',warped)
        T = threshold_local(warped, 11, offset=10, method="gaussian")
        warped = (warped > T).astype("uint8") * 255
    else:
        warped = original
        warped = cv2.cvtColor(warped , cv2.COLOR_BGR2GRAY)
        T = threshold_local(warped ,15,offset=4,method='gaussian')
        warped = (warped>T).astype('uint8')*255
    return warped

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
        if frame.shape[1]>3000:
            warped = document_scanner(frame,[1500,1300])
        elif frame.shape[1]<=3000:
            warped = document_scanner(frame,[500,700,1200])
        cv2.imshow("processed frame", warped)
        frame = Image.fromarray(frame)
        
        if cv2.waitKey(1) == ord("q"):
            text = tesserocr.image_to_text(frame)
            
            print("Detection: " + text)




