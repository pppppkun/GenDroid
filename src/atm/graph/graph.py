from abc import abstractmethod


class Graph:
    def __init__(self, graph_folder):
        self.graph_folder = graph_folder
        self.nodes = []
        self.edges = []
        pass

    @abstractmethod
    def import_graph(self): pass

    @abstractmethod
    def find_path_between_activity(self, src, tgt): pass

    @abstractmethod
    def add_edge(self, src, tgt): pass

    @abstractmethod
    def add_node(self, node): pass
