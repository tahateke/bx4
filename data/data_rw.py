import os
import time
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
from datetime import datetime

from .constants import *
from .lsm6ds33 import LSM6DS33  # Accel & Gyro (+ temp)
from .lis3mdl import LIS3MDL  # Magnetometer (+ temp)
from .lps25h import LPS25H  # Barometric Pressure & Temperature


class DataRW:
    def __init__(self):
        GPIO.setwarnings(False)  # Ignore warning for now
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering

        self.imu = LSM6DS33()  # Accelerometer and Gyroscope
        self.imu.enable()

        self.magnetometer = LIS3MDL()  # Magnetometer
        self.magnetometer.enable()

        self.barometer_thermometer = LPS25H()  # Barometric and Temperature
        self.barometer_thermometer.enable()

    def rw(self, mission_start, time_total, data_dirpath, run):
        """Capture flight data with the IMU and write it to a file"""

        # setup for data capture
        date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file = open(os.path.join(data_dirpath, date + '.csv'), 'w')
        header = 'Time,X-Gyro,Y-Gyro,Z-Gyro,X-Accel,Y-Accel,Z-Accel,X-Mag,Y-Mag,Z-Mag,Pressure,Altitude,Temperature\n'
        file.write(header)

        # print header to terminal if practice run
        if run == 'practice':
            print(header[:-1])

        # run until mission duration complete
        while True:
            # check if mission duration complete
            if time.perf_counter() - mission_start > time_total:
                break

            # make new strings to edit
            gyroscope_data = str(self.imu.getGyroscopeDPS())
            accelerometer_data = str(self.imu.getAccelerometerMPS2())
            magnetometer_data = str(self.magnetometer.getMagnetometerRaw())

            # chop brackets off the end of strings
            gyroscope_data = gyroscope_data[1:len(gyroscope_data) - 1]
            accelerometer_data = accelerometer_data[1:len(accelerometer_data) - 1]
            magnetometer_data = magnetometer_data[1:len(magnetometer_data) - 1]

            # get rid of whitespace
            gyroscope_data = gyroscope_data.replace(' ', '')
            accelerometer_data = accelerometer_data.replace(' ', '')
            magnetometer_data = magnetometer_data.replace(' ', '')
            pressure_data = str(self.barometer_thermometer.getBarometerMillibars())
            altitude_data = str(self.barometer_thermometer.getAltitude())
            temperature_data = str(self.barometer_thermometer.getTemperatureCelsius())

            # write imu data to file
            now = str(datetime.now())
            imu_data = ','.join([now, gyroscope_data, accelerometer_data, magnetometer_data, pressure_data,
                                 altitude_data, temperature_data + '\n'])
            file.write(imu_data)

            # print imu data to terminal if practice run
            if run == 'practice':
                print(imu_data[:-1])
