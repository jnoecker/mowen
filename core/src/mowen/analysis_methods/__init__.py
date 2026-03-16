"""Built-in analysis methods for the mowen pipeline."""

from mowen.analysis_methods.base import (
    AnalysisMethod,
    CentroidAnalysisMethod,
    NeighborAnalysisMethod,
    analysis_method_registry,
)
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod

# Import implementation modules so their @register decorators execute.
from mowen.analysis_methods import absolute_centroid as absolute_centroid
from mowen.analysis_methods import burrows_delta as burrows_delta
from mowen.analysis_methods import centroid as centroid
from mowen.analysis_methods import decision_tree as decision_tree
from mowen.analysis_methods import knn as knn
from mowen.analysis_methods import lda as lda
from mowen.analysis_methods import markov_chain as markov_chain
from mowen.analysis_methods import naive_bayes as naive_bayes
from mowen.analysis_methods import nearest_neighbor as nearest_neighbor
from mowen.analysis_methods import svm as svm

__all__ = [
    "AnalysisMethod",
    "CentroidAnalysisMethod",
    "NeighborAnalysisMethod",
    "SklearnAnalysisMethod",
    "analysis_method_registry",
]
