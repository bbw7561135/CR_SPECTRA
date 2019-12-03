#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 11:21:55 2019

@author: lbrahimi
"""

import numpy as np 
import matplotlib.pyplot as plt

###############################################################################
# FUNCTIONS IN ORDER TO CREATE A GOOD SPLINE !!!                              #
###############################################################################
# TriDiagonal matrix inversion function
def InverseTrigonalMatrix(T) : 
    n = len(T)
    
    a = np.zeros(n)
    b = np.zeros(n)
    c = np.zeros(n)
    for i in range(n) : 
        b[i] = T[i][i]
        if (i < n-1) : c[i] = T[i][i+1]
        if (i > 0) : a[i] = T[i][i-1]
    
    theta_mm  = 0
    theta_m   = 1
    theta = np.zeros(n)
    theta[0] = b[0]*theta_m #- a[0]*c[0]*theta_mm
    theta[1] = b[1]*theta[0] - a[1]*c[0]*theta_m
    for i in range(2, n, 1) : 
        theta[i] = b[i]*theta[i-1] - a[i]*c[i-1]*theta[i-2]
    
    phi_pp = 0
    phi_p  = 1
    phi = np.zeros(n+2)
    phi[n] = phi_p
    phi[n+1] = phi_pp
    phi[n-1] = b[n-1]*phi_p #- c[n-1]*a[n]*phi_pp
    phi[n-2] = b[n-2]*phi[n-1] - c[n-2]*a[n-1]*phi_p
    for i in range(n-3, -1, -1) : 
        phi[i] = b[i]*phi[i+1] - c[i]*a[i+1]*phi[i+2]
        
    
    Tinv = np.empty((n, n))
    for i in range(n) : 
        for j in range(n) : 
    #        print (i,j)
            if (i < j) : 
                p = 1.
                for ei in range(i, j, 1) : 
                    p = p*c[ei]
                if (i-1 == -1) : 
                    loc_theta = theta_m
                if (i-1 > -1) : 
                    loc_theta = theta[i-1]
                
                Tij = (-1)**(i+j)*p*loc_theta*phi[j+1]/theta[n-1]
            if (i == j) : 
                if (i-1 == -1) : 
                    loc_theta = theta_m
                if (i-1 > -1) : 
                    loc_theta = theta[i-1]
                Tij = loc_theta*phi[j+1]/theta[n-1]
            if (i > j) : 
                p = 1.
                for ei in range(j+1, i+1, 1) : 
                    p = p*a[ei]
                if (j-1 == -1) : 
                    loc_theta = theta_m
                if (j-1 > -1) : 
                    loc_theta = theta[j-1]
                Tij = (-1)**(i+j)*p*loc_theta*phi[i+1]/theta[n-1]
            Tinv[i, j] = Tij
    
    return Tinv 


def ProductMatrix(A, B) : 
    A_l = len(A)
    A_c = len(A[0])
    
    B_l = len(B)
    B_c = len(B[0])
    
    C_l = A_l
    C_c = B_c
    
    C = np.zeros((C_l, C_c))
    for i in range(C_l) : 
        for j in range(C_c) : 
            s = 0.
            for k in range(A_c) : 
                s += A[i][k]*B[k][j]
            C[i][j]=  s 

    return C


def InterpolatingSpline(X, Y) : 

    N = len(X)
#    print (N)

    h = []
    for i in range(N-1) : 
        h.append([X[i+1] - X[i]])
    
    lowF  = 0.
    highF = 0.
    F = [[lowF]]
    for i in range(1, N-1) : 
        F.append([(Y[i+1] - Y[i])/h[i] - (Y[i] - Y[i-1])/h[i-1]])
    F.append([highF])

    R = np.zeros((N, N))
    R[0][0]     = 1.
    R[N-1][N-1] = 1.
    
    for i in range(1, N-1) : 
        R[i][i]   = (h[i-1][0] + h[i][0])/3.
        R[i][i+1] = h[i][0]/6.
        R[i][i-1] = h[i-1][0]/6.
    

    R_inv = InverseTrigonalMatrix(R)

    M = ProductMatrix(R_inv, F)
    
    Ci  = np.empty(N-1)
    Cip = np.empty(N-1)
    
    for i in range(N-1) : 
        Ci[i]  = (Y[i+1] - Y[i])/h[i][0] - h[i][0]*(M[i+1][0] - M[i][0])/6.
        Cip[i] = Y[i] - M[i][0]*h[i][0]**2/6.
    
    
    def f(x) : 
        for k in range(0, N-1) : 
            if (x >= X[k] and x <= X[k+1]) : 
                loc_a = M[k][0]*(X[k+1] - x)**3/(6.*h[k][0])
                loc_b = M[k+1][0]*(x - X[k])**3/(6.*h[k][0])
                loc_c = Ci[k]*(x-X[k]) + Cip[k]
        return loc_a + loc_b + loc_c 
    
    return f
###############################################################################
    
import sys 
sys.path.append('../tools/')
import constants as cst


def Rsh(nt) : 

    xhi_m = 1 # Metallicity (1 for solar abundances)
    xhi_cr= 0.1
    E51   = 1 # [10^51 erg] Total energy released by the SNR
    Mej   = 1 # [Msum] Total mass released by the SNR
    C06   = 1 # 
    beta  = 1 #
    phi_c = 1 # Ratio of the thermal conductivity to the Spitzer (1962) value
    vej8  = 10.*(E51/Mej)**(0.5)
    ###############################################################################
    # FUNCTIONS IN ORDER TO MAKE OUR SNR EXPAND IN THE ISM                        #
    ###############################################################################
    # We define the characteristic times of our problem
    tini   = 1e-4*cst.kyr # [s]
    tfree  = 0.3*E51**(-0.5)*Mej*nt**(-1./3)*cst.kyr # [s]
    tPDS   = np.exp(-1.)*3.61e4*E51**(3./14)/(xhi_m**(5./14)*nt**(4./7))*cst.yr # [s]
    tMCS   = min(61*vej8**3/(xhi_m**(9./14)*nt**(3./7)*E51**(3./14)), 476./(xhi_m*phi_c)**(9./14))*tPDS # [s]
    tmerge = 153.*(E51**(1./14)*nt**(1./7)*xhi_m**(3./14)/(beta*C06))**(10./7)*tPDS # [s]
    tmax = min(tMCS, tmerge) # [s]
    
    # We define the characteristic radii of our problem
    R_free    = 5.0*(E51/nt)**(1./5)*(1 - (0.05*Mej**(5./6))/(E51**0.5*nt**(1./3)*(tfree/cst.kyr)))**(2./5)*(tfree/cst.kyr)**(2./5)*cst.pc # [cm]
    R_ini     = R_free*(tini/tfree)**(1.)
    R_PDS     = 5.0*(E51/nt)**(1./5)*(1 - (0.05*Mej**(5./6))/(E51**0.5*nt**(1./3)*(tPDS/cst.kyr)))**(2./5)*(tPDS/cst.kyr)**(2./5)*cst.pc # [cm] 
    R_MCS     = R_PDS*(tMCS/tPDS)**(3./10)
    R_merge   = R_MCS*(tmerge/tMCS)**(1./4)
    if (tMCS < tmerge) : 
        t = np.array([tini, tfree, tPDS, tMCS, tmerge])
        R = np.array([R_ini, R_free, R_PDS, R_MCS, R_merge])
    if (tMCS >= tmerge) : 
        t = np.array([tini, tfree, tPDS, tmerge])
        R = np.array([R_ini, R_free, R_PDS, R_merge])
    
    # We pass in the loglog space 
    logt = np.empty(len(t))
    logR = np.empty(len(R))
    for ii in range(len(t)) : 
        logt[ii] = np.log10(t[ii])
        logR[ii] = np.log10(R[ii])
    # We apply the spline interpolation
    f_SNR = InterpolatingSpline(logt, logR)
    logt_new = np.linspace(logt[0], logt[-1], 100)
    logr_new = np.empty(len(logt_new))
    for ii in range(len(logt_new)) : 
        logr_new[ii] = f_SNR(logt_new[ii])
    # We come back in the linear space 
    t_new = np.empty(len(logt_new))
    r_new = np.empty(len(logr_new))
    for ii in range(len(t_new)) : 
        t_new[ii] = 10**(logt_new[ii])
        r_new[ii] = 10**(logr_new[ii])
        
    return t, R, t_new, r_new
    
    
t_WNM, R_WNM, t_new_WNM, r_new_WNM = Rsh(0.35)
t_CNM, R_CNM, t_new_CNM, r_new_CNM = Rsh(30.)
t_DiM, R_DiM, t_new_DiM, r_new_DiM = Rsh(300.)


plt.figure(figsize=(10,6))

plt.loglog(t_new_WNM/cst.kyr, r_new_WNM/cst.pc, c="green", label="WNM", lw=2)
plt.loglog(t_new_CNM/cst.kyr, r_new_CNM/cst.pc, c="blue", label="CNM", lw=2)
plt.loglog(t_new_DiM/cst.kyr, r_new_DiM/cst.pc, c="red", label="DiM", lw=2)

for ii in range(len(t_WNM)) : 
    plt.loglog(t_WNM[ii]/cst.kyr, R_WNM[ii]/cst.pc, c="black", marker='o')
    plt.loglog(t_CNM[ii]/cst.kyr, R_CNM[ii]/cst.pc, c="black", marker='o')
    plt.loglog(t_DiM[ii]/cst.kyr, R_DiM[ii]/cst.pc, c="black", marker='o')


plt.xlim(1e-2, 1e4)
plt.ylim(4e-1, 1.5e2)

plt.xlabel("Time [kyr]")
plt.ylabel("R$_{sh}$ [pc]")
plt.legend(loc="best")

plt.savefig("./R_SNR.pdf")

