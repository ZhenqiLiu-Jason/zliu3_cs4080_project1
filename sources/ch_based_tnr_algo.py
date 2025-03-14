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


def get_ordering_shortcut(ref_graph_original, heuristic, online=True):
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
        # Only update if online
        if online:
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
                distance_table[frozenset([node1, node2])] = lengths[node2]

        # Add distance to itself to avoid problems in situations
        # Where source and target node share a transit node
        distance_table[frozenset([node1, node1])] = 0

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
        if node not in transit_nodes:

            # Run forward CH query
            current_access_nodes = []
            current_search_space = set()

            searched = []

            # Modified CH algorithm
            distance_queue = heapdict()
            distance_queue[node] = 0

            while distance_queue:
                u, du = distance_queue.popitem()

                # To prevent repeated search
                searched.append(u)

                # Prune the further search if this node is a transit node
                # And add this candidate transit node
                if u in transit_nodes:
                    current_access_nodes.append((u, du))
                    continue
                else:
                    # Add this node to the search space
                    current_search_space.add(u)


                # Update distances to the neighbors
                # Excluding those that are already in the search space
                # Also those that lead to a lower ordering
                for neighbor in [n for n in ref_graph.neighbors(u) if n not in searched]:

                    # Get the length to the neighbor, get the minimum if it is a MultiGraph
                    neighbor_edge_data = ref_graph.get_edge_data(u, neighbor)
                    neighbor_edge_length = min(attrs['length'] for attrs in neighbor_edge_data.values())

                    if (node_ordering[neighbor] > node_ordering[u] and
                    du + neighbor_edge_length < distance_queue.get(neighbor , float('inf'))):
                        distance_queue[neighbor] = du + neighbor_edge_length

            # Remove the bogus transit nodes using post-search-stalling
            # Iterate in reverse order to avoid index error
            for i in range(len(current_access_nodes) - 1, -1, -1):
                for j in range(len(current_access_nodes) - 1, i, -1):

                    # Get a pair of candidates transit nodes
                    t1, t1_distance = current_access_nodes[i]
                    t2, t2_distance = current_access_nodes[j]

                    if t1_distance + distance_table[frozenset([t1, t2])] <= t2_distance:
                        # Use pop() with index to avoid skipping
                        current_access_nodes.pop(j)

            # Store this auxiliary data associated with this non-transit node
            access_nodes[node] = current_access_nodes
            search_space[node] = current_search_space

    return access_nodes, search_space


def ch_based_tnr_query(source, target, ref_graph, distance_table, access_nodes, search_space, transit_nodes):
    """
    Returns the shortest path distance from a source node to a target node.
    """

    path_length = float('inf')

    if source == target:
        # If source and target is the same
        path_length = 0

    elif source in transit_nodes and target in transit_nodes:
        # If both nodes are transit nodes, then just return table entry
        path_length = distance_table[frozenset([source, target])]

    elif source in transit_nodes:
        # If only source is a transit node, only to loop up one table
        for t_an in access_nodes[target]:
            if t_an[1] + distance_table[frozenset([source, t_an[0]])] < path_length:
                path_length = t_an[1] + distance_table[frozenset([source, t_an[0]])]

    elif target in transit_nodes:
        # If only target is a transit node
        for s_an in access_nodes[source]:
            if s_an[1] + distance_table[frozenset([s_an[0], target])] < path_length:
                path_length = s_an[1] + distance_table[frozenset([s_an[0], target])]

    elif search_space[source].isdisjoint(search_space[target]):
        # If none of the nodes are transit node, then use TNR
        # (Global) Look up the tables and find the shortest distance

        # Iterate through all the combinations of access nodes
        # to find the minimum value combination
        for s_an in access_nodes[source]:
            for t_an in access_nodes[target]:
                if s_an[1] + t_an[1] + distance_table[frozenset([s_an[0], t_an[0]])] < path_length:
                    path_length = s_an[1] + t_an[1] + distance_table[frozenset([s_an[0], t_an[0]])]
    else:
        # (Local) Use regular bidirecitonal Dijkstra to find the distance
        path_length, path = nx.bidirectional_dijkstra(ref_graph, source, target, weight="length")

    return path_length
