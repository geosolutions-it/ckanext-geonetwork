import logging
import urllib

import ckan.model as model
import ckan.plugins as p
import ckan.lib.search as search
import ckan.lib.helpers as h

import ckan.logic as logic
from ckan.common import request

import ckanext.multilang.helpers as multilang_helpers

from ckanext.multilang.model import PackageMultilang

log = logging.getLogger(__file__)


def recent_updates(n):
    #
    # Return a list of the n most recently updated datasets.
    #
    log.debug('::::: Retrieving latest datasets: %r' % n)
    context = {'model': model,
               'session': model.Session,
               'user': p.toolkit.c.user or p.toolkit.c.author}

    data_dict = {'rows': n,
                 'sort': u'metadata_modified desc',
                 'facet': u'false'}

    try:
        search_results = logic.get_action('package_search')(context, data_dict)
    except search.SearchError as e:
        log.error('Error searching for recently updated datasets')
        log.error(e)
        search_results = {}

    for item in search_results.get('results'):
        log.info(':::::::::::: Retrieving the corresponding localized title and abstract :::::::::::::::')

        lang = multilang_helpers.getLanguage()

        q_results = model.Session.query(PackageMultilang)\
                                 .filter(PackageMultilang.package_id == item.get('id'),
                                         PackageMultilang.lang == lang).all()

        if q_results:
            for result in q_results:
                item[result.field] = result.text

    return search_results.get('results', [])

