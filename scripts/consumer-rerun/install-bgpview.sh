#
# This software is Copyright (c) 2015 The Regents of the University of
# California. All Rights Reserved. Permission to copy, modify, and distribute this
# software and its documentation for academic research and education purposes,
# without fee, and without a written agreement is hereby granted, provided that
# the above copyright notice, this paragraph and the following three paragraphs
# appear in all copies. Permission to make use of this software for other than
# academic research and education purposes may be obtained by contacting:
#
# Office of Innovation and Commercialization
# 9500 Gilman Drive, Mail Code 0910
# University of California
# La Jolla, CA 92093-0910
# (858) 534-5815
# invent@ucsd.edu
#
# This software program and documentation are copyrighted by The Regents of the
# University of California. The software program and documentation are supplied
# "as is", without any accompanying services from The Regents. The Regents does
# not warrant that the operation of the program will be uninterrupted or
# error-free. The end-user understands that the program was developed for research
# purposes and is advised not to rely exclusively on the program for any reason.
#
# IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST
# PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF
# THE UNIVERSITY OF CALIFORNIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE. THE UNIVERSITY OF CALIFORNIA SPECIFICALLY DISCLAIMS ANY WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE. THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS
# IS" BASIS, AND THE UNIVERSITY OF CALIFORNIA HAS NO OBLIGATIONS TO PROVIDE
# MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
#

set -e

BASEDIR=/home/mingwei/workspace/bgpview
SRCDIR=$BASEDIR/src
ENVDIR=$BASEDIR/env
LIBDIR=$ENVDIR/lib
HDRDIR=$ENVDIR/include

mkdir -p $BASEDIR $ENVDIR $LIBDIR $HDRDIR $SRCDIR

cd $SRCDIR
curl -O https://research.wand.net.nz/software/wandio/wandio-4.2.1.tar.gz
tar zxf wandio-4.2.1.tar.gz
cd wandio-4.2.1
CPPFLAGS="-I$HDRDIR" LDFLAGS="-L$LIBDIR" ./configure --prefix=$ENVDIR/
make
make install

cd $SRCDIR
wget https://github.com/yaml/libyaml/releases/download/0.2.5/yaml-0.2.5.tar.gz
tar xvzf yaml-0.2.5.tar.gz
cd yaml-0.2.5
CPPFLAGS="-I$HDRDIR" LDFLAGS="-L$LIBDIR" ./configure --prefix=$ENVDIR/
make
make install

cd $SRCDIR
wget https://github.com/CAIDA/libtimeseries/releases/download/v1.0.0/libtimeseries-1.0.0.tar.gz
tar xvzf libtimeseries-1.0.0.tar.gz
cd libtimeseries-1.0.0
CPPFLAGS="-I$HDRDIR" LDFLAGS="-L$LIBDIR" ./configure --prefix=$ENVDIR/
make
make install

cd $SRCDIR
wget https://github.com/CAIDA/libipmeta/releases/download/v3.1.0/libipmeta-3.1.0.tar.gz
tar xvzf libipmeta-3.1.0.tar.gz
cd libipmeta-3.1.0
CPPFLAGS="-I$HDRDIR" LDFLAGS="-L$LIBDIR" ./configure --prefix=$ENVDIR/
make
make install

cd $SRCDIR
wget https://github.com/CAIDA/libbgpstream/releases/download/v2.2.0/libbgpstream-2.2.0.tar.gz
tar xvzf libbgpstream-2.2.0.tar.gz
cd libbgpstream-2.2.0
# disable wandio check
sed '14210,14216{s/^/# /}' -i configure
CPPFLAGS="-I$HDRDIR" LDFLAGS="-L$LIBDIR" ./configure --without-kafka --prefix=$ENVDIR/
make
make install

cd $SRCDIR
git clone https://github.com/CAIDA/bgpview.git
cd bgpview
git checkout df301641f2663dcea437d1854e461c8a71aa9c42
./autogen.sh
CPPFLAGS="-I$HDRDIR" LDFLAGS="-L$LIBDIR" ./configure --prefix=$ENVDIR/
make
make install