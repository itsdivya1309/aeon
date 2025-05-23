"""Residual Network (ResNet) regressor."""

from __future__ import annotations

__maintainer__ = ["hadifawaz1999"]
__all__ = ["ResNetRegressor"]

import gc
import os
import time
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.utils import check_random_state

from aeon.networks import ResNetNetwork
from aeon.regression.deep_learning.base import BaseDeepRegressor

if TYPE_CHECKING:
    import tensorflow as tf
    from tensorflow.keras.callbacks import Callback


class ResNetRegressor(BaseDeepRegressor):
    """
    Residual Neural Network.

    Adapted from the implementation used in [1]_.

    Parameters
    ----------
        n_residual_blocks : int, default = 3
            the number of residual blocks of ResNet's model
        n_conv_per_residual_block : int, default = 3,
            the number of convolution blocks in each residual block
        n_filters : int or list of int, default = [128, 64, 64],
            the number of convolution filters for all the convolution layers in the same
            residual block, if not a list, the same number of filters is used in all
            convolutions of all residual blocks.
        kernel_sizes : int or list of int, default = [8, 5, 3],
            the kernel size of all the convolution layers in one residual block, if not
            a list, the same kernel size is used in all convolution layers
        strides : int or list of int, default = 1,
            the strides of convolution kernels in each of the
            convolution layers in one residual block, if not
            a list, the same kernel size is used in all convolution layers
        dilation_rate : int or list of int, default = 1,
            the dilation rate of the convolution layers in one residual block, if not
            a list, the same kernel size is used in all convolution layers
        padding : str or list of str, default = 'padding',
            the type of padding used in the convolution layers
            in one residual block, if not
            a list, the same kernel size is used in all convolution layers
        activation : str or list of str, default = 'relu',
            keras activation used in the convolution layers
            in one residual block, if not
            a list, the same kernel size is used in all convolution layers
        output_activation : str, default = "linear",
            the output activation for the regressor
        use_bias : bool or list of bool, default = True,
            condition on whether or not to use bias values in
            the convolution layers in one residual block, if not
            a list, the same kernel size is used in all convolution layers
        n_epochs : int, default = 1500
            the number of epochs to train the model
        batch_size : int, default = 16
            the number of samples per gradient update.
        use_mini_batch_size : bool, default = False
            condition on using the mini batch size formula Wang et al.
        callbacks : keras callback or list of callbacks,
            default = None
            The default list of callbacks are set to
            ModelCheckpoint and ReduceLROnPlateau.
        random_state : int, RandomState instance or None, default=None
            If `int`, random_state is the seed used by the random number generator;
            If `RandomState` instance, random_state is the random number generator;
            If `None`, the random number generator is the `RandomState` instance used
            by `np.random`.
            Seeded random number generation can only be guaranteed on CPU processing,
            GPU processing will be non-deterministic.
        file_path : str, default = './'
            file_path when saving model_Checkpoint callback
        save_best_model : bool, default = False
            Whether or not to save the best model, if the
            modelcheckpoint callback is used by default,
            this condition, if True, will prevent the
            automatic deletion of the best saved model from
            file and the user can choose the file name
        save_last_model : bool, default = False
            Whether or not to save the last model, last
            epoch trained, using the base class method
            save_last_model_to_file
        save_init_model : bool, default = False
            Whether to save the initialization of the  model.
        best_file_name : str, default = "best_model"
            The name of the file of the best model, if
            save_best_model is set to False, this parameter
            is discarded
        last_file_name : str, default = "last_model"
            The name of the file of the last model, if
            save_last_model is set to False, this parameter
            is discarded
        init_file_name : str, default = "init_model"
            The name of the file of the init model, if save_init_model is set to False,
            this parameter is discarded.
        verbose : boolean, default = False
            whether to output extra information
        loss : str, default = "mean_squared_error"
            The name of the keras training loss.
        optimizer : keras.optimizer, default = tf.keras.optimizers.Adam()
            The keras optimizer used for training.
        metrics : str or list[str], default="mean_squared_error"
            The evaluation metrics to use during training. If
            a single string metric is provided, it will be
            used as the only metric. If a list of metrics are
            provided, all will be used for evaluation.

    Notes
    -----
    Adapted from the implementation from source code
    https://github.com/hfawaz/dl-4-tsc/blob/master/classifiers/resnet.py

    References
    ----------
        .. [1] Wang et. al, Time series classification from
    scratch with deep neural networks: A strong baseline,
    International joint conference on neural networks (IJCNN), 2017.

    Examples
    --------
    >>> from aeon.regression.deep_learning import ResNetRegressor
    >>> from aeon.testing.data_generation import make_example_3d_numpy
    >>> X, y = make_example_3d_numpy(n_cases=10, n_channels=1, n_timepoints=12,
    ...                              return_y=True, regression_target=True,
    ...                              random_state=0)
    >>> rgs = ResNetRegressor(n_epochs=20, batch_size=4) # doctest: +SKIP
    >>> rgs.fit(X, y) # doctest: +SKIP
    ResNetRegressor(...)
    """

    def __init__(
        self,
        n_residual_blocks: int = 3,
        n_conv_per_residual_block: int = 3,
        n_filters: int | list[int] | None = None,
        kernel_size: int | list[int] | None = None,
        strides: int | list[int] = 1,
        dilation_rate: int | list[int] = 1,
        padding: str | list[str] = "same",
        activation: str | list[str] = "relu",
        use_bias: bool | list[bool] = True,
        n_epochs: int = 1500,
        callbacks: Callback | list[Callback] | None = None,
        verbose: bool = False,
        loss: str = "mean_squared_error",
        output_activation: str = "linear",
        metrics: str | list[str] = "mean_squared_error",
        batch_size: int = 64,
        use_mini_batch_size: bool = False,
        random_state: int | np.random.RandomState | None = None,
        file_path: str = "./",
        save_best_model: bool = False,
        save_last_model: bool = False,
        save_init_model: bool = False,
        best_file_name: str = "best_model",
        last_file_name: str = "last_model",
        init_file_name: str = "init_model",
        optimizer: tf.keras.optimizers.Optimizer | None = None,
    ):
        self.n_residual_blocks = n_residual_blocks
        self.n_conv_per_residual_block = n_conv_per_residual_block
        self.n_filters = n_filters
        self.kernel_size = kernel_size
        self.padding = padding
        self.strides = strides
        self.dilation_rate = dilation_rate
        self.n_epochs = n_epochs
        self.callbacks = callbacks
        self.verbose = verbose
        self.loss = loss
        self.metrics = metrics
        self.use_mini_batch_size = use_mini_batch_size
        self.random_state = random_state
        self.activation = activation
        self.output_activation = output_activation
        self.use_bias = use_bias
        self.file_path = file_path
        self.save_best_model = save_best_model
        self.save_last_model = save_last_model
        self.save_init_model = save_init_model
        self.best_file_name = best_file_name
        self.init_file_name = init_file_name
        self.optimizer = optimizer

        self.history = None

        super().__init__(batch_size=batch_size, last_file_name=last_file_name)

        self._network = ResNetNetwork(
            n_residual_blocks=self.n_residual_blocks,
            n_conv_per_residual_block=self.n_conv_per_residual_block,
            n_filters=self.n_filters,
            kernel_size=self.kernel_size,
            strides=self.strides,
            use_bias=self.use_bias,
            activation=self.activation,
            dilation_rate=self.dilation_rate,
            padding=self.padding,
        )

    def build_model(
        self, input_shape: tuple[int, ...], **kwargs: Any
    ) -> tf.keras.Model:
        """Construct a compiled, un-trained, keras model that is ready for training.

        In aeon, time series are stored in numpy arrays of shape (d,m), where d
        is the number of dimensions, m is the series length. Keras/tensorflow assume
        data is in shape (m,d). This method also assumes (m,d). Transpose should
        happen in fit.

        Parameters
        ----------
        input_shape : tuple
            The shape of the data fed into the input layer, should be (m,d)

        Returns
        -------
        output : a compiled Keras Model
        """
        import tensorflow as tf

        self.optimizer_ = (
            tf.keras.optimizers.Adam(learning_rate=0.01)
            if self.optimizer is None
            else self.optimizer
        )

        rng = check_random_state(self.random_state)
        self.random_state_ = rng.randint(0, np.iinfo(np.int32).max)
        tf.keras.utils.set_random_seed(self.random_state_)
        input_layer, output_layer = self._network.build_network(input_shape, **kwargs)

        output_layer = tf.keras.layers.Dense(
            units=1,
            activation=self.output_activation,
        )(output_layer)

        model = tf.keras.models.Model(inputs=input_layer, outputs=output_layer)
        model.compile(
            loss=self.loss,
            optimizer=self.optimizer_,
            metrics=self._metrics,
        )

        return model

    def _fit(self, X: np.ndarray, y: np.ndarray) -> ResNetRegressor:
        """Fit the regressor on the training set (X, y).

        Parameters
        ----------
        X : np.ndarray
            The training input samples of shape (n_cases, n_channels, n_timepoints).
        y : np.ndarray
            The training data target values of shape (n_cases,).

        Returns
        -------
        self : object
        """
        import tensorflow as tf

        # Transpose to conform to Keras input style.
        X = X.transpose(0, 2, 1)

        if isinstance(self.metrics, list):
            self._metrics = self.metrics
        elif isinstance(self.metrics, str):
            self._metrics = [self.metrics]

        self.input_shape = X.shape[1:]
        self.training_model_ = self.build_model(self.input_shape)

        if self.save_init_model:
            self.training_model_.save(self.file_path + self.init_file_name + ".keras")

        if self.verbose:
            self.training_model_.summary()

        self.file_name_ = (
            self.best_file_name if self.save_best_model else str(time.time_ns())
        )

        if self.callbacks is None:
            self.callbacks_ = [
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor="loss", factor=0.5, patience=50, min_lr=0.0001
                ),
                tf.keras.callbacks.ModelCheckpoint(
                    filepath=self.file_path + self.file_name_ + ".keras",
                    monitor="loss",
                    save_best_only=True,
                ),
            ]
        else:
            self.callbacks_ = self._get_model_checkpoint_callback(
                callbacks=self.callbacks,
                file_path=self.file_path,
                file_name=self.file_name_,
            )

        if self.use_mini_batch_size:
            mini_batch_size = min(self.batch_size, X.shape[0] // 10)
        else:
            mini_batch_size = self.batch_size

        self.history = self.training_model_.fit(
            X,
            y,
            batch_size=mini_batch_size,
            epochs=self.n_epochs,
            verbose=self.verbose,
            callbacks=self.callbacks_,
        )

        try:
            self.model_ = tf.keras.models.load_model(
                self.file_path + self.file_name_ + ".keras", compile=False
            )
            if not self.save_best_model:
                os.remove(self.file_path + self.file_name_ + ".keras")
        except FileNotFoundError:
            self.model_ = deepcopy(self.training_model_)

        if self.save_last_model:
            self.save_last_model_to_file(file_path=self.file_path)

        gc.collect()
        return self

    @classmethod
    def _get_test_params(
        cls, parameter_set: str = "default"
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
            For regressors, a "default" set of parameters should be provided for
            general testing, and a "results_comparison" set for comparing against
            previously recorded results if the general set does not produce suitable
            probabilities to compare against.

        Returns
        -------
        params : dict or list of dict, default={}
            Parameters to create testing instances of the class.
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
        """
        param = {
            "n_epochs": 10,
            "batch_size": 4,
            "n_residual_blocks": 1,
            "n_filters": 5,
            "n_conv_per_residual_block": 1,
            "kernel_size": 3,
        }

        return [param]
