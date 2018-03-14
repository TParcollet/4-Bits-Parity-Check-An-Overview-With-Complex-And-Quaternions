#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Authors: Parcollet Titouan
#

from keras import backend as K
import sys; sys.path.append('.')
from keras import backend as K
from keras import activations, initializers, regularizers, constraints
from keras.layers import Layer, InputSpec
import numpy as np
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from .utils import sqrt_init

class QuaternionDense(Layer):
    """Regular quaternion densely-connected NN layer.
    `QuaternionDense` implements the operation:
    `real_preact = dot(real_input, real_kernel) - dot(imag_input, imag_kernel)`
    `imag_preact = dot(real_input, imag_kernel) + dot(imag_input, real_kernel)`
    `output = activation(K.concatenate([real_preact, imag_preact]) + bias)`
    where `activation` is the element-wise activation function
    passed as the `activation` argument, `kernel` is a weights matrix
    created by the layer, and `bias` is a bias vector created by the layer
    (only applicable if `use_bias` is `True`).
    Note: if the input to the layer has a rank greater than 2, then
    AN ERROR MESSAGE IS PRINTED.
    # Arguments
        units: Positive integer, dimensionality of each of the real part
            and the imaginary part. It is actualy the number of complex units.
        activation: Activation function to use
            (see keras.activations).
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: `a(x) = x`).
        use_bias: Boolean, whether the layer uses a bias vector.
        kernel_initializer: Initializer for the complex `kernel` weights matrix.
            By default it is 'complex'.
            and the usual initializers could also be used.
            (see keras.initializers and init.py).
        bias_initializer: Initializer for the bias vector
            (see keras.initializers).
        kernel_regularizer: Regularizer function applied to
            the `kernel` weights matrix
            (see keras.regularizers).
        bias_regularizer: Regularizer function applied to the bias vector
            (see keras.regularizers).
        activity_regularizer: Regularizer function applied to
            the output of the layer (its "activation").
            (see keras.regularizers).
        kernel_constraint: Constraint function applied to the kernel matrix
            (see keras.constraints).
        bias_constraint: Constraint function applied to the bias vector
            (see keras.constraints).
    # Input shape
        a 2D input with shape `(batch_size, input_dim)`.
    # Output shape
        For a 2D input with shape `(batch_size, input_dim)`,
        the output would have shape `(batch_size, units)`.
    """

    def __init__(self, units,
                 activation=None,
                 use_bias=True,
                 init_criterion='he',
                 kernel_initializer=sqrt_init,
                 bias_initializer='zeros',
                 kernel_regularizer=None,
                 bias_regularizer=None,
                 activity_regularizer=None,
                 kernel_constraint=None,
                 bias_constraint=None,
                 seed=None,
                 **kwargs):
        if 'input_shape' not in kwargs and 'input_dim' in kwargs:
            kwargs['input_shape'] = (kwargs.pop('input_dim'),)
        super(QuaternionDense, self).__init__(**kwargs)
        self.units = units
        self.activation = activations.get(activation)
        self.use_bias = use_bias
        self.init_criterion = init_criterion
        if kernel_initializer in {'complex'}:
            self.kernel_initializer = kernel_initializer
        else:
            self.kernel_initializer = initializers.get(kernel_initializer)
        self.bias_initializer = initializers.get(bias_initializer)
        self.kernel_regularizer = regularizers.get(kernel_regularizer)
        self.bias_regularizer = regularizers.get(bias_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)
        self.kernel_constraint = constraints.get(kernel_constraint)
        self.bias_constraint = constraints.get(bias_constraint)
        if seed is None:
            self.seed = np.random.randint(1, 10e6)
        else:
            self.seed = seed
        self.input_spec = InputSpec(ndim=2)
        self.supports_masking = True

    def build(self, input_shape):
        assert len(input_shape) == 2
        assert input_shape[-1] % 2 == 0
        input_dim = input_shape[-1] // 4
        data_format = K.image_data_format()
        kernel_shape = (input_dim, self.units)
        fan_in, fan_out = initializers._compute_fans(
            kernel_shape,
            data_format=data_format
        )
        if self.init_criterion == 'he':
            s = 1. / np.sqrt(2*fan_in)
        elif self.init_criterion == 'glorot':
            s = 1. / np.sqrt(2*(fan_in + fan_out))
        rng = RandomStreams(seed=self.seed)

        # Equivalent initialization using amplitude phase representation:
        """modulus = rng.rayleigh(scale=s, size=kernel_shape)
        phase = rng.uniform(low=-np.pi, high=np.pi, size=kernel_shape)
        def init_w_real(shape, dtype=None):
            return modulus * K.cos(phase)
        def init_w_imag(shape, dtype=None):
            return modulus * K.sin(phase)"""

        # Initialization using euclidean representation:
        def init_w_real(shape, dtype=None):
            return rng.normal(
                size=kernel_shape,
                avg=0,
                std=s,
                dtype=dtype
            )
        def init_w_imag(shape, dtype=None):
            return rng.normal(
                size=kernel_shape,
                avg=0,
                std=s,
                dtype=dtype
            )
        if self.kernel_initializer in {'complex'}:
            real_init = init_w_real
            imag_init = init_w_imag
        else:
            real_init = self.kernel_initializer
            imag_init = self.kernel_initializer

        self.r = self.add_weight(
            shape=kernel_shape,
            initializer=real_init,
            name='r',
            regularizer=self.kernel_regularizer,
            constraint=self.kernel_constraint
        )
        self.i = self.add_weight(
            shape=kernel_shape,
            initializer=imag_init,
            name='i',
            regularizer=self.kernel_regularizer,
            constraint=self.kernel_constraint
        )
        self.j = self.add_weight(
            shape=kernel_shape,
            initializer=imag_init,
            name='j',
            regularizer=self.kernel_regularizer,
            constraint=self.kernel_constraint
        )
        self.k = self.add_weight(
            shape=kernel_shape,
            initializer=imag_init,
            name='k',
            regularizer=self.kernel_regularizer,
            constraint=self.kernel_constraint
        )
        
        if self.use_bias:
            self.bias = self.add_weight(
                shape=(4 * self.units,),
                initializer=self.bias_initializer,
                name='bias',
                regularizer=self.bias_regularizer,
                constraint=self.bias_constraint
            )
        else:
            self.bias = None

        self.input_spec = InputSpec(ndim=2, axes={-1: 4 * input_dim})
        self.built = True

    def call(self, inputs):
        input_shape = K.shape(inputs)
        input_dim = input_shape[-1] // 4
        
        cat_kernels_4_r = K.concatenate([self.r, -self.i, -self.j, -self.k], axis=-1)
        cat_kernels_4_i = K.concatenate([self.i, self.r, -self.k, self.j], axis=-1)
	cat_kernels_4_j = K.concatenate([self.j, self.k, self.r, -self.i], axis=-1)
	cat_kernels_4_k = K.concatenate([self.k, -self.j, self.i, self.r], axis=-1)
        cat_kernels_4_quaternion = K.concatenate([cat_kernels_4_r, cat_kernels_4_i, cat_kernels_4_j, cat_kernels_4_k], axis=0)
        
        ########### Pre Softmax for quaternions
        # Get the normof each quaternion to squash from 4D to 1D
        #norm  = K.sqrt(K.pow(r_input,2)+K.pow(i_input,2)+K.pow(j_input, 2)+K.pow(k_input, 2))
        #r_input = self.activation(r_input)
        #i_input = self.activation(i_input)
        #j_input = self.activation(j_input)
        #k_input = self.activation(k_input)
        #output = K.concatenate([r_input, i_input, j_input, k_input], axis = -1)
        
        output = K.dot(inputs, cat_kernels_4_quaternion)
        
        if self.use_bias:
            output = K.bias_add(output, self.bias)
        if self.activation is not None:
            output = self.activation(output)

        return output

    def compute_output_shape(self, input_shape):
        assert input_shape and len(input_shape) == 2
        assert input_shape[-1]
        output_shape = list(input_shape)
        output_shape[-1] = self.units * 4
        return tuple(output_shape)

    def get_config(self):
        if self.kernel_initializer in {'complex'}:
            ki = self.kernel_initializer
        else:
            ki = initializers.serialize(self.kernel_initializer)
        config = {
            'units': self.units,
            'activation': activations.serialize(self.activation),
            'use_bias': self.use_bias,
            'init_criterion': self.init_criterion,
            'kernel_initializer': ki,
            'bias_initializer': initializers.serialize(self.bias_initializer),
            'kernel_regularizer': regularizers.serialize(self.kernel_regularizer),
            'bias_regularizer': regularizers.serialize(self.bias_regularizer),
            'activity_regularizer': regularizers.serialize(self.activity_regularizer),
            'kernel_constraint': constraints.serialize(self.kernel_constraint),
            'bias_constraint': constraints.serialize(self.bias_constraint),
            'seed': self.seed,
        }
        base_config = super(QuaternionDense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

