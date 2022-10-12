# Visual prosthesis

This is the new repository of the Intelligent Visual Prosthesis project at Brown University.
The repository is intended to develop the next release of the Visual Prosthesis and will focus on three
modules: Object Localization, Object Grasping, and Optical Character Recognition.

    
<details open>
<summary>Install</summary>

Clone repo and install [requirements.txt](https://github.com/BrownVisualProsthesisProject/Visual_prosthesis/blob/main/requirements.txt) in a
[**Python>=3.7.0**](https://www.python.org/) environment.

```bash
pip install -r requirements.txt  # install
```

</details>

<details open>
<summary>Getting Started</summary>

To run the program use

```bash

python main_subclass.py

```

</details>

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

the multiprocessing queues for communication (soon to be changed with ZMQ communication),

```python
queue = Queue(1000 * 1000)
processed_queue = Queue(1000 * 1000)
message_queue = mp.Queue()
```

the text to voice engine to send sound,

```python
engine = text2voice()
```

and the webcam stream that will put frames in the queue variable.

```python
webcam_stream = WebcamStream(queue, stream_id=0)
webcam_stream.start()
```

The current code is working with dummy classes that inherit from multiprocessing.Process class to run the modules as a separate process.

```python
        # Initialize chosen process.
        if currentKey == "1":
            current_stream = Grayscale(queue, processed_queue, message_queue)
            engine.say("Grasping mode")

        elif currentKey == "2":
            current_stream = OCR(queue, processed_queue, message_queue)
            engine.say("Document OCR mode")

        elif currentKey == "3":
            current_stream = Detector(queue, processed_queue, message_queue)
            engine.say("Object location mode")
```
