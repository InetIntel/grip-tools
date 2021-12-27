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
import hashlib
import json
import logging
import multiprocessing as mp
import os
from datetime import datetime

import elasticsearch
import filelock as filelock

from bgphijacks.events.event import Event
from bgphijacks.utils.data.elastic import ElasticConn
from bgphijacks.utils.data.elastic_queries import query_in_range


class InferenceRunner:
    def __init__(self, debug):
        self.debug = debug
        self.esconn = ElasticConn()

    def rerun(self, start_ts, end_ts, old_index_pattern):
        """
        Rerun the inference code for the given time period.

        :param missing_inference:
        :param must_not_tags:
        :param must_tags:
        :param start_ts:
        :param end_ts:
        :param tr_worthy: weather to process only traceroute-worthy event
        :param inserted_before: only process events inserted before certain time
        :param inserted_after: only process events inserted after certain time
        :return:
        """
        self._show_time(start_ts, "start")
        self._show_time(end_ts, "end")

        query = query_in_range(start_ts, end_ts, size=10000)
        json.dumps(query, indent=4)
        for event_id in self.esconn.id_generator(index=old_index_pattern, query=query):
            index = self.esconn.infer_index_name_by_id(event_id)
            if not self.esconn.record_exists(index, event_id):
                new_index = index.replace("v3", "v2")
                event = self.esconn.get_event_by_id(event_id, index=new_index)
                assert (isinstance(event, Event))
                try:
                    self.esconn.index_event(event, debug=self.debug)
                except elasticsearch.exceptions.TransportError as error:
                    if error.status_code == 413:
                        # allow continuing the program if certain events are too large
                        logging.warning("event is too large to recommit: {}".format(event.event_id))
                    else:
                        raise error

    @staticmethod
    def _event_in_range(event: Event, before, after):
        if before and event.insert_ts > before:
            return False
        if after and event.insert_ts < after:
            return False
        return True

    @staticmethod
    def _show_time(ts: int, name: str):
        if ts:
            dt_object = datetime.utcfromtimestamp(ts)
            logging.info("{}: {}".format(name, dt_object))


def run_process(debug, start_ts, end_ts, old_index_pattern):
    InferenceRunner(debug) \
        .rerun(start_ts, end_ts, old_index_pattern)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate events to new index")

    parser.add_argument('-i', "--old_index", nargs="?", required=False, default="*",
                        help="old index pattern")

    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)

    parser.add_argument("-d", "--debug", action="store_true", default=False,
                        help="Whether to enable debug mode")
    parser.add_argument("-s", "--start_ts", type=int, nargs="?", required=False,
                        help="start time for rerun (unix time)")
    parser.add_argument("-e", "--end_ts", type=int, nargs="?",
                        help="end time for rerun (unix time)")
    parser.add_argument('-p', '--processes', nargs="?", type=int, required=False,
                        default=1,
                        help="Number of processes to divide the time range and run, specify 0 to use all available cores")

    opts = parser.parse_args()
    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)

    logging.getLogger('elasticsearch').setLevel(logging.INFO)

    processes = opts.processes
    if processes <= 0:
        processes = os.cpu_count()
    if processes > 1 and not (opts.end_ts and opts.start_ts):
        logging.info(
            "cannot start multi-threading due to lack of end_ts or start_ts, forced back to single-thread processing")
        processes = 1

    hash_str = hashlib.sha1((json.dumps(vars(opts), sort_keys=True, ensure_ascii=True)).encode()).hexdigest()
    lockfile = "/tmp/inference-runner-{}.lock".format(hash_str)
    lock = filelock.FileLock(lockfile)
    with lock.acquire(timeout=1):
        if processes == 1:
            logging.info("single-threaded processing starts...")
            run_process(opts.debug, opts.start_ts, opts.end_ts, opts.old_index)
        else:
            args = []
            step = int((opts.end_ts - opts.start_ts) / processes)
            cur_ts = opts.start_ts
            while cur_ts < opts.end_ts:
                cur_end = cur_ts + step
                args.append(
                    (opts.debug, cur_ts, cur_end, opts.old_index))
                cur_ts += step
            # logging.info(*args)

            with mp.Pool(processes=processes) as pool:
                pool.starmap(run_process, args)

    # remove lockfile if process finishes running
    if os.path.exists(lockfile):
        os.remove(lockfile)


if __name__ == "__main__":
    main()
