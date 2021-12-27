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

def fix_event_index(self):
    """
    this is a temporary script fixing events that were committed to dates of different indexes
    :return:
    """
    # 1. list all indexes
    # 2. for each index, find all events that do not match the corresponding time range
    # 3. update the correct event and remove the wrong event
    for index in self.esconn.es.indices.get_alias("observatory-*-*-*"):
        # get start and end time stamp
        year, month, day = map(lambda x: int(x), index.split("-")[2:])

        start = time.mktime(datetime.datetime(year, month, day).timetuple()) - 25200
        end = time.mktime((datetime.datetime(year, month, day) + datetime.timedelta(days=1)).timetuple()) - 25200
        query = query_out_of_range(start, end)

        found = False
        for event in self.esconn.search_generator(index=index, query=query):
            assert (isinstance(event, Event))
            view_ts = event.view_ts
            if view_ts > end or view_ts < start:
                logging.info("FOUND!", event.event_id, view_ts)
                found = True

        if found:
            # logging.info("start deleting matching items")
            # self.esconn.es.delete_by_query(index=index, body=query, wait_for_completion=True)
            # logging.info("deletion finished")
            break
