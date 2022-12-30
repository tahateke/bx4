import argparse

from controller import mission_controller


def main():
    # get command line arguments.
    parser = argparse.ArgumentParser(description='Execute the BX-4 mission.')
    parser.add_argument(
        '--run',
        choices=['mission', 'practice'],
        required=True,
        type=str,
        help='Choose to execute a mission or practice run')
    args = parser.parse_args()

    # execute mission
    mc = mission_controller.MissionController()
    mc.execute_mission(args.run)


if __name__ == '__main__':
    main()
