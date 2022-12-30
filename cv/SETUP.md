# Setup

## Set up the Raspberry Pi

Before you begin, you need to
[set up your Raspberry Pi](https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up) with
Raspberry Pi OS (preferably updated to the most recent version).


## Set up the Pi Camera

You also need to [connect and configure the Pi Camera](https://www.raspberrypi.org/documentation/configuration/camera.md).


## Install the TensorFlow Lite Runtime

Follow [these instructions](https://www.tensorflow.org/lite/guide/python#install_tensorflow_lite_for_python)
install the TensorFlow Lite Runtime.


## Install the Edge TPU Runtime

Follow [these instructions](https://coral.ai/docs/accelerator/get-started/#1-install-the-edge-tpu-runtime) to install
the Edge TPU Runtime. **(MAKE SURE TO INSTALL WITH MAXIMUM OPERATING FREQUENCY)**


## Install Additional Required Packages

In this directory, run the following command in the terminal:

```
python3 -m pip install -r requirements.txt
```