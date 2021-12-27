#  This software is Copyright (c) 2015 The Regents of the University of
#  California. All Rights Reserved. Permission to copy, modify, and distribute this
#  software and its documentation for academic research and education purposes,
#  without fee, and without a written agreement is hereby granted, provided that
#  the above copyright notice, this paragraph and the following three paragraphs
#  appear in all copies. Permission to make use of this software for other than
#  academic research and education purposes may be obtained by contacting:
#
#  Office of Innovation and Commercialization
#  9500 Gilman Drive, Mail Code 0910
#  University of California
#  La Jolla, CA 92093-0910
#  (858) 534-5815
#  invent@ucsd.edu
#
#  This software program and documentation are copyrighted by The Regents of the
#  University of California. The software program and documentation are supplied
#  "as is", without any accompanying services from The Regents. The Regents does
#  not warrant that the operation of the program will be uninterrupted or
#  error-free. The end-user understands that the program was developed for research
#  purposes and is advised not to rely exclusively on the program for any reason.
#
#  IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
#  DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST
#  PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF
#  THE UNIVERSITY OF CALIFORNIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
#  DAMAGE. THE UNIVERSITY OF CALIFORNIA SPECIFICALLY DISCLAIMS ANY WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE. THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS
#  IS" BASIS, AND THE UNIVERSITY OF CALIFORNIA HAS NO OBLIGATIONS TO PROVIDE
#  MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.

import argparse
import logging

import json
import wandio

from bgphijacks.utils.swift import SwiftUtils


def find_fill_missing_events(tagger_file, traceroute_file):
    lines = []
    ids = set()

    count = 0
    empty_line = False
    if traceroute_file is None:
        logging.info("no traceroute_file found, skip reading")
    else:
        with wandio.open(traceroute_file) as fin:
            logging.info("caching traceroute_file: %s", traceroute_file)
            for line in fin:
                # receive event from swift file
                if line.startswith("#"):
                    continue
                if not line or line.isspace():
                    # if emptyline found, rewrite the file
                    empty_line = True
                    continue
                event_dict = json.loads(line)
                ids.add(event_dict["id"])
                lines.append(line.strip())
                count += 1
            logging.info("read {} events".format(count))

    count = 0
    found_missing = 0
    with wandio.open(tagger_file) as fin:
        logging.info("reading tagger_file: %s", tagger_file)
        for line in fin:
            # receive event from swift file
            if line.startswith("#") or not line or line.isspace():
                continue
            event_dict = json.loads(line)
            event_id = event_dict["id"]
            if event_id not in ids:
                # this event is in tagger file but not in traceroute file
                # logging.info("found missing event: {}".format(line))
                lines.append(line.strip())
                found_missing += 1
            count += 1
        logging.info("read {} events".format(count))

    if found_missing > 0 or empty_line:
        if empty_line:
            logging.info("found empty line in traceroute file, rewrite it")
        if traceroute_file is None:
            # if no traceroute_file is provided, construct one first
            traceroute_file = tagger_file.replace("events", "traceroutes")
        logging.info("updating traceroute file: {}".format(traceroute_file))
        with wandio.open(traceroute_file, "w") as fout:
            for line in lines:
                fout.write("%s\n" % line)


def main():
    parser = argparse.ArgumentParser(
        description="Fix/refill any events missing in active probing result files")

    parser.add_argument("-t", "--type", nargs="?", required=True,
                        help="event type")
    parser.add_argument("-s", "--start_ts", type=int, nargs="?", required=True,
                        help="start time for rerun (unix time)")
    parser.add_argument("-e", "--end_ts", type=int, nargs="?",
                        help="end time for rerun (unix time)")

    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)
    opts = parser.parse_args()

    event_type = opts.type

    tagger_container = "bgp-hijacks-{}-events".format(event_type)
    traceroute_container = "bgp-hijacks-{}-traceroutes".format(event_type)

    swift = SwiftUtils()
    tagger_files = swift.swift_files_generator(tagger_container)
    traceroute_files = swift.swift_files_generator(traceroute_container)
    traceroute_dict = {}
    for f in traceroute_files:
        traceroute_dict[int(f.split("/")[5].split('=')[1])] = f
    for tagger_file in tagger_files:
        ts = int(tagger_file.split("/")[5].split('=')[1])
        if opts.start_ts and ts < opts.start_ts:
            continue
        if opts.end_ts and ts < opts.end_ts:
            continue

        tagger_file = "swift://%s/%s" % (tagger_container, tagger_file)
        if ts not in traceroute_dict:
            logging.error("missing file for {}".format(ts))
            traceroute_file = None
        else:
            traceroute_file = "swift://%s/%s" % (traceroute_container, traceroute_dict[ts])

        find_fill_missing_events(tagger_file, traceroute_file)


if __name__ == "__main__":
    main()
