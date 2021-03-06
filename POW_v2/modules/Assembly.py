# Copyright (c) 2012 EPFL (Ecole Polytechnique federale de Lausanne)
# Laboratory for Biomolecular Modeling, School of Life Sciences
#
# POW is free software ;
# you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation ;
# either version 2 of the License, or (at your option) any later version.
# POW is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY ;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with POW ;
# if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
#
# Author : Matteo Degiacomi, matteothomas.degiacomi@epfl.ch
# Web site : http://lbm.epfl.ch


import numpy as np
from Protein import Protein
from copy import deepcopy
import time

#in CG segmemts, 0=receptor, 1=ligand

class Assembly:
    def __init__(self,ligand_file,receptor_file,cg_atoms=np.array([])):
        self.ligand_file = ligand_file
        self.receptor_file = receptor_file
        self.cg_atoms=cg_atoms


        
    ###################
    #PRIVATE METHODS###
    ###################

    def _move_ligand_to_origin(self):
        #get the center of geometry
        xyzCenter = np.mean(self.ligand,axis=0)
        self.ligand -= xyzCenter
        if len(self.cg_atoms)>0:
            xyzCenter_cg=np.mean(self.cg_atoms[self.cg_atoms[:,5]==1,2:5],axis=0)
            self.cg_atoms[self.cg_atoms[:,5]==1,2:5]-= xyzCenter_cg
        
    def _translate(self):
        self.ligand += np.array([self.coords[0],self.coords[1],self.coords[2]])
        if len(self.cg_atoms)>0:
            self.cg_atoms[self.cg_atoms[:,5]==1,2:5]+= np.array([self.coords[0],self.coords[1],self.coords[2]])

    def _rotation(self):
    #angle in numpy need to be given in rad -> rad = deg * pi/180
        alpha = np.radians(self.coords[3])
        beta = np.radians(self.coords[4])
        gamma = np.radians(self.coords[5])
    #rotation around x
    #|1     0                0         |
    #|0     np.cos(alpha)      -np.sin(alpha)|
    #|0     np.sin(alpha)   np.cos(alpha) |
        Rx = np.array([[1,0,0], [0, np.cos(alpha), -np.sin(alpha)], [0, np.sin(alpha), np.cos(alpha)]])
        Ry = np.array([[np.cos(beta), 0, np.sin(beta)], [0, 1, 0], [-np.sin(beta), 0, np.cos(beta)]])
        Rz = np.array([[np.cos(gamma), -np.sin(gamma), 0], [np.sin(gamma), np.cos(gamma), 0], [0,0,1]])
        rotation = np.dot(Rx,np.dot(Ry,Rz))
        #multiply rotation matrice with each atom of the monomer
        self.ligand = np.dot(self.ligand,rotation)
        if len(self.cg_atoms)>0:
            self.cg_atoms[self.cg_atoms[:,5]==1,2:5]=np.dot(self.cg_atoms[self.cg_atoms[:,5]==1,2:5],rotation)
            #rotate cg ligand in cg matrix 


    ################
    #PUBLIC METHODS#
    ################
            
    def place_ligand(self, coords):

        self.coords = coords
        self.ligand = []
        self.ligand = deepcopy(self.ligand_file.data[:,5:8])
        self.receptor = []
        self.receptor = deepcopy(self.receptor_file.data[:,5:8])

        ###print "start: %s"%self.cg_atoms[90,2:5]
        self._move_ligand_to_origin()
        self._rotation()
        self._translate()

    def atomselect_ligand(self,chain,resid,atom,get_index=False):
        [m,index]=self.ligand_file.atomselect(chain,resid,atom,True)
        atoms = self.ligand[index]

        if get_index==True:
            return [atoms, index]
        else:
            return atoms

    def atomselect_receptor(self,chain,resid,atom,get_index=False):
        [m,index]=self.receptor_file.atomselect(chain,resid,atom,True)
        atoms = self.receptor[index]
        if get_index==True:
            return [atoms, index]
        else:
            return atoms

    #def get_width(self):
        #print ">> before to get the width here is the multimer = %s"%(self.multimer)
    #    maxXYZ = self._get_max_from_multimer()
    #    minXYZ = self._get_min_from_multimer()
        #print "get width took %s"%(end-start)
        #Simple way to calculate but take too much time
        #self.BigAtomArray = np.reshape(self.multimer,(-1,3))
        #self.MaxXYZ = np.amax(self.BigAtomArray,axis=0)
        #self.MinXYZ = np.amin(self.BigAtomArray,axis=0)

    #    return(maxXYZ[0]-minXYZ[0])

    #def get_height(self):
    #    maxXYZ = self._get_max_from_multimer()
    #    minXYZ = self._get_min_from_multimer()
    #    return(maxXYZ[2]-minXYZ[2])

    def get_ligand_xyz(self):
        return self.ligand

    def get_receptor_xyz(self):
        return self.receptor

    def distance(self,atom1,atom2):
        atom1np = np.array(atom1[0])
        atom2np = np.array(atom2[0])
        diff = atom1np - atom2np
        return np.sqrt(np.dot(diff,diff))

    def write_PDB(self,outname):

        f_out=open(outname,"w")

        self.ligand_file.set_xyz(self.ligand)
        #map intergers to characters from ligand data
        data_list=self.ligand_file.mapping(self.ligand_file.data)

        for i in xrange(0,len(data_list),1):
            #create and write PDB line
            l=(data_list[i][0],data_list[i][1],data_list[i][2],"L",data_list[i][4],data_list[i][5],data_list[i][6],data_list[i][7],data_list[i][8],data_list[i][9],data_list[i][10])
            L='ATOM  %5i  %-4s%-4s%1s%4i    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s\n'%l
            f_out.write(L)

        f_out.write("TER\n")


        #map intergers to characters from receptor data
        data_list=self.receptor_file.mapping(self.receptor_file.data)

        for i in xrange(0,len(data_list),1):
            #create and write PDB line
            l=(data_list[i][0],data_list[i][1],data_list[i][2],"R",data_list[i][4],data_list[i][5],data_list[i][6],data_list[i][7],data_list[i][8],data_list[i][9],data_list[i][10])
            L='ATOM  %5i  %-4s%-4s%1s%4i    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s\n'%l
            f_out.write(L)


        f_out.close()


    def get_CG_coords(self):
        return self.cg_atoms


    def get_CG_ligand(self):
        ###print "return: %s"%self.cg_atoms[90,2:5]
        return  self.cg_atoms[self.cg_atoms[:,5]==1]


    def get_CG_receptor(self):
        return  self.cg_atoms[self.cg_atoms[:,5]!=1]
