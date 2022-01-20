from uiautomator2 import Device
import uiautomator2 as u2
import logging


def get_all_installed_package(u: Device):
    ret = u.shell("pm list packages -f")
    if ret.exit_code == 0:
        return ret.output
    else:
        logging.warning('can\'t load installed package ')


def install_grant_runtime_permissions(u: Device, data):
    target = "/data/local/tmp/_tmp.apk"
    u.app_install(data)
    u.push(data, target, show_progress=True)
    ret = u.shell(['pm', 'install', "-r", "-t", "-g", target], timeout=300)
    if ret.exit_code != 0:
        raise RuntimeError(ret.output, ret.exit_code)

