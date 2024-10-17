"""Check collection utilities."""

import numpy as np
import pandas as pd

__maintainer__ = ["TonyBagnall"]


def is_tabular(X):
    """Check if input is a 2D table.

    Parameters
    ----------
    X : array-like

    Returns
    -------
    bool
        True if input is 2D, False otherwise.
    """
    if isinstance(X, np.ndarray):
        if X.ndim != 2:
            return False
        return True
    if isinstance(X, pd.DataFrame):
        return _is_pd_wide(X)


def is_collection(X, include_2d=False):
    """Check X is a valid collection data structure.

    Parameters
    ----------
    X : array-like
        Input data to be checked.
    include_2d : bool, optional
        If True, 2D numpy arrays and wide pandas DataFrames are also considered valid.

    Returns
    -------
    bool
        True if input is a collection, False otherwise.
    """
    if isinstance(X, np.ndarray):
        if X.ndim == 3:
            return True
        if include_2d and X.ndim == 2:
            return True
    if isinstance(X, pd.DataFrame):
        if X.index.nlevels == 2:
            return True
        if include_2d and _is_pd_wide(X):
            return True
    if isinstance(X, list):
        if isinstance(X[0], np.ndarray):
            if X[0].ndim == 2:
                return True
        if isinstance(X[0], pd.DataFrame):
            return True
    return False


def _is_pd_wide(X):
    """Check whether the input DataFrame is "pd-wide" type."""
    # only test is if all values are float.
    if isinstance(X, pd.DataFrame) and not isinstance(X.index, pd.MultiIndex):
        for col in X:
            if not np.issubdtype(X[col].dtype, np.floating):
                return False
        return True
    return False


def get_n_cases(X):
    """Return the number of cases in a collectiom.

    Handle the single exception of multi index DataFrame.

    Parameters
    ----------
    X : collection
        See aeon.utils.registry.COLLECTIONS_DATA_TYPES for details.

    Returns
    -------
    int
        Number of cases.
    """
    if isinstance(X, pd.DataFrame) and isinstance(X.index, pd.MultiIndex):
        return len(X.index.get_level_values(0).unique())
    return len(X)


def get_n_timepoints(X):
    """Return the number of timepoints in the first element of a collection.

    Handles the single exception of multi index DataFrames. If unequal length series,
    returns the length of the first series.

    Parameters
    ----------
    X : collection
        See aeon.utils.registry.COLLECTIONS_DATA_TYPES for details.

    Returns
    -------
    int
        Number of time points in the first case.
    """
    t = get_type(X)
    if t in ["numpy3D", "np-list"]:
        return X[0].shape[1]
    if t in ["numpy2D", "df-list"]:
        return X[0].shape[0]
    if t == "pd-multiindex":
        return len(X.index.get_level_values(1).unique())
    if t == "pd-wide":
        return len(X.iloc[0])


def get_n_channels(X):
    """Return the number of channels in the first element of a collectiom.

    Handle the single exception of multi index DataFrame.

    Parameters
    ----------
    X : collection
        See aeon.utils.registry.COLLECTIONS_DATA_TYPES for details.

    Returns
    -------
    int
        Number of channels in the first case.

    Raises
    ------
    ValueError
        X is list of 2D numpy but number of channels is not consistent.
        X is list of 2D pd.DataFrames but number of channels is not consistent.
    """
    t = get_type(X)
    if t == "numpy3D":
        return X[0].shape[0]
    if t == "np-list":
        if not all(arr.shape[0] == X[0].shape[0] for arr in X):
            raise ValueError(
                f"ERROR: number of channels is not consistent. "
                f"Found values: {np.unique([arr.shape[0] for arr in X])}."
            )
        return X[0].shape[0]
    if t in ["numpy2D", "pd-wide"]:
        return 1
    if t == "df-list":
        if not all(arr.shape[1] == X[0].shape[1] for arr in X):
            raise ValueError(
                f"ERROR: number of channels is not consistent. "
                f"Found values: {np.unique([arr.shape[1] for arr in X])}."
            )
        return X[0].shape[1]
    if t == "pd-multiindex":
        return len(X.columns)


def get_type(X):
    """Get the string identifier associated with different data structures.

    Parameters
    ----------
    X : collection
        See aeon.utils.registry.COLLECTIONS_DATA_TYPES for details.

    Returns
    -------
    input_type : string
        One of COLLECTIONS_DATA_TYPES.

    Raises
    ------
    ValueError
        X pd.ndarray but wrong dimension
        X is list but not of np.ndarray or p.DataFrame.
        X is a pd.DataFrame of non float primitives.

    Examples
    --------
    >>> from aeon.utils.validation import get_type
    >>> get_type( np.zeros(shape=(10, 3, 20)))
    'numpy3D'
    """
    if isinstance(X, np.ndarray):  # "numpy3D" or numpy2D
        if X.ndim == 3:
            return "numpy3D"
        elif X.ndim == 2:
            return "numpy2D"
        else:
            raise ValueError(
                f"ERROR np.ndarray must be 2D or 3D but found " f"{X.ndim}"
            )
    elif isinstance(X, list):  # np-list or df-list
        if isinstance(X[0], np.ndarray):  # if one a numpy they must all be 2D numpy
            for a in X:
                if not (isinstance(a, np.ndarray) and a.ndim == 2):
                    raise TypeError(
                        f"ERROR nnp-list must contain 2D np.ndarray but found {a.ndim}"
                    )
            return "np-list"
        elif isinstance(X[0], pd.DataFrame):
            for a in X:
                if not isinstance(a, pd.DataFrame):
                    raise TypeError("ERROR df-list must only contain pd.DataFrame")
            return "df-list"
        else:
            raise TypeError(
                f"ERROR passed a list containing {type(X[0])}, "
                f"lists should either 2D numpy arrays or pd.DataFrames."
            )
    elif isinstance(X, pd.DataFrame):  # Nested univariate, hierarchical or pd-wide
        if isinstance(X.index, pd.MultiIndex):
            return "pd-multiindex"
        elif _is_pd_wide(X):
            return "pd-wide"
        raise TypeError(
            "ERROR unknown pd.DataFrame, contains non float values, "
            "not hierarchical nor is it nested pd.Series"
        )
    raise TypeError(
        f"ERROR passed input of type {type(X)}, must be of type "
        f"np.ndarray, pd.DataFrame or list of np.ndarray/pd.DataFrame"
    )


def is_equal_length(X):
    """Test if X contains equal length time series.

    Assumes input_type is a valid type (COLLECTIONS_DATA_TYPES).

    Parameters
    ----------
    X : collection
        See aeon.utils.registry.COLLECTIONS_DATA_TYPES for details.

    Returns
    -------
    boolean
        True if all series in X are equal length, False otherwise.

    Raises
    ------
    ValueError
        input_type not in COLLECTIONS_DATA_TYPES.

    Examples
    --------
    >>> from aeon.utils.validation import is_equal_length
    >>> is_equal_length( np.zeros(shape=(10, 3, 20)))
    True
    """
    return _equal_length(X, get_type(X))


def has_missing(X):
    """Check if X has missing values.

    Parameters
    ----------
    X : collection
    input_type : string
        One of COLLECTIONS_DATA_TYPES.

    Returns
    -------
    boolean
        True if there are any missing values, False otherwise

    Raises
    ------
    ValueError
        Input_type not in COLLECTIONS_DATA_TYPES.

    Examples
    --------
    >>> from aeon.utils.validation import has_missing
    >>> has_missing( np.zeros(shape=(10, 3, 20)))
    False
    """
    type = get_type(X)
    if type == "numpy3D" or type == "numpy2D":
        return np.any(np.isnan(np.min(X)))
    if type == "np-list":
        for x in X:
            if np.any(np.isnan(np.min(x))):
                return True
        return False
    if type == "df-list":
        for x in X:
            if x.isnull().any().any():
                return True
        return False
    if type == "pd-wide":
        return X.isnull().any().any()
    if type == "pd-multiindex":
        if X.isna().values.any():
            return True
        return False


def is_univariate(X):
    """Check if X is multivariate."""
    type = get_type(X)
    if type == "numpy2D" or type == "pd-wide":
        return True
    if type == "numpy3D":
        return X.shape[1] == 1
    # df list (n_timepoints, n_channels)
    if type == "df-list":
        return X[0].shape[1] == 1
    # np list (n_channels, n_timepoints)
    if type == "np-list":
        return X[0].shape[0] == 1
    if type == "pd-multiindex":
        return X.columns.shape[0] == 1


def _equal_length(X, input_type):
    """Test if X contains equal length time series.

    Assumes input_type is a valid type (COLLECTIONS_DATA_TYPES).

    Parameters
    ----------
    X : collection
    input_type : string
        one of COLLECTIONS_DATA_TYPES

    Returns
    -------
    boolean
        True if all series in X are equal length, False otherwise

    Raises
    ------
    ValueError
        input_type not in COLLECTIONS_DATA_TYPES.

    Examples
    --------
    >>> _equal_length( np.zeros(shape=(10, 3, 20)), "numpy3D")
    True
    """
    always_equal = {"numpy3D", "numpy2D", "pd-wide"}
    if input_type in always_equal:
        return True
    # np-list are shape (n_channels, n_timepoints)
    if input_type == "np-list":
        first = X[0].shape[1]
        for i in range(1, len(X)):
            if X[i].shape[1] != first:
                return False
        return True
    # df-list are shape (n_timepoints, n_channels)
    if input_type == "df-list":
        first = X[0].shape[0]
        for i in range(1, len(X)):
            if X[i].shape[0] != first:
                return False
        return True
    if input_type == "pd-multiindex":  # multiindex dataframe
        X = X.reset_index(-1).drop(X.columns, axis=1)
        return (
            X.groupby(level=0, group_keys=True, as_index=True).count().nunique()[0] == 1
        )
    raise ValueError(f" unknown input type {input_type}")
    return False
