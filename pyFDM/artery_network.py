# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np

from artery import Artery
from lax_wendroff import LaxWendroff
import utils


class ArteryNetwork(object):
    """
    Class representing a network of arteries.
    """
    
    
    def __init__(self, R, a, b, lam, sigma, rho, mu, depth, **kwargs):
        self._depth = depth
        self._arteries = []
        self.setup_arteries(R, a, b, lam, sigma, rho, mu, **kwargs)
        self._t = 0.
        self._ntr = kwargs['ntr']
        self._progress = 10
        
        
    def setup_arteries(self, R, a, b, lam, sigma, rho, mu, **kwargs):
        pos = 0
        self.arteries.append(Artery(pos, R, lam, sigma, rho, mu, **kwargs)) 
        pos += 1
        radii = [R]
        for i in range(1,self.depth):
            new_radii = []
            for radius in radii:    
                ra = radius * a
                rb = radius * b
                self.arteries.append(Artery(pos, ra, lam, sigma, rho, mu, **kwargs))
                pos += 1
                self.arteries.append(Artery(pos, rb, lam, sigma, rho, mu, **kwargs))
                pos += 1
                new_radii.append(ra)
                new_radii.append(rb)
            radii = new_radii
            
            
    def initial_conditions(self, u0, ntr):
        for artery in self.arteries:
            artery.initial_conditions(u0, self.ntr)            
            
            
    def mesh(self, nx):
        for artery in self.arteries:
            artery.mesh(nx)
            
    
    def set_time(self, nt, dt, T=0.0, tc=1):
        self._nt = nt
        self._dt = dt
        self._tf = nt * dt
        self._dtr = nt*dt/(self.ntr-1)
        self._T = T
        self._tc = tc
            
            
    def timestep(self):
        self._t += self.dt
            
    
    @staticmethod        
    def inlet_bc(artery, u_prev, u_in, dt):
        c_prev = artery.wave_speed(u_prev[0,0])
        w_prev = u_prev[1,0:2] - 4*c_prev
        lam_2 = u_prev[1,0] - c_prev
        x_0 = artery.x[0] - lam_2 * dt
        w_2 = utils.extrapolate(x_0, artery.x[0:2], w_prev)
        a_in = (u_in - w_2)**4 / 64 * (artery.rho/artery.beta)**2
        return np.array([a_in, u_in])
     
    
    @staticmethod
    def outlet_bc(artery, u_prev, a_out, dt):
        c_prev = artery.wave_speed(u_prev[0,-1])
        w_prev = u_prev[1,-2:] + 4*c_prev
        lam_1 = u_prev[1,-1] + c_prev
        x_0 = artery.x[-1] - lam_1 * dt
        w_1 = utils.extrapolate(x_0, artery.x[-2:], w_prev)
        u_out = w_1 - 4*a_out**(1/4) * np.sqrt(artery.beta/(2*artery.rho))
        return np.array([a_out, u_out])
        
    
    @staticmethod
    def bifurcation_bc(artery, p, d1, d2):
        pass
    
    
    @staticmethod
    def cfl_condition(artery, dt):
        c = artery.wave_speed(artery.U0[0,1])
        u = artery.U0[1,1]
        v = (u + c, u - c)
        left = dt/artery.dx
        right = np.power(np.absolute(v), -1)
        return False if (left > right).any() else True
            
    
    def solve(self, u0, u_in, p_out, T):
        # solution list holds numpy arrays of solution
        tr = np.linspace(self.tf-self.T, self.tf, self.ntr)
        #tr = np.linspace(0, self.tf, self.ntr)
        i = 0
        
        #np.savetxt("./data/artery_inlet.csv" , u_in(np.linspace(0, T, self.nt)), delimiter=",")
        
        while self.t < self.tf:
            save = False            
            
            if (self.t == self.tf) or (i < self.ntr and abs(self.t - tr[i]) < self.dtr):
                save = True
                i += 1
                
            for artery in self.arteries:
                nx = len(artery.x)
                lw = LaxWendroff(nx, artery.dx)
                
                if artery.pos == 0:
                    # inlet boundary condition
                    if self.T > 0:
                        in_t = utils.periodic(self.t, self.T)
                    else:
                        in_t = self.t
                    U_in = ArteryNetwork.inlet_bc(artery, artery.U0, u_in(in_t), self.dt)
                else:
                    #todo: bifurcation inlet boundary
                    pass
                if artery.pos >= (len(self.arteries) - 2**(self.depth-1)):
                    # outlet boundary condition
                    U_out = ArteryNetwork.outlet_bc(artery, artery.U0, artery.A0, self.dt)
                else:
                    #todo: bifurcation outlet condition
                    pass
                
                artery.solve(lw, U_in, U_out, self.t, self.dt, save, i-1, T=self.T)
                if ArteryNetwork.cfl_condition(artery, self.dt) == False:
                    raise ValueError(
                            "CFL condition not fulfilled at time %e. Reduce \
time step size." % (self.t))
                    sys.exit(1)                
                
            self.timestep()
            
            if self.t % (self.tf/10) < self.dt:
                print "Progress {:}%".format(self._progress)
                self._progress += 10
            
            
    def dump_results(self, suffix, data_dir):
        for artery in self.arteries:
            artery.dump_results(suffix, data_dir)
                       
                       
    def spatial_plots(self, suffix, plot_dir, n):
        for artery in self.arteries:
            artery.spatial_plots(suffix, plot_dir, n)
        
        
    def time_plots(self, suffix, plot_dir, n):
        time = np.linspace(self.tf-self.T, self.tf, self.ntr)
        for artery in self.arteries:
            artery.time_plots(suffix, plot_dir, n, time)

            
    @property
    def depth(self):
        return self._depth
        
        
    @property
    def arteries(self):
        return self._arteries
        
        
    @property
    def nt(self):
        return self._nt
        
        
    @property
    def dt(self):
        return self._dt
        
    
    @property        
    def tf(self):
        return self._tf
        
        
    @property
    def T(self):
        return self._T
        
        
    @property
    def tc(self):
        return self._tc
        
        
    @property
    def t(self):
        return self._t
        
        
    @property
    def ntr(self):
        return self._ntr
        
        
    @property
    def dtr(self):
        return self._dtr