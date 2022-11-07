"""OCR module with Tesseract."""

# Third party modules
import cv2
import imagezmq
import pytesseract


if __name__ == "__main__":
    # Pytesseract configuration.
    custom_config = r"--oem 3 --psm 6"
    # Initialize frame receiver.
    imagehub = imagezmq.ImageHub(open_port='tcp://127.0.0.1:5557', REQ_REP=False)

    while True:
        # Grab new frame.
        rpi_name, frame = imagehub.recv_image()
        # Run OCR engine over frame.
        res = pytesseract.image_to_string(frame, config=custom_config)
        # Print result.
        print(res)

