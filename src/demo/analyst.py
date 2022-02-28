import xml.etree.ElementTree as et
import logging
from functools import reduce
from androguard.core.analysis.analysis import Analysis

analyst_log = logging.getLogger('analyst')
analyst_log.setLevel(logging.DEBUG)
analyst_log_ch = logging.StreamHandler()
analyst_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
analyst_log_ch.setFormatter(formatter)
analyst_log.addHandler(analyst_log_ch)

class Analyst:
    def gui_analysis(self, gui):
        pass

    def description_analysis(self, description):
        pass

    def analysis(self):
        pass
# if __name__ == '__main__':
#     analysis = Analysis()
#     analysis.add()