#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@File    :   ml_regression.py
@Author  :   Tom Jessel
@Contact :   jesselt@cardiff.ac.uk

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
21/09/2022 09:23   tomhj      1.0         Functions to create and evaluate NN regression models
"""
import os
import time
from typing import Dict, Any, List, Union
import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from keras import Sequential
from scikeras.wrappers import KerasRegressor
from sklearn.model_selection import KFold, train_test_split, RepeatedKFold
from sklearn.model_selection import cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV
from tensorflow import keras
import tensorflow as tf

from .experiment import load

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')
    console_formatter = logging.Formatter('%(name)s: %(levelname)s: %(message)s')

    file_handler = logging.FileHandler('ML.log')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def get_regression(
        meta: Dict[str, Any],
        hidden_layer_sizes: iter,
        dropout: float,
        init_mode: str
        ) -> Sequential:
    """
    Generate keras sequential regression model for SciKeras module

    Args:
        meta: Metadata from scikeras module containing model info.
        hidden_layer_sizes: Iterable setting the number of hidden layers and neurons of the model.
        dropout: Dropout rate for each dropout layer in the model, float between 0-1.
        init_mode: node initialization function to be used for each neuron.

    Returns:
        Keras sequential regression model, with the specified properties.
    """

    n_features_in_ = meta['n_features_in_']
    model = keras.models.Sequential()
    model.add(keras.layers.Input(shape=(n_features_in_,)))
    for hidden_layer_size in hidden_layer_sizes:
        model.add(keras.layers.Dense(hidden_layer_size, activation='relu', kernel_initializer=init_mode))
        model.add(keras.layers.Dropout(dropout))
    model.add(keras.layers.Dense(1))
    return model


def model_gridsearch(
        model: Union[KerasRegressor, Pipeline],
        Xdata: np.ndarray,
        ydata: np.ndarray,
        para_grid: Dict[str, iter],
        cv: int = 5
        ) -> [Union[KerasRegressor, Pipeline], Any]:
    """
    Gridsearch with cross-validation for given hyper-parameters of inputted model.

    Args:
        model: Pipeline/Model to analyse the hyper-parameters with.
        Xdata: Feature training data to carry out gridsearch with.
        ydata: Corresponding training data output.
        para_grid: Dict containing the name and values of the hyper-parameters to evaluate.
        cv: Number of splits to carry out when cross-validating each fitted model.

    Returns:
        Tuple containing the best performing estimator with given hyper-parameters, and the grid results object.

    """

    kfold = KFold(n_splits=cv, shuffle=True)

    grid = GridSearchCV(
        estimator=model,
        param_grid=para_grid,
        n_jobs=-1,
        cv=kfold,
        scoring={'r2': 'r2', 'MAE': 'neg_mean_absolute_error', 'MSE': 'neg_mean_squared_error'},
        refit='r2',
        verbose=True,
        return_train_score=True,
    )
    logger.info(f'___GridSearchCV___')
    logger.info('-' * 65)
    logger.info(f'Parameter grid: ')
    logger.info('-' * 65)
    for key, value in para_grid.items():
        logger.info(f'{key} - {value}')
    logger.info('-' * 65)
    gd_result = grid.fit(Xdata, ydata)
    best_estimator = gd_result.best_estimator_

    logger.info(f'Best Estimator:')
    logger.info('-' * 65)
    logger.info(f'Score: {gd_result.best_score_:.6f}')
    logger.info(f'Params:')
    for key, value in gd_result.best_params_.cv_items():
        logger.info(f'{key}: {value}')
    logger.info('-' * 65)

    logger.info('Results:')
    logger.info('-' * 65)
    means = gd_result.cv_results_['mean_test_r2']
    stds = gd_result.cv_results_['std_test_r2']
    params = gd_result.cv_results_['params']
    for mean, stdev, param in zip(means, stds, params):
        logger.info(f'{mean:.4f} ({stdev:.4f}) with: {param}')
    logger.info('-' * 65)
    return best_estimator, gd_result


def score_train(
        model: Any,
        Xdata: np.ndarray,
        ydata: np.ndarray,
        cv_splits: int = 10,
        cv_repeats: int = 5
        ) -> [Union[KerasRegressor, Pipeline], Dict]:
    """
    Score a model/pipeline on it's training set, using RepeatedKFold cross validation.

    Args:
        model: Model/Pipeline to score.
        Xdata: Training set input data.
        ydata: Corresponding training set outputs.
        cv_splits: Number of splits for cross validation per repetition.
        cv_repeats: Number of repeats to be carried out for repeated cross validation.

    Returns:
        Tuple containing the best scoring model/pipeline, and a Dict containing the scoring and timing data from
            cross-validation.
    """

    kfold = RepeatedKFold(n_splits=cv_splits, n_repeats=cv_repeats)
    scoring = {
        'MAE': 'neg_mean_absolute_error',
        'MSE': 'neg_mean_squared_error',
        'r2': 'r2',
    }
    # print('Scoring Model...\n')
    logger.info(f'___Cross Validating Model - Repeated KFold___')

    scores_ = cross_validate(
        estimator=model,
        X=Xdata,
        y=ydata,
        cv=kfold,
        scoring=scoring,
        return_train_score=True,
        verbose=0,
        # n_jobs=-1,
        return_estimator=True,
    )
    ind = np.argmax(scores_['test_r2'])
    best_model = scores_['estimator'][ind]

    # logger.info(best_model.model_.summary(print_fn=logger.info))
    logger.info('-' * 65)
    logger.info(f'Model Training Scores:')
    logger.info('-' * 65)
    logger.info(f'Train time = {np.mean(scores_["fit_time"]):.2f} s')
    logger.info(f'Predict time = {np.mean(scores_["score_time"]):.2f} s')
    logger.info(f'MAE = {np.abs(np.mean(scores_["test_MAE"])) * 1000:.3f} um')
    logger.info(f'MSE = {np.abs(np.mean(scores_["test_MSE"])) * 1_000_000:.3f} um^2')
    logger.info(f'R^2 = {np.mean(scores_["test_r2"]):.3f}')
    logger.info('-' * 65)
    return best_model, scores_


def score_test(
        model: Union[KerasRegressor, Pipeline],
        Xtest: np.ndarray,
        ytest: np.ndarray
        ) -> Dict[str, float]:
    """
    Score a fitted model/pipeline on test set data.

    Args:
        model: Model/Pipeline for scoring.
        Xtest: Test set input data.
        ytest: Corresponding test set output data.

    Returns:
        Dict containing the scores for the fitted model.
    """
    logger.info('Evaluating model with TEST set')
    y_pred = model.predict(Xtest, verbose=0)

    _test_score = {
        'MAE': mean_absolute_error(ytest, y_pred),
        'MSE': mean_squared_error(ytest, y_pred),
        'r2': r2_score(ytest, y_pred),
    }
    logger.info('-' * 65)
    logger.info(f'Model Test Scores:')
    logger.info('-' * 65)
    logger.info(f'MAE = {np.abs(_test_score["MAE"]) * 1000:.3f} um')
    logger.info(f'MSE = {np.abs(_test_score["MSE"]) * 1_000_000:.3f} um^2')
    logger.info(f'R^2 = {np.mean(_test_score["r2"]):.3f}')
    logger.info('-' * 65)

    fig, ax = plt.subplots()
    ax.plot(ytest, color='red', label='Real data')
    ax.plot(y_pred, color='blue', ls='--', label='Predicted data')
    ax.set_title('Model Predictions - Test Set')
    ax.set_ylabel('Mean Radius (mm)')
    ax.set_xlabel('Data Points')
    ax.legend()
    png_name = fr'ML Predictions Test Set.png'
    fig.savefig(fr'Figures/ML-Regression/{png_name}', dpi=300)
    logger.info(f'Figure saved - {png_name}')
    fig.show()
    logger.info('=' * 65)
    return _test_score


def train_history(model: Union[KerasRegressor, Pipeline]) -> None:
    """
    Plot training history of model, to show scores over epochs.

    Args:
        model: Fitted model/pipeline to plot training history of.

    """
    logger.info('___Model learning/validation history___')
    logger.info('-' * 65)
    pipe_bool = False
    if type(model) == Pipeline:
        pipe_bool = True

    if pipe_bool:
        hist = model['mlp_reg'].history_
    else:
        hist = model.history_
    history = pd.DataFrame(hist).drop(columns=['loss', 'val_loss']).rename(columns={
        'mean_absolute_error': 'MAE-train',
        'mean_squared_error': 'MSE-train',
        'val_mean_absolute_error': 'MAE-val',
        'val_mean_squared_error': 'MSE-val',
    })

    # Graph History Results

    ax = history.plot(
        subplots=[('MAE-train', 'MAE-val'), ('MSE-train', 'MSE-val')],
        xlabel='Epoch',
        xlim=(-1, len(history)),
        title='Regression Model Learning History'
    )
    ax[0].set_ylabel('Mean\nAbsolute Error')
    ax[1].set_ylabel('Mean\nSquared Error')
    fig_ = ax[1].get_figure()
    png_name_ = fr'ML learning history.png'
    fig_.savefig(fr'Figures/ML-Regression/{png_name_}', dpi=300)
    fig_.show()
    logger.info(f'Figure saved - {png_name_}')


def split_dataset(
        df: pd.DataFrame,
        split_frac: float = 0.2
        ) -> [np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Separate dataset into training and test set from full dataset (last column is results).

    Args:
        df: Dataset to separate and then split.
        split_frac: Fraction of dataset to split into the test set.

    Returns:
        Tuple containing the input training set, input test set, output test set, output training set.
    """
    dataset = df.values
    x = dataset[:, :-1]
    y = dataset[:, -1]

    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=split_frac)
    # logger.info('Split Dataset into Train and Test')
    return x_tr, x_te, y_tr, y_te


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create pipeline using input paramters. Made up of StandardScaler and KerasRegressor model.

    Args:
        **kwargs: Input paramters to create Keras regressor model with SciKeras, (i.e.
            model=get_regression,
            model__init_mode='glorot_normal',
            model__dropout=0.1,
            model__hidden_layer_sizes=(30, 30),
            optimizer='adam',
            optimizer__learning_rate=0.001,
            loss='mae',
            metrics=['MAE', 'MSE'],
            batch_size=10,
            epochs=500,
            verbose=0,)

    Returns:
        Pipeline made up of a standard scaler and keras regressor.
    """
    reg = KerasRegressor(**kwargs)
    p = Pipeline([
        ('scaler', StandardScaler()),
        ('mlp_reg', reg),
    ])
    return p


def plot_grid_results(gd_results: Any, comp_variable: str) -> None:
    """
    Plot gridsearchcv scores relative to a variable within the param grid.

    Args:
        gd_results: Gridsearch results object.
        comp_variable: Variable name to plot on the x-axis, must be specific enough to identify only one param.

    """
    params = list(gd_results.param_grid.keys())
    param = [p for p in params if comp_variable in p]
    param = 'param_' + param[0]

    # Get the regular numpy array from the MaskedArray
    x_axis = np.array(gd_results.cv_results_[param].data, dtype=float)
    for scorer, color in zip(sorted(gd_results.scoring), ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8']):
        plt.figure()
        plt.title(f'GridSearchCV results comparing {comp_variable}')
        plt.xlabel(comp_variable.capitalize())
        plt.ylabel("Score")
        ax = plt.gca()
        for sample, style in (("train", "--"), ("test", "-")):
            sample_score_mean = gd_results.cv_results_["mean_%s_%s" % (sample, scorer)]
            sample_score_std = gd_results.cv_results_["std_%s_%s" % (sample, scorer)]
            ax.fill_between(
                x_axis,
                sample_score_mean - sample_score_std,
                sample_score_mean + sample_score_std,
                alpha=0.1 if sample == "test" else 0,
                color=color,
            )
            ax.plot(
                x_axis,
                sample_score_mean,
                style,
                color=color,
                alpha=1 if sample == "test" else 0.7,
                label="%s (%s)" % (scorer, sample),
            )
        plt.legend(loc="best")
    plt.grid(False)
    plt.show()


if __name__ == '__main__':
    logger.info('=' * 65)
    exp = load(file='Test 5')
    logger.info('Loaded Dateset')
    dataframe = exp.features.drop(columns=['Runout', 'Form error']).drop([0, 1, 23, 24])

    logdir = 'ml-results/logs/MLP/CV/'
    run_name = f'{logdir}MLP-{time.strftime("%Y%m%d-%H%M%S", time.localtime())}'
    tb_writer = tf.summary.create_file_writer(run_name)

    pipe = create_pipeline(
        model=get_regression,
        model__init_mode='glorot_normal',
        model__dropout=0.1,
        model__hidden_layer_sizes=(30, 30),
        optimizer='adam',
        optimizer__learning_rate=0.001,
        loss='mae',
        metrics=['MAE', 'MSE'],
        batch_size=10,
        epochs=500,
        verbose=0,
        callbacks=[tf.keras.callbacks.TensorBoard(log_dir=run_name, histogram_freq=1)]
    )

    param_grid = dict(
        # model__init_mode=['lecun_uniform', 'glorot_normal', 'glorot_uniform', 'he_normal', 'he_uniform'],
        # model__hidden_layer_sizes=[(80,), (30, 25), (30, 30)],
        # model__dropout=[0, 0.1, 0.3, 0.5],
        # loss=['mse', 'mae'],
        # batch_size=[5, 8, 10, 15, 25, 32],
        # reg__epochs=np.arange(200, 1025, 25)
        # optimizer=['adam', 'SGD', 'RMSprop', 'Adagrad', 'Adamax', 'Adadelta'],
        # optimizer__learning_rate=[0.0005, 0.0075, 0.001, 0.0025, 0.005, 0.01],
    )

    X_train, X_test, y_train, y_test = split_dataset(dataframe)

    # pipe, grid_result = model_gridsearch(model=pipe, Xdata=X_train, ydata=y_train, para_grid=param_grid, cv=10)
    # plot_grid_results(grid_result, 'epochs')

    pipe, train_scores = score_train(model=pipe, Xdata=X_train, ydata=y_train)

    pipe.fit(X_train, y_train, reg__validation_split=0.2)
    train_history(pipe)

    test_score = score_test(pipe, X_test, y_test)
