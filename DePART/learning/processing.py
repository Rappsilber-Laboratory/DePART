# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 21:06:31 2018

@author: hanjo
"""
import numpy as np
import pandas as pd
import seaborn as sns
from joblib import Parallel, delayed
from keras import backend as K
from keras.utils import np_utils
from keras.utils.generic_utils import get_custom_objects
from pyteomics import achrom
from scipy import stats
from sklearn.metrics import mean_absolute_error, auc, mean_squared_error, r2_score, f1_score, accuracy_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

# cross imports
from DePART.learning import models


def swish(x):
    return (K.sigmoid(x) * x)

get_custom_objects().update({'swish': swish})


def eval_predictions_complex(y_test, y_pred, name, get_metrics=False):
    """
    Evaluation of the prediction. Generates the following metrics in a list:
        - mean absolute error
        - men squared error
        - f1
        - accuracy
        - mean distance (predicted vs. true)
        - std distance (""---------------")
        - eq_pred - predicted == true
        - oneoff -fiveoff - classification distance
        - correlation - pearsonr
        - name - method name (e.g. OLS, OLR, etc.)
        
    Parameters:
    ---------------------------------------
    y_test: ar,
            test observations
    y_pred: ar,
            predicted observations
    name: str, 
          method name
    get_metrics: bool,
                if True, only the column names for the metrics are rturned
                if False, computes the actual metrics
        
    """
    def help_diff(y_pred, y_test, t=0):
        """
        Create indicator to measure how far off the prediction is.
        """
        if t == 0:
            return(sum([1. if i==j else 0 for i,j in zip(y_test, [int(i) for i in np.round(y_pred)])])/y_test.shape[0] * 100)
        else:
            return(sum([1. if np.abs(i-j) <= t else 0 for i,j in zip(y_test, [int(i) for i in np.round(y_pred)])])/y_test.shape[0] * 100)
                
    if get_metrics:
        return(["MSA", "MSE", "R^2", "F1 (weighted)", "Accuracy", "mean. dist", 
                 "std. dist", "AUC",
                  "0-off-pred", "1-off-pred", "2-off-pred", "3-off-pred", 
                  "5-off-pred", "Correlation", "Method"])
    else:
        #compute difference and count occurrences
        diff = np.abs((y_test-y_pred).astype(int))
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        aucres = auc(y_test, y_pred, reorder=True)
        rsq = r2_score(y_test, y_pred)
        f1 = f1_score(np.round(y_test), [int(i) for i in np.round(y_pred)], average="weighted")
        acc = accuracy_score(np.round(y_test), np.round(y_pred))
        mean_dist =  np.mean(diff)
        std_dist = np.std(diff)
        eq_pred = help_diff(y_pred, y_test, t=0) 
        oneoff = help_diff(y_pred, y_test, t=1)
        twooff = help_diff(y_pred, y_test, t=2)
        throff = help_diff(y_pred, y_test, t=3)
        fiveoff = help_diff(y_pred, y_test, t=4)
        correlation = stats.pearsonr(y_test, y_pred)[0]
        return([mae, mse, rsq, f1, acc, mean_dist,std_dist, aucres, eq_pred,
                oneoff, twooff, throff, fiveoff, correlation, name])
    

def cv_splitter(split=5):
    """
    Prepares kfold cross-validation with reproduceable split.
    
    Parameters:
    --------------------------
            
    split: int,
            number of folds to return (iterator)
    """
    kf = KFold(n_splits=split, random_state=42)
    return(kf)


def fit_model(clf, traindf, testdf, trainy, testy, name, epochs=100,
              batch_size=512, return_pred=False, scale=False,
              regression=False, diagnostics=True):
    """
    Generic function that fits a model and retrieves the error rates.
    
    Parameters:
    --------------------------
    clf: classifier (sklearn),
         a classifier object that is either a sklearn classifier or a supported
         other object (e.g pyteomics, keras). This can only be
         distinguished if a corect name is used ("Pyteomics" or "Keras").
        
    traindf: ar-like,
            Can either be a numpy matrix or pandas dataframe with the
            training data.
    
    testdf: ar-like,
            Can either be a numpy matrix or pandas dataframe with the
            testing data.
            
    trainy: ar-like,
            Vector with y variables. Needs to be adapted for Keras!
            (softmax)

    testy: ar-like,
            Vector with y variables. Needs to be adapted for Keras!
            (softmax)
    name: str,
            Idstring for the classifier. The two hard coded clauses
            are "Pyteomics" which uses the pyteomics module to predict
            retention times and "Keras" which uses the keras
            framework for prediction. All other names don't have a special
            meaning. There, the clf object is more important and needs to be
            similar to the sklearn API.
    nomod: bool,
          if True, supports modifications in the pyteomics model.
          return_pred: bool,
          if True, returns the predicted target variables (default:False)     
 
    #debug:
    for train_index, test_index in kf.split(X_train_full):
        break
    clf = initialize_neural_network()
    traindf = np.array(X_train_full.iloc[train_index])
    testdf = np.array(X_train_full.iloc[test_index])
    trainy = np_utils.to_categorical(encoder.transform(y_train_full.iloc[train_index]))
    testy = np_utils.to_categorical(encoder.transform(y_train_full.iloc[test_index]))
    name = "Keras"
    
    """
    if scale:
        scaler = StandardScaler()
        scaler.fit(traindf)
        traindf = scaler.transform(traindf)
        testdf = scaler.transform(testdf)
        
    #train 
    clf.fit(traindf, trainy, epochs=epochs, batch_size=batch_size, verbose=0)
    
    #predict
    if not regression:
        yhat_train = clf.predict(traindf).argmax(axis=1)
        yhat_test = clf.predict(testdf).argmax(axis=1)
        
        trainy = trainy.argmax(axis=1)
        testy = testy.argmax(axis=1)        
    else:
        yhat_train = np.ravel(clf.predict(traindf))
        yhat_test = np.ravel(clf.predict(testdf))
        

    #evaluate
    res_train = eval_predictions_complex(trainy, yhat_train, name+"_Train")
    res_test = eval_predictions_complex(testy, yhat_test, name+"_Test")
    res_df = pd.DataFrame([res_train, res_test])  
    res_df.columns = eval_predictions_complex(None, None, None, True)
    
    if diagnostics:
        sns.jointplot(trainy, yhat_train)
        sns.jointplot(testy, yhat_test)
                
    if return_pred:
        return(clf, res_df, yhat_train, yhat_test)
    else:
        return(clf, res_df)
    
    
def process_df(ml_df):
    """
    Split df into datastructures that are useable with sklearn. So essentially,
    removing the sequence column and target column from the dataframe.
    
    Parameters:
    -------------------------------
    ml_df: ml_df,
            any dataframe where the Sequence and Fraction column should be
            removed.
    """
    tmp_df = ml_df.copy()
    seqs = tmp_df.Sequence
    fractions = tmp_df.Fraction
    
    if "PyteomicsSequence" in tmp_df.columns:
        del tmp_df["PyteomicsSequence"]
        
    if "Modified sequence" in tmp_df.columns:
        del tmp_df["PyteomicsSequence"]
        
    if "Sequence" in tmp_df.columns:
        del tmp_df["Sequence"]
        
    if "Fraction" in tmp_df.columns:
        del tmp_df["Fraction"]
        
    if "Score" in tmp_df.columns:
        del tmp_df["Score"]
        
    return(tmp_df, seqs, fractions)
    
        
def cross_validation(train_df, valid_df, name="", nkfold=5, n_jobs=5, nn_args={},
                     use_joblib=True, epochs=100, batch_size=512, verbose=False,
                     model=models.SAX_Model, loss="categorical_accuracy"):
    """
    Function for cross-validation on the training data and evaluation 
    on the hold-out set. It stores the predictions and computes more than
    the usual error metrics. For short evaluations use the build in keras
    cv function.
    
    Parameters:
    --------------------------
    train_df: df,
              training data
    valid_: df,
              validation data              
    nkfolds: int,
            number of folds
    n_jobs:int,
            number of jobs for parallel execution of cv
    nn_args: dict,
            keywrd arguments for the neural network init
    """
    def identity(x):
        return(x)
    
    print ("Training Size: {}".format(train_df.shape))

    #format the dtaframe for ML 
    X_train_full, Seqs_train_full, y_train_full = process_df(train_df)
    
    if loss == "categorical_accuracy":
        # encode class values as integers
        encoder = LabelEncoder()
        encoder.fit(y_train_full)
        encoded_y = pd.DataFrame(np_utils.to_categorical(encoder.transform(y_train_full)))
        encoded_y.index = y_train_full.index
        regression=False
        output_dims = len(np.unique(train_df.Fraction))
    else:
        #regression
        #identiy encoder
        encoded_y = y_train_full
        regression = True
        output_dims = 1
        
    #output dims depending on the number of fractions
    output_dims = len(np.unique(train_df.Fraction))
    input_dims = X_train_full.shape[1]
    
    #init cross-validation
    kf = cv_splitter(nkfold)
    results_store = []
    if use_joblib:
        results_store.extend(Parallel(n_jobs=n_jobs)(delayed(fit_model)
                        (model(output_dim=output_dims, input_dim=input_dims,
                               loss=loss, **nn_args), 
                         np.array(X_train_full.iloc[train_index]),
                         np.array(X_train_full.iloc[test_index]),
                         np.array(encoded_y.iloc[train_index]),
                         np.array(encoded_y.iloc[test_index]),
                         name,
                         regression=regression) for train_index, test_index in kf.split(X_train_full)))
    else:
        for train_index, test_index in kf.split(X_train_full):
            #prep data
            tmp_train = np.array(X_train_full.iloc[train_index])
            tmp_test = np.array(X_train_full.iloc[test_index])
            
            #ydata
            tmp_ytrain = np.array(encoded_y.iloc[train_index])
            tmp_ytest = np.array(encoded_y.iloc[test_index])
            
            tmp_model = model(output_dim=output_dims, input_dim=input_dims, 
                              loss=loss, *nn_args)
                       
            results_store.append(fit_model(tmp_model, tmp_train, tmp_test,
                                           tmp_ytrain, tmp_ytest, name,
                                           epochs=epochs, 
                                           regression=regression,
                                           batch_size=batch_size))
                         
                         
    classifier, res_ar = zip(*results_store)
    eval_df = pd.concat(res_ar)
    eval_df["Classifier"] = [i.split("_")[0] for i in eval_df["Method"]]
    eval_df = eval_df.groupby("Method").aggregate([np.mean, stats.sem])
    eval_df["data"] = [i.split("_")[1] for i in eval_df.index]
    eval_df["min_acc"] = eval_df["0-off-pred"]["mean"] - eval_df["0-off-pred"]["sem"]
    eval_df["max_acc"] = eval_df["0-off-pred"]["mean"] + eval_df["0-off-pred"]["sem"]
    eval_df["diff"] = eval_df["max_acc"] -  eval_df["min_acc"]
    eval_df = eval_df.round(3)    
    return(eval_df)
    
    
def train_validation(train_df, valid_df, epochs=100, batch_size=512, plot=False,
                     nn_args={}):
    """
    Wrapper for training on the complete training data and evaluating the
    performance on the hold-out set.
    
    Parameter:
    -------------------
    train_df: df,
                train df with features and
    valid_df: df,
               validation df with features
               
    Returns:
    -------------------
    res_df: metrics
    nnmodel: neural network model
    """
    #format the dtaframe for ML 
    X_train_full, Seqs_train_full, y_train_full = process_df(train_df)
    X_valid_full, Seqs_valid_full, y_valid_full = process_df(valid_df)    
    
    # encode class values as integers
    encoder = LabelEncoder()
    encoder.fit(y_train_full)

    #output dims depending on the number of fractions
    output_dims = len(np.unique(train_df.Fraction))
    input_dims = X_train_full.shape[1]
    
    nnmodel = models.SAX_Model(output_dim=output_dims, 
                               input_dim=input_dims, **nn_args)
    print (nnmodel.summary())
    history = nnmodel.fit(np.array(X_train_full),
                          np_utils.to_categorical(encoder.transform(y_train_full)),
                          epochs=epochs, batch_size=batch_size)
    
    #fit the model to the complete training data
    yhat_train_prob = nnmodel.predict(np.array(X_train_full))
    yhat_train_disc = yhat_train_prob.argmax(axis=1) + 1

    yhat_val_prob = nnmodel.predict(np.array(X_valid_full))
    yhat_val_disc = yhat_val_prob.argmax(axis=1) + 1
            
    #evaluate
    res_train = pd.DataFrame(eval_predictions_complex(y_train_full, yhat_train_disc, "keras_Train"))
    res_valid = pd.DataFrame(eval_predictions_complex(y_valid_full, yhat_val_disc, "keras_Valid"))
    
    res_df = pd.concat([res_train.transpose(), res_valid.transpose()])
    res_df.columns = eval_predictions_complex(None, None, None, True)
    
    if plot:
        x = np.arange(-4, 30, 1)
        ax1 = sns.jointplot(x=y_valid_full, y=yhat_val_disc, kind="kde",
                            xlim=(-4, 30 ), ylim=(-4, 30 ))
        ax1.set_axis_labels(xlabel="True Fraction", ylabel="Prediction")
        ax1.ax_joint.plot(x, x, '-k')
    print ("Results on the validation data:")
    print (res_df)
    return(res_df, nnmodel, history)
    

 
def pyteomcis_snippets(traindf, trainy, testdf, nomod=True):
    """
    """
    #pyteomics
    clf = achrom.get_RCs_vary_lcp([str(i).replace("U", "C") 
                                                for i in traindf], trainy)
    print ("Pyteomics LCP: {}".format(clf["lcp"]))
    yhat_train = [achrom.calculate_RT(i, clf, raise_no_mod=nomod) for i in 
                  traindf]
    yhat_test = [achrom.calculate_RT(i, clf, raise_no_mod=nomod) for i in 
                 testdf]
    return(yhat_train, yhat_test)
    
    
    