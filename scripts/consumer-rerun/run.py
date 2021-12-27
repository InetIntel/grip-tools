import argparse
import subprocess


def build_bgpcorsaro_command(event_type, start, until, cache=0):
    consumer_command = ""
    cache_param = ""
    if cache!=0:
        cache_param = "-w {}".format(cache)
    subdir="{}-{}".format(start,until)

    if event_type == "moas":
        consumer_command = "moas {} -o /oasis/projects/nsf/sds183/mingwei/grip/run/results/moas". format(cache_param)
    elif event_type == "submoas":
        consumer_command = "subpfx -m submoas -o /oasis/projects/nsf/sds183/mingwei/grip/run/results/submoas".format()
    elif event_type == "defcon":
        consumer_command = "subpfx -m defcon -o /oasis/projects/nsf/sds183/mingwei/grip/run/results/defcon".format()
    elif event_type == "edges":
        consumer_command = "edges {} -o /oasis/projects/nsf/sds183/mingwei/grip/run/results/edges".format(cache_param)
    elif event_type == "pfx-origins":
        consumer_command = "pfx-origins -o /oasis/projects/nsf/sds183/mingwei/grip/run/results/pfx-origins".format(cache_param)
    else:
        raise ValueError("unknown event_type: {}".format(event_type))

    return  [
        "/oasis/projects/nsf/sds183/mingwei/grip/env/bin/bgpview-consumer",
        "-i", "bsrt -i300 -P 86400 -p routeviews -p ris -w{},{} -a -O/tmp/deleteme.%X".format(start,until),
        "-b", "ascii",
        "-c", "visibility",
        "-c", consumer_command,
    ]

def extract_process_range(start, until, p_total, p_id, cache=86400):
    assert(isinstance(start, int))
    assert(isinstance(until, int))
    assert(isinstance(p_total, int))
    assert(isinstance(p_id, int))

    total_time = until - start
    per_process_time = total_time / p_total

    p_start = start + per_process_time * p_id
    p_end = p_start + per_process_time
    p_start = p_start - cache

    return p_start, p_end


def main():
    parser = argparse.ArgumentParser(
        description="Utility to listen for new events and trigger active measurements.")
    parser.add_argument('-t', "--type", nargs="?", required=True,
                        help="Event type to listen for")
    parser.add_argument("-s", "--start_ts", type=int, nargs="?", required=True,
                        help="start time for rerun (unix time)")
    parser.add_argument("-e", "--end_ts", type=int, nargs="?", required=True,
                        help="end time for rerun (unix time)")
    parser.add_argument("-T", "--total_processes", type=int, nargs="?", required=True,
                        help="total number of processes to divide the ranges")
    parser.add_argument("-i", "--process_id", type=int, nargs="?", required=True,
                        help="the id of the current process, start from 0")
    parser.add_argument("-c", "--cache_time", type=int, nargs="?", required=False, default=86400,
                        help="cache time in seconds, default 86400 (1 day)")
    parser.add_argument("-d", "--dry_run", default=False, action="store_true",
                        help="dry run the script")
    opts = parser.parse_args()

    p_start, p_end = extract_process_range(opts.start_ts, opts.end_ts, opts.total_processes, opts.process_id, opts.cache_time)

    command = build_bgpcorsaro_command(opts.type, p_start, p_end, opts.cache_time)
    print("to run:")
    print("{}".format(command))
    # subprocess.call(["ls", "-ls"])
    if opts.dry_run:
        return
    subprocess.call(command)

if __name__=="__main__":
    main()