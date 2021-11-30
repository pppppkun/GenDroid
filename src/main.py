import argparse
from demo.device import Device

parser = argparse.ArgumentParser(description='demo')
parser.add_argument('-apk_path', '-ap', dest='apk_path', type=str, help='point a apk file which want to execute on avd',
                    required=True)
parser.add_argument('-test_script_path', '-tsp', dest='test_script_path', type=str,
                    help='point a test script path of the apk')
parser.add_argument('-script_executor', '-se', dest='script_executor', help='point the executor of script',
                    choices=['appium'])
if __name__ == '__main__':
    args = parser.parse_args()
    d = Device(port=1234)