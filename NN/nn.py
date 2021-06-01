from random import random, randrange, choice, uniform
from random import seed
import math
import numpy as np
from copy import deepcopy
import json

def sigmoid(x, deriv = False):
    if not deriv:
        np.clip(x, -500, 500)
        return (1.0/(1.0 + np.exp(-1*x))).round(8)
    else:
        return sigmoid(x)*(1 - sigmoid(x))

def linear(x, deriv=False):
    if not deriv:
        np.clip(x, -500, 500)
        return x
    else:
        return 1

def relu(x, deriv = False):
    if not deriv:
        np.clip(x, -500, 500)
        return np.maximum(0, x)
    else:
        return np.array([1 if i > 0 else 0 for i in x])
    
def leaky_relu(x, deriv = False):
    if not deriv:
        np.clip(x, -500, 500)
        return np.maximum(0.1*x, x)
    else:
        return np.array([1 if i > 0 else 0.1 for i in x])
    
##MAKE THIS WORK sometime soon
def softmax(x, deriv = False):
    if not deriv:
        return np.exp(x)/(np.sum(np.exp(x), axis=0))
    else:
        SM = x.reshape((-1,1))
        jac = np.diagflat(x) - np.dot(SM, SM.T)
        return jac
    
def probability(x):
    return x / np.sum(x, axis=0)
    
def hubert_loss(prediction, target, deriv = False):
    delta = 1.35 #tune this accordingly
    loss = np.abs(prediction - target)
    
    if not deriv:
        return (.5*(loss**2)) if loss <= delta else (delta*loss - .5*(delta**2))
    else:
        return (prediction - target) if loss <= delta else (math.copysign(1, prediction - target) * delta)
    
def random_init(layers, l):
    params = {}
    
    params['weights'] = (np.random.randn(layers[l], layers[l-1]) * 10).round(7)
    params['biases'] = np.zeros((layers[l], 1))
        
    return params

def he_init(layers, l):
    params = {}
    
    sd = math.sqrt(2/layers[l-1])
    params['weights'] = (np.random.randn(layers[l], layers[l-1]) * sd).round(7)
    params['biases'] = np.zeros((layers[l], 1))
        
    return params

def zero_init(layers, l):
    params = {}
    
    params['weights'] = np.zeros((layers[l], layers[l-1]))
    params['biases'] = np.zeros((layers[l], 1))
    
    return params


#Test
def calculate_deriv(Z, W, x):
    dir_matrix = np.zeros((W.shape[0] * W.shape[1], Z.shape[0]))
    
    for k in range(0, Z.shape[0]):
        for i in range(0, W.shape[1]):
            for j in range(0, W.shape[0]):
                if i == k:
                    dir_matrix[(i*W.shape[0]) + j][k] = x[j]
     
    return dir_matrix

class ANN:
    def __init__(self, layers_dimensions, layer_activ_funcs = None, layer_init_funcs = None):
        if layer_activ_funcs == None:
            layer_activ_funcs = [sigmoid for i in range(len(layers_dimensions))]
        if layer_init_funcs == None:
            layer_init_funcs = [random_init for i in range(len(layers_dimensions))]
            
        self.activation_funcs = layer_activ_funcs
        self.init_funcs = layer_init_funcs
        
        self.nn = self.init_network(layers_dimensions)

    ##FOR NETWORK
    def init_network(self, layers_dimensions):
        network = []
        for x in range(1, len(layers_dimensions)):
            params = self.init_funcs[x - 1](layers_dimensions, x)
            new_layer = [{'w': params['weights'][i], 'b': params['biases'][i]} for i in range(layers_dimensions[x])]
            network.append(new_layer)
        return network

    def init_network_from_list(self, list):
        self.nn = list

    def activate(self, weights, bias, inputs):
        sum = bias
        for i in range(len(weights)):
            sum += weights[i] * inputs[i]
        return sum

    def forward_propagate(self, inputs):
        nextInputs = inputs
        for i in range(len(self.nn)):
            layer = self.nn[i]
            newInputs = []
            activations = np.array([])
            for j in range(len(layer)):
                val = (self.activate(layer[j]['w'], deepcopy(layer[j]['b']), nextInputs)).round(8)
                layer[j]['activ'] = val
                activations = np.append(activations, val, axis=None)
                                            
            for j in range(len(layer)):
                layer[j]['output'] = self.activation_funcs[i](activations)[j]
            newInputs.extend(self.activation_funcs[i](activations))
            nextInputs = newInputs

        return nextInputs

    def get_highest_output(self, inputs):
        outputs = self.forward_propagate(inputs)
        return outputs.index(max(outputs))
    
    ##BACKPROPAGATION
    #Need to clean a bit after I better understand
    def backward_propagate(self, target):
        for i in reversed(range(len(self.nn))):
            layer = self.nn[i]
            errors = list()
            if i != len(self.nn)-1:
                for j in range(len(layer)):
                    error = 0.0
                    for neuron in self.nn[i + 1]:
                        error += (neuron['w'][j] * neuron['delta'])
                    errors.append(error)
            else:
                for j in range(len(layer)):
                    neuron = layer[j]
                    loss_to_error_deriv = hubert_loss(neuron['output'], target[j], deriv=True) 
                    errors.append(loss_to_error_deriv)
            for j in range(len(layer)):
                neuron = layer[j]
                neuron['delta'] = errors[j] * self.activation_funcs[i](neuron['activ'], deriv=True)
                
    # Update network weights with error
    def update_weights(self, input, l_rate):
        for i in range(len(self.nn)):
            inputs = input[:-1]
            if i != 0:
                inputs = [neuron['output'] for neuron in self.nn[i - 1]]
            for neuron in self.nn[i]:
                for j in range(len(inputs)):
                    neuron['w'][j] -= l_rate * neuron['delta'] * inputs[j]
                neuron['b'] -= l_rate * neuron['delta']
                
    def print_matrix(self):
        for layer in self.nn:
            for neuron in layer:
                print(str(neuron) + "\n")
            print("\n")
    
    def print_error_sum(self, expected):
        print(sum([hubert_loss(self.nn[-1][i]['output'], expected[i]) for i in range(len(expected))]))
        
    #WIP
    def train_network(self, data, l_rate, n_epoch):
        for epoch in range(n_epoch):
            sum_error = 0
            for row in data:
                outputs = self.forward_propagate(row)
                expected = [0 for i in range(len(self.nn[-1]))]
                expected[row[-1]] = 1
                sum_error += sum([hubert_loss(self.nn[-1][i]['output'], expected[i]) for i in range(len(expected))])
                self.backward_propagate(expected)
                self.update_weights(row, l_rate)
            print('>epoch=%d, lrate=%.3f, error=%.3f' % (epoch, l_rate, sum_error))
            
    
        

def store(nns, file):
    with open(file, 'w') as fileHandle:
        json.dump(nns, fileHandle)

def restore(file):
    with open(file, 'r') as fileHandle:
        return json.load(fileHandle)


#Debug
# dummy_dataset = []
# for i in range(20):
#     inputs = [(random()) for j in range(50)]
#     inputs.append(choice([0, 1, 2, 3]))
#     dummy_dataset.append(inputs)