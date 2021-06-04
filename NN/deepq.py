import numpy as np
import sys, os
from random import *
from NN.nn import *
from collections import deque

class DQN:
    minibatch_size = 8
    
    def __init__(self, layers_dimensions, layer_activ_funcs = None, layer_init_funcs = None):
        self.main_model = ANN(layers_dimensions, layer_activ_funcs, layer_init_funcs)
        self.target_model = ANN(layers_dimensions, layer_activ_funcs, layer_init_funcs)
        self.target_model.nn = deepcopy(self.main_model.nn)
        self.experience = deque([])
        self.max_experience = 1000
        self.gamma = 0.05
        self.learning_rate = 0.01
        
        #Debug
        self.mean_error = 0.0
        self.losses = []
        self.last_minibatch = []
        
    def init_from_list(self, list):
        self.main_model.init_network_from_list(list)
        self.update_target_model()
        
    def load_from_file(self, filename):
        if os.path.exists(filename):
            existing_data = np.load(filename, allow_pickle=True)
            games = existing_data[2]
            moves = existing_data[3]
            existing_net = existing_data[0]
            experience = existing_data[1]
            
            self.init_from_list(np.array(existing_net))
            self.experience = experience
            
            return games, moves
        return 0, 0
        
    def predict_action(self, state):
        return np.argmax(self.main_model.forward_propagate(state))
        
    def update_target_model(self):
        self.target_model.nn = deepcopy(self.main_model.nn)
        
    def train(self):
        states, actions, rewards, next_states, dead = self.get_minibatch(self.minibatch_size)
        self.losses = []
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
            self.losses.append(hubert_loss(max(predicted_output), target_value))
            
        self.mean_error = sum(self.losses) / len(states)
            
            
        
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
        e_hyper = 0.001 #ensures that no transition has zero priority
        a_hyper = 0.9 #controls the difference between high and low error
        surprise_p = [((x[5] + e_hyper)**a_hyper) for x in self.experience]
        surprise_coef = probability(surprise_p)
        cs = np.cumsum(surprise_coef)
        indices = [sum(cs < np.random.rand()) for i in range(batch_size)]
        
        self.last_minibatch = []
        
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

#For Keras
from tensorflow.keras.models import Sequential
from tensorflow.keras import layers
from tensorflow import keras
import tensorflow as tf

class KerasDQN:
    minibatch_size=8
    
    def __init__(self, layers_dimensions = None, layer_activ_funcs = None, layer_init_funcs = None):
        #model = Sequential()
        # model.add(Dense(layers_dimensions[1], input_dim=layers_dimensions[0], activation='relu'))
        # for x in layers_dimensions[2:-1]:
        #     model.add(Dense(x, activation='relu'))
        # model.add(Dense(layers_dimensions[-1], activation='linear'))
        # self.main_model = model.compile(optimizer='adam', loss='huber_loss')
        self.main_model = self.create_q_model()
        self.target_model = self.create_q_model()
        self.update_target_model()
        
        #Experience replay
        self.experience = deque([])
        self.max_experience = 1000
        self.gamma = 0.05
        self.learning_rate = 0.0025
        
        #Have no clue
        self.loss_function = keras.losses.Huber()
        self.optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate, clipnorm=1.0)
        
    def create_q_model(self):
        inputs = layers.Input(shape=(122,))

        layer1 = layers.Dense(110, activation="relu")(inputs)
        layer2 = layers.Dense(90, activation="relu")(layer1)
        
        action = layers.Dense(4, activation="linear")(layer2)

        return keras.Model(inputs=inputs, outputs=action)
    
    def load_from_file(self, filename):
        if os.path.exists(filename + ".npy"):
            existing_data = np.load(filename + ".npy", allow_pickle=True)
            games = existing_data[1]
            moves = existing_data[2]
            experience = existing_data[0]
            
            self.main_model = keras.models.load_model(filename + ".model")
            self.update_target_model()
            self.experience = experience
            
            return games, moves
        return 0, 0
    
    def save_to_file(self, filename, data):
        np.save(filename, data)
        self.main_model.save(filename + ".model")
        
    def predict_without_tensor(self, state, target=False):
        state_tensor = tf.convert_to_tensor(state)
        state_tensor = tf.expand_dims(state_tensor, 0)
        
        return (self.main_model if not target else self.target_model)(state_tensor, training=False)[0]
        
    def predict_action(self, state):
        return np.argmax(self.predict_without_tensor(state))
        
    def update_target_model(self):
        self.target_model.set_weights(self.main_model.get_weights())
        
    def train(self):
        states, actions, rewards, next_states, dead = self.get_minibatch(self.minibatch_size)
        #Pls understand tensors and why the fuck you use them
        dead = tf.convert_to_tensor([float(x) for x in dead])
        
        #Predict rewards for future states (DDQN) using the main model
        future_rewards = self.main_model.predict(next_states)
        updated_q_values = rewards + self.gamma * tf.reduce_max(future_rewards, axis=1) * dead
        
        masks = tf.one_hot(actions, 4) #4 is a bit of a magic number: is the number of possible actions the agent can take
        
        with tf.GradientTape() as tape:
            #Train thee model
            q_values = self.main_model(states)
            
            #Apply the masks (one_hot tensor) to the q-values to get the q-value for action taken
            q_action = tf.reduce_sum(tf.multiply(q_values, masks), axis=1)
            #Calculate loss
            loss = self.loss_function(updated_q_values, q_action)
        
        #Backprop
        grads = tape.gradient(loss, self.main_model.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.main_model.trainable_variables))

    def store_experience(self, state, action, reward, next_state, dead, surprise = None):
        if len(self.experience) > self.max_experience:
            self.experience.pop()
        
        if surprise == None: 
            #Calculate surprise factor
            future_reward = self.predict_action(next_state)
            if dead:
                target_output = reward
            else:
                target_output = reward + self.gamma * self.predict_without_tensor(next_state, target=True)[future_reward]
            predicted_output = max(self.predict_without_tensor(state))
            surprise = abs(target_output - predicted_output)
                        
        self.experience.appendleft([state, action, reward, next_state, dead, surprise])

    def get_minibatch(self, batch_size):
        e_hyper = 0.001 #ensures that no transition has zero priority
        a_hyper = 0.9 #controls the difference between high and low error
        surprise_p = [((x[5] + e_hyper)**a_hyper) for x in self.experience]
        surprise_coef = probability(surprise_p)
        cs = np.cumsum(surprise_coef)
        indices = [sum(cs < np.random.rand()) for i in range(batch_size)]
        
        self.last_minibatch = []
        
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
