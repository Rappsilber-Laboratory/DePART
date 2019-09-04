# -*- coding: utf-8 -*-
"""
Created on Fri Mar 30 18:28:55 2018

@author: hanjo
"""

from keras import optimizers
from keras.layers import Dense, Dropout
from keras.models import Sequential


def SAX_Model(ini_mode="normal", optimizer="adam", loss="categorical_crossentropy", 
              act=["relu", "tanh", "relu"], dr1=0.0, dr2=0.0, dr3=0.0, 
              input_dim=218, output_dim=29):
    """
    Returns the best-performing neural network model from the manuscript.
    """
    model = Sequential()
    model.add(Dense(50, input_dim=input_dim, kernel_initializer=ini_mode, 
                    activation=act[0]))
    model.add(Dropout(dr1)) 
    model.add(Dense(40, kernel_initializer='normal', activation=act[1]))
    model.add(Dropout(dr2)) 
    model.add(Dense(35, kernel_initializer='normal', activation=act[2]))
    model.add(Dropout(dr3)) 
    model.add(Dense(output_dim, kernel_initializer='normal', activation='softmax'))
    # Compile model
    model.compile(loss=loss, optimizer=optimizer, 
                  metrics=['categorical_accuracy', 'accuracy'])
    return(model)


def FNN_Classifier(ini_mode="normal", optimizer="adam", 
                              loss="categorical_crossentropy", 
                              act=["relu", "tanh", "relu"],
                              dropout=[0.0, 0.0, 0.0], input_dim=218,
                              output_dim=29):
    """
    Returns the best-performing neural network model from the manuscript.
    """
    model = Sequential()
    model.add(Dense(50, input_dim=input_dim, kernel_initializer=ini_mode, 
                    activation=act[0]))
    model.add(Dropout(dropout[0])) 
    model.add(Dense(40, kernel_initializer='normal', activation=act[1]))
    model.add(Dropout(dropout[1])) 
    model.add(Dense(35, kernel_initializer='normal', activation=act[2]))
    model.add(Dropout(dropout[2])) 
    model.add(Dense(output_dim, kernel_initializer='normal', activation='softmax'))
    # Compile model
    model.compile(loss=loss, optimizer=optimizer, 
                  metrics=['categorical_accuracy', 'accuracy'])
    return(model)
    
    
def FNN_Regressor(ini_mode="normal", loss="mse", act=["relu", "tanh", "relu"],
                  dropout=[0.0, 0.0, 0.0], input_dim=218, output_dim=1,
                  lr=0.001, neurons=[50, 40, 35]):
    """
    Returns the best-performing neural network model from the manuscript.
    """
    model = Sequential()
    model.add(Dense(neurons[0], input_dim=input_dim, kernel_initializer=ini_mode, 
                    activation=act[0]))
    
    model.add(Dropout(dropout[0])) 
    model.add(Dense(neurons[1], kernel_initializer='normal', activation=act[1]))
    
    model.add(Dropout(dropout[1])) 
    model.add(Dense(neurons[2], kernel_initializer='normal', activation=act[2]))
    
    #output layer
    model.add(Dropout(dropout[2])) 
    model.add(Dense(1, kernel_initializer='normal', activation='relu'))
    # Compile model
    optimizer =  optimizers.Adam(lr=lr)
    model.compile(loss=loss, optimizer=optimizer, metrics=['mse'])
    #kernel_regularizer=regularizers.l2(0.01)
    return(model)
