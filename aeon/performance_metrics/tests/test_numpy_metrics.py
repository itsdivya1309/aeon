"""Tests for numpy metrics in _functions module."""

from inspect import getmembers, isfunction

import numpy as np
import pandas as pd
import pytest

from aeon.performance_metrics.forecasting import _functions
from aeon.testing.data_generation._legacy import make_series

numpy_metrics = getmembers(_functions, isfunction)

exclude_starts_with = ("_", "check", "gmean", "weighted_geometric_mean")
numpy_metrics = [x for x in numpy_metrics if not x[0].startswith(exclude_starts_with)]

names, metrics = zip(*numpy_metrics)


@pytest.mark.parametrize("n_columns", [1, 2])
@pytest.mark.parametrize("multioutput", ["uniform_average", "raw_values"])
@pytest.mark.parametrize("metric", metrics, ids=names)
def test_metric_output(metric, multioutput, n_columns):
    """Test output is correct class."""
    y_pred = make_series(n_columns=n_columns, n_timepoints=20, random_state=21)
    y_true = make_series(n_columns=n_columns, n_timepoints=20, random_state=42)

    # coerce to DataFrame since make_series does not return consisten output type
    y_pred = pd.DataFrame(y_pred)
    y_true = pd.DataFrame(y_true)

    res = metric(
        y_true=y_true,
        y_pred=y_pred,
        multioutput=multioutput,
        y_pred_benchmark=y_pred,
        y_train=y_true,
    )

    if multioutput == "uniform_average":
        assert isinstance(res, float)
    elif multioutput == "raw_values":
        assert isinstance(res, np.ndarray)
        assert res.ndim == 1
        assert len(res) == len(y_true.columns)
