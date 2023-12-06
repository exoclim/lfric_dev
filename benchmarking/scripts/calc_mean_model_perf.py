#!/usr/bin/env python
"""Read LFRic timer.txt file(s) and calculate model performance."""
import json
from glob import glob
from pathlib import Path
from typing import Optional

import click
import pandas as pd
from benchmark_plot import timer_file_to_dataframe


def load_as_single_dataframe(inp_path: str):
    """Read LFRic timer.txt file(s) as a single data frame."""
    files = glob(inp_path)
    frames = []
    for file in files:
        frames.append(timer_file_to_dataframe(file))
    return pd.concat(frames)


@click.command()
@click.option("-i", "--inp_path", type=str, help="Input directory(ies)")
@click.option("-d", "--days", type=float, help="Number of days per job")
@click.option("-e", "--executable", default="lfric_atm", type=str, help="Executable")
def main(inp_path: str, days: float, executable: Optional[str] = "lfric_atm"):
    """Main entry."""
    full_frame = load_as_single_dataframe(inp_path)
    n_steps = int(
        full_frame[full_frame.Routine.str.endswith("semi_implicit_timestep_alg")][
            "No. calls"
        ].values[0]
    )

    main_exec_stats = full_frame[full_frame.Routine.str.endswith(executable)]
    time_per_job = main_exec_stats["mean time(s)"].mean()

    stats = {
        "per job (s)": time_per_job,
        "per model day (min)": time_per_job / days / 60,
        "per time step (s)": time_per_job / n_steps,
        "throughput (day/day)": 86400 / (time_per_job / days),
    }
    inp_parts = Path(inp_path).parts
    stats_file_name = Path(f"{executable}_perf__{inp_parts[-5]}__{inp_parts[-2]}.json")
    with stats_file_name.open("w") as f_out:
        json.dump(stats, f_out, indent=4)

    for key, value in stats.items():
        print(f"{key:>20}: {value:.2f}")


if __name__ == "__main__":
    main()
