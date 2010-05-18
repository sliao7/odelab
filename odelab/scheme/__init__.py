# -*- coding: UTF-8 -*-
from __future__ import division

import numpy as np
import numpy.linalg

class Scheme(object):
		
	def __str__(self):
		try:
			h = self.h
			hs = "%.2e" % h
		except AttributeError:
			hs = "-"
		return '<%s: h=%s>' % (self.__class__.__name__, hs)

	tail_length = 1

	@property
	def system(self):
		return self.solver.system
	
	def increment_stepsize(self):
		"""
		Change the step size based on error estimation.
		To be overridden for a variable step size method.
		"""
		pass
	
	h_default = .01
	
	# to be removed; use a signal instead
	def get_h(self):
		return self._h
	def set_h(self, h):
		self._h = h
		self._h_dirty = True
	h = property(get_h, set_h)

	def initialize(self):
		try:
			self.h = self.solver.h
		except AttributeError:
			self.h = self.h_default

class ExplicitEuler (Scheme):
	def step(self, t, u):
		return t + self.h, u + self.h*self.system.f(t, u)

class ImplicitEuler (Scheme):
	def step(self, t, u):
		res = self.system.f.res(u, t, self.h)
		return t + self.h, res


class RungeKutta4 (Scheme):
	"""
	Runge-Kutta of order 4.
	"""
	def step(self, t, u):
		f = self.system.f
		h = self.h
		Y1 = f(t, u)
		Y2 = f(t + h/2., u + h*Y1/2.)
		Y3 = f(t + h/2., u + h*Y2/2.)
		Y4 = f(t + h, u + h*Y3)
		return t+h, u + h/6.*(Y1 + 2.*Y2 + 2.*Y3 + Y4)

class RungeKutta34 (Scheme):
	"""
	Adaptive Runge-Kutta of order four.
	"""
	error_order = 4.
	# default tolerance
	tol = 1e-6

	def increment_stepsize(self):
		if self.error > 1e-15:
			self.h *= (self.tol/self.error)**(1/self.error_order)
		else:
			self.h = 1.

	def step(self, t, u):
		f = self.system.f
		h = self.h
		Y1 = f(t, u)
		Y2 = f(t + h/2., u + h*Y1/2.)
		Y3 = f(t + h/2, u + h*Y2/2)
		Z3 = f(t + h, u - h*Y1 + 2*h*Y2)
		Y4 = f(t + h, u + h*Y3)
		self.error = np.linalg.norm(h/6*(2*Y2 + Z3 - 2*Y3 - Y4))
		return t+h, u + h/6*(Y1 + 2*Y2 + 2*Y3 + Y4)

class ode15s(Scheme):
	"""
	Simulation of matlab's ``ode15s`` solver.
	It is a BDF method of max order 5
	"""
	
	
	def __init__(self, **kwargs):
		self.integrator_kwargs = kwargs

	def initialize(self): # the system must be defined before this is called!
		super(ode15s,self).initialize()
		import scipy.integrate
		self.integ = scipy.integrate.ode(self.system.f)
		vodevariant = ['vode', 'zvode'][np.iscomplexobj(self.solver.us[0])]
		self.integ.set_integrator(vodevariant, method='bdf', order=5, nsteps=3000, **self.integrator_kwargs)
		self.integ.set_initial_value(self.solver.us[0], self.solver.ts[0])

	def step(self, t, u):
		self.integ.integrate(self.integ.t + self.h)
		if not self.integ.successful():
			print("vode error")
		return self.integ.t, self.integ.y
