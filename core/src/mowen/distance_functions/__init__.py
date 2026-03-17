"""Built-in distance functions for the mowen pipeline."""

from mowen.distance_functions.base import DistanceFunction, distance_function_registry

# Import implementation modules so their @register decorators execute.
# Ordered: most commonly used / best-performing first, niche last.
from mowen.distance_functions import cosine as cosine
from mowen.distance_functions import manhattan as manhattan
from mowen.distance_functions import euclidean as euclidean
from mowen.distance_functions import chi_square as chi_square
from mowen.distance_functions import kl_divergence as kl_divergence
from mowen.distance_functions import cross_entropy as cross_entropy
from mowen.distance_functions import hellinger as hellinger
from mowen.distance_functions import bhattacharyya as bhattacharyya
from mowen.distance_functions import bray_curtis as bray_curtis
from mowen.distance_functions import canberra as canberra
from mowen.distance_functions import intersection as intersection
from mowen.distance_functions import histogram_intersection as histogram_intersection
from mowen.distance_functions import pearson_correlation as pearson_correlation
from mowen.distance_functions import kendall_correlation as kendall_correlation
from mowen.distance_functions import keselj_weighted as keselj_weighted
from mowen.distance_functions import angular_separation as angular_separation
from mowen.distance_functions import chord as chord
from mowen.distance_functions import matusita as matusita
from mowen.distance_functions import soergel as soergel
from mowen.distance_functions import wave_hedges as wave_hedges
from mowen.distance_functions import wed as wed
from mowen.distance_functions import nominal_ks as nominal_ks

__all__ = ["DistanceFunction", "distance_function_registry"]
