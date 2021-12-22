import argparse
import json

from demo.device import Device
from demo.analyst import Analyst
from demo.series import Series
from demo.repair import Repair
from demo.executor import Executor

parser = argparse.ArgumentParser(description='demo')
parser.add_argument('-apk_path', '-ap', dest='apk_path', type=str, help='point a apk file which want to execute on avd',
                    required=True)
parser.add_argument('-test_record', '-tr', dest='test_record', type=str, help='point a test record')
parser.add_argument('-repair_strategy', '-rs', dest='repair_strategy', type=str, help='Specify a repair policy')
parser.add_argument('-verbose', dest='verbose', action='store_true', help='start detailed output')
if __name__ == '__main__':
    args = parser.parse_args()
    device = Device(apk_path=args.apk_path)
    analysis = Analyst()
    record = json.load(open(args.test_record, 'r'))
    series = Series(record['record_list'])
    repair = Repair(args.repair_strategy)
    executor = Executor(device, analysis, series, repair, args.verbose)
    executor.execute()
