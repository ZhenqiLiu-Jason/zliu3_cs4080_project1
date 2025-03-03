from get_graph import get_graph
from ch_based_tnr_algo import *
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

place_name = "Piedmont, California"
G = get_graph(place_name, undirected=True)

ordering, shortcuts = get_ordering_shortcut(G, get_edge_diff)



#fig, ax = ox.plot_graph(G, save=True, filepath='ch_non_overlap.png', dpi=300)
G = nx.compose(G, shortcuts)


# Save the graph
#fig, ax = ox.plot_graph(G, save=True, filepath='ch_overlap.png', dpi=300)


# get transit nodes
transit_nodes = get_transit_nodes(ordering, 100)
distance_table = get_transit_nodes_distance(G, transit_nodes)

# Get access nodes
access_nodes, search_space= get_access_nodes(G, ordering, transit_nodes, distance_table)






print(f"# shortcuts = {shortcuts.number_of_edges()}")

# Create a color map: red for transit nodes, gray for others
node_colors = ['red' if node in transit_nodes else 'gray' for node in G.nodes]
# Draw the original graph with highlighted transit nodes
fig, ax = plt.subplots(figsize=(10, 10))
ox.plot_graph(G, node_color=node_colors, edge_color='lightgray', node_size=30, ax=ax)
# Save the plot
plt.savefig("highlighted_transit_nodes.png")
plt.clf()

node_colors = ['green' if node in search_space[10232094660] else 'gray' for node in G.nodes]
fig, ax = plt.subplots(figsize=(10, 10))
ox.plot_graph(G, node_color=node_colors, edge_color='lightgray', node_size=30, ax=ax)
plt.savefig("highlighted_search_nodes.png")
plt.clf()



