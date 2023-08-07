"""
This script reads in a LFRic benchmarking timer file and plots the top
most costly routine calls as a histogram plot.
"""

import matplotlib.pyplot as plt
import pandas as pd
import argparse
import json

from pathlib import Path
from io import StringIO


def timer_file_to_dataframe(timer_file_path: str) -> pd.DataFrame:
    """
    This function reads in a LFRic timer file into a pandas data frame

    Parameters
    ----------
    timer_file_path : str
        Path to LFRic timer file

    Returns
    -------
    pd.Dataframe :
        A pandas dataframe containing LFRic timer file data
    """

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


def generate_most_expensive_cost_plot(
    timer_file_path: str,
    output_file_name: str,
    plot_label: str,
    top_number: int,
) -> None:
    """
    This method creates a histogram plot of the top most costly routine calls.

    Parameters
    ----------
    timer_file_path : str
        Path to LFRic timer file
    output_file_name : str
        Path to output file name
    plot_label : str
        A plot label for plot title string
    top_number : int
        No of most expensive routines to plot.
    """

    # Process the LFRic timer file into a pandas data frame
    df = timer_file_to_dataframe(timer_file_path=timer_file_path)

    # Sort the dataframe in descending order of expensive routine calls
    df.sort_values(by=["mean time(s)"], inplace=True, ascending=False)

    # Create a bar chart of the most expensive routine calls
    routine = df["Routine"].head(top_number)
    compute_cost = df["mean time(s)"].head(top_number)

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
    title = "Mean time (s) for " + plot_label
    ax.set_title(title, loc="left")

    # Save plot to file
    plt.savefig(output_file_name + ".png")

    # Close the plot
    plt.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_map_path", help="Path to config timings map file", type=str
    )
    parser.add_argument(
        "-t",
        "--top_number",
        help="Number of top most expensive routines to plot",
        type=int,
        default=15,
    )

    args = parser.parse_args()

    with open(Path(args.config_map_path)) as file:
        config_map = json.load(file)

    for count, config in enumerate(config_map):
        timer_file_path = config_map[config]
        image_file_name = "benchmark_plot_" + str(count)
        generate_most_expensive_cost_plot(
            timer_file_path=Path(timer_file_path),
            output_file_name=image_file_name,
            plot_label=config,
            top_number=args.top_number,
        )
