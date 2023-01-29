import numpy as np
from sklearn.metrics import mean_squared_error as MSE

from ._tree import TreeStruct, RecursiveTreeBuilder
from ._splitter import PurelyRandomSplitter, MidPointRandomSplitter, MaxEdgeRandomSplitter, MSEReductionSplitter, GINIReductionSplitter, MSEReductionMaxEdgeSplitter, GINIReductionMaxEdgeSplitter

from ._estimator import NaiveRegressionEstimator, ExtraRegressionEstimator



SPLITTERS = {"purely": PurelyRandomSplitter,
             "midpoint": MidPointRandomSplitter, 
             "maxedge": MaxEdgeRandomSplitter, 
             "msereduction": MSEReductionSplitter,
             "ginireduction": GINIReductionSplitter,
             "msemaxedge": MSEReductionMaxEdgeSplitter,
             "ginimaxedge": GINIReductionMaxEdgeSplitter
             }

ESTIMATORS = {"naive_regression": NaiveRegressionEstimator,
              "extra_regression": ExtraRegressionEstimator,
              }

class BaseRecursiveTree(object):
    def __init__(self, 
                 splitter = None, 
                 estimator = None, 
                 min_samples_split = None,
                 min_samples_leaf = None,
                 max_depth = None, 
                 order = None, 
                 log_Xrange = None, 
                 random_state = None,
                 parallel_jobs = None,
                 V = None,
                 r_range_up = None,
                 r_range_low = None,
                 lamda = None,
                 max_features = None,
                 search_number = None,
                 threshold = None
                ):
        self.splitter = splitter
        self.estimator = estimator
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_depth = max_depth
        self.order = order
        self.log_Xrange = log_Xrange
        self.random_state = random_state
        self.parallel_jobs = parallel_jobs
        self.V = V
        self.r_range_up = r_range_up
        self.r_range_low = r_range_low
        self.lamda = lamda
        self.max_features = max_features
        self.search_number = search_number
        self.threshold = threshold
             
    def fit(self, X, Y, X_range = "unit"):
        
        self.n_samples, self.dim = X.shape
        
        if X_range == "unit":
            X_range = np.array([np.zeros(self.dim),np.ones(self.dim)])
        if X_range is None:
            X_range = np.zeros(shape = (2, X.shape[1]))
            X_range[0] = X.min(axis = 0) - 0.01 * (X.max(axis = 0) - X.min(axis = 0))
            X_range[1] = X.max(axis = 0) + 0.01 * (X.max(axis = 0) - X.min(axis = 0))
        self.X_range = X_range


        
        if self.V == "auto":
            V =  max(5, int(X.shape[0]* 2**(-self.max_depth-2)))
        else:
            V = self.V
        


        # begin
        splitter = SPLITTERS[self.splitter](self.random_state, self.max_features, self.search_number, self.threshold)
        
        Estimator = ESTIMATORS[self.estimator]
        self.tree_ = TreeStruct(self.n_samples, self.dim, self.log_Xrange)
        builder = RecursiveTreeBuilder(splitter, 
                                       Estimator, 
                                       self.min_samples_split, 
                                       self.max_depth, 
                                       self.order,
                                       V,
                                      self.r_range_up,
                                      self.r_range_low,
                                      self.lamda)
        builder.build(self.tree_, X, Y, X_range)
        
    def apply(self, X):
        return self.tree_.apply(X)
    
    def get_info(self,x):
        return self.tree_.get_info(x)
    
    def get_node_idx(self,X):
        return self.apply(X)
    
    def get_node(self,X):
        return [self.tree_.leafnode_fun[i] for i in self.get_node_idx(X)]
    
    def get_all_node(self):
        return list(self.tree_.leafnode_fun.values())
    
    def predict(self, X):
        if self.parallel_jobs != 0:
            #print("we are using parallel computing!")
            y_hat = self.tree_.predict_parallel(X, self.parallel_jobs)
        else:
            y_hat = self.tree_.predict(X)
        
        # check boundary
        check_lowerbound = (X - self.X_range[0] >= 0).all(axis = 1)
        check_upperbound = (X - self.X_range[1] <= 0).all(axis = 1)
        is_inboundary = check_lowerbound * check_upperbound
        # assign 0 to points outside the boundary
        y_hat[np.logical_not(is_inboundary)] = 0
        return y_hat
    
    def get_params(self, deep=True):
        """Get parameters for this estimator.

        Parameters
        ----------
        deep : boolean, optional
            If True, will return the parameters for this estimator and
            contained subobjects that are estimators.

        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.
        """
        out = dict()
        for key in ['min_samples_split', "max_depth", "order", "V", 
                    "r_range_low", "r_range_up", "lamda", "max_features",
                    "search_number", "threshold" ]:
            value = getattr(self, key, None)
            if deep and hasattr(value, 'get_params'):
                deep_items = value.get_params().items()
                out.update((key + '__' + k, val) for k, val in deep_items)
            out[key] = value
        return out
    
    
    def set_params(self, **params):
        """Set the parameters of this estimator.

        The method works on simple estimators as well as on nested objects
        (such as pipelines). The latter have parameters of the form
        ``<component>__<parameter>`` so that it's possible to update each
        component of a nested object.

        Returns
        -------
        self
        """
        if not params:
            # Simple optimization to gain speed (inspect is slow)
            return self
        valid_params = self.get_params(deep=True)


        for key, value in params.items():
            if key not in valid_params:
                raise ValueError('Invalid parameter %s for estimator %s. '
                                 'Check the list of available parameters '
                                 'with `estimator.get_params().keys()`.' %
                                 (key, self))
            setattr(self, key, value)
            valid_params[key] = value

        return self
    
    


class StandardTreeRegressor(BaseRecursiveTree):
    def __init__(self, splitter = "maxedge", 
                 min_samples_split = 5, 
                 min_samples_leaf = 2,
                 max_depth = 2, 
                 order = 0, 
                 log_Xrange = True, 
                 random_state = 666,
                 parallel_jobs = 0, 
                 V = 2,
                 r_range_low = 0,
                 r_range_up = 1,
                 lamda = 0.01, 
                 max_features = 1.0,
                 search_number = 10,
                 threshold = 0):
        super(StandardTreeRegressor, self).__init__(splitter = splitter,
                                             estimator = "naive_regression", 
                                             min_samples_split = min_samples_split,
                                             min_samples_leaf = min_samples_leaf,
                                             max_depth = max_depth, 
                                             log_Xrange = log_Xrange, 
                                             random_state = random_state,
                                             parallel_jobs = parallel_jobs,
                                             max_features = max_features,
                                             search_number = search_number,
                                             threshold = threshold)
        
    def score(self, X, y):
        return -MSE(self.predict(X),y)
    
    

class ExtraTreeRegressor(BaseRecursiveTree):
    def __init__(self, splitter = "maxedge", 
                 min_samples_split = 5, 
                 min_samples_leaf = 2,
                 max_depth = 2, 
                 order = 0, 
                 log_Xrange = True, 
                 random_state = 666,
                 parallel_jobs = 0, 
                 V = 2,
                 r_range_low = 0,
                 r_range_up = 1,
                 lamda = 0.01, 
                 max_features = 1.0,
                 search_number = 10,
                 threshold = 0):
        super(ExtraTreeRegressor, self).__init__(splitter = splitter,
                                             estimator = "extra_regression", 
                                             min_samples_split = min_samples_split,
                                             min_samples_leaf = min_samples_leaf,
                                             max_depth = max_depth, 
                                             order = order,
                                             log_Xrange = log_Xrange, 
                                             random_state = random_state,
                                             parallel_jobs = parallel_jobs,
                                             V = V,
                                             r_range_low = r_range_low,
                                             r_range_up = r_range_up,
                                             lamda = lamda,
                                             max_features = max_features,
                                             search_number = search_number,
                                             threshold = threshold)
        
    def score(self, X, y):
        return -MSE(self.predict(X),y)

