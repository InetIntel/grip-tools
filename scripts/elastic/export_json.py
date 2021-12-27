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
import gzip
import json
import logging
from datetime import datetime

from bgphijacks.utils.data.elastic import ElasticConn
from bgphijacks.utils.data.elastic_queries import query_in_range


class Exporter:
    """
    Exporter retrieve events from ElasticSearch and export it to JSON files.
    """

    def __init__(self, event_type):
        self.event_type = event_type
        self.esconn = ElasticConn()

    def list_events(self, start_ts, end_ts, min_susp=None, max_susp=None, simplify=True):
        """
        Rerun the inference code for the given time period.

        :param min_susp:
        :param max_susp:
        :param simplify:
        :param start_ts:
        :param end_ts:
        :return:
        """
        show_time(start_ts, "start_ts")
        show_time(end_ts, "end_ts")
        query = query_in_range(start_ts, end_ts, min_susp=min_susp, max_susp=max_susp)
        if simplify:
            query["_source"] = ["id", "event_type", "view_ts", "last_modified_ts", "summary"]  # we only want timestamps
        index_pattern = self.esconn.get_index_name(event_type=self.event_type)
        logging.info(index_pattern)

        for e in self.esconn.search_generator(index=index_pattern, query=query, raw_json=simplify):
            if simplify:
                # we will have e as raw json, and then simply it
                inf = e["summary"]["inference_result"]
                try:
                    event = {
                        "event_id": e["id"],
                        "event_type": e["event_type"],
                        "event_time": e["view_ts"],
                        "property_tags": e["summary"]["tags"],
                        "inference_tags": [i["inference_id"] for i in inf["inferences"]],
                        "suspicion_level": inf["primary_inference"]["suspicion_level"],
                        "confidence": inf["primary_inference"]["confidence"],
                        "url": f"https://dev.hicube.caida.org/feeds/hijacks/events/{e['event_type']}/{e['id']}"
                    }
                    # print(event)
                    yield event
                except TypeError as error:
                    print(json.dumps(e, indent=4))
                    raise error
            else:
                yield e


def show_time(ts: int, name: str, count=None):
    if ts:
        dt_object = datetime.utcfromtimestamp(ts)
        if count:
            log_str = f"{name} ({count}: {dt_object}"
        else:
            log_str = f"{name}: {dt_object}"
        logging.info(log_str)


def dump_events(event_type, start_ts, end_ts, dump_all):
    lister = Exporter(event_type)

    if dump_all:
        count = 0
        with gzip.open("grip_events_dump.{}.{}.{}.txt.gz".format(event_type, start_ts, end_ts), "wb") as of:
            for event in lister.list_events(start_ts=start_ts, end_ts=end_ts, min_susp=0, simplify=False):
                of.write("{}\n".format(event.as_json()).encode())
                count += 1
                if count % 10000 == 0:
                    show_time(event.view_ts, "event_ts", count=count)
    else:
        normal_events = []
        all_events = []
        for event in lister.list_events(start_ts=start_ts, end_ts=end_ts):
            all_events.append(event)
            if event["suspicion_level"] > 0:
                normal_events.append(event)
            if len(all_events) % 10000 == 0:
                print(datetime.utcfromtimestamp(event["event_time"]))
                print(f"{len(normal_events)}/{len(all_events)}")
                print(event)

        with open("grip_events_normal.json", "w") as nof:
            json.dump(normal_events, nof, indent=4, sort_keys=True)
        with open("grip_events_all.json", "w") as aof:
            json.dump(all_events, aof, indent=4, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(
        description="Utility to listen for new events and trigger active measurements.")

    parser.add_argument('-t', "--type", nargs="?", required=True,
                        help="Event type to listen for")
    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)
    parser.add_argument("-s", "--start_ts", type=int, nargs="?", required=True,
                        help="start time for rerun (unix time)")
    parser.add_argument("-e", "--end_ts", type=int, nargs="?", required=True,
                        help="end time for rerun (unix time)")
    parser.add_argument("-d", "--dump_all", action="store_true", default=False,
                        help="dump all events in one gz file")

    opts = parser.parse_args()
    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)

    logging.getLogger('elasticsearch').setLevel(logging.INFO)
    dump_events(opts.type, opts.start_ts, opts.end_ts, opts.dump_all)


if __name__ == "__main__":
    main()
