import re
import os
import argparse

import numpy as np
from scipy.stats import gmean
import matplotlib.pyplot as plt


def plot_charts(outdir, filenames, data, labels):
    if not filenames:
        print("No valid data to plot.")
        return

    plt.figure(figsize=(16, 10))

    for i in range(0, len(data)):
        plt.plot(
            filenames,
            data[i]["ipc_values"],
            marker="o",
            label=f'{labels[i]}, gmean IPC = {data[i]["gmean_ipc"]}',
        )

    plt.title("Cumulative IPC by file")
    plt.xlabel("File Name")
    plt.ylabel("Cumulative IPC")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{outdir}/ipc_predictors_plot.png")
    plt.close()
    print(f"IPC plot saved as {outdir}/ipc_predictors_plot.png")

    # MPKI
    plt.figure(figsize=(16, 10))

    for i in range(0, len(data)):
        plt.plot(
            filenames,
            data[i]["mpki_values"],
            marker="o",
            label=f'{labels[i]}, gmean MPKI = {data[i]["gmean_mpki"]}',
        )

    plt.title("MPKI by file")
    plt.xlabel("File Name")
    plt.ylabel("MPKI")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{outdir}/mpki_predictors_plot.png")
    plt.close()
    print(f"MPKI plot saved as {outdir}/mpki_predictors_plot.png")


def extract_ipc_and_mpki(data):
    ipc_pattern = r"CPU 0 cumulative IPC:\s*([\d.]+)"
    mpki_pattern = r"MPKI:\s*([\d.]+)"

    ipc_match = re.search(ipc_pattern, data)
    mpki_match = re.search(mpki_pattern, data)

    ipc = float(ipc_match.group(1)) if ipc_match else None
    mpki = float(mpki_match.group(1)) if mpki_match else None

    return ipc, mpki


def read_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return None


def process_directory(directory_path):
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return

    filenames = []
    ipc_values = []
    mpki_values = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        print(f"\nProcessing file: {filename}")

        data = read_file(file_path)
        ipc, mpki = extract_ipc_and_mpki(data)

        filenames.append(filename)
        ipc_values.append(ipc)
        mpki_values.append(mpki)

        print(f"Cumulative IPC: {ipc}")
        print(f"MPKI: {mpki}")

    gmean_ipc = np.round(gmean(ipc_values), 3)
    gmean_mpki = np.round(gmean(mpki_values), 3)

    result = {
        "ipc_values": ipc_values,
        "mpki_values": mpki_values,
        "gmean_ipc": gmean_ipc,
        "gmean_mpki": gmean_mpki,
    }

    return filenames, result


def setup_argparser():
    parser = argparse.ArgumentParser(description="Branch predictors comparator")
    parser.add_argument(
        "--bimodal_dir", required=True, help="Directory path for bimodal predictor data"
    )
    parser.add_argument(
        "--markov_dir", required=True, help="Directory path for Markov predictor data"
    )
    parser.add_argument(
        "--prob_markov_dir",
        required=True,
        help="Directory path for probabilistic Markov predictor data",
    )
    parser.add_argument(
        "--images_dir", required=True, help="Directory path for output images"
    )
    return parser.parse_args()


def main():
    args = setup_argparser()
    filenames_b, bimodal_result = process_directory(args.bimodal_dir)
    filenames_m, markov_result = process_directory(args.markov_dir)
    filenames_pm, prob_markov_result = process_directory(args.prob_markov_dir)

    # Assert that filenames list are identical across all directories
    assert len(filenames_b) == len(filenames_m)
    assert len(filenames_b) == len(filenames_pm)
    for i in range(0, len(filenames_b)):
        assert filenames_b[i] == filenames_m[i]
        assert filenames_b[i] == filenames_pm[i]

    os.makedirs(args.images_dir, exist_ok=True)

    results = [bimodal_result, markov_result, prob_markov_result]
    labels = ["Bimodal", "Markov", "Probabilistic markov"]

    plot_charts(args.images_dir, filenames_b, results, labels)


if __name__ == "__main__":
    main()
