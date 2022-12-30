# README

## Overview

The controls system software hasn't been built yet because the hardware and algorithms have not been
finalized at the moment. Overall, the controls system should take rocket prediction coordinates from
the computer vision and use that information to pivot the payload such that BX-4 is pointing directly
at the rocket, with the rocket at the center of the camera's view.


## High-level Code

Like the other mission tasks, the run length of the controls system is the mission length of 20 seconds.
Currently, the computer vision makes a prediction for the rocket in view and shares that information with 
the controls system. The x, y coordinates of each bounding box corner for the prediction are what the 
computer vision shares with the controls system.