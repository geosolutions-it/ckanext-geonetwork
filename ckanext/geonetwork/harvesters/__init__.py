try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

from ckanext.geonetwork.harvesters.geonetwork import GeoNetworkHarvester
from ckanext.geonetwork.harvesters.utils import GeoNetworkClient
