"""Built-in analysis methods for the mowen pipeline."""

from mowen.analysis_methods.base import (
    AnalysisMethod,
    CentroidAnalysisMethod,
    NeighborAnalysisMethod,
    analysis_method_registry,
)
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod

# Import implementation modules so their @register decorators execute.
# Ordered: most commonly used / best-performing first.

# --- Distance-based (classic stylometry) ---
from mowen.analysis_methods import nearest_neighbor as nearest_neighbor
from mowen.analysis_methods import burrows_delta as burrows_delta
from mowen.analysis_methods import centroid as centroid
from mowen.analysis_methods import knn as knn
from mowen.analysis_methods import absolute_centroid as absolute_centroid
from mowen.analysis_methods import bagging_nn as bagging_nn
from mowen.analysis_methods import markov_chain as markov_chain
from mowen.analysis_methods import thin_xent as thin_xent
from mowen.analysis_methods import mahalanobis as mahalanobis
from mowen.analysis_methods import eders_delta as eders_delta
from mowen.analysis_methods import imposters as imposters
from mowen.analysis_methods import unmasking as unmasking

# --- Sklearn classifiers (also work with embeddings) ---
from mowen.analysis_methods import svm as svm
from mowen.analysis_methods import random_forest as random_forest
from mowen.analysis_methods import logistic_regression as logistic_regression
from mowen.analysis_methods import lda as lda
from mowen.analysis_methods import naive_bayes as naive_bayes
from mowen.analysis_methods import decision_tree as decision_tree
from mowen.analysis_methods import mlp as mlp

__all__ = [
    "AnalysisMethod",
    "CentroidAnalysisMethod",
    "NeighborAnalysisMethod",
    "SklearnAnalysisMethod",
    "analysis_method_registry",
]
