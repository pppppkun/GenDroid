import os
import logging
import subprocess
import traceback
import argparse
from gendroid.event import VirtualEvent
from gendroid.executor import ExecutorMode
from threading import Timer

api_log = logging.getLogger('api')
api_log.setLevel(logging.DEBUG)
api_log_ch = logging.StreamHandler()
api_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
api_log_ch.setFormatter(formatter)
api_log.addHandler(api_log_ch)

parser = argparse.ArgumentParser(description='api')
parser.add_argument('--output', dest='output', type=str, default='demo')
parser.add_argument('--mode', dest='mode', type=str, help='Specify the mode of executor\n\t dynamic, static, hybrid',
                    default='dynamic')
parser.add_argument('--position', dest='use_position', action='store_true',
                    help='Specify whether use position in description', default=True)
parser.add_argument('--no-position', dest='use_position', action='store_false')
parser.add_argument('--device', dest='device', default='emulator-5554')


# parser.add_argument('-test_record', '-tr', dest='test_record', type=str, help='point a test record')
# parser.add_argument('-repair_strategy', '-rs', dest='repair_strategy', type=str, help='Specify a repair policy')
# parser.add_argument('-verbose', dest='verbose', action='store_true', help='start detailed output')


def set_app(apk_folder, app_name):
    """
    1. apktool d {apk} -f -o apk_folder/{decompile}
    2. mkdir apk_folder/out
    :param apk_folder:
    :param app_name:
    :return:
    """
    td_path = '/Users/pkun/PycharmProjects/ui_api_automated_test/TrimDroid.jar'
    apk = os.path.join(apk_folder, app_name + ".apk")
    decompile = os.path.join(apk_folder, 'decompile')
    out = os.path.join(apk_folder, 'out')
    screenshot = os.path.join(apk_folder, 'screenshots')
    api_log.info(f'mkdir {decompile}, {out}, {screenshot}')
    if not os.path.exists(decompile):
        os.system(f'mkdir {decompile}')
        os.system(f'apktool d {apk} -f -o {decompile} > /dev/null')
    os.system(f'mkdir {out}')
    os.system(f'mkdir {screenshot}')
    api_log.info(f'decompiler {apk} to {decompile}')
    # api_log.info(f'Analysis ATM using TrimDroid to {out}')
    # os.system(f'java -jar {td_path} {apk_folder} {app_name} {out} > /dev/null')
    api_log.info(f'Dynamic Analysis App using Droidbot (BFS)')
    # adb
    # root & & adb
    # logcat - c | | adb
    # logcat - c & & droidbot - a
    # simpleCalendarPro.apk - o
    # output - is_emulator - policy
    # bfs_greedy - count
    # 100
    # os.system(f'adb root & adb logcat -c & droidbot -a {apk} -o output -is_emulator -count 300')
    pass


class Tester:
    def __init__(self, apk_folder, app_name, timeout=60 * 30, have_install=False, is_debug=False):
        self.timer = None
        self.args = parser.parse_args()
        api_log.info(self.args)
        set_app(apk_folder, app_name)
        from gendroid.device import Device
        from gendroid.executor import Executor
        from gendroid.db import DataBase
        from gendroid.analyst import Analyst
        from gendroid.FSM import FSM
        from gendroid.construct import Constructor
        from gendroid.confidence import Confidence

        self.__graph = FSM(graph_folder=os.path.join(apk_folder, 'output'))
        self.__device = Device(os.path.join(apk_folder, app_name + '.apk'), self.__graph, have_install, self.args.device)
        self.__db = DataBase(decompile_folder=os.path.join(apk_folder, 'decompile'),
                             atm_folder=os.path.join(apk_folder, 'out'), package=self.__device.package)
        self.__confidence = Confidence()
        self.__analyst = Analyst(device=self.__device, graph=self.__graph, data_base=self.__db,
                                 confidence=self.__confidence, use_position=self.args.use_position)
        self.__constructor = Constructor(db=self.__db)
        self.__executor = Executor(device=self.__device, analyst=self.__analyst, constructor=self.__constructor,
                                   mode=ExecutorMode[self.args.mode.upper()])
        self.__descriptions = []
        self.__timeout = timeout
        self.__is_debug = is_debug

    def pre_condition(self, direction):
        event = self.__constructor.generate_scroll_event(direction)
        self.__device.execute(event, is_add_edge=False)
        return self

    def add_description(self, description, data=None):
        ve = VirtualEvent(description, data)
        self.__descriptions.append(ve)
        return self

    def construct(self, file_name=None):
        try:
            if not os.path.exists(self.args.output):
                os.mkdir(self.args.output)
            file_name = os.path.join(self.args.output, file_name)
            if not self.__is_debug:
                logging.basicConfig(filename=file_name + '.log',
                                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            else:
                logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            api_log.info(f'now {file_name}')
            self.__executor.execute(self.__descriptions)
        except BaseException or SystemExit:
            traceback.print_exc()
            api_log.info('nice to meet bug')
        api_log.info('to script')
        self.__executor.to_scripts(file_name)
        return self

    def stop(self, file_name=None):
        self.__executor.to_scripts(file_name)
        self.timer.cancel()
        api_log.info('timeout!')
        exit(0)


class InteractiveTester:
    def __init__(self, apk_folder, app_name):
        self.timer = None
        set_app(apk_folder, app_name)
        from gendroid.device import Device
        from gendroid.executor import Executor
        from gendroid.db import DataBase
        from gendroid.analyst import Analyst
        from gendroid.FSM import FSM
        from gendroid.construct import Constructor
        from gendroid.confidence import Confidence

        self.__graph = FSM(graph_folder=os.path.join(apk_folder, 'output'))
        self.__device = Device(os.path.join(apk_folder, app_name + '.apk'), self.__graph, have_install=True)
        self.__db = DataBase(decompile_folder=os.path.join(apk_folder, 'decompile'),
                             atm_folder=os.path.join(apk_folder, 'out'), package=self.__device.package)
        self.__confidence = Confidence()
        self.__analyst = Analyst(device=self.__device, graph=self.__graph, data_base=self.__db,
                                 confidence=self.__confidence, use_position=True)
        self.__constructor = Constructor(db=self.__db)
        self.__executor = Executor(device=self.__device, analyst=self.__analyst, constructor=self.__constructor,
                                   mode=ExecutorMode['INTERACTIVE'])
        self.__descriptions = []

    def start(self):
        self.__executor.interactive()

def execute_script(path):
    if type(path) != list:
        path = [path]
    for p in path:
        get_all_test(p)


def get_all_test(p):
    os.system('which python3')
    files = list(os.listdir(p))
    for f in files:
        if f.endswith('.py') and not f.startswith('test'):
            print(f)
            mark_file = 'test_' + f + '.log'
            # if mark_file not in files:
            # command = 'python3 ' + os.path.join(p, f)
            # print(command)
            # os.system(command)


def compare(folder1, folder2, filepaths):
    import subprocess
    for filepath in filepaths:
        t1 = os.path.join(folder1, 'test_' + filepath)
        t2 = os.path.join(folder2, 'test_' + filepath)
        print(t1, t2)
        subprocess.call(['diff', t1, t2])


def run_all_test(filenames, target_folder, mode, device='emulator-5554'):
    for filepath in filenames:
        run_test(filepath, target_folder, mode, device)


def run_test(filepath, target_folder, mode, device='emulator-5554'):
    target = 'test_' + filepath
    if not os.path.exists(os.path.join(target_folder, target)):
        subprocess.call(["python3", filepath, '--output', target_folder, '--mode', mode, '--device', device])

if __name__ == '__main__':
    pass
    # execute_script('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/chrome')
