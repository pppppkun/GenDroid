from atm.graph.graph import Graph
import os
import json
import re


class GatorGraph(Graph):
    def __init__(self, graph_folder):
        super().__init__(graph_folder)
        self.import_graph()

    def import_graph(self):

        graph = os.path.join(self.graph_folder, 'graph.json')
        assert os.path.exists(os.path.join(self.graph_folder, 'graph.json'))
        graph = json.load(open(graph, 'r'))
        nodes = graph['nodes']
        edges = graph['edges']
        self.nodes = [Node(**node) for node in nodes]
        for edge in edges:
            if Edge.is_drop(edge):
                pass
            else:
                self.edges.append(Edge(**edge))


class Edge:
    stop_action = ['implicit', 'power', 'rotate']

    def __init__(self, edge_id, src, tgt, action, widget_id):
        self.edge_id = edge_id
        self.src = src
        self.tgt = tgt
        self.action = action
        self.widget_id = self.process_widget_id(widget_id)

    @classmethod
    def process_widget_id(cls, widget_id):
        # INFL[android.widget.TextView,WID[2131296564|tv_new_task_priority]488, 5135]5144
        pattern = re.compile(r'\[(\d+)')
        l = pattern.findall(widget_id)
        # assert len(l) == 1
        if len(l) != 1:
            return None
        return pattern.findall(widget_id)[0]

    @classmethod
    def is_drop(cls, edge):
        for stop in cls.stop_action:
            if stop in edge['action']:
                return True
        if cls.process_widget_id(edge['widget_id']) is None:
            return True
        pass


class Node:
    def __init__(self, id, activity, type):
        self.id = id
        self.activity = activity
        self.type = type
        pass


if __name__ == '__main__':
    graph = GatorGraph('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/out')
