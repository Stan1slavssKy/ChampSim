import os
import argparse

from multiprocessing import Pool

CHAMPSIM_BIN = "./bin/champsim"
WARMUP_INSTRUCTIONS = 10_000_000
SIMULATION_INSTRUCTIONS = 50_000_000


def run_trace(args):
    trace_file, tracedir, outdir = args
    trace_path = os.path.join(tracedir, trace_file)
    output_path = os.path.join(outdir, f"{trace_file}.txt")
    cmd = f"{CHAMPSIM_BIN} --warmup_instructions {WARMUP_INSTRUCTIONS} --simulation_instructions {SIMULATION_INSTRUCTIONS} {trace_path} > {output_path}"
    print(f"Run cmd: {cmd}")
    os.system(cmd)


def setup_argparser():
    parser = argparse.ArgumentParser(description="ChampSim runner")
    parser.add_argument("--tracedir", required=True, help="Directory with traces")
    parser.add_argument("--outdir", required=True, help="Output directory")
    return parser.parse_args()


def main():
    args = setup_argparser()

    os.makedirs(args.outdir, exist_ok=True)

    traces = [f for f in os.listdir(args.tracedir) if f.endswith(".champsimtrace.xz")]
    task_args = [(trace, args.tracedir, args.outdir) for trace in traces]

    with Pool() as pool:
        pool.map(run_trace, task_args)


if __name__ == "__main__":
    main()
