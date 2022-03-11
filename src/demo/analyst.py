import logging
import demo.db as db
import demo.utils as utils
import xml.etree.ElementTree as et

analyst_log = logging.getLogger('analyst')
analyst_log.setLevel(logging.DEBUG)
analyst_log_ch = logging.StreamHandler()
analyst_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
analyst_log_ch.setFormatter(formatter)
analyst_log.addHandler(analyst_log_ch)

widget_attempt_action_map = {
    'ImageView': ['click'],
    'EditText': ['set_text'],
    'TextView': ['click'],
    'Button': ['click'],
    'ImageButton': ['click'],
    'CheckBox': ['click']
}

LOW_CONFIDENCE = 0
MEDIUM_CONFIDENCE = 1
HIGH_CONFIDENCE = 2

CONCRETE_WIDGETS_INFER = 3
WIDGETS_LEN_INFER = 4
WIDGETS_TYPE_INFER = 5


class Analyst:
    def __init__(self, device, threshold):
        self.device = device
        self.threshold = threshold

    def co_analysis(self, description):
        """
        d1 similarity now-d2 & HIGH_CONFIDENCE -> directly construct (infer concrete widgets)
        d1 similarity now-d2 & LOW_CONFIDENCE -> origin methods (only infer len and type)
        d1 similarity now-d2 & MEDIUM_CONFIDENCE -> one by one construct and follow the event by d1
                                                    (may have the same result. (need more consideration))
        d1 non-similarity now-d2 & HIGH_CONFIDENCE -> origin methods (different intent on same activity)
        d1 non-similarity now-d2 & LOW_CONFIDENCE -> origin methods (totally different)
        d1 non-similarity now-d2 & MEDIUM_CONFIDENCE -> have different flow (d1 is ok but d2 is refuse)
        :param description:
        :return:
        """
        gui_analysis_result = self.gui_analysis()
        description_analysis_result = self.description_analysis(description)
        pass

    def gui_analysis(self):
        selectors_by_rid = db.get_selectors_by_rid()
        result = dict()
        for rid in selectors_by_rid:
            selectors = selectors_by_rid[rid]
            result.setdefault(rid, 0)
            for selector in selectors:
                if self.device.exists_widget(selector):
                    result[rid] += 1
        """ if score > 1 -> do lots of event on the fragment of activity (for example : full form) """
        """ if score == 1 -> maybe only one event have to do on the activity (for example : save, create event, more option...)|
                            maybe the whole events were done on multi screen (VERY HARD)"""

        for rid in result:
            score = result[rid]
            len_of_events = len(selectors_by_rid[rid])
            if score > 1:
                result[rid] = HIGH_CONFIDENCE
            if score == 1:
                if len_of_events == 1:
                    result[rid] = HIGH_CONFIDENCE
                if len_of_events > 1:
                    result[rid] = MEDIUM_CONFIDENCE
            if score < 1:
                result[rid] = LOW_CONFIDENCE

        return result

    def description_analysis(self, description):
        descriptions = db.get_description_by_rid()
        """ 
        use s-bert to find similarity between description,
        """
        pass

    def event_analysis(self):
        pass

    def action_analysis(self, widget):
        events = db.get_all_events()
        for event in events:
            r = utils.is_same_widget_from_widget_info(widget, event.widget)
            if r:
                return event.action

        d = dict()
        for event in events:
            class_ = utils.get_class(event.widget)
            d.setdefault(class_, dict())
            d[class_].setdefault(event.action, 0)
            d[class_][event.action] += 1

        class_ = utils.get_class(widget)
        if class_ in d:
            actions = d[class_]
            action = max(zip(actions.values(), actions.keys()))[0]
            return action

        return widget_attempt_action_map[class_]

    # static analysis to get action is better!
    def analysis(self, apk):
        pass
