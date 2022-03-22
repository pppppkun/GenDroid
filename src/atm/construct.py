import logging

construct_log = logging.getLogger('construct')
construct_log.setLevel(logging.DEBUG)
construct_log_ch = logging.StreamHandler()
construct_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
construct_log_ch.setFormatter(formatter)
construct_log.addHandler(construct_log_ch)


class Constructor:
    def __init__(self, db):
        self.db = db
        pass

    def generate_events(self, widgets, action=None):
        pass


# # TODO more freestyle description
# def construct(self, gui, v_event: VirtualEvent):
#
#     ui_info = v_event.description
#     root = et.fromstringlist(gui)
#     construct_log.info('transfer gui and record to model')
#
#     def create_event(node_with_confidence, data=None):
#         result = list()
#         selector = get_node_attribute(node_with_confidence.node)
#         # action should study from history (ie same widget have same action, new widget should consider the
#         # static analysis result)
#         # action = self.analyst.action_analysis(node_with_confidence.node)
#         action = get_action_based_classes(node_with_confidence.node)[0]
#         if action == 'set_text' and data is None:
#             data = {'text': 'place_holder'}
#         event_data = EventData(action=action, selector=selector, data=data)
#         try:
#             event_ = event_factory[action](event_data)
#             event_.confidence = node_with_confidence.confidence
#             result.append(event_)
#             return result
#         except:
#             construct_log.error(action, selector, data)
#             return []
#
#     f = FunctionWrap((_node for _node in root.iter()))
#     f.append(
#         filter,
#         lambda _node: filter_by_class(_node)
#     ).append(
#         map,
#         lambda x: self.confidence(x, ui_info)
#     ).append(
#         sorted,
#         lambda x: -x.confidence
#     ).append(
#         map,
#         lambda x: create_event(x, v_event.data)
#     ).append(
#         reduce,
#         lambda x, y: x + y
#     )
#     events = f.do()
#     return deque(events)


if __name__ == '__main__':
    s1 = 'fab create'
    s2 = 'create notify'
    s3 = 'create'
