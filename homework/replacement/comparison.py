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

    fig, ax = plt.subplots(1, 1, figsize=(6, 5))

    for i in range(0, len(data)):
        gmean = data[labels[i]]["gmean_miss"]

        ax.bar(
            labels[i],
            data[labels[i]]["gmean_miss"],
            label=f"{labels[i]}, gmean miss {gmean}",
        )


    ax.set_ylabel("L2 gmean miss rate")
    ax.set_xlabel("label")
    ax.set_title("L2 gmean miss rate by replacement policy")
    ax.legend()
    ax.grid(True)
    plt.yticks(np.arange(0,1,0.1))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(f"{outdir}/replacement_misses.png")
    plt.close()


def extract_miss_and_access(data):
    match = re.search(r'cpu0->cpu0_L2C TOTAL\s+ACCESS:\s+(\d+)\s+HIT:\s+\d+\s+MISS:\s+(\d+)', data)
    
    miss = float(match.group(2)) if match else None
    access = float(match.group(1)) if match else None

    return miss, access


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


def gmean(iterable):
    return np.exp(np.log(iterable).mean())
    
def process_directory(directory_path):
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return

    filenames = []
    miss_rates = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        print(f"\nProcessing directory {directory_path}")
        print(f"\nProcessing file: {filename}")

        data = read_file(file_path)
        miss, access = extract_miss_and_access(data)
        if (miss == None or access == None):
            raise Exception(f"Failed to extract MISS for file {file_path}")

        filenames.append(filename)
        miss_rates.append(miss / access)

        print(f"miss: {miss}")
        print(f"access: {access}")
        print(f"miss rate: {miss / access}")

    gmean_miss = np.round(gmean(miss_rates), 6)

    results = {
        "miss_rate_values": miss_rates,
        "gmean_miss": gmean_miss,
    }

    return filenames, results


def setup_argparser():
    parser = argparse.ArgumentParser(description="Replacement comparator")
    parser.add_argument(
        "--replacement_dir", required=True, help="Directory path for replacement dir with subdirectories with policies"
    )
    parser.add_argument(
        "--images_dir", required=True, help="Directory path for output images with charts"
    )
    return parser.parse_args()


def collect_labels_and_data_dirs(directory_path):
    labels = []
    data_dirs = []

    for d in os.listdir(directory_path):
        full_path = os.path.join(directory_path, d)
        if os.path.isdir(full_path):
            labels.append(d)  # Subdirectory name as label
            out_path = os.path.join(full_path, "out")
            data_dirs.append(out_path)

    return labels, data_dirs


def main():
    args = setup_argparser()

    labels, data_dirs = collect_labels_and_data_dirs(args.replacement_dir)

    filenames = []
    results = {}

    for idx in range(len(data_dirs)):
        filenames, res = process_directory(data_dirs[idx])
        results[labels[idx]] = res

    os.makedirs(args.images_dir, exist_ok=True)

    plot_charts(args.images_dir, filenames, results, labels)


if __name__ == "__main__":
    main()
