import multiprocessing
import os
import time

from data import data_rw
from cv import cv_detect
from controls import controls_system


class MissionController:
    def __init__(self, time_total=20, data_dirpath=os.path.abspath('./data/output/IMU/'),
                 model_filepath=os.path.abspath('./cv/efficientdet-lite2-rocket-quant_edgetpu.tflite'),
                 labels_filepath=os.path.abspath('./cv/rocket-labels.txt'), camera_width=448, camera_height=448,
                 threshold=0.25):
        # variables related to computer vision
        self.time_total = time_total
        self.data_dirpath = data_dirpath
        self.model_filepath = model_filepath
        self.labels_filepath = labels_filepath
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.threshold = threshold

        # objects that run flight data capture, computer vision, and controls
        self.data = data_rw.DataRW()
        self.detect = cv_detect.CVDetect()
        self.controls = controls_system.ControlsSystem()

        # run multiple processes and share memory across them
        self.process_manager = multiprocessing.Manager()

    def execute_collecting_data(self, mission_start, run):
        """Data capture."""
        self.data.rw(mission_start, self.time_total, self.data_dirpath, run)

    def execute_object_detection(self, mission_start, prediction, run):
        """Computer vision."""
        self.detect.cv(mission_start, self.time_total, self.camera_width, self.camera_height, self.model_filepath,
                       self.labels_filepath, self.threshold, prediction, run)

    def execute_controls_systems(self, mission_start, prediction, run):
        """Controls."""
        self.controls.controls(mission_start, self.time_total, prediction, run)

    def execute_mission(self, run):
        """BX-4 Mission."""

        # keep track of best prediction throughout multiple processes
        prediction = self.process_manager.dict({
            'prediction': {
                "xmin": None,
                "ymin": None,
                "width": None,
                "height": None,
                "index": -1
            }
        })

        # synchronize mission time across multiple processes
        mission_start = time.perf_counter()

        # prepare computer vision, controls, and data capture for multiprocessing
        cv_process = multiprocessing.Process(target=self.execute_object_detection, args=(mission_start, prediction, run,))
        controls_process = multiprocessing.Process(target=self.execute_controls_systems, args=(mission_start, prediction, run,))
        data_process = multiprocessing.Process(target=self.execute_collecting_data, args=(mission_start, run,))

        # start computer vision, controls, and data capture processes
        cv_process.start()
        controls_process.start()
        data_process.start()

        # join computer vision, controls, and data capture processes after completion
        cv_process.join()
        controls_process.join()
        data_process.join()
