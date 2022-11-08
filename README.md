# Visual prosthesis

This is the new repository of the Intelligent Visual Prosthesis project at Brown University.
The repository is intended to develop the next release of the Visual Prosthesis and will focus on three
modules: Object Localization, Object Grasping, and Optical Character Recognition.

    
<details close>
<summary>Install</summary>

Clone repo and install [requirements.txt](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/requirements.txt) in a
[**Python>=3.7.0**](https://www.python.org/) environment ([venv](https://virtualenv.pypa.io/en/latest/) [poetry](https://python-poetry.org/)).

```bash
pip install -r requirements.txt  # install
```

</details>

<details close>
<summary>Getting Started</summary>

To run the program use

```bash

python main_subclass.py

```


The program will start the keyboard listener to change between modes using the keys '1', '2', and '3' from the keyboard,


```python
def start_key_listener(currentKey):
    """Keyboard listener."""

    def on_press(key):
        """Stores selected key."""
        try:
            global currentKey
            currentKey = key.char
            print("alphanumeric key {0} pressed".format(key.char))
        except AttributeError:
            print("special key {0} pressed".format(key))

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return currentKey
```

ZMQ sender to publish the camera frames,

```python
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
        # Initialize/switch process.
        if currentKey == "1":
            current_stream = subprocess.Popen(['python', 'Modes/grasping.py'])
            engine.say("Grasping mode")

        elif currentKey == "2":
            current_stream = subprocess.Popen(['python', 'Modes/ocr.py'],
                    bufsize=0)
            engine.say("Document OCR mode")

        elif currentKey == "3":
            current_stream = subprocess.Popen(['python', 'Modes/locate.py'],
                    bufsize=0)
            engine.say("Object location mode")
```

</details>

<details close>
<summary>Modes</summary>
    
#### Localization
+ The module has to use YoloV5 to detect a specific set of everyday use objects TBD. To test the module, it is possible to
run YoloV5 with pre-trained weights. 
+ The module has to use the Text2Voice module to name the objects in the scene (going from left to right.)
    
#### Grasping
+ The module has to use YoloV5 to detect a specific set of everyday use objects TBD and the hands of the patient. 
+ The module has to use the Text2Voice module to guide the hand of the patient to touch and grasp the desired object of the specific set of everyday use objects.
    
#### OCR
+ The module must use an OCR library such as pytesseract of PaddleOCR (pytessearct is already working.)
+ Overall, the module must help the patient to read text (which text? TBD).
+ For instance, if the handwritten text on a piece of paper is the desired text to be read. Then, the module has to detect the piece of paper, cut that part of the image, preprocess the cropped to improve the OCR results, and run the OCR library over that preprocessed cropped image.



The main goal at this phase is to develop a reliable Manager that can switch (start and kill) between Processes (modes.), while developing each module in parallel (pytesseract, Yolov5, localization...).     


</details>


