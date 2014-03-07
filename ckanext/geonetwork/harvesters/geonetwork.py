import re
import urllib
import urlparse

import logging

from ckan import model

from ckan.plugins.core import SingletonPlugin, implements

from ckanext.harvest.interfaces import IHarvester
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra

from ckanext.spatial.lib.csw_client import CswService
from ckanext.spatial.harvesters.base import SpatialHarvester, text_traceback
from ckanext.spatial.harvesters.csw import CSWHarvester


from  ckan.lib.helpers import json
import math


log = logging.getLogger(__name__)

class GeoNetworkHarvester(CSWHarvester, SingletonPlugin):

   def info(self):
      return {
         'name': 'geonetwork',
         'title': 'CSW server (GeoNetwork)',
         'description': 'Harvests GeoNetwork instances via CSW',
         'form_config_interface': 'Text'
      }

   def get_package_dict(self, iso_values, harvest_object):

      package_dict = super(GeoNetworkHarvester, self).get_package_dict(iso_values, harvest_object)

      # Add default_tags from config
      default_tags = self.source_config.get('default_tags',[])
      if default_tags:
         for tag in default_tags:
            package_dict['tags'].append({'name': tag})

      # Add default_extras from config
      default_extras = self.source_config.get('default_extras',{})
      if default_extras:
         override_extras = self.source_config.get('override_extras',False)

         existing_keys = [entry.get('key') for entry in package_dict['extras'] ]

         for key,value in default_extras.iteritems():
            log.debug('Processing extra %s', key)
            if not key in existing_keys or override_extras:
               # Look for replacement strings
               if isinstance(value,basestring):
                  value = value.format(
                           harvest_source_id=str(harvest_object.job.source.id),
                           harvest_source_url=str(harvest_object.job.source.url).strip('/'),
                           harvest_source_title=str(harvest_object.job.source.title),
                           harvest_job_id=str(harvest_object.job.id),
                           harvest_object_id=str(harvest_object.id),
                           guid=str(harvest_object.guid))
               package_dict['extras'].append( {'key': key,   'value': value })
            else:
               log.debug('Skipping existing extra %s', key)


      # Add GeoNetowrk specific extras       
      gn_localized_url = harvest_object.job.source.url.strip('/')

      if gn_localized_url[-3:] == 'csw' :
         gn_localized_url = gn_localized_url[:-3]

      log.debug('GN localized URL %s', gn_localized_url)
      #log.debug('Package dict is %r ', package_dict['extras'])

      package_dict['extras'].append( {'key': 'gn_view_metadata_url', 'value': gn_localized_url + '/metadata.show?uuid=' + harvest_object.guid })
      package_dict['extras'].append( {'key': 'gn_localized_url',     'value': gn_localized_url })


      # End of processing, return the modified package
      return package_dict

