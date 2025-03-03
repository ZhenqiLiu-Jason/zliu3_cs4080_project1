import time
import math
import statistics
import os
import numpy as np
import random
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

from savefigure import save_plot
from get_graph import get_graph
from ch_based_tnr_algo import *


def preprocess(ref_graph, k_percent, heuristic, online=True):
    """
    Run all the TNR preprocessing steps and return all the auxiliary data.
    """
    
    # First, get the node ordering and all the shortcuts from CH
    ordering, shortcuts = get_ordering_shortcut(ref_graph, heuristic, online)

    # Union the original graph with the shortcuts
    ref_graph = nx.compose(ref_graph, shortcuts)

    # Get transit nodes and the distance table among them
    transit_nodes = get_transit_nodes(ordering, ref_graph.number_of_nodes() * k_percent // 100)
    distance_table = get_transit_nodes_distance(ref_graph, transit_nodes)

    # Get access nodes for non-transit nodes
    access_nodes, search_space = get_access_nodes(ref_graph, ordering, transit_nodes, distance_table)

    return ref_graph, ordering, shortcuts, transit_nodes, distance_table, access_nodes, search_space


def run_experiments(ref_graph, percent_transit_nodes, heuristic, online=True, num_query_trials=50):
    """
    Run experiments on how much time it would take to preprocess everything
    with a specified percent number of transit nodes.
    """

    # Create the directory, including any intermediate directories
    os.makedirs('../images', exist_ok=True)

    preprocessing_times_result = {}
    preprocessing_times = []

    average_query_times_result = {}
    average_query_times = []
    average_bidi_query_times = []

    # Run preprocessing for each number of transit nodes
    for k_percent in percent_transit_nodes:

        start_time = time.perf_counter()
        preprocess_result = preprocess(ref_graph, k_percent, heuristic, online)
        end_time = time.perf_counter()

        preprocessing_times.append(end_time - start_time)

        # Now run some query to find the average query time
        G = preprocess_result[0]
        ordering = preprocess_result[1]
        shortcuts = preprocess_result[2]
        transit_nodes = preprocess_result[3]
        distance_table = preprocess_result[4]
        access_nodes = preprocess_result[5]
        search_space = preprocess_result[6]

        # Generate a plot containing the transit nodes
        # and the search space for a randomly selected node
        all_nodes = list(G.nodes)
        non_transit_nodes = [node for node in all_nodes if node not in transit_nodes]
        select_search_space = search_space[random.choice(non_transit_nodes)]

        # Assign colors based on the type of node
        node_colors = ['red' if node in transit_nodes else 'green' if 
                node in select_search_space else 'blue' for node in all_nodes]

        file_name = f'../images/deliverable2_search_space{k_percent}.png'

        # Plot graph with custom node colors and save to file
        fig, ax = ox.plot_graph(
            ref_graph,
            node_color=node_colors,
            node_size=10,
            edge_linewidth=0.5,
            bgcolor='white',
            save=True,
            filepath=file_name,
            dpi=600
        )

        plt.clf()
        plt.close()

        # Run some query and compute the average time
        trial_runs = []
        trial_runs_bidi = []
        for _ in range(num_query_trials):
            source = random.choice(all_nodes)
            target = random.choice(all_nodes)

            # Calculate the time used for TNR qeury
            start_time = time.perf_counter()
            path_length = ch_based_tnr_query(source, target, G, distance_table, 
                    access_nodes, search_space, transit_nodes)
            end_time = time.perf_counter()

            trial_runs.append(end_time - start_time)

            # Calculate the time used for BiDi query
            start_time = time.perf_counter()
            path_length_bidi, _ = nx.bidirectional_dijkstra(G, 
                    source, target, weight='length')
            end_time = time.perf_counter()

            trial_runs_bidi.append(end_time - start_time)

            # Check the output, make sure they agree
            if math.isclose(path_length, path_length_bidi, rel_tol=1e-9, abs_tol=0.0):
                print(f"{source} -- {target}: Results Agree")
            else:
                raise ValueError(f"(TNR){path_length} != (BiDi){path_length_bidi}")

        # Store the average query time
        average_query_times.append(statistics.mean(trial_runs))
        average_bidi_query_times.append(statistics.mean(trial_runs_bidi))
        
    x_axis = np.array(percent_transit_nodes)
    average_query_times_result["TNR Query Time"] = (x_axis, np.array(average_query_times), '-')
    average_query_times_result["BiDi Query Time"] = (x_axis, np.array(average_bidi_query_times), '-')
    preprocessing_times_result["Preproccesing Time"] = (x_axis, np.array(preprocessing_times), '-')

    # Plot the result and save
    if online:
        save_plot(preprocessing_times_result,
            filename='../images/deliverable2_preprocessing_time.png',
            xlabel=r'The percent of total nodes as transit nodes',
            ylabel=r'Preprocessing Time',
            title="Preprocessing Time vs Number of Transit Nodes",
            y_bot_lim=0,
            annotation=False)

        save_plot(average_query_times_result,
            filename='../images/deliverable2_average_query_time.png',
            xlabel=r'The percent of total nodes as transit nodes',
            ylabel=r'Average Query Time',
            title="Average Query Time vs Number of Transit Nodes",
            y_bot_lim=0,
            annotation=False)



# Start the main execution
# Using undirected graphs for simplier implementation
place_name = "Boulder, Colorado, USA"
G = get_graph(place_name, undirected=True)

# A list of percentages for transit nodes
percent_transit_nodes = [5, 10, 20, 50, 80]

# Run experiment
run_experiments(G, percent_transit_nodes, get_edge_diff)
