"""
Base class template for estimators.

Interface specifications below.

---

Parameter inspection and setter methods
    inspect parameter values      - get_params()
    setting parameter values      - set_params(**params)
    fitted parameter inspection - get_fitted_params()

Tag inspection and setter methods
    inspect tags (all)            - get_tags()
    inspect tags (one tag)        - get_tag(tag_name: str, tag_value_default=None)
    inspect tags (class method)   - get_class_tags()
    inspect tags (one tag, class) - get_class_tag(tag_name:str, tag_value_default=None)
    setting dynamic tags          - set_tags(**tag_dict: dict)
    set/clone dynamic tags        - clone_tags(estimator, tag_names=None)

Blueprinting: resetting and cloning, post-init state with same hyper-parameters
    reset estimator to post-init  - reset()
    cloneestimator (copy&reset)   - clone()

Testing with default parameters methods
    getting default parameters (all sets)         - get_test_params()
    get one test instance with default parameters - create_test_instance()
    get list of all test instances plus name list - create_test_instances_and_names()

State:
    fitted model/strategy   - by convention, any attributes ending in "_"
    fitted state flag       - is_fitted (property)
    fitted state check      - check_is_fitted (raises error if not is_fitted)
"""

__maintainer__ = ["MatthewMiddlehurst", "TonyBagnall"]
__all__ = ["BaseEstimator"]

import inspect
from copy import deepcopy

from sklearn import clone
from sklearn.base import BaseEstimator as _BaseEstimator
from sklearn.ensemble._base import _set_random_states
from sklearn.exceptions import NotFittedError


class BaseEstimator(_BaseEstimator):
    """Base class for defining estimators in aeon."""

    _tags = {
        "python_version": None,
        "python_dependencies": None,
        "cant-pickle": False,
        "non-deterministic": False,
        "algorithm_type": None,
        "capability:missing_values": False,
        "capability:multithreading": False,
    }

    def __init__(self):
        self._is_fitted = False  # flag to indicate if fit has been called
        self._tags_dynamic = dict()  # storage for dynamic tags

        super().__init__()

    def reset(self, keep=None):
        """Reset the object to a clean post-init state.

        Equivalent to sklearn.clone but overwrites self.
        After ``self.reset()`` call, self is equal in value to
        ``type(self)(**self.get_params(deep=False))``

        Detail behaviour:
        removes any object attributes, except:
            hyper-parameters = arguments of ``__init__``
            object attributes containing double-underscores, i.e., the string "__"
        runs ``__init__`` with current values of hyper-parameters (result of get_params)

        Not affected by the reset are:
        object attributes containing double-underscores
        class and object methods, class attributes
        """
        # retrieve parameters to copy them later
        params = self.get_params(deep=False)

        # delete all object attributes in self
        attrs = [attr for attr in dir(self) if "__" not in attr]
        cls_attrs = [attr for attr in dir(type(self))]
        self_attrs = set(attrs).difference(cls_attrs)

        # keep specific attributes if set
        if keep is not None:
            if isinstance(keep, str):
                keep = [keep]
            elif not isinstance(keep, list):
                raise TypeError(
                    "keep must be a string or list of strings containing attributes "
                    "to keep after the reset."
                )
            for attr in keep:
                self_attrs.discard(attr)

        for attr in self_attrs:
            delattr(self, attr)

        # run init with a copy of parameters self had at the start
        self.__init__(**params)

        return self

    def clone(self, random_state=None):
        """
        Obtain a clone of the object with same hyper-parameters.

        A clone is a different object without shared references, in post-init state.
        This function is equivalent to returning sklearn.clone of self.
        Equal in value to ``type(self)(**self.get_params(deep=False))``.

        Returns
        -------
        instance of ``type(self)``, clone of self (see above)
        """
        estimator = clone(self)

        if random_state is not None:
            _set_random_states(estimator, random_state)

        return estimator

    @classmethod
    def get_class_tags(cls):
        """
        Get class tags from estimator class and all its parent classes.

        Returns
        -------
        collected_tags : dict
            Dictionary of tag name : tag value pairs. Collected from _tags
            class attribute via nested inheritance. NOT overridden by dynamic
            tags set by set_tags or mirror_tags.
        """
        collected_tags = dict()

        # We exclude the last two parent classes: sklearn.base.BaseEstimator and
        # the basic Python object.
        for parent_class in reversed(inspect.getmro(cls)[:-2]):
            if hasattr(parent_class, "_tags"):
                # Need the if here because mixins might not have _more_tags
                # but might do redundant work in estimators
                # (i.e. calling more tags on BaseEstimator multiple times)
                more_tags = parent_class._tags
                collected_tags.update(more_tags)

        return deepcopy(collected_tags)

    @classmethod
    def get_class_tag(cls, tag_name, tag_value_default=None, raise_error=False):
        """
        Get tag value from estimator class (only class tags).

        Parameters
        ----------
        tag_name : str
            Name of tag value.
        tag_value_default : any type
            Default/fallback value if tag is not found.
        raise_error : bool
            Whether a ValueError is raised when the tag is not found.

        Returns
        -------
        tag_value :
            Value of the `tag_name` tag in self. If not found, returns an error if
            raise_error is True, otherwise it returns `tag_value_default`.

        Raises
        ------
        ValueError if raise_error is True i.e. if tag_name is not in self.get_tags(
        ).keys()

        See Also
        --------
        get_tag : Get a single tag from an object.
        get_tags : Get all tags from an object.
        get_class_tag : Get a single tag from a class.

        Examples
        --------
        >>> from aeon.classification import DummyClassifier
        >>> DummyClassifier.get_class_tag("capability:multivariate")
        True
        """
        collected_tags = cls.get_class_tags()

        tag_value = collected_tags.get(tag_name, tag_value_default)

        if raise_error and tag_name not in collected_tags.keys():
            raise ValueError(f"Tag with name {tag_name} could not be found.")

        return tag_value

    def get_tags(self):
        """
        Get tags from estimator class.

        Includes the dynamic tag overrides.

        Returns
        -------
        dict
            Dictionary of tag name : tag value pairs. Collected from _tags
            class attribute via nested inheritance and then any overrides
            and new tags from _tags_dynamic object attribute.

        See Also
        --------
        get_tag : Get a single tag from an object.
        get_class_tags : Get all tags from a class.
        get_class_tag : Get a single tag from a class.

        Examples
        --------
        >>> from aeon.classification import DummyClassifier
        >>> d = DummyClassifier()
        >>> tags = d.get_tags()
        """
        collected_tags = self.get_class_tags()

        if hasattr(self, "_tags_dynamic"):
            collected_tags.update(self._tags_dynamic)

        return deepcopy(collected_tags)

    def get_tag(self, tag_name, tag_value_default=None, raise_error=True):
        """
        Get tag value from estimator class.

        Uses dynamic tag overrides.

        Parameters
        ----------
        tag_name : str
            Name of tag to be retrieved.
        tag_value_default : any type, default=None
            Default/fallback value if tag is not found.
        raise_error : bool
            Whether a ValueError is raised when the tag is not found.

        Returns
        -------
        tag_value :
            Value of the `tag_name` tag in self. If not found, returns an error if
            raise_error is True, otherwise it returns `tag_value_default`.

        Raises
        ------
        ValueError if raise_error is True i.e. if tag_name is not in self.get_tags(
        ).keys()

        See Also
        --------
        get_tags : Get all tags from an object.
        get_clas_tags : Get all tags from a class.
        get_class_tag : Get a single tag from a class.

        Examples
        --------
        >>> from aeon.classification import DummyClassifier
        >>> d = DummyClassifier()
        >>> d.get_tag("capability:multivariate")
        True
        """
        collected_tags = self.get_tags()

        tag_value = collected_tags.get(tag_name, tag_value_default)

        if raise_error and tag_name not in collected_tags.keys():
            raise ValueError(f"Tag with name {tag_name} could not be found.")

        return tag_value

    def set_tags(self, **tag_dict):
        """
        Set dynamic tags to given values.

        Parameters
        ----------
        **tag_dict : dict
            Dictionary of tag name : tag value pairs.

        Returns
        -------
        Self :
            Reference to self.

        Notes
        -----
        Changes object state by setting tag values in tag_dict as dynamic tags
        in self.
        """
        tag_update = deepcopy(tag_dict)
        if hasattr(self, "_tags_dynamic"):
            self._tags_dynamic.update(tag_update)
        else:
            self._tags_dynamic = tag_update

        return self

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """
        Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.

        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class. Each dict are
            parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`.
        """
        # default parameters = empty dict
        return {}

    @classmethod
    def create_test_instance(cls, parameter_set="default", return_first=True):
        """
        Construct Estimator instance if possible.

        Calls the `get_test_params` method and returns an instance or list of instances
        using the returned dict or list of dict.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
        return_first : bool, default=True
            If True, return the first instance of the list of instances.
            If False, return the list of instances.

        Returns
        -------
        instance : BaseEstimator or list of BaseEstimator
            Instance of the class with default parameters. If return_first
            is False, returns list of instances.
        """
        # todo, update all methods to use parameter_set and remove when done
        if "parameter_set" in inspect.getfullargspec(cls.get_test_params).args:
            params = cls.get_test_params(parameter_set=parameter_set)
        else:
            params = cls.get_test_params()

        if isinstance(params, list):
            if return_first:
                return cls(**params[0])
            else:
                return [cls(**p) for p in params]
        else:
            if return_first:
                return cls(**params)
            else:
                return [cls(**params)]

    @classmethod
    def create_test_instances_and_names(cls, parameter_set="default"):
        """
        Create list of all test instances and a list of names for them.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.

        Returns
        -------
        objs : list of instances of cls
            i-th instance is cls(**cls.get_test_params()[i]).
        names : list of str, same length as objs
            i-th element is name of i-th instance of obj in tests
            convention is {cls.__name__}-{i} if more than one instance
            otherwise {cls.__name__}.
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
        """
        if "parameter_set" in inspect.getfullargspec(cls.get_test_params).args:
            param_list = cls.get_test_params(parameter_set=parameter_set)
        else:
            param_list = cls.get_test_params()

        objs = []
        if not isinstance(param_list, (dict, list)):
            raise RuntimeError(
                f"Error in {cls.__name__}.get_test_params, "
                "return must be param dict for class, or list thereof"
            )
        if isinstance(param_list, dict):
            param_list = [param_list]
        for params in param_list:
            if not isinstance(params, dict):
                raise RuntimeError(
                    f"Error in {cls.__name__}.get_test_params, "
                    "return must be param dict for class, or list thereof"
                )
            objs += [cls(**params)]

        n_cases = len(param_list)
        if n_cases > 1:
            names = [cls.__name__ + "-" + str(i) for i in range(n_cases)]
        else:
            names = [cls.__name__]

        return objs, names

    @classmethod
    def _has_implementation_of(cls, method):
        """
        Check if method has a concrete implementation in this class.

        This assumes that having an implementation is equivalent to
            one or more overrides of `method` in the method resolution order.

        Parameters
        ----------
        method : str
            name of method to check implementation of.

        Returns
        -------
        bool, whether method has implementation in cls
            True if cls.method has been overridden at least once in
                the inheritance tree (according to method resolution order).
        """
        # walk through method resolution order and inspect methods
        #   of classes and direct parents, "adjacent" classes in mro
        mro = inspect.getmro(cls)
        # collect all methods that are not none
        methods = [getattr(c, method, None) for c in mro]
        methods = [m for m in methods if m is not None]

        for i in range(len(methods) - 1):
            # the method has been overridden once iff
            #  at least two of the methods collected are not equal
            #  equivalently: some two adjacent methods are not equal
            overridden = methods[i] != methods[i + 1]
            if overridden:
                return True

        return False

    def is_composite(self):
        """
        Check if the object is composite.

        A composite object is an object which contains objects, as parameters.
        Called on an instance, since this may differ by instance.

        Returns
        -------
        composite: bool
            Whether self contains a parameter which is BaseEstimator.
        """
        # walk through method resolution order and inspect methods
        #   of classes and direct parents, "adjacent" classes in mro
        params = self.get_params(deep=False)
        composite = any(isinstance(x, BaseEstimator) for x in params.values())

        return composite

    def _components(self, base_class=None):
        """
        Return references to all state changing BaseEstimator type attributes.

        This *excludes* the blue-print-like components passed in the __init__.

        Caution: this method returns *references* and not *copies*.
            Writing to the reference will change the respective attribute of self.

        Parameters
        ----------
        base_class : class, optional, default=None, must be subclass of BaseEstimator
            if None, behaves the same as `base_class=BaseEstimator`
            if not None, return dict collects descendants of `base_class`.

        Returns
        -------
        dict with key = attribute name, value = reference to attribute.
        dict contains all attributes of `self` that inherit from `base_class`, and:
            whose names do not contain the string "__", e.g., hidden attributes
            are not class attributes, and are not hyper-parameters (`__init__` args).
        """
        if base_class is None:
            base_class = BaseEstimator
        if base_class is not None and not inspect.isclass(base_class):
            raise TypeError(f"base_class must be a class, but found {type(base_class)}")
        # if base_class is not None and not issubclass(base_class, BaseEstimator):
        #     raise TypeError("base_class must be a subclass of BaseEstimator")

        # retrieve parameter names to exclude them later
        param_names = self.get_params(deep=False).keys()

        # retrieve all attributes that are BaseEstimator descendants
        attrs = [attr for attr in dir(self) if "__" not in attr]
        cls_attrs = [attr for attr in dir(type(self))]
        self_attrs = set(attrs).difference(cls_attrs).difference(param_names)

        comp_dict = {x: getattr(self, x) for x in self_attrs}
        comp_dict = {x: y for (x, y) in comp_dict.items() if isinstance(y, base_class)}

        return comp_dict

    def save(self, path=None):
        """
        Save serialized self to bytes-like object or to (.zip) file.

        Behaviour:
        if `path` is None, returns an in-memory serialized self
        if `path` is a file location, stores self at that location as a zip file

        saved files are zip files with following contents:
        _metadata - contains class of self, i.e., type(self)
        _obj - serialized self. This class uses the default serialization (pickle).

        Parameters
        ----------
        path : None or file location (str or Path).
            if None, self is saved to an in-memory object
            if file location, self is saved to that file location. If:
                path="estimator" then a zip file `estimator.zip` will be made at cwd.
                path="/home/stored/estimator" then a zip file `estimator.zip` will be
                stored in `/home/stored/`.

        Returns
        -------
        if `path` is None - in-memory serialized self
        if `path` is file location - ZipFile with reference to the file.
        """
        import pickle
        import shutil
        from pathlib import Path
        from zipfile import ZipFile

        if path is None:
            return (type(self), pickle.dumps(self))
        if not isinstance(path, (str, Path)):
            raise TypeError(
                "`path` is expected to either be a string or a Path object "
                f"but found of type:{type(path)}."
            )

        path = Path(path) if isinstance(path, str) else path
        path.mkdir()

        pickle.dump(type(self), open(path / "_metadata", "wb"))
        pickle.dump(self, open(path / "_obj", "wb"))

        shutil.make_archive(base_name=path, format="zip", root_dir=path)
        shutil.rmtree(path)
        return ZipFile(path.with_name(f"{path.stem}.zip"))

    @classmethod
    def load_from_serial(cls, serial):
        """
        Load object from serialized memory container.

        Parameters
        ----------
        serial : object
            First element of output of `cls.save(None)`.

        Returns
        -------
        deserialized self resulting in output `serial`, of `cls.save(None)`.
        """
        import pickle

        return pickle.loads(serial)

    @classmethod
    def load_from_path(cls, serial):
        """
        Load object from file location.

        Parameters
        ----------
        serial : object
            Result of ZipFile(path).open("object).

        Returns
        -------
        deserialized self resulting in output at `path`, of `cls.save(path)`
        """
        import pickle
        from zipfile import ZipFile

        with ZipFile(serial, "r") as file:
            return pickle.loads(file.open("_obj").read())

    @property
    def is_fitted(self):
        """Whether ``fit`` has been called."""
        return self._is_fitted

    def check_is_fitted(self):
        """
        Check if the estimator has been fitted.

        Raises
        ------
        NotFittedError
            If the estimator has not been fitted yet.
        """
        if not self.is_fitted:
            raise NotFittedError(
                f"This instance of {self.__class__.__name__} has not "
                f"been fitted yet; please call `fit` first."
            )

    def get_fitted_params(self, deep=True):
        """Get fitted parameters.

        State required:
            Requires state to be "fitted".

        Parameters
        ----------
        deep : bool, default=True
            Whether to return fitted parameters of components.

            * If True, will return a dict of parameter name : value for this object,
              including fitted parameters of fittable components
              (= BaseEstimator-valued parameters).
            * If False, will return a dict of parameter name : value for this object,
              but not include fitted parameters of components.

        Returns
        -------
        fitted_params : dict with str-valued keys
            Dictionary of fitted parameters, paramname : paramvalue
            keys-value pairs include:

            * always: all fitted parameters of this object
            * if ``deep=True``, also contains keys/value pairs of component parameters
              parameters of components are indexed as ``[componentname]__[paramname]``
              all parameters of ``componentname`` appear as ``paramname`` with its value
            * if ``deep=True``, also contains arbitrary levels of component recursion,
              e.g., ``[componentname]__[componentcomponentname]__[paramname]``, etc.
        """
        if not self.is_fitted:
            raise NotFittedError(
                f"estimator of type {type(self).__name__} has not been "
                "fitted yet, please call fit on data before get_fitted_params"
            )

        # collect non-nested fitted params of self
        fitted_params = self._get_fitted_params()

        # the rest is only for nested parameters
        # so, if deep=False, we simply return here
        if not deep:
            return fitted_params

        def sh(x):
            """Shorthand to remove all underscores at end of a string."""
            if x.endswith("_"):
                return sh(x[:-1])
            else:
                return x

        # add all nested parameters from components that are aeon BaseEstimator
        c_dict = self._components()
        for c, comp in c_dict.items():
            if isinstance(comp, BaseEstimator) and comp._is_fitted:
                c_f_params = comp.get_fitted_params()
                c_f_params = {f"{sh(c)}__{k}": v for k, v in c_f_params.items()}
                fitted_params.update(c_f_params)

        # add all nested parameters from components that are sklearn estimators
        # we do this recursively as we have to reach into nested sklearn estimators
        n_new_params = 42
        old_new_params = fitted_params
        while n_new_params > 0:
            new_params = dict()
            for c, comp in old_new_params.items():
                if isinstance(comp, _BaseEstimator):
                    c_f_params = self._get_fitted_params_default(comp)
                    c_f_params = {f"{sh(c)}__{k}": v for k, v in c_f_params.items()}
                    new_params.update(c_f_params)
            fitted_params.update(new_params)
            old_new_params = new_params.copy()
            n_new_params = len(new_params)

        return fitted_params

    def _get_fitted_params_default(self, obj=None):
        """Obtain fitted params of object, per sklearn convention.

        Extracts a dict with {paramstr : paramvalue} contents,
        where paramstr are all string names of "fitted parameters".

        A "fitted attribute" of obj is one that ends in "_" but does not start with "_".
        "fitted parameters" are names of fitted attributes, minus the "_" at the end.

        Parameters
        ----------
        obj : any object, optional, default=self.

        Returns
        -------
        fitted_params : dict with str keys
            fitted parameters, keyed by names of fitted parameter.
        """
        obj = obj if obj else self

        # default retrieves all self attributes ending in "_"
        # and returns them with keys that have the "_" removed
        fitted_params = [attr for attr in dir(obj) if attr.endswith("_")]
        fitted_params = [x for x in fitted_params if not x.startswith("_")]
        fitted_params = [x for x in fitted_params if hasattr(obj, x)]
        fitted_param_dict = {p[:-1]: getattr(obj, p) for p in fitted_params}

        return fitted_param_dict

    def _get_fitted_params(self):
        """Get fitted parameters.

        private _get_fitted_params, called from get_fitted_params

        State required:
            Requires state to be "fitted".

        Returns
        -------
        fitted_params : dict with str keys
            fitted parameters, keyed by names of fitted parameter.
        """
        return self._get_fitted_params_default()


def _clone_estimator(base_estimator, random_state=None):
    estimator = clone(base_estimator)

    if random_state is not None:
        _set_random_states(estimator, random_state)

    return estimator
