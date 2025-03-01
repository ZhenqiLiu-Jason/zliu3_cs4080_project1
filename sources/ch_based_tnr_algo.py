from heapdict import heapdict
import networkx as nx
import copy

def get_edge_diff(ref_graph, node):
    """
    This function computes the edge difference of a given node on the
    given graph.
    """

    # We first get the neighbors of the node
    # We need to exclude the node itself from the neighbor's list
    neighbors = [n for n in ref_graph.neighbors(node) if n != node]

    # The number of edges removed will just be the number of neighbors
    num_edges_removed = len(neighbors)

    # Compute the number of shortcuts added by check all the pairs of
    # neighbors
    num_shortcuts_added = 0

    for i in range(len(neighbors)):
        for j in range(i + 1, len(neighbors)):

            # Get a neighbor pair
            neighbor1 = neighbors[i]
            neighbor2 = neighbors[j]

            # Compute the shortes path between these neighbors
            # using Bidirectional Dijkstra
            path_length, path = nx.bidirectional_dijkstra(ref_graph, neighbor1, neighbor2, weight="length")

            # If a the node exist in the shortest path, then
            # I need to add a shortcut
            if node in path:
                num_shortcuts_added += 1

    return num_shortcuts_added - num_edges_removed


def get_ordering_shortcut(ref_graph_original, heuristic):
    """
    This function computes the CH node ordering based on a heuristic
    It also returns the resulted shortcuts
    """

    # The auxiliary data that holds all the shortcuts and node ordering
    shortcuts = type(ref_graph_original)()
    node_ordering = {}

    # Get a copy of the original graph
    ref_graph = copy.deepcopy(ref_graph_original)

    # Compute an initial ordering
    ordering = heapdict()

    for node in ref_graph.nodes:
        ordering[node] = heuristic(ref_graph, node)

    # Start shortcutting the nodes based on the ordering
    order_count = 0
    while ordering:

        # Get the next node to be shortcutted
        node, edge_diff = ordering.popitem()

        # Add node ordering
        node_ordering[node] = order_count
        order_count += 1

        # We first get the neighbors of the node
        # Exclude node itself from the neighbor list to avoid problem
        neighbors = [n for n in ref_graph.neighbors(node) if n != node]

        # Iterate through all the pairs and add shortcuts accordingly
        # (if the node exist in the shortest path between two neighbors)
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):

                # Get a neighbor pair
                neighbor1 = neighbors[i]
                neighbor2 = neighbors[j]

                # Compute the shortes path between these neighbors
                # using Bidirectional Dijkstra
                path_length, path = nx.bidirectional_dijkstra(ref_graph, neighbor1, neighbor2, weight="length")

                # If the node exist in the shortest path, then
                # I need to add a shortcut
                if node in path:
                    ref_graph.add_edge(neighbor1, neighbor2, length=path_length)
                    shortcuts.add_edge(neighbor1, neighbor2, length=path_length)

        # Remove this node and all its associated edges
        ref_graph.remove_node(node)

        # Recompute the heuristic of the neighbors
        for neighbor in neighbors:
            ordering[neighbor] = heuristic(ref_graph, neighbor)

    return node_ordering, shortcuts
