import demo.utils as utils
import pydot
import os
import re
import networkx as nx
from collections import defaultdict


class CallGraphParser:
    def __init__(self, atm_folder):
        self.atm_folder = atm_folder
        self.activity_to_nodes = defaultdict(list)
        self.activity_to_onCreate_node = dict()
        self.self_loops = defaultdict(list)
        self.onCreate_param = {'android.os.Bundle'}
        self.G = self.get_graph_from_dot_file()
        self.group_nodes()

    def get_graph_from_dot_file(self):
        if os.path.exists(os.path.join(self.atm_folder, 'gendroid.gv')):
            graphs = pydot.graph_from_dot_file(os.path.join(self.atm_folder, 'gendroid.gv'))
            (g2,) = graphs
            G = nx.nx_pydot.from_pydot(g2)
            # remove edges with label "GUI (NULL)"
            G2 = nx.MultiDiGraph()
            for n in G.nodes:
                G2.add_node(n)
            for e in G.edges:
                lbl = G.edges[e]['label']
                if lbl != '"GUI (NULL)"':
                    G2.add_edge(e[0], e[1], label=lbl)
            return G2
        else:
            return nx.MultiDiGraph()

    def group_nodes(self):
        param_pattern = re.compile('.*\((.*)\)')
        for node in self.G.nodes:
            act = utils.get_activity(node)
            self.activity_to_nodes[act].append(node)
            if ': void onCreate(' in node:
                assert node not in self.activity_to_onCreate_node
                self.activity_to_onCreate_node[act] = node
                param = param_pattern.match(node).group(1)
                # param = node.split('(')[1].split(')')[0]
                self.onCreate_param.add(param)
        for activity in self.activity_to_nodes.keys():
            self.activity_to_nodes[activity] = sorted(
                self.activity_to_nodes[activity],
                key=lambda x: (x.split(':')[0], len(utils.get_method(x)))
            )

    def get_paths_between_activities(self, activity_from, activity_to, consider_naf_only_widget=False):
        all_paths = {}
        nodes_from, nodes_to = self.activity_to_nodes[activity_from], self.activity_to_nodes[activity_to]
        for n_from in nodes_from:
            for n_to in nodes_to:
                n_paths = self.get_paths_between_nodes(n_from, n_to, consider_naf_only_widget)
                for path in n_paths:
                    key = ''.join(path)
                    if key not in all_paths:
                        all_paths[key] = path
        return list(all_paths.values())

    def get_paths_between_nodes(self, n_from, n_to, consider_naf_only_widget=False):
        """For now, only return one path for n_from -> n_to"""
        gui_paths = {}
        if n_from != n_to:
            for hops in nx.all_simple_paths(self.G, source=n_from, target=n_to):
                # print(hops)
                gui_path = []
                for i in range(len(hops) - 1):  # try to find a GUI action for each pair of hops
                    u, v = hops[i], hops[i + 1]
                    for j in range(self.G.number_of_edges(u, v)):
                        e_attrs = self.G.edges[(u, v, j)]
                        gui_event = None
                        m = re.search(r"GUI \((.+)\)", e_attrs['label'])
                        if m and m.group(1) != 'NULL':  # info from static analysis
                            # e.g., '"GUI (newShortcut)"'; '"GUI (2131296593)"'
                            gui_event = m.group(1) + ' (' + utils.get_method(v) + ')'
                        elif e_attrs['label'].startswith('D@'):  # info from dynamic exploration
                            # e.g, D@class=android.widget.TextView&content-desc=&naf=&resource-id=create&text=Create (onClick)
                            gui_event = e_attrs['label']
                        if gui_event:
                            gui_path += [utils.get_activity(u), gui_event]
                            break
                gui_path.append(utils.get_activity(n_to))
                key = ''.join(gui_path)
                if key not in gui_paths and len(gui_path) > 2:
                    gui_paths[key] = gui_path
                    # add one more step at the end if there a self-loop
                    for lbl in self.self_loops.get(n_to, []):  # to repeat at the last activity
                        gui_path_with_a_loop = [h for h in gui_path]
                        if lbl != gui_path_with_a_loop[-2]:  # not to repeat the same GUI event again
                            gui_path_with_a_loop.insert(-1, lbl)
                            key = ''.join(gui_path_with_a_loop)
                            if key not in gui_paths:
                                gui_paths[key] = gui_path_with_a_loop
                    # to repeat at the 2nd to last activity, a31-a35-b31
                    if utils.get_activity(gui_path[-1]) != utils.get_activity(gui_path[-3]):
                        second_to_last = gui_path[-3]
                        nodes = self.activity_to_nodes[second_to_last]
                        for node in nodes:
                            for lbl in self.self_loops.get(node, []):
                                gui_path_with_a_loop = [h for h in gui_path]
                                if lbl != gui_path_with_a_loop[-2]:  # not to repeat the same GUI event again
                                    gui_path_with_a_loop.insert(-2, lbl)
                                    key = ''.join(gui_path_with_a_loop)
                                    if key not in gui_paths:
                                        gui_paths[key] = gui_path_with_a_loop
        else:  # n_from == n_to
            for lbl in self.self_loops.get(n_from, []):
                gui_path = [utils.get_activity(n_from), lbl, utils.get_activity(n_from)]
                key = ''.join(gui_path)
                if key not in gui_paths:
                    gui_paths[key] = gui_path
        if not consider_naf_only_widget:
            CallGraphParser.remove_paths_with_naf_only_widgets(gui_paths)
        return list(gui_paths.values())

    def add_edge(self, act_from, act_to, w_stepping):
        """add a dynamically found edge into G"""
        # nx automatically takes care of non-existing / duplicated node issue when adding an edge
        # every node is unique in a graph_ by its name
        w_stepping['content-desc'] = w_stepping['contentDescription']
        w_stepping['resource-id'] = w_stepping['resourceName']
        if w_stepping['text'] is None:
            w_stepping['text'] = ''
        """
        add node which create activity_from/to
        """
        if act_from not in self.activity_to_onCreate_node:
            self.activity_to_onCreate_node[act_from] = act_from + ': void onCreate(' + list(self.onCreate_param)[
                0] + ')'
        if act_to not in self.activity_to_onCreate_node:
            self.activity_to_onCreate_node[act_to] = act_to + ': void onCreate(' + list(self.onCreate_param)[0] + ')'
        node_create_act_from = self.activity_to_onCreate_node[act_from]
        node_create_act_to = self.activity_to_onCreate_node[act_to]
        attrs = set(utils.FEATURE_KEYS).difference({'clickable', 'password'})
        values = [w_stepping[a] for a in attrs]
        # lbl_stepping is ...&${attrs}=${values}&...
        lbl_stepping = '&'.join([a + '=' + v for a, v in zip(attrs, values)])
        action = ' (onLongClick)' if w_stepping['action'][0] == 'long_press' else ' (onClick)'
        lbl_stepping = 'D@' + lbl_stepping + action
        if node_create_act_from != node_create_act_to:
            is_edge_existed = False
            for i in range(self.G.number_of_edges(node_create_act_from, node_create_act_to)):
                if lbl_stepping == self.G.edges[(node_create_act_from, node_create_act_to, i)]['label']:
                    is_edge_existed = True
                    break
            if not is_edge_existed:
                print(f'Adding edge: from {node_create_act_from} to {node_create_act_to}\nlabel is: {lbl_stepping}')
                self.G.add_edge(node_create_act_from, node_create_act_to, label=lbl_stepping)
                self.update_act_to_nodes(node_create_act_from)
                self.update_act_to_nodes(node_create_act_to)
        else:
            if lbl_stepping not in self.self_loops[node_create_act_from]:
                print(f'Adding self-loop: {node_create_act_from}, label: {lbl_stepping}')
                self.self_loops[node_create_act_from].append(lbl_stepping)
                self.G.add_edge(node_create_act_from, node_create_act_from, label=lbl_stepping)
                self.update_act_to_nodes(node_create_act_from)

    def update_act_to_nodes(self, node):
        act = utils.get_activity(node)
        if act not in self.activity_to_nodes:
            self.activity_to_nodes[act].append(node)
        else:
            if node not in self.activity_to_nodes[act]:
                self.activity_to_nodes[act].insert(0, node)

    @classmethod
    def remove_paths_with_naf_only_widgets(cls, gui_paths):
        # e.g., a gui_path = ['com.rainbowshops.activity.ProfileActivity',
        #                     'D@text=Log In&class=android.widget.Button&content-desc=&resource-id=button_log_in&naf= (onClick)',
        #                     'D@text=&class=android.widget.ImageButton&content-desc=&resource-id=&naf=true (onClick)',
        #                     'com.rainbowshops.activity.LoginAndSignUpActivity']
        discarded_keys = []
        for k, gpath in gui_paths.items():
            for hop in gpath:
                if CallGraphParser.is_naf_only_widget(hop):
                    discarded_keys.append(k)
                    break
        for k in discarded_keys:
            gui_paths.pop(k, None)

    @classmethod
    def is_naf_only_widget(cls, hop):
        # e.g., 'D@text=&class=android.widget.ImageButton&content-desc=&resource-id=&naf=true (onClick)'
        if not hop.startswith('D@'):
            return False
        hop = ' '.join(hop.split()[:-1])
        kv_pairs = hop[2:].split('&')
        kv = [kvp.split('=') for kvp in kv_pairs]
        # e.g., [['text', 'Art '], [' Collectibles'], ['class', 'android.widget.TextView']]
        curated_kv = []
        for pairs in kv:
            if len(pairs) == 2:
                curated_kv.append(pairs)
            elif len(pairs) == 1:
                curated_kv[-1][1] += '&' + pairs[0]
            else:
                assert False
        criteria = {k: v for k, v in curated_kv}
        if all([v for k, v in criteria.items() if k in ['class', 'naf']]) \
                and not any([v for k, v in criteria.items() if k not in ['class', 'naf']]):
            return True
        return False


NODE_TYPE = [
    'dynamic',
    'static'
]


class Edge:
    def __init__(self, type, attrib, action):
        self.type = type
        self.attrib = attrib
        self.action = action

    def __str__(self):
        return f"{self.type}  {self.action}  {self.attrib}"

    def to_graph_node(self):
        pass


if __name__ == '__main__':
    cgp = CallGraphParser(atm_folder='/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/out')
    # print(cgp.activity_to_nodes['org.secuso.privacyfriendlytodolist.view.MainActivity'])
    # for node in cgp.G.nodes:
    #     print(node)
    # for edge in cgp.G.edges:
    #     print(edge[0], edge[1], cgp.G.edges[edge]['label'])
    # print(cgp.activity_to_nodes.keys())
    # print(cgp.activity_to_onCreate_node)
    # for path in cgp.get_paths_between_activities('Root',
    #                                              'org.secuso.privacyfriendlytodolist.view.dialog.ProcessTodoTaskDialog'):
    #     print(path)
