import numpy as np 
from ExtraEnsemble import GradientBoostingTreeRegressor, GradientBoostingExtraTreeRegressor


def test_standard_forest_regressor():
    
    for splitter in ["purely", "midpoint", "maxedge", "msereduction", "msemaxedge"]:
        for threshold in [0, 0.1]:
            for parallel_jobs in [0, 5]:
                for max_features in [0, 0.9]:
                    for max_samples in [0, 0.9]:
                
                        np.random.seed(666)
                        X_train = np.random.rand(2000).reshape(-1,2)
                        X_test = np.random.rand(2000).reshape(-1,2)
                        Y_train = np.ones(1000)
        
                        model = GradientBoostingTreeRegressor( n_estimators = 20,
                                                max_features = max_features,
                                                max_samples = max_samples,
                                                rho = 0.1,
                                                ensemble_parallel = int(5-parallel_jobs),
                                                splitter = splitter,
                                                min_samples_split = 5, 
                                                min_samples_leaf = 2,
                                                max_depth = 2, 
                                                log_Xrange = True, 
                                                random_state = 666,
                                                parallel_jobs = parallel_jobs, 
                                                max_features = 1.0,
                                                search_number = 10,
                                                threshold = threshold)
                        model.fit(X_train, Y_train)
                        print(model.predict(X_test))
                        assert (model.predict(X_test)==1).all()
    
    
def test_extra_forest_regressor():
    
    for splitter in ["purely", "midpoint", "maxedge", "msereduction", "msemaxedge"]:
        for order in [0,1,5]:
            for threshold in [0,0.1]:
                for parallel_jobs in [0,5]:
                    for lamda in [0,0.001]:
                        for max_features in [0, 0.9]:
                            for max_samples in [0, 0.9]:
                    
                                np.random.seed(666)
                                X_train = np.random.rand(2000).reshape(-1,2)
                                X_test = np.random.rand(2000).reshape(-1,2)
                                Y_train = np.ones(1000)
        
                                model = GradientBoostingExtraTreeRegressor( n_estimators = 20,
                                                        max_features = max_features,
                                                        max_samples = max_samples,
                                                        rho = 0.1,
                                                        ensemble_parallel = int(5-parallel_jobs),
                                                        splitter = splitter,
                                                        min_samples_split = 5, 
                                                        min_samples_leaf = 2,
                                                        max_depth = 2, 
                                                        order = order, 
                                                        log_Xrange = True, 
                                                        random_state = 666,
                                                        parallel_jobs = parallel_jobs, 
                                                        V = 10,
                                                        r_range_low = 0,
                                                        r_range_up = 1,
                                                        lamda = lamda, 
                                                        max_features = 1.0,
                                                        search_number = 10,
                                                        threshold = threshold)
                                model.fit(X_train, Y_train)
        
                              
                                assert ((model.predict(X_test)-1)**2).mean()<0.01
                    
                    
