"""Stores the identifiers for internal data types for series and collections.

Identifiers relate to single series (SERIES_DATA_TYPES), collections of series
(COLLECTIONS_DATA_TYPES) and hierarchical collections of series
(HIERARCHICAL_DATA_TYPES). String identifiers are used to check and convert types,
since there are internal constraints on some representations, for example in terms of
the index.

Checks of input data are handled in the `aeon.utils.validation` module,
and conversion  is handled in the `aeon.utils.conversion` module.
"""

from enum import Enum


class SeriesDataTypeTag(Enum):
    """Tags for Series Data Type."""

    PD_SERIES = "pd.Series"  # univariate time series of shape (n_timepoints)
    PD_DATAFRAME = "pd.DataFrame"  # uni/multivariate time series of shape (n_timepoints
    # ,n_channels) by default or (n_channels, n_timepoints) if set by axis == 1
    NDARRAY = "np.ndarray"  # uni/multivariate time series of shape (n_timepoints,
    # n_channels) by default or (n_channels, n_timepoints) if set by axis ==1


class CollectionDataTypeTag(Enum):
    """Tags for Collection Data Type."""

    NUMPY_3D = "numpy3D"  # 3D np.ndarray of format (n_cases, n_channels, n_timepoints)
    NP_LIST = "np-list"  # python list of 2D np.ndarray of length [n_cases],
    # each of shape (n_channels, n_timepoints_i)
    DF_LIST = "df-list"  # python list of 2D pd.DataFrames of length [n_cases], each
    # of shape (n_channels, n_timepoints_i)
    NUMPY_2D = "numpy2D"  # 2D np.ndarray of shape (n_cases, n_timepoints)
    PD_WIDE = "pd-wide"  # 2D pd.DataFrame of shape (n_cases, n_timepoints)
    PD_MULTIINDEX = "pd-multiindex"  # pd.DataFrame with multi-index,


class HierarchicalDataTypeTag(Enum):
    """Tags for Hierarchical Data Type."""

    PD_MULTIINDEX_HIER = "pd_multiindex_hier"  # pd.DataFrame


ALL_TIME_SERIES_TYPES = (
    [item.value for item in SeriesDataTypeTag]
    + [item.value for item in CollectionDataTypeTag]
    + [item.value for item in HierarchicalDataTypeTag]
)
