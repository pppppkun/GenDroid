from abc import abstractmethod


class Graph:
    def __init__(self, graph_folder):
        self.graph_folder = graph_folder
        self.nodes = []
        self.edges = []
        pass

    @abstractmethod
    def import_graph(self):
        pass


# class TrimDroidGraph(Graph):
#     def __init__(self, graph_folder):
#         super().__init__(graph_folder)
#         self.import_graph()
#
#     def import_graph(self):
#         if os.path.exists(os.path.join(self.graph_folder, 'atm.gv')):
#             pass


class Edge:
    def __init__(self):
        pass


class Node:
    def __init__(self):
        pass
