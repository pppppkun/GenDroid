from abc import ABC
from atm.graph.graph import Graph, graph_log
from collections import deque, namedtuple
from networkx.exception import NetworkXNoPath
import networkx as nx
import os
import json
import re


class FSM(Graph, ABC):
    def __init__(self, graph_folder):
        super().__init__(graph_folder)
        self.g = nx.MultiDiGraph()
        self.states = []
        self.edges = []

    def import_graph(self):
        pass

    def find_shortest_path_between_activity(self, src, tgt):
        pass

    def add_edge(self, src, tgt, event):
        pass

    def add_node(self, new_state):
        assert new_state.activity
        assert new_state.widgets
        for state in self.states:
            if state == new_state:
                return
        self.states.append(new_state)


class State:
    def __init__(self, activity, widgets):
        self.activity = activity
        self.widgets = widgets
        pass

    # TODO
    def __eq__(self, other):
        if other.activity != self.activity:
            return False
        for other_widget in other.widgets:
            for self_widget in self.widgets:
                pass


class Edge:
    def __init__(self):
        pass


if __name__ == '__main__':
    pass
