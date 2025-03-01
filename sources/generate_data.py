from get_graph import get_graph
from ch_based_tnr_algo import *
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

place_name = "Piedmont, California"
G = get_graph(place_name, undirected=True)

ordering, shortcuts = get_ordering_shortcut(G, get_edge_diff)





fig, ax = ox.plot_graph(G, save=True, filepath='ch_non_overlap.png', dpi=300)
G = nx.compose(G, shortcuts)


for u, v, d in G.edges(data=True):
    print(d["length"])

# Save the graph
fig, ax = ox.plot_graph(G, save=True, filepath='ch_overlap.png', dpi=300)
