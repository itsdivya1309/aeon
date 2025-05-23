"""Encoder Regressor."""

from __future__ import annotations

__author__ = ["AnonymousCodes911", "hadifawaz1999"]
__all__ = ["EncoderRegressor"]


import gc
import os
import time
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import numpy as np
from sklearn.utils import check_random_state

from aeon.networks import EncoderNetwork
from aeon.regression.deep_learning.base import BaseDeepRegressor

if TYPE_CHECKING:
    import tensorflow as tf
    from tensorflow.keras.callbacks import Callback


class EncoderRegressor(BaseDeepRegressor):
    """
    Establishing the network structure for an Encoder.

    Adapted from the implementation used in classification.deeplearning

    Parameters
    ----------
    kernel_size : array of int, default = [5, 11, 21]
        Specifying the length of the 1D convolution windows.
    n_filters : array of int, default = [128, 256, 512]
        Specifying the number of 1D convolution filters used for each layer,
        the shape of this array should be the same as kernel_size.
    max_pool_size : int, default = 2
        Size of the max pooling windows.
    activation : string, default = sigmoid
        Keras activation function.
    output_activation   : str, default = "linear",
        the output activation of the regressor
    dropout_proba : float, default = 0.2
        Specifying the dropout layer probability.
    padding : string, default = same
        Specifying the type of padding used for the 1D convolution.
    strides : int, default = 1
        Specifying the sliding rate of the 1D convolution filter.
    fc_units : int, default = 256
        Specifying the number of units in the hidden fully
        connected layer used in the EncoderNetwork.
    file_path : str, default = "./"
        File path when saving model_Checkpoint callback.
    save_best_model : bool, default = False
        Whether or not to save the best model, if the
        modelcheckpoint callback is used by default,
        this condition, if True, will prevent the
        automatic deletion of the best saved model from
        file and the user can choose the file name.
    save_last_model : bool, default = False
        Whether or not to save the last model, last
        epoch trained, using the base class method
        save_last_model_to_file.
    save_init_model : bool, default = False
        Whether to save the initialization of the  model.
    best_file_name : str, default = "best_model"
        The name of the file of the best model, if
        save_best_model is set to False, this parameter
        is discarded.
    last_file_name : str, default = "last_model"
        The name of the file of the last model, if
        save_last_model is set to False, this parameter
        is discarded.
    init_file_name : str, default = "init_model"
        The name of the file of the init model, if save_init_model is set to False,
        this parameter is discarded.
    n_epochs:
        The number of times the entire training dataset
        will be passed forward and backward
        through the neural network.
    random_state : int, RandomState instance or None, default=None
        If `int`, random_state is the seed used by the random number generator;
        If `RandomState` instance, random_state is the random number generator;
        If `None`, the random number generator is the `RandomState` instance used
        by `np.random`.
        Seeded random number generation can only be guaranteed on CPU processing,
        GPU processing will be non-deterministic.
    loss : str, default = "mean_squared_error"
        The name of the keras training loss.
    metrics : str or list[str], default="mean_squared_error"
        The evaluation metrics to use during training. If
        a single string metric is provided, it will be
        used as the only metric. If a list of metrics are
        provided, all will be used for evaluation.
    use_bias:
        Whether to use bias in the dense layers.
    optimizer : keras.optimizer, default = tf.keras.optimizers.Adam()
        The keras optimizer used for training.
    verbose:
        Whether to print progress messages during training.
    callbacks : keras callback or list of callbacks,
        default = None
        The default list of callbacks are set to
        ModelCheckpoint.

    Notes
    -----
    Adapted from source code
    https://github.com/hfawaz/dl-4-tsc/blob/master/classifiers/encoder.py

    References
    ----------
    ..[1] Serrà et al. Towards a Universal Neural Network Encoder for Time Series
    In proceedings International Conference of the Catalan Association
    for Artificial Intelligence, 120--129 2018.

    """

    def __init__(
        self,
        n_epochs: int = 100,
        batch_size: int = 12,
        kernel_size: list[int] | None = None,
        n_filters: list[int] | None = None,
        dropout_proba: float = 0.2,
        activation: str = "sigmoid",
        output_activation: str = "linear",
        max_pool_size: int = 2,
        padding: str = "same",
        strides: int = 1,
        fc_units: int = 256,
        callbacks: Callback | list[Callback] | None = None,
        file_path: str = "./",
        save_best_model: bool = False,
        save_last_model: bool = False,
        save_init_model: bool = False,
        best_file_name: str = "best_model",
        last_file_name: str = "last_model",
        init_file_name: str = "init_model",
        verbose: bool = False,
        loss: str = "mean_squared_error",
        metrics: str | list[str] = "mean_squared_error",
        use_bias: bool = True,
        optimizer: tf.keras.optimizers.Optimizer | None = None,
        random_state: int | np.random.RandomState | None = None,
    ):
        self.n_filters = n_filters
        self.max_pool_size = max_pool_size
        self.kernel_size = kernel_size
        self.strides = strides
        self.activation = activation
        self.output_activation = output_activation
        self.padding = padding
        self.dropout_proba = dropout_proba
        self.fc_units = fc_units
        self.random_state = random_state
        self.callbacks = callbacks
        self.file_path = file_path
        self.save_best_model = save_best_model
        self.save_last_model = save_last_model
        self.save_init_model = save_init_model
        self.best_file_name = best_file_name
        self.init_file_name = init_file_name
        self.n_epochs = n_epochs
        self.verbose = verbose
        self.loss = loss
        self.metrics = metrics
        self.use_bias = use_bias
        self.optimizer = optimizer

        self.history = None

        super().__init__(
            batch_size=batch_size,
            last_file_name=last_file_name,
        )

        self._network = EncoderNetwork(
            kernel_size=self.kernel_size,
            max_pool_size=self.max_pool_size,
            n_filters=self.n_filters,
            fc_units=self.fc_units,
            strides=self.strides,
            padding=self.padding,
            dropout_proba=self.dropout_proba,
            activation=self.activation,
        )

    def build_model(
        self, input_shape: tuple[int, ...], **kwargs: Any
    ) -> tf.keras.Model:
        """Construct a compiled, un-trained, keras model that is ready for training.

        In aeon, time series are stored in numpy arrays of shape (d, m), where d
        is the number of dimensions, m is the series length. Keras/tensorflow assume
        data is in shape (m, d). This method also assumes (m, d). Transpose should
        happen in fit.

        Parameters
        ----------
        input_shape : tuple
        The shape of the data fed into the input layer, should be (m, d).
        Gives
        -------
        output : a compiled Keras Model
        """
        import tensorflow as tf

        rng = check_random_state(self.random_state)
        self.random_state_ = rng.randint(0, np.iinfo(np.int32).max)
        tf.keras.utils.set_random_seed(self.random_state_)
        input_layer, output_layer = self._network.build_network(input_shape, **kwargs)

        output_layer = tf.keras.layers.Dense(
            units=1, activation=self.output_activation
        )(output_layer)

        self.optimizer_ = (
            tf.keras.optimizers.Adam(learning_rate=0.00001)
            if self.optimizer is None
            else self.optimizer
        )

        model = tf.keras.models.Model(inputs=input_layer, outputs=output_layer)
        model.compile(
            loss=self.loss,
            optimizer=self.optimizer_,
            metrics=self._metrics,
        )

        return model

    def _fit(self, X: np.ndarray, y: np.ndarray) -> EncoderRegressor:
        """Fit the classifier on the training set (X, y).

        Parameters
        ----------
        X : np.ndarray of shape = (n_cases, n_channels, n_timepoints)
            The training input samples.
        y : np.ndarray of shape n
            The training data Target Values.

        Gives
        -------
        self : object
        """
        import tensorflow as tf

        # Transpose X to conform to Keras input style
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

        self.history = self.training_model_.fit(
            X,
            y,
            batch_size=self.batch_size,
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
        parameter_set : str, default = "default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return "default" set.
            For regressors, a "default" set of parameters should be provided for
            general testing, and a "results_comparison" set for comparing against
            previously recorded results if the general set does not produce suitable
            predictions to compare against.

        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class.
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
        """
        param1 = {
            "n_epochs": 8,
            "batch_size": 4,
            "use_bias": False,
            "fc_units": 8,
            "strides": 2,
            "dropout_proba": 0,
        }

        test_params = [param1]

        return test_params
