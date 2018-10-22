# -*- coding: utf-8 -*-
import logging
#import re
import urllib
import urllib2
import zipfile
import requests
from StringIO import StringIO
from lxml import etree

GEONETWORK_V26 = "2.6"
GEONETWORK_V210 = "2.10"
GEONETWORK_V34 = "3.4"
GEONETWORK_VERSIONS = [GEONETWORK_V26, GEONETWORK_V210, GEONETWORK_V34]

logger = logging.getLogger(__name__)


class GeoNetworkClient(object):

    def __init__(self, base, version):
        if version is None:
            version = GEONETWORK_V34

        assert version in GEONETWORK_VERSIONS
        self.version = version
        self.base = base

    def retrieveInfo(self, uuid):
        # MEF export works for all versions listed in GEONETWORK_VERSIONS
        urlbase = self.base[:-1] if self.base.endswith('/') else self.base
        if not urlbase.endswith('srv/en'):
            url = "%s/srv/en/mef.export" % urlbase
        else:
            url = "%s/mef.export" % urlbase

        logger.info('Loading MEF for %s from %s', uuid, url)
        resp = requests.get(url, params={'uuid': uuid}, stream=True)

        zdata = StringIO(resp.content)
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

        logger.debug('Retrieved Metadata Categories: %s' % cats)
        return cats

