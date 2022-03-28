from abc import abstractmethod
import logging

graph_log = logging.getLogger('graph_')
graph_log.setLevel(logging.DEBUG)
graph_log_ch = logging.StreamHandler()
graph_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
graph_log_ch.setFormatter(formatter)
graph_log.addHandler(graph_log_ch)


class Graph:
    def __init__(self, graph_folder):
        self.graph_folder = graph_folder
        self.nodes = []
        self.edges = []
        pass

    @abstractmethod
    def import_graph(self): pass

    @abstractmethod
    def find_shortest_path_between_activity(self, src, tgt):
        """
        find the shortest path between src and tgt
        :param src: id of src_node
        :param tgt: id of tgt_node
        :return:
        """
        pass

    @abstractmethod
    def add_edge(self, src, tgt, event):
        """
        this method will add an edge between src and tgt because event is trigger.
        :param src: the id of src_node
        :param tgt: the id of tgt_node
        :param event: must have widget and action
        :return:
        """
        pass

    @abstractmethod
    def add_node(self, node):
        """
        this method will add a node to graph_
        :param node: must have id and other information will be referred inside method.
        :return:
        """
        pass


class Node:
    def __init__(self, node_id):
        self.node_id = node_id


class Edge:
    def __init__(self, src, tgt, event):
        self.src = src
        self.tgt = tgt
        self.event = event
