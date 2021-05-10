from random import random, randrange, choice, uniform
from random import seed
import math

##For evolution
def nn_to_vector(nn):
    #-1 is end of node
    #-2 is end of layer
    vec = []
    for layer in nn:
        for node in layer:
            vec.extend(node['w'])
            vec.append(node['b'])
            vec.append(-1)
        vec.append(-2)
    return vec

def vec_to_nn(vec):
    nn = []
    layer = []
    buf = []
    for x in vec:
        if x == -1:
            node = {}
            node['b'] = buf.pop()
            node['w'] = buf
            layer.append(node)
            buf = []
        elif x == -2:
            nn.append(layer)
            layer = []
        else:
            buf.append(x)
    return nn

def mutate(vec):
    nbOfMutations = randrange(0, math.ceil(0.05*len(vec)))
    for i in range(nbOfMutations):
        alleleToMutate = randrange(0, len(vec))
        while vec[alleleToMutate] in [-1, -2]:
            alleleToMutate = randrange(0, len(vec))
        vec[alleleToMutate] = uniform(-1, 1)

    return vec

def breedTwo(nn1, nn2):
    vec1 = nn_to_vector(nn1)
    vec2 = nn_to_vector(nn2)

    for i in range(len(vec1)):
        a1 = vec1[i]
        a2 = vec2[i]
        vec1[i] = choice([a1, a2])
        vec2[i] = choice([a1, a2])

    vec1 = mutate(vec1)
    vec2 = mutate(vec2)

    return [vec_to_nn(vec1), vec_to_nn(vec2)]
