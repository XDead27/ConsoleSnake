from random import random, randrange, choice, uniform
from random import seed
import math
import json

def sigmoid(x):
    return 1.0/(1.0 + math.exp(-x))

class QuirkyComputer:
    def __init__(self, ninput, nhidden, noutput):
        self.nn = self.init_network(ninput, nhidden, noutput)

    ##FOR NETWORK
    def init_network(self, ninput, nhidden, noutput):
        network = []
        for x in range(len(nhidden)):
            hidden_layer = [{'w': [uniform(-1, 1) for i in range(ninput if x == 0 else nhidden[x - 1])], 'b': uniform(-1, 1)} for i in range(nhidden[x])]
            network.append(hidden_layer)
        output_layer = [{'w': [uniform(-1, 1) for i in range(nhidden[-1])], 'b': uniform(-1, 1)} for i in range(noutput)]
        network.append(output_layer)
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
        for layer in self.nn:
            newInputs = []
            for n in layer:
                val = self.activate(n['w'], n['b'], nextInputs)
                newInputs.append(sigmoid(val))
            nextInputs = newInputs

        return nextInputs

    def get_highest_output(self, inputs):
        outputs = self.forward_propagate(inputs)
        return outputs.index(max(outputs))

def store(nns, file):
    with open(file, 'w') as fileHandle:
        json.dump(nns, fileHandle)

def restore(file):
    with open(file, 'r') as fileHandle:
        return json.load(fileHandle)
