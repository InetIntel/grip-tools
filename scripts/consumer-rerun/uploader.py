#!/usr/bin/env python3

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
import glob
import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from swiftclient.service import SwiftService, SwiftUploadObject


class SwiftUtils:
    def __init__(self, env):
        # load swift credentials
        load_dotenv(env, override=True)
        swift_auth_options = {
            "auth_version": '3',
            "os_username": os.environ.get('OS_USERNAME', None),
            "os_password": os.environ.get('OS_PASSWORD', None),
            "os_project_name": os.environ.get('OS_PROJECT_NAME', None),
            "os_auth_url": os.environ.get('OS_AUTH_URL', None),
        }

        self.auth_options = swift_auth_options
        assert not any([option is None for option in self.auth_options.values()])
        self.swift_service = SwiftService(self.auth_options)

    def _parse_file_name(self, filename):
        relative_fn = filename.split("/")[-1]
        timestr = relative_fn.split(".")[1]
        ts = int(timestr)
        datestr = datetime.utcfromtimestamp(ts).strftime("year=%Y/month=%m/day=%d/hour=%H")

        parts = relative_fn.split(".")
        file_type = parts[0]
        assert file_type in ["moas", "pfx-origins"]
        if file_type == "moas":
            container = "bgp-hijacks-moas"
            del parts[2]
        elif file_type == "pfx-origins":
            container = "bgp-hijacks-pfx-origins"
        else:
            container = ""

        dst = "{}/{}".format(datestr, ".".join(parts))
        return dst, container

    def upload(self, filename, check_done_flag=True, delete_on_success=True, no_op=False):
        # INPUT:  moas.1577786400.36000s-window.events.gz
        # OUTPUT: year=2014/month=12/day=26/hour=08/moas.1419580800.events.gz

        # check done flag first
        if check_done_flag and not os.path.exists(filename+".done"):
            logging.warning(".done flag file not exist for {}".format(filename))
            return

        # extract to upload destination name and container based on input file
        dst, container = self._parse_file_name(filename)
        logging.info("to upload: {} to {}/{} ...".format(filename, container, dst))

        if no_op:
            logging.info("\tupload and deletion skipped")
            return
        for r in self.swift_service.upload(container, [SwiftUploadObject(filename, dst)]):
            if r['success']:
                if 'object' in r:
                    logging.info("\tuploaded: {}".format(r['object']))

                    # attempt to delete input file if succeeded
                    if delete_on_success and (os.path.isfile(filename) or os.path.islink(filename)):
                        try:
                            os.remove(filename)
                            logging.info("\toriginal file deleted {}".format(filename))
                            os.remove(filename+".done")
                            logging.info("\tflag file deleted {}".format(filename+".done"))
                        except OSError:
                            pass

        logging.info("\tdone")


def main():
    parser = argparse.ArgumentParser(description="""
    Generates entities for the Charthouse Metadata Database
    """)

    parser.add_argument('-d', '--dir',
                        nargs='?', required=True,
                        help='directory to watch'
                        )
    parser.add_argument('-e', '--env',
                        nargs='?', required=True,
                        help='envfile path'
                        )
    parser.add_argument("-n", "--no-op", action="store_true", default=False,
                        help="debug, no action executed")
    parser.add_argument("-D", "--delete", action="store_true", default=False,
                        help="delete original file on upload success")

    logging.basicConfig(level="INFO",
                        format="%(asctime)s|%(levelname)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    opts, _ = parser.parse_known_args()

    swift_utils = SwiftUtils(env=opts.env)
    files = []
    while True:
        for filename in glob.glob("{}/*.gz".format(opts.dir)):
            files.append(filename)
            swift_utils.upload(filename, delete_on_success=opts.delete, no_op=opts.no_op)

        time.sleep(3600)



if __name__ == "__main__":
    main()
