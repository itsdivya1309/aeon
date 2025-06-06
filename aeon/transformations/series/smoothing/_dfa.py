"""Discrete Fourier Approximation filter transformation for smoothing."""

__maintainer__ = ["Cyril-Meyer"]
__all__ = ["DiscreteFourierApproximation"]


import numpy as np

from aeon.transformations.series.base import BaseSeriesTransformer


class DiscreteFourierApproximation(BaseSeriesTransformer):
    """Filter a times series using a Discrete Fourier Approximation.

    Smooths the series by first transforming into the frequency domain, discarding
    the high frequency terms, then transforming back to the time domain.

    Parameters
    ----------
    r : float, default=0.5
        Proportion of Fourier terms to retain [0, 1]
    sort : bool, default=False
        Sort the Fourier terms by amplitude to keep most important terms

    References
    ----------
    .. [1] Cooley, J., Lewis, P., Welch, P.: The fast fourier transform and its
        applications. IEEE Trans. Educ. 12(1), 27–34 (1969)

    Examples
    --------
    >>> import numpy as np
    >>> from aeon.transformations.series.smoothing import DiscreteFourierApproximation
    >>> X = np.random.random((2, 100)) # Random series length 100
    >>> dft = DiscreteFourierApproximation()
    >>> X_ = dft.fit_transform(X)
    >>> X_.shape
    (2, 100)
    """

    _tags = {
        "capability:multivariate": True,
        "X_inner_type": "np.ndarray",
        "fit_is_empty": True,
    }

    def __init__(self, r=0.5, sort=False):
        self.r = r
        self.sort = sort
        super().__init__(axis=1)

    def _transform(self, X, y=None):
        """Transform X and return a transformed version.

        Parameters
        ----------
        X : np.ndarray
            time series in shape (n_channels, n_timepoints)
        y : ignored argument for interface compatibility

        Returns
        -------
        transformed version of X
        """
        # Compute DFT
        dft = np.fft.fft(X)

        # Mask array of terms to keep and number of terms to keep
        mask = np.zeros_like(dft, dtype=bool)
        keep = max(int(self.r * dft.shape[1]), 1)

        # If sort is set, sort the indices by the decreasing dft amplitude
        if self.sort:
            sorted_indices = np.argsort(np.abs(dft))[:, ::-1]
            for i in range(dft.shape[0]):
                mask[i, sorted_indices[i, 0:keep]] = True
        # Else, keep the first terms
        else:
            mask[:, 0:keep] = True

        # Invert DFT with masked terms
        X_ = np.fft.ifft(dft * mask).real

        return X_
