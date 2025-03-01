import os
import osmnx as ox
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import box

# Define file paths
graphml_path = "colorado_springs.graphml"
plot_path = "colorado_springs_grid_overlay.png"

# Check if the graph already exists, if not, download and save it
if not os.path.exists(graphml_path):
    print("Downloading Colorado Springs road network...")
    G = ox.graph.graph_from_place("Colorado Springs, Colorado, USA", network_type="drive")
    ox.io.save_graphml(G, filepath=graphml_path)
else:
    print("Loading saved Colorado Springs road network...")
    G = ox.io.load_graphml(graphml_path)

# Reproject the graph to Web Mercator (EPSG:3857) for proper alignment
G = ox.project_graph(G, to_crs="EPSG:3857")

# Get graph bounding box
nodes, edges = ox.graph_to_gdfs(G)
nodes = nodes.to_crs(epsg=3857)
edges = edges.to_crs(epsg=3857)
xmin, ymin, xmax, ymax = nodes.total_bounds

# Define grid size in meters (adjust as needed)
grid_size = 2000  # 2000m = 2km per cell

# Compute number of rows and columns
rows = int((ymax - ymin) / grid_size)
cols = int((xmax - xmin) / grid_size)

# Generate grid cells
grid_cells = []
for i in range(cols):  # Removed +1
    for j in range(rows):  # Removed +1
        x1, x2 = xmin + i * grid_size, xmin + (i + 1) * grid_size
        y1, y2 = ymin + j * grid_size, ymin + (j + 1) * grid_size
        grid_cells.append(box(x1, y1, x2, y2))

# Convert grid to GeoDataFrame
grid_gdf = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:3857")

# Debugging prints
print(f"Bounding Box: xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}")
print(f"Grid Size: {grid_size}m | Rows: {rows}, Cols: {cols}")
print(grid_gdf.head())  # Print first few grid cells

# Plot the graph
fig, ax = plt.subplots(figsize=(10, 10))

# Manually set plot limits to ensure the grid is visible
ax.set_xlim([xmin, xmax])
ax.set_ylim([ymin, ymax])

# Plot road network with small nodes
ox.plot.plot_graph(G, ax=ax, show=False, node_size=5, edge_color="gray", node_color="green")

# Overlay grid cells
grid_gdf.boundary.plot(ax=ax, color="red", linewidth=2, linestyle="--")

# Save the plot
fig.savefig(plot_path, dpi=300, bbox_inches="tight")
print(f"Graph plot with grid overlay saved as {plot_path}")

