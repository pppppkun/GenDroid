import uiautomator2 as u2
import logging

logging.basicConfig(level=logging.INFO)

class Device:
    def __init__(self, apk_path, serial=None):
        if serial:
            self.u = u2.connect(serial)
        else:
            self.u = u2.connect()
        self.install_apk(apk_path)

    def install_apk(self, apk_path):
        logging.info('push and install apk {}'.format(apk_path))
        self.u.app_install(apk_path)
        logging.info('install done.')


if __name__ == '__main__':
    d = Device(serial='emulator-5554', apk_path='../../benchmark/etar/etar1.0.25.apk')