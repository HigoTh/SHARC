# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 14:13:58 2017

@author: Calil
"""

import numpy as np
from sharc.antenna.antenna import Antenna
from sharc.support.named_tuples import AntennaPar


class AntennaRadaltM2319(Antenna):
    """
    Implement the Radalt antenna pattern.

    Attributes
    ----------
        g_max (float): maximum antenna gain
        phi_3db (float): 3dB beamwidth of single element [degrees]
    """
    
    def __init__(self, par: AntennaPar):
        """
        Constructs an AntennaRadalt object.

        Parameters
        ---------
            par (AntennaPar): antenna parameters
        """

        self.param = par

        self.g_max = par.element_max_g
        self.phi_3dB = par.element_phi_3db

    def calculate_gain(self, *args, **kwargs) -> np.array:
        """
        Calculates the Radalt radiation pattern.

        Parameters
        ----------
            phi (np.array): elevation angle [degrees]
            theta (np.array): azimuth angle [degrees]

        Returns
        -------
            gain (np.array): Radalt radiation pattern gain value
        """
        phi = np.absolute(kwargs["off_axis_angle_vec"])

        gain = -( 12.0 / self.phi_3dB**2 ) * phi**2 + self.g_max
        
        return gain
