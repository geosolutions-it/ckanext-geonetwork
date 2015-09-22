from .utils import GeoNetworkClient
from .utils import GEONETWORK_V210, GEONETWORK_V26

import re

import logging

from ckan import model
from ckan.model import Session

from ckan.plugins.core import SingletonPlugin

from ckanext.spatial.lib.csw_client import CswService
from ckanext.spatial.harvesters.csw import CSWHarvester

from ckanext.spatial.model import ISODocument
from ckanext.spatial.model import ISOElement

from ckan.logic import ValidationError, NotFound, get_action

from pylons import config
from datetime import datetime

log = logging.getLogger(__name__)

# Extend the ISODocument definitions by adding some more useful elements

log.info('GeoNetwork harvester: extending ISODocument with TimeInstant')
ISODocument.elements.append(
    ISOElement(
        name="temporal-extent-instant",
        search_paths=[
            "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition/text()",
        ],
        multiplicity="*",
     ))

# Some old GN instances still uses the old GML URL
# We'll add more xpath for addressing this issue
log.info('GeoNetwork harvester: adding old GML URI')
ISOElement.namespaces['oldgml'] = "http://www.opengis.net/gml"

for element in ISODocument.elements:
    newpaths = []

    for path in element.search_paths:
        if "gml:" in path:
            newpath = path.replace('gml:', 'oldgml:')
            newpaths.append(newpath)

    for newpath in newpaths:
        element.search_paths.append(newpath)
        log.info("Added old URI for gml to %s", element.name)


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
        default_tags = self.source_config.get('default_tags', [])
        if default_tags:
            for tag in default_tags:
                package_dict['tags'].append({'name': tag})

        # Add default_extras from config
        default_extras = self.source_config.get('default_extras', {})
        if default_extras:
            override_extras = self.source_config.get('override_extras', False)

            existing_keys = [entry.get('key') for entry in package_dict['extras']]

            for key, value in default_extras.iteritems():
                log.debug('Processing extra %s', key)
                if not key in existing_keys or override_extras:
                    # Look for replacement strings
                    if isinstance(value, basestring):
                        value = value.format(
                               harvest_source_id=str(harvest_object.job.source.id),
                               harvest_source_url=str(harvest_object.job.source.url).strip('/'),
                               harvest_source_title=str(harvest_object.job.source.title),
                               harvest_job_id=str(harvest_object.job.id),
                               harvest_object_id=str(harvest_object.id),
                               guid=str(harvest_object.guid))
                        package_dict['extras'].append({'key': key, 'value': value})
                    else:
                        log.debug('Skipping existing extra %s', key)

        # Add GeoNetwork specific extras
        gn_localized_url = harvest_object.job.source.url.strip('/')

        if gn_localized_url[-3:] == 'csw':
            gn_localized_url = gn_localized_url[:-3]

        log.debug('GN localized URL %s', gn_localized_url)
        #log.debug('Package dict is %r ', package_dict['extras'])

        package_dict['extras'].append({'key': 'gn_view_metadata_url', 'value': gn_localized_url + '/metadata.show?uuid=' + harvest_object.guid})
        package_dict['extras'].append({'key': 'gn_localized_url', 'value': gn_localized_url})

        # Add other elements from ISO metadata
        time_extents = self.infer_timeinstants(iso_values)
        if time_extents:
            log.info("Adding Time Instants...")
            package_dict['extras'].append({'key': 'temporal-extent-instant', 'value': time_extents})
        
        ## Configuring package groups            
        group_mapping = self.source_config.get('group_mapping', {})

        if group_mapping:
            groups = self.handle_groups(harvest_object, group_mapping, gn_localized_url, iso_values)
            if groups:
                package_dict['groups'] = groups

        #log.debug('::::::::::::::::::::::: %r ', self.source_config.get('private_datasets'))
        if self.source_config.get('private_datasets') == "True":
            package_dict['private'] = True
        #log.debug('::::::::::::::::::::::: %r ', package_dict['private'])

        # Fix resources type according to resource_locator_protocol
        self.fix_resource_type(package_dict['resources'])

        # End of processing, return the modified package
        return package_dict

    def infer_timeinstants(self, values):
        extents = []

        for extent in values["temporal-extent-instant"]:
            if extent not in extents:
                extents.append(extent)

        log.info("%d TIME ISTANTS FOUND", len(extents))

        if len(extents) > 0:
            return ",".join(extents)

        return

    def handle_groups(self, harvest_object, group_mapping, gn_localized_url, values):
        try:
            context = {'model': model, 'session': Session, 'user': 'harvest'}
            validated_groups = []
            cats = []

            harvest_iso_categories = self.source_config.get('harvest_iso_categories')
            if harvest_iso_categories == "True":
                # Handle groups mapping using metadata TopicCategory
                cats = values["topic-category"]
                log.info(':::::::::::::-TOPIC-CATEGORY-::::::::::::: %r ', cats)
            else:
                # Handle groups mapping using GeoNetwork categories
                version = self.source_config.get('version')
                client = GeoNetworkClient(gn_localized_url, version)
                cats = client.retrieveMetadataCategories(harvest_object.guid)
            
            for cat in cats:
                groupname = group_mapping[cat]

                printname = groupname if not None else "NONE"
                log.debug("category %s mapped into %s" % (cat, printname))

                if groupname:
                    try:
                        data_dict = {'id': groupname}
                        get_action('group_show')(context, data_dict)
                        #log.info('Group %s found %s' % (groupname, group))
                        #if self.api_version == 1:
                            #validated_groups.append(group['name'])
                        #else:
                        #validated_groups.append(group['id'])
                        validated_groups.append({'name': groupname})
                    except NotFound, e:
                        log.warning('Group %s from category %s is not available' % (groupname, cat))
        except Exception, e:
            log.warning('Error handling groups for metadata %s' % harvest_object.guid)

        return validated_groups

    def fix_resource_type(self, resources):
        for resource in resources:
            if 'OGC:WMS' in resource['resource_locator_protocol']:
                resource['format'] = 'wms'

                if config.get('ckanext.spatial.harvest.validate_wms', False):
                    # Check if the service is a view service
                    url = resource['url']
                    test_url = url.split('?')[0] if '?' in url else url
                    if self._is_wms(test_url):
                        resource['verified'] = True
                        resource['verified_date'] = datetime.now().isoformat()

