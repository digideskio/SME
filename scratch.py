__author__ = 'rockt'

import numpy as np
import theano.tensor as T
from theano import function

x = T.dscalar('x')
y = T.dscalar('y')
z = x + y
f = function([x, y], z)

print f(2, 3)

a = np.random.random((2, 2, 2))
b = np.random.random((1, 2))
print "a\n", a, "\n\nb\n", b

c = np.outer(a, b)

print "a outer b", c

