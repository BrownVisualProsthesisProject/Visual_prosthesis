# Visual prosthesis

This is the new repository of the Intelligent Visual Prosthesis project at Brown University.
The repository is intended to develop the next release of the Visual Prosthesis and will focus on three
modules: Object Localization, Object Grasping, and Optical Character Recognition.

    
<details close>
<summary>Install</summary>

Clone repo and install [requirements_jetson.txt](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/requirements_jetson.txt) in a
[**Python>=3.7.0**](https://www.python.org/) environment ([venv](https://virtualenv.pypa.io/en/latest/) [poetry](https://python-poetry.org/)).

```bash
pip install -r requirements_jetson.txt  # install
```

</details>

<details close>
<summary>Getting Started</summary>

To run the program use

```bash

python main_subclass.py

```


The program will start the keyboard listener to change between modes using the keys '1', '2', '3', '4', and '5' from the keyboard,


```python
currentKey = start_key_listener(currentKey)
```

ZMQ sender to publish the camera frames,

```python
# Accept connections on all tcp addresses, port 5557
sender = imagezmq.ImageSender(connect_to='tcp://127.0.0.1:5557', REQ_REP=False)
host_name = socket.gethostname() 
```

the text to voice engine to send sound,

```python
engine = text2voice()
```

and the webcam stream. 

```python
webcam = cv2.VideoCapture(0)
```

The current code works with the [subprocess](https://docs.python.org/3/library/subprocess.html) standard library to run the `if __name__ == "__main__":`  boilerplate of each module.

```python
def choose_mode(currentKey, audios):
    """Initialize or switch desired mode as a subprocess."""
    if currentKey == "1":
        current_stream = subprocess.Popen(['python3', 'Modes/grasping.py'])
        audio_stream = subprocess.Popen(['python3', 'Modes/hand_sound.py', "--approach", "1"]) #type 1
        play(audios["grasping"])

    elif currentKey == "2":
        current_stream = subprocess.Popen(['python3', 'Modes/easy.py'],
                    bufsize=0)
        audio_stream = None
        play(audios["ocr"])

    elif currentKey == "3" or currentKey == "4" or currentKey == "5" :
        current_stream = subprocess.Popen(['python3', 'Modes/locate.py'],
                    bufsize=0)
        if currentKey == "3":
            audio_stream = subprocess.Popen(['python3', 'Modes/3d_locate_sound.py', "--approach", "1"]) #type 1
        elif currentKey == "4":
            audio_stream = subprocess.Popen(['python3', 'Modes/3d_locate_sound.py', "--approach", "2"]) #type 2
        else:
            audio_stream = subprocess.Popen(['python3', 'Modes/3d_locate_sound.py', "--approach", "3"]) #type 3

        play(audios["localization"])
    return current_stream,audio_stream
 ```

</details>

<details close>
    
<summary>Modes</summary>
    
#### Localization
+ The module uses [YoloV5](https://github.com/ultralytics/yolov5) to detect a specific set of everyday use objects TBD. Currently, it detects the classes from [COCO dataset](https://cocodataset.org/#home)
+ The main process starts concurrently a subprocess that will play the audio of the objects. It currently works with the "person" class.

![](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/Documentation/localization.gif)
    
#### Grasping
+ The module uses YoloV5 for the detection.
+ The module uses [MediaPipe](https://google.github.io/mediapipe/solutions/hands.html) for hand keypoint detection.
+ The module has to use the Text2Voice module to guide the hand of the patient to touch and grasp the desired object of the specific set of everyday use objects. Currently, the hand is guided with sound queues (up, down, left, right) to a random location marked as a red dot on the screen.

![](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/Documentation/grasping.gif)

    
#### OCR
+ The module must use an OCR library such as pytesseract, EasyOCR, or PaddleOCR.
+ Overall, the module must help the patient to read text (which text? TBD).
+ For instance, if the handwritten text on a piece of paper is the desired text to be read. Then, the module has to detect the piece of paper, cut that part of the image, preprocess the cropped to improve the OCR results and run the OCR library over that preprocessed cropped image.

![alt text](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/Documentation/ocr1.png)
![alt text](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/Documentation/ocr2.png

</details>


### Comments

[x] The main goal at this phase is to develop a reliable Manager that can switch (start and kill) between Processes (modes) while developing each module in parallel (pytesseract, Yolov5, localization...).

[ ] The current objective is to have an object detector for a small subset of everyday items (cellphones and keys) while enhancing each module and managing technical debt (improving code quality and speed, refactoring, and documentation) in parallel.
