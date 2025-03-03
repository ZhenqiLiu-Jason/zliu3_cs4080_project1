import numpy as np
import matplotlib.pyplot as plt
from adjustText import adjust_text

# Function to save plots
def save_plot(traces, filename, xlabel, ylabel, title, y_top_lim=None, y_bot_lim=None, annotation=True):
    """
    traces contain the following:

    key: a label for this trace
    value: a tuple of this structure:
        (np.array-x, np.array-y, 'linestyle')
    """

    if not traces:
        raise ValueError("The traces dictionary is empty; add data to plot.")


    plt.figure(figsize=(5, 4), dpi=600)

    texts = []

    # Plot all the traces from the dictionary
    for key, (x_vals, y_vals, linestyle) in traces.items():
        plt.plot(x_vals, y_vals, label=key,linestyle=linestyle, linewidth=2.5)

        # Add text annotations without overlap
        if annotation:
            texts.append(plt.text(
                x_vals[-1], y_vals[-1], 
                key, fontsize=12))

    # Automatically adjust text annotations to avoid overlap
    adjust_text(texts)

    # Adjust the vertical axis limits
    plt.ylim(top=y_top_lim, bottom=y_bot_lim)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)

    # Ensures the layout doesn't have overlapping elements
    plt.tight_layout()

    # Append '.png' if no file extension is provided
    if not filename.endswith('.png'):
        filename += '.png'

    plt.savefig(filename)
    plt.close()
