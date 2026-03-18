"""General Imposters Method (Koppel & Winter 2014).

Authorship verification method that measures whether an unknown document
is consistently closer to a candidate author's texts than to "imposter"
texts by other authors, across random feature subsets.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

from mowen.analysis_methods.base import NeighborAnalysisMethod, analysis_method_registry
from mowen.parameters import ParamDef
from mowen.types import Attribution, Document, Event, Histogram


def _restrict_histogram(h: Histogram, feature_subset: set[Event]) -> Histogram:
    """Build a new Histogram containing only the specified events."""
    return Histogram({e: h.absolute_frequency(e) for e in feature_subset if e in h})


@analysis_method_registry.register("imposters")
@dataclass
class GeneralImposters(NeighborAnalysisMethod):
    """Attribute authorship using the General Imposters Method.

    For each candidate author, runs many iterations where a random subset
    of features is selected and a random subset of imposter documents is
    sampled.  The unknown document is compared to the candidate's nearest
    document and the nearest imposter; the fraction of iterations where the
    candidate is closer gives the verification score.

    Score semantics: higher = more likely same author (0-1 proportion).
    """

    lower_is_better: bool = False
    verification_threshold: float = 0.5

    display_name: str = "General Imposters Method"
    description: str = (
        "Authorship verification via random feature subsets and imposter comparison "
        "(Koppel & Winter 2014)."
    )

    _author_histograms: dict[str, list[Histogram]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _all_events: set[Event] = field(
        default_factory=set,
        init=False,
        repr=False,
    )

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="n_iterations",
                description="Number of random iterations per candidate.",
                param_type=int,
                default=100,
                min_value=1,
                max_value=10000,
            ),
            ParamDef(
                name="feature_subset_ratio",
                description="Fraction of vocabulary to sample each iteration.",
                param_type=float,
                default=0.5,
                min_value=0.01,
                max_value=1.0,
            ),
            ParamDef(
                name="n_imposters",
                description="Number of imposter documents to sample each iteration.",
                param_type=int,
                default=10,
                min_value=1,
                max_value=1000,
            ),
            ParamDef(
                name="random_seed",
                description="Random seed for reproducibility (0 = non-deterministic).",
                param_type=int,
                default=0,
            ),
            ParamDef(
                name="calibration_low",
                description=(
                    "Lower calibration threshold. Scores in "
                    "[low, high] are set to 0.5 (non-answer). "
                    "Set both to 0.0 to disable calibration."
                ),
                param_type=float,
                default=0.0,
                min_value=0.0,
                max_value=1.0,
            ),
            ParamDef(
                name="calibration_high",
                description=(
                    "Upper calibration threshold. Scores in "
                    "[low, high] are set to 0.5 (non-answer). "
                    "Set both to 0.0 to disable calibration."
                ),
                param_type=float,
                default=0.0,
                min_value=0.0,
                max_value=1.0,
            ),
        ]

    def train(self, known_docs: list[tuple[Document, Histogram]]) -> None:
        """Group known documents by author and collect vocabulary."""
        super().train(known_docs)

        self._author_histograms = defaultdict(list)
        self._all_events = set()

        for doc, hist in self._known_docs:
            author = doc.author or ""
            self._author_histograms[author].append(hist)
            self._all_events.update(hist.unique_events())

    def analyze(self, unknown_histogram: Histogram) -> list[Attribution]:
        """Return attributions ranked by imposter verification score."""
        df = self._require_distance_function()

        n_iterations: int = self.get_param("n_iterations")
        feature_ratio: float = self.get_param("feature_subset_ratio")
        n_imposters: int = self.get_param("n_imposters")
        seed: int = self.get_param("random_seed")
        rng = random.Random(seed if seed != 0 else None)

        all_events_list = sorted(self._all_events, key=lambda e: e.data)
        n_features = max(1, int(len(all_events_list) * feature_ratio))

        authors = list(self._author_histograms.keys())
        attributions: list[Attribution] = []

        for candidate in authors:
            candidate_hists = self._author_histograms[candidate]

            # Collect imposter histograms (all docs not by this candidate)
            imposter_hists: list[Histogram] = []
            for other_author, hists in self._author_histograms.items():
                if other_author != candidate:
                    imposter_hists.extend(hists)

            # If no imposters available, score is 1.0 (only candidate)
            if not imposter_hists:
                attributions.append(Attribution(author=candidate, score=1.0))
                continue

            wins = 0
            for _ in range(n_iterations):
                # Sample feature subset
                subset = set(
                    rng.sample(all_events_list, min(n_features, len(all_events_list)))
                )

                # Sample imposters (with replacement if needed)
                n_sample = min(n_imposters, len(imposter_hists))
                sampled_imposters = rng.choices(imposter_hists, k=n_sample)

                # Restrict histograms to feature subset
                unknown_r = _restrict_histogram(unknown_histogram, subset)

                # Find nearest candidate document
                min_cand_dist = min(
                    df.distance(unknown_r, _restrict_histogram(h, subset))
                    for h in candidate_hists
                )

                # Find nearest imposter document
                min_imp_dist = min(
                    df.distance(unknown_r, _restrict_histogram(h, subset))
                    for h in sampled_imposters
                )

                if min_cand_dist < min_imp_dist:
                    wins += 1

            score = wins / n_iterations
            attributions.append(Attribution(author=candidate, score=score))

        # Apply dual-threshold calibration (non-answer band)
        cal_lo: float = self.get_param("calibration_low")
        cal_hi: float = self.get_param("calibration_high")
        if cal_lo > 0 or cal_hi > 0:
            attributions = [
                Attribution(
                    author=a.author,
                    score=0.5 if cal_lo <= a.score <= cal_hi else a.score,
                )
                for a in attributions
            ]

        attributions.sort(key=lambda a: a.score, reverse=True)
        return attributions
