#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 08:10:35 2019

@author: lbrahimi
"""
# We refers to the tools setup folder
import sys
import os 
sys.path.append('../tools/')
 
#import freader as fr 
#import fwritter as fw
import constants as cst
import d1_grid_generator as grid 
import phases_collection as ism
import damping as dmp
#import damping as dp
import mathmethods as mh


# Function to get a mean VA in a given phase 
def getVA(E, phase) : 
    VA = []
    for ii in range(2**NE) : 
        if (abs(dmp.indamping_alfven_nopos(E[ii], phase).get("VA")) > 100) : 
            VA.append(dmp.indamping_alfven_nopos(E[ii], phase).get("VA"))   
        else : 
            VA.append(0.)
    return VA

def getDamping(E, phase) : 
    damping_in   = []
    damping_lz   = []
    for ii in range(2**NE) : 
        damping_in.append(abs(dmp.IonNeutral_Damping(E[ii], phase, nu_n = 0, theta = 0).get("wi")))
        damping_lz.append(abs(dmp.damping_lazarian_nopos(E[ii], phase)[0]))
    return [damping_in, damping_lz]

###############################################################################
#      OUTPUT FOLDER CREATOR                                                  #
###############################################################################
# Relative position of the ouput folder
folder_name = "s_0.5_12"
folder_path = "../../WorkFolder/Fiducial_synchrotron_for_thesis/" # The path containing the folder

total_path = folder_path+folder_name

try : 
    os.mkdir(total_path)
    os.mkdir(total_path+"/data_out")
    os.mkdir(total_path+"/data_ini")
    os.mkdir(total_path+"/data_analysis")
    os.mkdir(total_path+"/tools")
except : 
    print ("!!! The output folder already exists, remove it if you want to create a new one !!!")




###############################################################################
#      GRID PARAMETERS                                                        #
###############################################################################
NX        = 4  # 2**NX is the X-size of the grid 
NE        = 12  # 2**NE is the E-size of the grid 

Xmin      = 0.*cst.pc
Xmax      = 2000.*cst.pc
xgridtype = "cartesian"#"cartesian" # No choice

Emin      = 10.*cst.GeV
Emax      = 10.*cst.TeV
egridtype = "logspace" # Type of grid - # logspace type recomended (only option for the moment)

box_center = 1000.*cst.pc  # Position of the center of the CR source 

# Phase space 
X = grid.grid(Xmin, Xmax, 2**NX, xgridtype, 
              s_center = box_center, width = 200.*cst.pc, smooth = 20.*cst.pc, dXmin = 1.*cst.pc)
E = grid.grid(Emin, Emax, 2**NE, egridtype)  

###############################################################################
#       OTHER TERMS                                                           #
###############################################################################
in_damping       = True     # Ion neutral damping of waves
lz_damping       = True     # Lazarian damping of waves
nlld_damping     = True     # Non-linear Landau damping of waves (Wiener et al. 2013)
Pcr_1GeV         = 1*cst.eV # [erg cm^-3] CR background pressure at 1 GeV 
Pe_1GeV          = 1*cst.eV # [erg cm^-3] e- background pressure at 1 GeV
bdiff_model      = "ISM_independant" #ISM_(independant, dependant) 



###############################################################################
#        ISM STRUCTURE                                                        #
###############################################################################
phases  = [] # Phases list
# Append phases in the order of the setup you want to create
# phases.append([ism.WNM, dict(Xmin=0.*cst.pc,    Xmax=300.*cst.pc),  getVA(E, ism.WNM)]) 
# phases.append([ism.CNM, dict(Xmin=300.*cst.pc,  Xmax=500.*cst.pc),  getVA(E, ism.CNM)])
# phases.append([ism.DiM, dict(Xmin=500.*cst.pc,  Xmax=600.*cst.pc),  getVA(E, ism.DiM)]) 
# phases.append([ism.CNM, dict(Xmin=600.*cst.pc,  Xmax=800.*cst.pc),  getVA(E, ism.CNM)])
# phases.append([ism.WNM, dict(Xmin=800.*cst.pc,  Xmax=950.*cst.pc),  getVA(E, ism.WNM)])
# phases.append([ism.HII, dict(Xmin=950.*cst.pc,  Xmax=1050.*cst.pc), getVA(E, ism.HII)]) 
# phases.append([ism.WNM, dict(Xmin=1050.*cst.pc, Xmax=1200.*cst.pc), getVA(E, ism.WNM)])
# phases.append([ism.CNM, dict(Xmin=1200.*cst.pc, Xmax=1400.*cst.pc), getVA(E, ism.CNM)]) 
# phases.append([ism.DiM, dict(Xmin=1400.*cst.pc, Xmax=1500.*cst.pc), getVA(E, ism.DiM)]) 
# phases.append([ism.CNM, dict(Xmin=1500.*cst.pc, Xmax=1700.*cst.pc), getVA(E, ism.CNM)]) 
# phases.append([ism.WNM, dict(Xmin=1700.*cst.pc, Xmax=2000.*cst.pc), getVA(E, ism.WNM)]) 

phases.append([ism.DeC, dict(Xmin=Xmin,    Xmax=Xmax),  getVA(E, ism.DeC), 
                getDamping(E, ism.DeC)[0], getDamping(E, ism.DeC)[1]]) 

# phases.append([ism.DeM, dict(Xmin=Xmin,    Xmax=Xmax),  getVA(E, ism.DeM), 
#                getDamping(E, ism.DeM)[0], getDamping(E, ism.DeM)[1]]) 



smooth_width_transition = 10.*cst.pc # Smooth width transition between two phases (10 pc min to avoid jumps)

# We calculate the smoothed variables
T, B, ni, nn, nt, Xi, mi, mn, va, gamma_in, gamma_lz = mh.SmoothPhaseTransition(X, E, phases, smooth_width_transition)
# ISM secondary variables 
ism_values = dict(T=T, B=B, ni=ni, nn=nn, nt=nt, X=Xi, mi=mi, mn=mn, VA=va, gamma_in = gamma_in, gamma_lz = gamma_lz)


