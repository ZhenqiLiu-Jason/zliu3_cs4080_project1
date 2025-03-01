import os
import osmnx as ox
import matplotlib.pyplot as plt

# Define file paths
graphml_path = "colorado_springs.graphml"
plot_path = "colorado_springs_graph.png"

# Check if the graph already exists, if not, download and save it
if not os.path.exists(graphml_path):
    print("Downloading Colorado Springs road network...")
    G = ox.graph.graph_from_place("Colorado Springs, Colorado, USA", network_type="drive")
    ox.io.save_graphml(G, filepath=graphml_path)  # Updated saving method
else:
    print("Loading saved Colorado Springs road network...")
    G = ox.io.load_graphml(graphml_path)  # Updated loading method

# Plot the graph
fig, ax = ox.plot.plot_graph(G, show=False, save=False, node_size=5)

# Save the plot
fig.savefig(plot_path, dpi=300, bbox_inches="tight")
print(f"Graph plot saved as {plot_path}")

