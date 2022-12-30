# python3
#
# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Using TF Lite to detect objects with the Raspberry Pi camera and an Edge TPU."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import io
import re
import time

from .annotation import Annotator

import numpy as np
import picamera

from PIL import Image
from tflite_runtime.interpreter import load_delegate
from tflite_runtime.interpreter import Interpreter


class CVDetect:
    def __init__(self):
        pass

    def load_labels(self, path):
        """Loads the labels file. Supports files with or without index numbers."""
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            labels = {}
            for row_number, content in enumerate(lines):
                pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
                if len(pair) == 2 and pair[0].strip().isdigit():
                    labels[int(pair[0])] = pair[1].strip()
                else:
                    labels[row_number] = pair[0].strip()
        return labels

    def set_input_tensor(self, interpreter, image):
        """Sets the input tensor."""
        tensor_index = interpreter.get_input_details()[0]['index']
        input_tensor = interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def get_output_tensor(self, interpreter, index):
        """Returns the output tensor at the given index."""
        output_details = interpreter.get_output_details()[index]
        tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
        return tensor

    def detect_objects(self, interpreter, image, threshold):
        """Returns a list of detection results, each a dictionary of object info."""
        self.set_input_tensor(interpreter, image)
        interpreter.invoke()

        # get all output details
        boxes = self.get_output_tensor(interpreter, 0)
        class_ids = self.get_output_tensor(interpreter, 1)
        scores = self.get_output_tensor(interpreter, 2)

        # find best detection
        best_detection = None
        max_score = np.float('-inf')
        for box, class_id, score in zip(boxes, class_ids, scores):
            if score >= threshold and score >= max_score:
                best_detection = {
                    'bounding_box': box,
                    'class_id': class_id,
                    'score': score
                }
                max_score = score

        return best_detection

    def annotate_objects(self, annotator, results, labels, camera_width, camera_height):
        """Draws the bounding box and label for each object in the results."""
        for obj in results:
            # convert the bounding box figures from relative coordinates to absolute coordinates based on the original resolution
            ymin, xmin, ymax, xmax = obj['bounding_box']
            xmin = int(xmin * camera_width)
            xmax = int(xmax * camera_width)
            ymin = int(ymin * camera_height)
            ymax = int(ymax * camera_height)

            # overlay the box, label, and score on the camera preview
            annotator.bounding_box([xmin, ymin, xmax, ymax])
            annotator.text([xmin, ymin],
                           '%s\n%.2f' % (labels[obj['class_id']], obj['score']))

    def cv(self, mission_start, time_total, camera_width, camera_height, model_filepath, labels_filepath, threshold, prediction, run):
        """Capture frames with the camera and use the deep learning model to make detection predictions."""

        # setup for computer vision
        labels = self.load_labels(labels_filepath)
        interpreter = Interpreter(model_filepath,
                                  experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        interpreter.allocate_tensors()
        _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']

        # use picamera with customizable camera settings
        with picamera.PiCamera(resolution=(camera_width, camera_height), framerate=30) as camera:
            # view object detection's camera view if practice run
            if run == 'practice':
                camera.start_preview()
                annotator = Annotator(camera)

            # stream to store frames from camera capture
            stream = io.BytesIO()

            # capture frames with the camera
            # run until mission duration complete
            for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
                # check if mission duration complete
                if time.perf_counter() - mission_start > time_total:
                    break

                # get new frame from camera
                stream.seek(0)
                image = Image.open(stream).convert('RGB').resize((input_width, input_height), Image.ANTIALIAS)

                # track prediction time if practice run
                if run == 'practice':
                    start_time = time.monotonic()

                # get best prediction for recent frame
                best_detection = self.detect_objects(interpreter, image, threshold)

                # check if an object is detected and get coordinates for prediction
                if best_detection is not None:
                    ymin, xmin, ymax, xmax = best_detection['bounding_box']
                    xmin = int(xmin * camera_width)
                    ymin = int(ymin * camera_height)
                    width = int(xmax * camera_width) - xmin
                    height = int(ymax * camera_height) - ymin
                else:
                    xmin = None
                    ymin = None
                    width = None
                    height = None

                # update prediction based on recent detections
                prediction['prediction'] = {
                    "xmin": xmin,
                    "ymin": ymin,
                    "width": width,
                    "height": height,
                    "index": prediction['prediction']["index"] + 1
                }

                # annotate detected objects if practice run
                if run == 'practice':
                    # track prediction time
                    elapsed_ms = (time.monotonic() - start_time) * 1000

                    # clear previous annotations and replace with new ones if any objects detected
                    annotator.clear()
                    if best_detection is not None:
                        self.annotate_objects(annotator, [best_detection], labels, camera_width, camera_height)

                    # update annotations
                    annotator.text([5, 0], '%.1fms' % elapsed_ms)
                    annotator.update()

                # clear previous frames captured by camera
                stream.seek(0)
                stream.truncate()

            # stop object detection's camera view if practice run
            if run == 'practice':
                camera.stop_preview()
