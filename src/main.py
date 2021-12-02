import argparse
from demo.device import Device

parser = argparse.ArgumentParser(description='demo')
parser.add_argument('-apk_path', '-ap', dest='apk_path', type=str, help='point a apk file which want to execute on avd',
                    required=True)
parser.add_argument('-test_record', '-tr', dest='test_record', type=str, help='point a test record')
if __name__ == '__main__':
    args = parser.parse_args()
    d = Device(port=1234)
