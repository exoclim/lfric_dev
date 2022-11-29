import matplotlib.pyplot as plt
import pandas as pd
import argparse

from pathlib import Path
from io import StringIO

if __name__ == "__main__":
    """This script reads in a LFRic benchmarking timer file and plots the top
    15 most costly routine calls as a histogram plot."""

    parser = argparse.ArgumentParser()
    parser.add_argument("timer_file_path", help="Location path to timer file")
    args = parser.parse_args()

    # Process the LFRic timer file into a pandas data frame
    timer_file_path = Path(args.timer_file_path)
    with open(timer_file_path, "r") as file:
        data = file.read()
        data = data.replace("||", ",")
        data = data.replace("=", "")
    df = pd.read_csv(StringIO(data), sep=",", header=0)
    df = df.iloc[:, 1:-1]
    headings_dict = {}
    for heading in df.columns:
        headings_dict[heading] = heading.strip()
    df.rename(columns=headings_dict, inplace=True)

    # Sort the dataframe in descending order of expensive routine calls
    df.sort_values(by=["mean time(s)"], inplace=True, ascending=False)

    # Create a bar chart of the 15 most expensive routine calls
    routine = df["Routine"].head(15)
    compute_cost = df["mean time(s)"].head(15)

    # Figure Size
    fig, ax = plt.subplots(figsize=(16, 9))

    # Horizontal Bar Plot
    ax.barh(routine, compute_cost)

    # Remove axes splines
    for s in ["top", "bottom", "left", "right"]:
        ax.spines[s].set_visible(False)

    # Remove x, y Ticks
    ax.xaxis.set_ticks_position("none")
    ax.yaxis.set_ticks_position("none")

    # Add x, y gridlines
    ax.grid(visible=True, color="grey", linestyle="-.", linewidth=0.5, alpha=0.2)

    # Add Plot Title
    ax.set_title("Mean time (s)", loc="left")

    # Save plot to file
    plt.savefig("benchmark_plot.png")
