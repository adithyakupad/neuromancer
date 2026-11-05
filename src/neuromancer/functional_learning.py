"""Prospective M013 task and standardized readout, separate from neural dynamics."""
import numpy as np
from .substrate import Command


def balanced_symbols(size, rng):
    if size % 4:
        raise ValueError('Balanced split requires a multiple of four')
    symbols = np.tile(np.array([[0,0],[0,1],[1,0],[1,1]]),(size//4,1))
    return symbols[rng.permutation(size)]


def schedule(a, b, delay_ms, start_us, trial_id):
    if a not in (0,1) or b not in (0,1) or delay_ms < 20 or delay_ms % 20:
        raise ValueError('Invalid task symbols or delay')
    rows = np.zeros((8+delay_ms//20,4))
    rows[0,a] = 30
    rows[1,a] = 60
    rows[2,a] = 30
    second = 2+delay_ms//20
    rows[second,2+b] = 30
    rows[second+1,2+b] = 60
    rows[second+2,2+b] = 30
    commands = [Command(trial_id,str(start_us+i*20000),start_us+i*20000,tuple(row))
                for i,row in enumerate(rows)]
    return commands, slice(second+2,second+4)


def ridge_fit(features, targets, alpha):
    design = np.column_stack((np.ones(len(features)),features))
    return np.linalg.solve(design.T@design+alpha*np.eye(design.shape[1]),design.T@targets)


def predict(features, coefficients):
    return np.column_stack((np.ones(len(features)),features))@coefficients


def balanced_accuracy(targets, predictions):
    targets = np.asarray(targets)
    predicted = np.asarray(predictions) >= .5
    if set(targets) != {0,1}:
        raise ValueError('Both classes required')
    return float(np.mean([np.mean(predicted[targets==label]==label) for label in [0,1]]))


def probe_fit(features, labels, validation, validation_labels):
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale==0] = 1.
    training = (features-mean)/scale
    held_out = (validation-mean)/scale
    fits = []
    scores = []
    for alpha in [.1,1.,10.]:
        coefficients = ridge_fit(training,labels,alpha)
        fits.append(coefficients)
        scores.append(balanced_accuracy(validation_labels,predict(held_out,coefficients)))
    selected = int(np.argmax(scores))
    return mean,scale,fits[selected],selected,scores


def probe_predict(features, fit):
    mean,scale,coefficients,_,_ = fit
    return predict((features-mean)/scale,coefficients)
