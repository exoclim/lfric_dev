import matplotlib.pyplot as plt
import pandas as pd
import argparse
import json

from pathlib import Path
from io import StringIO


def timer_file_to_dataframe(timer_file_path):
    """This method read in a LFRic timer file into a pandas data frame"""

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

    return df


def generate_most_expensive_cost_plot(timer_file_path, output_file_name):
    """This method generates a plot of the top 15 most costly routine
    calls as a histogram plot."""

    # Process the LFRic timer file into a pandas data frame
    df = timer_file_to_dataframe(timer_file_path=timer_file_path)

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
    plt.savefig(output_file_name + ".png")


if __name__ == "__main__":
    """This script reads in a LFRic benchmarking timer file and plots the top
    15 most costly routine calls as a histogram plot."""

    parser = argparse.ArgumentParser()
    parser.add_argument("timer_file_path", help="Path to config timings map file")
    parser.add_argument("output_file_name", help="Path to config timings map file")
    args = parser.parse_args()

    generate_most_expensive_cost_plot(
        timer_file_path=Path(args.timer_file_path),
        output_file_name=args.output_file_name,
    )
