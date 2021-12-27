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

from bgphijacks.events.event import Event
from bgphijacks.tagger.tagger import Tagger
from bgphijacks.tagger.tagger_defcon import DefconTagger
from bgphijacks.tagger.tagger_edges import EdgesTagger
from bgphijacks.tagger.tagger_moas import MoasTagger
from bgphijacks.tagger.tagger_submoas import SubMoasTagger

TAGGER = {
    "defcon": DefconTagger,
    "edges": EdgesTagger,
    "moas": MoasTagger,
    "submoas": SubMoasTagger,
}


def from_json(event_json: str):
    d = json.loads(event_json)
    return Event.from_dict(d)


def retag_events(tagger: Tagger, events_file):
    """
    Retag an existing event.
    :param events_file:
    :param tagger:
    :param event:
    :return: event
    """

    logging.info("counting events from {} ...".format(events_file))
    total = 0
    for _ in gzip.open(events_file):
        total += 1
    logging.info("{} events in total".format(total))

    for event_json in gzip.open(events_file):
        event = from_json(event_json)
        assert isinstance(event, Event)
        logging.info("retagging event {}".format(event.event_id))
        ts = event.view_ts
        tagger.update_datasets(ts)
        tagger.methodology.prepare_for_view(ts)
        tagger.tag_event(event)
        logging.info("tagging finished")


def main():
    parser = argparse.ArgumentParser(
        description="Utility to retag events")

    parser.add_argument('-t', "--type", nargs="?", required=True,
                        help="Event type to retag for (moas, submoas, defcon, edges)")
    parser.add_argument("-f", "--events-file", nargs="?", required=True,
                        help="Events file to load")
    parser.add_argument("-p", "--pfx2as-file", help="Prefix to AS mapping file", default=None)
    parser.add_argument("-o", "--offsite-mode", action="store_true", default=False,
                        help="Run tagging off from production site")

    opts = parser.parse_args()

    # set logging level to be INFO, ElasticSearch operations will be logged to output
    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)

    tagger = TAGGER[opts.type](options={
        # "in_memory_data": opts.in_memory,
        "enable_finisher": False,
        "debug": True,
        "verbose": False,
        "force_process_view": True,
        "offsite_mode": opts.offsite_mode,
        "pfx2as_file": opts.pfx2as_file,
    })

    retag_events(tagger, opts.events_file)


if __name__ == "__main__":
    main()
