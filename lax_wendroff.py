# -*- coding: utf-8 -*-

from __future__ import division

import numpy as np
from scipy.interpolate import interp1d

from blood_flow import *


class LaxWendroff(object):
    """
    Class implementing Richtmyer's 2 step Lax-Wendroff method.
    """
    
    
    @property   
    def nt(self):
        return self._nt
        
        
    @property   
    def nx(self):
        return self._nx
        
        
    @property   
    def dt(self):
        return self._dt
        
        
    @property   
    def dx(self):
        return self._dx
        
        
    @property   
    def dtr(self):
        return self._dtr
        
        
    @property   
    def init_cond(self):
        return self._init_cond
        
        
    @property   
    def U(self):
        return self._U
        
        
    @U.setter
    def U(self, value): 
        self._U = value
        
        
    @property   
    def ir(self):
        return self._ir
        
        
    @ir.setter
    def ir(self, value): 
        self._ir = value
        

    def __init__(self, nt, nx, dt, dx, init_cond, ntr=100):
        self._nt = int(nt)
        self._nx = int(nx)
        self._dt = dt
        self._dx = dx
        self._dtr = nt*dt/(ntr-1)
        self._U = np.zeros((2, ntr, nx))
        self._ir = 1
        self._init_cond = init_cond
        
        
    def initial_conditions(self):
        U0 = np.zeros((2,self.nx))
        N = len(self.init_cond)
        # check that we're dealing with 2 equations
        if N != 2:
            raise ValueError("%d initial conditions supplied, 2 expected."\
                        % (N))
        for i in range(N):
            U0[i,:] = self.init_cond[i]
        return U0
     
     
    def solve(self, inlet_bc, outlet_bc, cfl_condition, F, S, in_args,
                  out_args, cfl_args, F_args, S_args):
        # U0: previous timestep, U1 current timestep
        U0 = self.initial_conditions()
        np.copyto(self.U[:,0,:], U0)
        i = 1
        
        while i < self.nt:
            i += 1
            U1 = np.zeros((2,self.nx))
            t = i * self.dt
            # inlet boundary condition
            U1[:,0] = inlet_bc(U0, t, in_args)
            # outlet boundary condition
            U1[:,-1] = outlet_bc(U0, t, out_args)
            
            for j in range(1,self.nx-1):
                U_prev = U0[:,j-1:j+2]
                if len(U_prev[0,:]) == 2:
                    U_prev = U0[:,j-1:]
                F_prev = F(U_prev, F_args)
                S_prev = S(U_prev, S_args)
                U1[:,j] = self.lax_wendroff(U_prev, F_prev, S_prev, F, S,
                            F_args, S_args)
                
                if cfl_condition(U1[:,j], cfl_args) == False:
                    raise ValueError(
                        "CFL condition not fulfilled at time step %d, \
position %d.\nReduce time step size." % (i,j))
                    sys.exit(1)
            if abs(t - self.dtr*self.ir) < self.dt:
                np.copyto(self.U[:,self.ir,:], U1)
                self.ir += 1
            np.copyto(U0, U1)
        return self.U
                    
                    
    def lax_wendroff(self, U_prev, F_prev, S_prev, F, S, F_args, S_args):
        # u_prev = [U[m-1], U[m], U[m+1]], F_prev, S_prev analogously
        U_np_mp = (U_prev[:,2]+U_prev[:,1])/2 + self.dt/2 *\
                    (-(F_prev[:,2]-F_prev[:,1])/self.dx +\
                    (S_prev[:,2]+S_prev[:,1])/2)
        U_np_mm = (U_prev[:,1]+U_prev[:,0])/2 + self.dt/2 *\
                    (-(F_prev[:,1]-F_prev[:,0])/self.dx +\
                    (S_prev[:,1]+S_prev[:,0])/2)
        F_np_mp = F(U_np_mp, F_args)
        F_np_mm = F(U_np_mm, F_args)
        S_np_mp = S(U_np_mp, S_args)
        S_np_mm = S(U_np_mm, S_args)
        
        U_np = U_prev[:,1] - self.dt/self.dx * (F_np_mp-F_np_mm) + self.dt/2 *\
                (S_np_mp+S_np_mm)
        return U_np
        
        