import time


class ControlsSystem:
    def __init__(self):
        pass

    def controls(self, mission_start, time_total, prediction, run):
        # run until mission duration complete
        while True:
            # check if mission duration complete
            if time.perf_counter() - mission_start > time_total:
                # print(prediction['prediction'])
                break

            # do something if practice run
            if run == 'practice':
                pass
