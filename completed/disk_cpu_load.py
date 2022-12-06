import argparse
import os
import re
import subprocess


def cpu_times():
    """Opens the '/proc/stat' file and reads in the cpu line, then splits that
    line into a list of integers representing the different cpu times"""
    with open("/proc/stat", "r") as f:
        cpu = f.readline().strip("\n")
    cpu_load = [int(x) for x in cpu[5:].split(" ")]
    return cpu_load


# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument('device_filename', nargs="?", default="/dev/sda",
                    help="""This is the WHOLE-DISK device filename (with or
                    without "/dev/"), e.g. "sda" or "/dev/sda". The script
                    finds a filesystem on that device, mounts it if necessary,
                    and runs the tests on that mounted filesystem.
                    Defaults to /dev/sda.""")
parser.add_argument('--max-load', type=int, default=30, metavar="<load>",
                    help="""The maximum acceptable CPU load, as a percentage.
                    Defaults to 30.""")
parser.add_argument('--xfer', type=int, default=4096, metavar="<mebibytes>",
                    help="""The amount of data to read from the disk, in
                    mebibytes. Defaults to 4096 (4 GiB).""")
parser.add_argument('--verbose', action="store_true",
                    help="""If present, produce more verbose output""")
args = parser.parse_args()

# Adds "/dev/" if it was omitted
disk_device = re.sub(r"\/dev[\/]+dev\/", "/dev/",
                     f"/dev/{args.device_filename}")
if not os.path.exists(disk_device):
    print(f"Unknown block device {disk_device}")
    parser.print_help()
    exit()

# Start Main Process
print(f"Testing CPU load when reading {args.xfer} MiB from {disk_device}")
print(f"Maximum acceptable CPU load is {args.max_load}")

# Clears disk buffer
subprocess.run(["blockdev", "--flushbufs", f"{disk_device}"])

# Reading from Disk
start_load = cpu_times()
if args.verbose:
    print("Beginning disk read....")
subprocess.run(["dd", f"if={disk_device}", "of=/dev/null",
                "bs=1048576", f"count={args.xfer}"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if args.verbose:
    print("Disk read complete!")
end_load = cpu_times()

# Analyzing CPU Times
start_total = sum(start_load)
end_total = sum(end_load)
diff_total = end_total - start_total
diff_idle = end_load[3] - start_load[3]  # 3rd Entry is idle
diff_used = diff_total - diff_idle
if args.verbose:
    print(f"Start CPU time = {start_total}")
    print(f"End CPU time = {end_total}")
    print(f"CPU time used = {diff_used}")
    print(f"Total elapsed time = {diff_total}")

# Calculating CPU Usage Percentage
if diff_total != 0:
    cpu_load = diff_used*100/diff_total
else:
    cpu_load = 0
print(f"Detected disk read CPU load is {'%.2f'%cpu_load}")
if cpu_load > args.max_load:
    print("*** DISK CPU LOAD TEST HAS FAILED! ***")
