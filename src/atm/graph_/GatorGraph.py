from abc import ABC
from atm.graph_.graph import Graph, graph_log
from collections import deque, namedtuple
from networkx.exception import NetworkXNoPath
import networkx as nx
import os
import json
import re


class GatorGraph(Graph, ABC):
    def __init__(self, graph_folder):
        super().__init__(graph_folder)
        self.g = nx.MultiDiGraph()
        self.import_graph()

    def import_graph(self):

        graph_ = os.path.join(self.graph_folder, 'graph_.json')
        assert os.path.exists(os.path.join(self.graph_folder, 'graph_.json'))
        graph_ = json.load(open(graph_, 'r'))
        nodes = graph_['nodes']
        edges = graph_['edges']
        self.nodes = [Node(**node) for node in nodes]
        for edge in edges:
            if Edge.is_drop(edge):
                pass
            else:
                self.edges.append(Edge(**edge))
        for node in self.nodes:
            self.g.add_node(node.id)
        for edge in self.edges:
            self.g.add_edge(edge.src, edge.tgt, id=edge.edge_id)

    def find_shortest_path_between_activity(self, src, tgt):
        try:
            paths = nx.all_shortest_paths(self.g, source=src, target=tgt)
            return paths
        except NetworkXNoPath:
            return []

    def add_edge(self, src, tgt, event):
        max_id = 0
        for edge in self.edges:
            if edge.edge_id > max_id:
                max_id = edge.edge_id + 1
            if edge.src == src and edge.tgt == tgt:
                if edge.action == event.action and event.widget_id == edge.widget_id:
                    graph_log.info('Edge already exists')
                    return
        e = Edge(max_id, src, tgt, event.action, None)
        e.widget_id = event.widget_id
        self.edges.append(e)

    def add_node(self, node_):
        max_id = 0
        for node in self.nodes:
            if node.id > max_id:
                max_id = node.id + 1
            if node_.activity == node.activity and node_.type == node.activity:
                return
        self.nodes.append(Node(max_id, node_.activity, node_.type))
        pass

    def get_out_edge(self, src):
        edges = []
        for edge in self.edges:
            if edge.src == src:
                edges.append(edge)
        return edges


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
