# -*- coding: utf-8 -*-
import logging
#import re
import urllib
import urllib.request
import zipfile
import io
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
            # url = "%s/srv/en/mef.export" % self.base
            url = "%smef.export?uuid=%s" % (self.base, uuid)

            logger.info('URL %r ', url)

            request = urllib.request.Request(url, method='GET')
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(), urllib.request.HTTPRedirectHandler())

            response = opener.open(request)  # will get a ZIP file
            content = response.read()
                
            #print 'RESPONSE ', content

            zdata = io.BytesIO(content)
            zfile = zipfile.ZipFile(zdata)

            xml = None

            for name in zfile.namelist():
                #logger.info(' MEF entry: %s', name)
                #print ' MEF entry: ', name
                if name == 'metadata.xml':
                    uncompressed = zfile.read(name)
                    xml = etree.fromstring(uncompressed)
            
            return xml

    def retrieveMetadataCategories(self, uuid):
        xml = self.retrieveInfo(uuid)
        cats = []

        for cat in xml.findall('categories/category'):
            logger.info('cat %r', cat)
            cats.append(cat.get('name')) 

        return cats
