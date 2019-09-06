#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 15:17:05 2018

@author: lbrahimi
"""

import numpy as np
import matplotlib.pyplot as plt 
import sys 
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec
from scipy import interpolate


# We refers to the tools setup folder
import sys
sys.path.append('./tools/')
 
import freader as fr 
import fwritter as fw
import constants as cst
import d1_grid_generator as grid 
import phases_collection as ism
import damping as dp



###############################################################################
#   INFORMATIONS COMING FROM THE NAMELIST                                     #
###############################################################################
# !!! Do not modify this part !!! #
import namelist as nml

# Phase space 
X         = nml.X
E         = nml.E
nx        = nml.NX
ne        = nml.NE

# ISM secondary variables 
ism_values = nml.ism_values
B  = ism_values.get("B")
ni = ism_values.get("ni")
mn = ism_values.get("mn")
T  = ism_values.get("T")
Xi = ism_values.get("X")

# Calculation of the Alfven velocity and the ion-neutral damping 
VA             = np.zeros((len(E), len(X)))
gamma_in       = np.zeros((len(E), len(X)))
gamma_lazarian = np.zeros((len(E), len(X)))
gamma_tot      = np.zeros((len(E), len(X)))
Pcr            = np.zeros((len(E), len(X)))
for e in range(len(E)) : 
    print (e,"/",len(E))
    for xi in range(len(X)) : 
        in_damping = dp.indamping_alfven(xi , E[e], ism_values) 
        VA[e][xi] = in_damping.get('VA')
        if (nml.in_damping) : gamma_in[e][xi] = in_damping.get('wi')
        if (nml.lz_damping) : gamma_lazarian[e][xi] = -dp.damping_lazarian(xi, E[e], ism_values)
        gamma_tot[e][xi] = gamma_in[e][xi] + gamma_lazarian[e][xi]
        Pcr[e][xi] = nml.Pcr_1GeV*(E[e]/cst.GeV)**(-2.7)

# Initial diffusion coefficients -> Initial waves I
d00     = np.zeros(len(X)) # Spatial component of the background diffusion coefficient of CRs 
D       = np.zeros((len(E), len(X))) # Initial diffusion coefficient of CRs 
Db      = np.zeros((len(E), len(X))) # Bohm diffusion coefficient of CRs 
I       = np.zeros((len(E), len(X))) # Initial resonnant waves energy density 


for xi in range(len(X)) : 
    d00[xi] = 1e28


for e in range(len(E)) : 
    print (e,"/",len(E))
    for xi in range(len(X)) : 
        Db[e][xi] = (4*cst.c)/(3*np.pi)*(E[e]/(cst.e*B[xi]))
        D[e][xi]  = d00[xi]*(E[e]/(10.*cst.GeV))**0.5
        I[e][xi] = Db[e][xi]/D[e][xi]



###############################################################################
#      WRITE THE INITAL CONDITIONS                                            #
###############################################################################
fw.write1D( "Alfven.dat", nx=nx, ne=ne, variable=VA.T, path="./data_ini/") 
fw.write1D("DCRpara.dat", nx=nx, ne=ne,  variable=D.T, path="./data_ini/")
fw.write1D(  "DBohm.dat", nx=nx, ne=ne, variable=Db.T, path="./data_ini/")
fw.write1D(     "Ip.dat", nx=nx, ne=ne,  variable=I.T, path="./data_ini/")   
fw.write1D(    "Pcr.dat", nx=nx, ne=ne,variable=Pcr.T, path="./data_ini/")    
fw.write1D("damping.dat", nx=nx, ne=ne, variable=gamma_tot.T, path="./data_ini/")  
fw.write1Daxis("X.dat", variable=X, nx=nx, path="./data_ini/")
fw.write1Daxis("E.dat", variable=E, nx=ne, path="./data_ini/")
fw.write1Daxis("B.dat", variable=B, nx=nx, path="./data_ini/")




variables = {"NX"       : nx,
             "NE"       : ne,
             "ni"       : ni[0],
             "X"        : Xi[0],
             "mn"       : mn[0],
             "T"        : T[0]}

fw.fileWrite("parameters", variables = variables, path='./', ext='.dat') 



















  