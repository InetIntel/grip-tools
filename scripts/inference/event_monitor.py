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

import confluent_kafka
import logging
import signal
import sys

import bgphijacks.common
from bgphijacks.utils.data.elastic import ElasticConn

KAFKA_POOLING_INTERVAL = 5


class EventMonitor:

    def __init__(self):
        pass

    def _init_kafka_consumer(self, brokers, topic, group, offset):
        """initialize kafka consumer for listening events from tagger"""
        if brokers is None:
            brokers = bgphijacks.common.KAFKA_BROKERS
        if topic is None:
            topic = "bgphijacks.monitor"
        if group is None:
            group = topic
        self.kafka_consumer = confluent_kafka.Consumer({
            "bootstrap.servers": brokers,
            "group.id": group,
            "default.topic.config": {"auto.offset.reset": offset},
            "socket.keepalive.enable": True
        })
        self.kafka_consumer.subscribe([topic])

    def listen(self, brokers, topic, group, offset):
        """listen for traceroute request IDs from driver and retrieve results"""

        es_conn = ElasticConn()

        shutdown = {"count": 0}

        def _stop_handler(_signo, _stack_frame):
            logging.info("Caught signal, shutting down at next opportunity")
            shutdown["count"] += 1
            if shutdown["count"] > 3:
                logging.warn("Caught %d signals, shutting down NOW", shutdown["count"])
            sys.exit(0)

        signal.signal(signal.SIGTERM, _stop_handler)
        signal.signal(signal.SIGINT, _stop_handler)
        self._init_kafka_consumer(brokers, topic, group, offset)

        while True:
            if shutdown["count"] > 0:
                logging.info("Shutting down")
                break

            # quickly polling all pending messages from kafka before processing results
            msg = self.kafka_consumer.poll(KAFKA_POOLING_INTERVAL)
            if msg is not None and not msg.error():
                # the message only contains the index and id for elasticsearch entries
                index, event_id = msg.value().split(";")

                # the actual event dictionary
                event = es_conn.get_event_by_id(event_id=event_id)

                # the following is the processing of events
                # pass

                continue  # continue to poll next kafka message


def main():
    parser = argparse.ArgumentParser(
        description="Utility to listen for processed events.")

    # add argument for list of brokers
    kafka_grp = parser.add_argument_group("kafka options")
    kafka_grp.add_argument('-b', "--brokers", nargs="?",
                           help="Comma-separated list of Kafka brokers",
                           default=bgphijacks.common.KAFKA_BROKERS)
    kafka_grp.add_argument('-n', "--topic", nargs="?",
                           help="Kafka topic to use")
    parser.add_argument('-g', "--group", nargs="?",
                        help="Listener group to join")

    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s",
                        # filename=LOG_FILENAME,
                        level=logging.INFO)

    opts = parser.parse_args()

    if opts.group is None:
        opts.group = "bgphijacks.monitor"
    if opts.topic is None:
        opts.topic = "bgphijacks.monitor"

    logging.info("listening to topic %s", opts.topic)

    EventMonitor().listen(
        group=opts.group,
        offset="latest",
        topic=opts.topic,
        brokers=opts.brokers,
    )


if __name__ == "__main__":
    main()
