# -*- coding: utf-8 -*-
import logging
#import re
import urllib
import urllib2
import zipfile
from StringIO import StringIO
from lxml import etree

GEONETWORK_V26 = "2.6"
GEONETWORK_V210 = "2.10"
GEONETWORK_VERSIONS = [GEONETWORK_V26, GEONETWORK_V210]

logger = logging.getLogger(__name__)


class GeoNetworkClient(object):

    def __init__(self, base, version):
        if version is None:
            version = GEONETWORK_V210

        assert version in GEONETWORK_VERSIONS
        self.version = version
        self.base = base

    def retrieveInfo(self, uuid):

        if self.version == GEONETWORK_V26:
            url = "%s/srv/en/mef.export" % self.base
            #headers = {
                #"Content-Type": "application/x-www-form-urlencoded",
                #"Accept": "text/plain"
            #}
            query = urllib.urlencode({
                "uuid": uuid
            })

            logger.info('Loading MEF for %s', uuid)
            request = urllib2.Request(url, query)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(), urllib2.HTTPRedirectHandler())

            response = opener.open(request)  # will get a ZIP file
            content = response.read()

            #logger.info('----> %s', content)
            #print 'RESPONSE ', content

            zdata = StringIO(content)
            zfile = zipfile.ZipFile(zdata)

            xml = None

            for name in zfile.namelist():
                #logger.info(' MEF entry: %s', name)
                #print ' MEF entry: ', name
                if name == 'info.xml':
                    uncompressed = zfile.read(name)
                    xml = etree.fromstring(uncompressed)

            return xml

    def retrieveMetadataCategories(self, uuid):
        xml = self.retrieveInfo(uuid)

        cats = []

        for cat in xml.findall('categories/category'):
            cats.append(cat.get('name'))

        return cats

