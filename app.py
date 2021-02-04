from sys import stdout
from makeup_artist import Makeup_artist
import logging
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
from camera import Camera
from utils import base64_to_pil_image, pil_image_to_base64
import cv2
import numpy as np
import base64
import io
from imageio import imread
import matplotlib.pyplot as plt

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(stdout))
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app)
camera = Camera(Makeup_artist())


@socketio.on('input image', namespace='/test')
def test_message(input):
    input = input.split(",")[1]
    camera.enqueue_input(input)
    image_data = input # Do your magical Image processing here!!
    #image_data = image_data.decode("utf-8")

    img = imread(io.BytesIO(base64.b64decode(image_data)))
    im_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    #Facecascde = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    Facecascde=cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    faces = Facecascde.detectMultiScale(cv2_img, 1.5, 3)
    for (x, y, w, h) in faces:
        #cv2_img = cv2.rectangle(cv2_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        im_rgb = cv2.rectangle(im_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)

    #cv2.imwrite("reconstructed.jpg", cv2_img)
    #retval, buffer = cv2.imencode('.jpg', cv2_img)
    cv2.imwrite("reconstructed.jpg", im_rgb)
    retval, buffer = cv2.imencode('.jpg', im_rgb)

    b = base64.b64encode(buffer)
    b = b.decode()
    image_data = "data:image/jpeg;base64," + b

    print("OUTPUT " + image_data)
    emit('out-image-event', {'image_data': image_data}, namespace='/test')
    #camera.enqueue_input(base64_to_pil_image(input))


@socketio.on('connect', namespace='/test')
def test_connect():
    app.logger.info("client connected")


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen():
    """Video streaming generator function."""

    app.logger.info("starting to generate frames!")
    while True:
        frame = camera.get_frame() #pil_image_to_base64(camera.get_frame())

        print(type(frame))
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    socketio.run(app)
