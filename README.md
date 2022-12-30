# README

## Overview

The BX-4 software runs computer vision, flight data capture, and controls system. Each task has its own package.

Additionally, there is mission controller that is a centralized controller for the execution of the various
mission tasks. It uses multiprocessing to run each task in parallel and to share data between tasks. To read more
about the mission controller, check [here](./controller/README.md).

The computer vision uses TensorFlow Lite with Python3 on a Raspberry Pi to perform real-time object detection
using images streamed from the Pi Camera using a Google Coral USB Accelerator. It shares bounding box coordinates
of the best rocket prediction with the controls system. To read more about the computer vision, check [here](./cv/README.md).

The flight data capture reads related flight data with the Pololu AltIMU-10 v5 and writes it to a file. To read
more about the flight data capture, check [here](./data/README.md).

The controls system software hasn't been built yet because the hardware and algorithms have not been
finalized at the moment. However, the controls system should take rocket prediction coordinates from
the computer vision and use that information to pivot the payload such that BX-4 is pointing directly
at the rocket, with the rocket at the center of the camera's view. To read more about the controls system,
check [here](./controls/README.md).

## Run

There are two ways to run the program: `mission` and `practice`.

In a `mission` run, the computer vision and flight data capture are parallelly run in the background.
The computer vision shares with the controls system and flight data capture writes the flight data to
a file. To do a `mission` run, run the following command in terminal from this directory:

`python3 main.py --run mission`


In a `practice` run, the computer vision opens the camera preview with a bounding box over the rocket 
prediction and the flight data capture opens a terminal window with the flight data displayed. To do a
`practice` run, run the following command in terminal from this directory:

`python3 main.py --run practice`
