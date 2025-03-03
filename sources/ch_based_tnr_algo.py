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


def get_transit_nodes(node_ordering, k):
    """
    Get the top k transit nodes based on the node ordering.
    Returns a list of transit nodes.
    """

    # Sort nodes by importance (highest to lowest) and get the top k
    transit_nodes = sorted(node_ordering, key=node_ordering.get, reverse=True)[:k]

    return transit_nodes


def get_transit_nodes_distance(ref_graph, transit_nodes):
    """
    Computes the distance table for all the transit nodes.

    Returns a dictionary structured like this:

    Key: (transit_node1, transit_node2)
    Value: the length between these transit nodes
    """

    distance_table = {}

    # Compute shortest path lengths between all transit node pairs
    for node1 in transit_nodes:

        # Get shortest paths from node1 to all other nodes using 'length' as weight
        lengths, _ = nx.single_source_dijkstra(ref_graph, node1, weight='length')

        # Store distances in the table for all pairs
        for node2 in transit_nodes:
            if node1 != node2 and node2 in lengths:
                distance_table[(node1, node2)] = lengths[node2]

    return distance_table


def get_access_nodes(ref_graph, node_ordering, transit_nodes, distance_table):
    """
    This function gets all the access nodes for all non-transit nodes.

    Runs forward CH query to find all the candidate access nodes.
    Then prune any bogus transit nodes.

    Each non-transit node's search space will also be saved.
    """

    # Dictionary to store access nodes and search space for all non-trnasit nodes
    access_nodes = {}
    search_space = {}

    # Find the access nodes for each non-transit nodes
    for node in ref_graph.nodes:
        if node not in transit_ndoes:

            # Run forward CH query
            current_access_nodes = []
            current_search_space = []
            current_distance = {}

            # Modified CH algorithm
            distance_queue = heapdict()
            distance_queue[node] = 0

            while distance_queue:
                u, du = distance_queue.popitem()

                # Prune the further search if this node is a transit node
                # And add this candidate transit node
                if u in transit_nodes:
                    current_access_nodes.append(u)
                    current_distance[u] = du
                    continue
                else:
                    # Add this node to the search space
                    current_search_space.append(u)

                # Update distances to the neighbors
                # Excluding those that are already in the search space
                # Also those that lead to a lower ordering
                for neighbor in [n for n in ref_graph.neighbors(u) if n not in current_search_space]:
                    if (node_ordering[neighbor] > node_ordering[u] and
                    du + ref_graph.get_edge_data(u, neighbor)['length'] 
                    < distance_queue.get(neighbor , float('inf'))):
                        distance_queue[neighbor] = du + ref_graph.get_edge_data(u, neighbor)['length']

            # Remove the bogus transit nodes using post-search-stalling
            for i in range(len(current_access_nodes)):
                for j in range(i + 1, len(current_access_nodes)):

                    # Get a pair of candidates transit nodes
                    t1 = current_access_nodes[i]
                    t2 = current_access_nodes[j]

                    if current_distance[t1] + distance_table[(t1, t2)] <= current_distance[t2]:
                        current_access_nodes.remove(t2)

            # Store this auxiliary data associated with this non-transit node
            access_nodes[node] = current_access_nodes
            search_space[node] = current_search_space

    return access_nodes, search_space
