import os
import logging
import time

from atm.event import VirtualEvent
from threading import Timer

api_log = logging.getLogger('api')
api_log.setLevel(logging.DEBUG)
api_log_ch = logging.StreamHandler()
api_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
api_log_ch.setFormatter(formatter)
api_log.addHandler(api_log_ch)


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
    os.system(f'mkdir {decompile}')
    os.system(f'mkdir {out}')
    os.system(f'mkdir {screenshot}')
    api_log.info(f'decompiler {apk} to {decompile}')
    os.system(f'apktool d {apk} -f -o {decompile} > /dev/null')
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
    def __init__(self, apk_folder, app_name, timeout=60 * 30):
        set_app(apk_folder, app_name)
        from atm.device import Device
        from atm.executor import Executor
        from atm.db import DataBase
        from atm.analyst import Analyst
        from atm.FSM import FSM
        from atm.construct import Constructor
        from atm.confidence import Confidence
        self.__graph = FSM(graph_folder=os.path.join(apk_folder, 'output'))
        self.__device = Device(os.path.join(apk_folder, app_name + '.apk'), self.__graph)
        self.__db = DataBase(decompile_folder=os.path.join(apk_folder, 'decompile'),
                             atm_folder=os.path.join(apk_folder, 'out'), package=self.__device.package)
        self.__confidence = Confidence()
        self.__analyst = Analyst(device=self.__device, graph=self.__graph, data_base=self.__db,
                                 confidence=self.__confidence)
        self.__constructor = Constructor(db=self.__db)
        self.__executor = Executor(device=self.__device, analyst=self.__analyst, constructor=self.__constructor)
        self.__descriptions = []
        self.__timeout = timeout
        pass

    def add_description(self, description, data=None):
        ve = VirtualEvent(description, data)
        self.__descriptions.append(ve)
        return self

    def construct(self, file_name=None):
        try:
            self.timer = Timer(self.__timeout, self.stop, args=(file_name,))
            self.timer.start()
            logging.basicConfig(filename=file_name+'.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.__executor.execute(self.__descriptions)
        except BaseException or SystemExit:
            logging.info('nice to meet bug')
        api_log.info('to script')
        self.__executor.to_scripts(file_name)
        return self

    def stop(self, file_name=None):
        self.__executor.to_scripts(file_name)
        self.timer.cancel()
        api_log.info('timeout!')
        exit(0)


if __name__ == '__main__':
    pass
