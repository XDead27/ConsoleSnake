from os import replace
import numpy as np
import sys
from random import *
from numpy.core.numeric import indices
sys.path.insert(1, '/home/mrxdead/Documents/Projects/ConsoleSnake')
from NN.nn import *
from collections import deque
from bisect import insort

class DQN:
    minibatch_size = 8
    
    def __init__(self, layers_dimensions, layer_activ_funcs = None, layer_init_funcs = None):
        self.main_model = ANN(layers_dimensions, layer_activ_funcs, layer_init_funcs)
        self.target_model = ANN(layers_dimensions, layer_activ_funcs, layer_init_funcs)
        self.target_model.nn = deepcopy(self.main_model.nn)
        self.experience = deque([])
        self.max_experience = 1200
        self.gamma = 0.1
        self.learning_rate = 0.008
        
        #Debug
        self.mean_error = 0.0
        self.last_minibatch = []
        
    def init_from_list(self, list):
        self.main_model.init_network_from_list(list)
        self.update_target_model()
        
    def predict_action(self, state):
        return np.argmax(self.main_model.forward_propagate(state))
        
    def update_target_model(self):
        self.target_model.nn = deepcopy(self.main_model.nn)
        
    def train(self):
        states, actions, rewards, next_states, dead = self.get_minibatch(self.minibatch_size)
        sum_error = 0.0
        #Iterate through all data from the minibatch
        for i in range(len(states)):
            #Calculate target Q value based on previous instance of network
            predicted_old_action = self.predict_action(next_states[i])
            if dead[i]:
                target_value = rewards[i]
            else:
                target_value = rewards[i] + self.gamma * self.target_model.forward_propagate(next_states[i])[predicted_old_action]
                
            #Calculate prediction for that state and action
            predicted_output = self.main_model.forward_propagate(states[i])
                
            #Calculate target output for our network
            target_output = np.array(predicted_output)
            target_output[actions[i]] = target_value
            
            #Now backprop and update weights
            self.main_model.backward_propagate(target_output)
            self.main_model.update_weights(states[i], self.learning_rate)
            
            #Update state surprise factor
            new_surprise = abs(np.max(predicted_output) - target_value)
            self.store_experience(states[i], actions[i], rewards[i], next_states[i], dead[i], new_surprise)
            
            #Update error for debug
            sum_error += hubert_loss(max(predicted_output), target_value)
            
        self.mean_error = sum_error / len(states)
            
            
        
    def store_experience(self, state, action, reward, next_state, dead, surprise = None):
        if len(self.experience) > self.max_experience:
            self.experience.pop()
        
        if surprise == None: 
            #Calculate surprise factor
            predicted_old_action = self.predict_action(next_state)
            if dead:
                target_output = reward
            else:
                target_output = reward + self.gamma * self.target_model.forward_propagate(next_state)[predicted_old_action]
            predicted_output = max(self.main_model.forward_propagate(state))
            surprise = abs(target_output - predicted_output)
                        
        self.experience.appendleft([state, action, reward, next_state, dead, surprise])

    def get_minibatch(self, batch_size):
        surprise_coef = softmax([x[5] for x in self.experience])
        cs = np.cumsum(surprise_coef)
        indices = [sum(cs < np.random.rand()) for i in range(batch_size)]
        
        states = []; actions =[]; rewards=[]; next_states=[]; dead=[]
        for idx in indices:
            states.append(self.experience[idx][0])
            actions.append(self.experience[idx][1])
            rewards.append(self.experience[idx][2])
            next_states.append(self.experience[idx][3])
            dead.append(self.experience[idx][4])
            self.last_minibatch.append(deepcopy(self.experience[idx]))
            
        for idx in sorted(dict.fromkeys(indices), reverse=True):
            del self.experience[idx]
                    
        return np.array(states), np.array(actions), np.array(rewards), np.array(next_states), np.array(dead)

# hank = DQN([24, 12, 12, 4], [leaky_relu, leaky_relu, leaky_relu], [he_init, he_init, he_init])
