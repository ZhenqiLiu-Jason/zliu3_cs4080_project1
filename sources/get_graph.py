import networkx as nx
import osmnx as ox

def get_graph(place_name, undirected=False):
    """
    This function returns a graph from osmnx module
    """

    # Get a graph from osmnx
    ref_graph = ox.graph_from_place(place_name, network_type="drive")

    # Convert graph to undirected if necessary
    if undirected:
        ref_graph = ox.convert.to_undirected(ref_graph)

    return ref_graph
