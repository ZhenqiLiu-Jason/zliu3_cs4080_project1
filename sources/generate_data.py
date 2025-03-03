import time
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

        # Run some query and compute the average time
        all_nodes = list(G.nodes)
        trial_runs = []
        for _ in range(num_query_trials):
            source = random.choice(all_nodes)
            target = random.choice(all_nodes)

            # Calculate the time used for TNR qeury
            start_time = time.perf_counter()
            ch_based_tnr_query(source, target, G, distance_table, 
                    access_nodes, search_space, transit_nodes)
            end_time = time.perf_counter()

            trial_runs.append(end_time - start_time)

        # Store the average query time
        average_query_times.append(statistics.mean(trial_runs))
        
    x_axis = np.array(percent_transit_nodes)
    average_query_times_result["TNR Query Time"] = (x_axis, np.array(average_query_times), '-')
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


def get_transit_node_search_space_plot():



    place_name = "Boulder, Colorado, USA"
    G = get_graph(place_name, undirected=True)

    run_experiments(G, [5, 10, 20, 50, 80], get_edge_diff)

    result = preprocess(G, 20, get_edge_diff)
    G = result[0]
    ordering = result[1]
    shortcuts = result[2]
    transit_nodes = result[3]
    distance_table = result[4]
    access_nodes = result[5]
    search_space = result[6]


    # Run some queries
    all_nodes = list(G.nodes)
    source = random.choice(all_nodes)
    target = random.choice(all_nodes)

    print(f"Source - {source}")
    print(f"Target - {target}")

    correct_answer, _ = nx.bidirectional_dijkstra(G, source, target, weight="length")
    print(f"Correct Answer is: {correct_answer}")

    tnr_answer = ch_based_tnr_query(source, target, G, distance_table, access_nodes, search_space, transit_nodes)
    print(f"TNR Answer is: {tnr_answer}")

    print(f"# nodes = {G.number_of_nodes()}")
    print(f"# shortcuts = {shortcuts.number_of_edges()}")



    # Create a color map: red for transit nodes, gray for others
    node_colors = ['red' if node in transit_nodes else 'gray' for node in G.nodes]
    # Draw the original graph with highlighted transit nodes
    fig, ax = plt.subplots(figsize=(10, 10))
    ox.plot_graph(G, node_color=node_colors, edge_color='lightgray', node_size=30, ax=ax)
    # Save the plot
    plt.savefig("highlighted_transit_nodes.png")
    plt.clf()

    non_transit_nodes = [node for node in all_nodes if node not in transit_nodes]
    node_to_search = random.choice(non_transit_nodes)
    node_colors = ['green' if node in search_space[node_to_search] else 'gray' for node in G.nodes]
    fig, ax = plt.subplots(figsize=(10, 10))
    ox.plot_graph(G, node_color=node_colors, edge_color='lightgray', node_size=30, ax=ax)
    plt.savefig("highlighted_search_nodes.png")
    plt.clf()





place_name = "Boulder, Colorado, USA"
G = get_graph(place_name, undirected=True)

run_experiments(G, [5, 10, 20, 50, 80], get_edge_diff)

