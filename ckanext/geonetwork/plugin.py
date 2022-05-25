import ckan.plugins as plugins
import logging

import ckan.lib.base as base
import ckan.plugins.toolkit as plugins_toolkit
import routes.mapper as routes_mapper
from flask import Blueprint

import ckanext.geonetwork.helpers as helpers

import ckanext.dcatapit.interfaces as interfaces

from ckan.common import _

try:
    from ckan.lib.plugins import DefaultTranslation
except ImportError:
    class DefaultTranslation():
        pass

log = logging.getLogger(__name__)

static_pages = ['faq', 'acknowledgements', 'legal_notes', 'privacy']


class GeoNetworkPlugin(plugins.SingletonPlugin, DefaultTranslation):
    # IConfigurer
    plugins.implements(plugins.IConfigurer)

    # IConfigurable
    plugins.implements(plugins.IConfigurable)

    # ITemplateHelpers
    plugins.implements(plugins.ITemplateHelpers)

    # IBluePrint
    plugins.implements(plugins.IBlueprint)

    # IPackageController
    plugins.implements(plugins.IPackageController, inherit=True)

    # ICustomSchema
    plugins.implements(interfaces.ICustomSchema)

    # ITranslation
    if plugins_toolkit.check_ckan_version(min_version='2.5.0'):
        plugins.implements(plugins.ITranslation, inherit=True)

    # Implementation of ICustomSchema
    # ------------------------------------------------------------

    def get_custom_schema(self):
        return [
            {
                'name': 'fields_description',
                'validator': ['ignore_missing'],
                'element': 'textarea',
                'label': _('Fields Description'),
                'placeholder': _('description of the dataset fields'),
                'is_required': False,
                'localized': True,
                'ignore_from_info': True
            },
        ]

    # Implementation of IConfigurer
    # ------------------------------------------------------------

    def update_config(self, config):
        plugins_toolkit.add_public_directory(config, 'public')
        plugins_toolkit.add_template_directory(config, 'templates')
        plugins_toolkit.add_resource('assets', 'geonetwork')  # path, webasset name
        plugins_toolkit.add_public_directory(config, 'assets')  # needed workaround to have webasset find files

    # Implementation of IConfigurable
    # ------------------------------------------------------------

    def configure(self, config):
        self.ga_conf = {
            'id': config.get('googleanalytics.id'),
            'domain': config.get('googleanalytics.domain'),
        }

    # Implementation of IBluePrint
    def get_blueprint(self):
        datitrentinoit = Blueprint('geonetwork', __name__)
        for page_name in static_pages:
            def get_action(name):
                def action():
                    return base.render('pages/{0}.html'.format(name))

                return action

            action = get_action(page_name)
            action.__name__ = page_name

            page_slug = page_name.replace('_', '-')
            #             m.connect(page_name, '/' + page_slug, action=page_name)
            datitrentinoit.add_url_rule('/' + page_slug, page_name, view_func=action)
        return datitrentinoit

    # Implementation of ITemplateHelpers
    def get_helpers(self):
        return {
            'dti_ga_site_id': self._get_ga_site_id,
            'dti_ga_site_domain': self._get_ga_site_domain,
            'dti_recent_updates': helpers.recent_updates,
        }

    def _get_ga_site_id(self):
        return self.ga_conf['id']

    def _get_ga_site_domain(self):
        return self.ga_conf['domain']

