import argparse
import json

from gendroid.device import Device
from gendroid.executor import Executor
from gendroid.analyst import Analyst
from gendroid.graph import CallGraphParser
from gendroid.construct import Constructor

parser = argparse.ArgumentParser(description='demo')
parser.add_argument('-apk_path', '-ap', dest='apk_path', type=str, help='point a apk file which want to execute on avd',
                    required=True)
parser.add_argument('-test_record', '-tr', dest='test_record', type=str, help='point a test record')
parser.add_argument('-repair_strategy', '-rs', dest='repair_strategy', type=str, help='Specify a repair policy')
parser.add_argument('-verbose', dest='verbose', action='store_true', help='start detailed output')

if __name__ == '__main__':
    device = Device()