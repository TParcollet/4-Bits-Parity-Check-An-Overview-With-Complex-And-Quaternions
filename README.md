Complex and Quaternion Dense Neural Networks Layers for solving the 4-Bit parity check problem
=====================

This repository contains code which evaluates the abilities of Real,
Complex, and quaternion based Dense Layers to solve the 4-bit parity
check problem. It demonstrates the effectiveness of using other
algebras to reduce the size of Neural Networks for a given task. 


Requirements
------------

Install requirements for experiments with pip:
```
pip install numpy Theano keras tensorflow
```

Depending on your Python installation you might want to use anaconda or other tools. 

Experiments
-----------

1. Run models:

```
python xor.py
```

Parameters can be modified directly in xor.py, such as:
    
- Number of epochs
- Batch Size
- Optimizer

Original Paper
-----------

This work is based on the original paper of Tohru Nitta: "A Solution to the 4-bit Parity Problem with a Single Quaternary Neuron"
