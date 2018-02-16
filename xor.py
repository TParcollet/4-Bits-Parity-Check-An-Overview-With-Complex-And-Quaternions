from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import SGD,Adagrad
import numpy as np 
import itertools
import complexnn
from complexnn import *

######## Preparing the 4-Bit parity check
lst = list(itertools.product([0, 1], repeat=4))
x = np.asarray(lst)
lst = list(itertools.product([0, 1], repeat=4))
y = np.asarray(lst)

######## Parameters
opt = Adagrad(lr=0.1, epsilon=None, decay=0.0)
epochs = 100
batch_size = 1
bias = False

######## Quaternions
model_q = Sequential()
model_q.add(QuaternionDense(1,use_bias=bias, input_dim=4))
model_q.add(Activation('sigmoid'))
model_q.compile(loss='binary_crossentropy', \
        optimizer=opt)
model_q.fit(x, y, batch_size=batch_size, nb_epoch=epochs)

######## Complex
model_c = Sequential()
model_c.add(ComplexDense(2,use_bias=bias, input_dim=4))
model_c.add(Activation('sigmoid'))
model_c.compile(loss='binary_crossentropy', \
        optimizer=opt)
model_c.fit(x, y, batch_size=batch_size, nb_epoch=epochs)

######## Reals
model_r = Sequential()
model_r.add(Dense(4,use_bias=bias, input_dim=4))
model_r.add(Activation('sigmoid'))
model_r.compile(loss='binary_crossentropy', \
        optimizer=opt)
model_r.fit(x, y, batch_size=batch_size, nb_epoch=epochs)

######## Reports
print "Inputs : "
print x
print "Labels : "
print y
print "Real model, number of parameters : " \
        +str(model_r.count_params())
print model_r.predict_proba(x)
print "Complex model, number of parameters : " \
        +str(model_c.count_params())
print model_c.predict_proba(x)
print "Quaternion model, number of parameters : "\
        +str(model_q.count_params())
print model_q.predict_proba(x)
