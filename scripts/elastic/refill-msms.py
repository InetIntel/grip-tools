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
import gzip
import logging

from ripe.atlas.cousteau import MeasurementRequest, AtlasResultsRequest
from bgphijacks.active.ripe_atlas.ripe_atlas_msm import AtlasMeasurement as HijacksMeasurement
import re

# tested matching for all four cases
#
# examples:
# moas-1546298700-136450_138522_65529:136450
# submoas-1546299900-14858=14858_19058:19058
# defcon-1569949200-4761:1
# edges-1547505300-266094-26592:26592
from bgphijacks.active.as_traceroute import AsTracerouteDriver
from bgphijacks.active.ripe_atlas.ripe_atlas_utils import extract_atlas_response
from bgphijacks.events.event import Event
from bgphijacks.events.pfxevent import PfxEvent
from bgphijacks.redis import Pfx2AsHistorical
from bgphijacks.utils.data.elastic import ElasticConn
from bgphijacks.utils.data.elastic_queries import query_missing_traceroutes
import json


class RefillMsms:

    regex_map = {
        "moas": "^moas-\\d+-[\\d_]+:\\d+$",
        "submoas": "^submoas-\\d+-[\\d_=]+:\\d+$",
        "defcon": "^defcon-\\d+-[\\d_]+:\\d+$",
        "edges": "^edges-\\d+-[\\d\-_]+:\\d+$",
    }

    def __init__(self):
        self.esconn = ElasticConn()
        pass

    def extract_msm_ids(self):

        for t in ["moas", "submoas", "defcon", "edges"]:
            filters = {
                "search": t,
                "type": "traceroute",
                "start_time__gt": 1546300800,  # "2019-01-01T00:00:00",
            }
            measurements = MeasurementRequest(
                return_objects=True, user_agent="RIPE Atlas Tools (Magellan)", **filters)
            with open("atlas-map-{}.csv".format(t), "w") as outf:
                for msm in measurements:
                    if re.match(self.regex_map[t], msm.description):
                        description = msm.description
                        msm_id = msm.id
                        out_str = "{},{}".format(msm_id, description)
                        outf.write(out_str+"\n")
                        print(out_str)

    def _event_has_tr_results(self, event):
        assert(isinstance(event, Event))
        has_results = False
        for pfx_event in event.pfx_events:
            assert(isinstance(pfx_event, PfxEvent))
            if not pfx_event.traceroutes.get("msms", []) == []:
                has_results = True
                break
        return has_results

    def refill_msms_2(self):
        """
        Refill by checking all events that has Atlas results and check if they need refill, if so then refill.
        :return:
        """
        as_traceroute_driver = AsTracerouteDriver()
        pfx_origin_db = Pfx2AsHistorical()

        for t in ["moas", "submoas", "defcon", "edges"]:
            msms_map = self._read_msms_from_file("atlas-map-{}.csv.gz".format(t))

            for event_id, msms in msms_map.items():
                if t == "defcon":
                    event_as = event_id.split("-")[-1]
                    if any([target_asn != event_as for _, target_asn in msms]):
                        # skip traceroutes that were wrongfully created.
                        # example: [('23081510', '1'), ('23081511', '9'), ('23081512', '3'), ('23081513', '1'), ('23081514', '9'), ('23081515', '3')]
                        continue
                event = self.esconn.get_event_by_id(event_id)
                if event is None:
                    continue

                if not event.summary.tr_worthy or self._event_has_tr_results(event):
                    continue

                view_ts = event.view_ts
                for msm_id, target_asn in msms:
                    # now refill measurements to corresponding pfx events

                    # retrieve measurement results first
                    kwargs = {"msm_id": msm_id}
                    is_success, responses = AtlasResultsRequest(**kwargs).create()

                    if not is_success:
                        continue

                    # responses are there, should put it into corresponding pfx events
                    for pfx_event in event.pfx_events:
                        assert(isinstance(pfx_event, PfxEvent))
                        if not pfx_event.traceroutes.get("msms",[]) == []:
                            # this prefix event already has measurement results, skipping
                            continue

                        pfx_event.traceroutes["msms"] = []
                        if target_asn in pfx_event.details.get_current_origins():
                            res = extract_atlas_response(responses=responses, pfx_origin_db=pfx_origin_db)
                            if not res:
                                continue
                            as_traceroute_driver.fill_as_traceroute_results(traceroute_results=res, view_ts=view_ts)
                            try:
                                msm_obj = HijacksMeasurement(
                                    msm_id=msm_id, probe_ids=[msm["prb_id"] for msm in res], target_ip=res[-1]["dst"], target_pfx=res[-1]["dst"]+"/32", target_asn=target_asn,
                                    request_error="", event_id=event.event_id, results=res
                                )
                            except Exception as e:
                                print(json.dumps(res, indent=4))
                                raise e

                            pfx_event.traceroutes["msms"].append(msm_obj)
                            break

                # at last, update the event
                self.esconn.index_event(event)

    def refill_msms(self):
        """
        Refill by searching for elasticsseach objects and check if we have them on Atlas
        :return:
        """
        query = query_missing_traceroutes(min_ts=1546300800)
        as_traceroute_driver = AsTracerouteDriver()

        pfx_origin_db = Pfx2AsHistorical()
        for t in ["moas", "submoas", "defcon", "edges"]:
            msms_map = self._read_msms_from_file("atlas-map-{}.csv.gz".format(t))
            logging.info("searching for events that are traeroute worthy but lacks traceroute results")
            for event in self.esconn.search_generator(index="observatory-events-{}-*".format(t), query=query):
                if event.event_id in msms_map:
                    # we have results for the event
                    logging.info("event {} has result but not loaded in elasticsearch yet. refill now".format(event.event_id))
                    # reaching here means the status is either 4: Stopped, or 5: Forced to stop
                    # meaning we can extract the results now
                    view_ts = event.view_ts
                    msms = msms_map[event.event_id]
                    for msm_id, target_asn in msms:
                        kwargs = {"msm_id": msm_id}
                        is_success, responses = AtlasResultsRequest(**kwargs).create()
                        if is_success:
                            # responses are there, should put it into corresponding pfx events

                            for pfx_event in event.pfx_events:
                                assert(isinstance(pfx_event, PfxEvent))
                                if not pfx_event.traceroutes.get("msms",[]) == []:
                                    # this prefix event already has measurement results, skipping
                                    continue

                                pfx_event.traceroutes["msms"] = []
                                if target_asn in pfx_event.details.get_current_origins():
                                    res = extract_atlas_response(responses=responses, pfx_origin_db=pfx_origin_db)
                                    as_traceroute_driver.fill_as_traceroute_results(traceroute_results=res, view_ts=view_ts)

                                    try:
                                        msm_obj = HijacksMeasurement(
                                            msm_id=msm_id, probe_ids=[msm["prb_id"] for msm in res], target_ip=res[-1]["dst"], target_pfx=res[-1]["dst"]+"/32", target_asn=target_asn,
                                            request_error="", event_id=event.event_id, results=res
                                        )
                                    except Exception as e:
                                        json.dumps(res, indent=4)
                                        raise e

                                    pfx_event.traceroutes["msms"].append(msm_obj)
                    self.esconn.index_event(event)

    def _read_msms_from_file(self, filename):
        msms_map = {}
        logging.info("loading cached measurements mapping file from {}".format(filename))
        with gzip.open(filename) as input_file:
            for line in input_file:
                line = line.strip()
                msm_id, event_fingerprint = line.split(",")
                event_id, target_asn = event_fingerprint.split(":")
                # reprocess edges event id
                segments = event_id.split("-")
                event_id = "-".join([segments[0], segments[1], "_".join(segments[2:])])
                msms = msms_map.get(event_id, [])
                msms.append((msm_id, target_asn))
                msms_map[event_id] = msms
        logging.info("finished loading mapping file")
        return msms_map


if __name__ == '__main__':

    logging.basicConfig(format="%(levelname)s %(asctime)s: %(message)s", level=logging.INFO)
    refill = RefillMsms()
    # refill.refill_msms_from_file("atlas-map-moas.csv.gz")
    refill.refill_msms_2()

