# -*- coding: utf-8 -*-
"""
Created on Sat Apr 15 16:29:36 2017

@author: Calil
"""

from sharc.support.named_tuples import AntennaPar, AntennaParGen
from numpy import load
import typing
from typing import List
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from sharc.parameters.parameters_base import ParametersBase
from sharc.parameters.imt.load_antenna_params_imt import load_antenna_params_from_file
from sharc.parameters.imt.load_antenna_params_imt import AntennaParamsFromFile

@dataclass
class ParametersAntennaSubarrayImt(ParametersBase):
    """
    Parameters for subarray as defined in R23-WP5D-C-0413, Annex 4.2
    """
    # to use subarray, set this to true
    is_enabled: bool = False

    # Number of rows in subarray
    n_rows: int = 3

    # BS array element vertical spacing (d/lambda).
    element_vert_spacing: float = 0.5
    # element_vert_spacing: float = 0.5

    # notice that electrical tilt == -1 * downtilt
    # Sub array eletrical downtilt [deg]
    eletrical_downtilt: float = 3.0


@dataclass
class ParametersAntennaImt(ParametersBase):
    """
    Defines the antenna model and related parameters to be used in compatibility
    studies between IMT and other services in adjacent bands.
    """
    section_name: str = "imt_antenna"

    # Normalization application flags for base station (BS) and user equipment (UE).
    normalization: bool = False

    # Normalization files for BS and UE beamforming.
    normalization_file: str = "antenna/beamforming_normalization/norm.npz"

    # Radiation pattern of each antenna element.
    element_pattern: str = "M2101"

    # Minimum array gain for the beamforming antenna [dBi].
    minimum_array_gain: float = -200.0

    # beamforming angle limitation [deg].
    # PS: it isn't implemented for UEs
    # and current implementation doesn't make sense for UEs
    horizontal_beamsteering_range: tuple[float | int, float | int] = (-180., 180.)
    vertical_beamsteering_range: tuple[float | int, float | int] = (0., 180.)

    # Mechanical downtilt [degrees].
    # PS: downtilt doesn't make sense on UE's
    downtilt: float = 6.0

    # BS/UE maximum transmit/receive element gain [dBi].
    element_max_g: float = 5.0

    # BS/UE horizontal 3dB beamwidth of single element [degrees].
    element_phi_3db: float = 65.0

    # BS/UE vertical 3dB beamwidth of single element [degrees].
    element_theta_3db: float = 65.0

    # BS/UE number of rows and columns in antenna array.
    n_rows: int = 8
    n_columns: int = 8

    # BS/UE array element spacing (d/lambda).
    element_horiz_spacing: float = 0.5
    element_vert_spacing: float = 0.5

    # BS/UE front to back ratio and single element vertical sidelobe attenuation [dB].
    element_am: int = 30
    element_sla_v: int = 30

    # Multiplication factor k used to adjust the single-element pattern.
    multiplication_factor: int = 12

    adjacent_antenna_model: typing.Literal["BEAMFORMING", "SINGLE_ELEMENT"] = None

    subarray: ParametersAntennaSubarrayImt = field(default_factory=ParametersAntennaSubarrayImt)

    # Flag for reading parameters from file
    from_database: bool = False
    # Path to database file
    database_file: str = "antenna/database.csv"

    def load_subparameters(self, ctx: str, params: dict, quiet=True):
        """
        Loads the parameters when is placed as subparameter
        """
        super().load_subparameters(ctx, params, quiet)

    def set_external_parameters(self, *, adjacent_antenna_model: typing.Literal["BEAMFORMING", "SINGLE_ELEMENT"]):
        self.adjacent_antenna_model = adjacent_antenna_model

    def validate(self, ctx: str):
        # Additional sanity checks specific to antenna parameters can be implemented here

        # Sanity check for adjacent_antenna_model
        if self.adjacent_antenna_model not in ["SINGLE_ELEMENT", "BEAMFORMING"]:
            raise ValueError("adjacent_antenna_model must be 'SINGLE_ELEMENT'")

        # Sanity checks for normalization flags
        if not isinstance(self.normalization, bool):
            raise ValueError("normalization must be a boolean value")

        # Sanity checks for database read flag
        if not isinstance(self.from_database, bool):
            raise ValueError("from_file must be a boolean value")

        # Sanity checks for element patterns
        if self.element_pattern.upper() not in ["M2101", "F1336", "FIXED"]:
            raise ValueError(
                f"Invalid element_pattern value {self.element_pattern}",
            )
        if isinstance(self.horizontal_beamsteering_range, list):
            self.horizontal_beamsteering_range = tuple(self.horizontal_beamsteering_range)

        if not isinstance(self.horizontal_beamsteering_range, tuple):
            raise ValueError(
                f"Invalid {ctx}.horizontal_beamsteering_range={self.horizontal_beamsteering_range}\n"
                "It needs to be a tuple"
            )
        if len(self.horizontal_beamsteering_range) != 2\
            or not all(map(
                lambda x: isinstance(x, float) or isinstance(x, int), self.horizontal_beamsteering_range
            )):
            raise ValueError(
                f"Invalid {ctx}.horizontal_beamsteering_range={self.horizontal_beamsteering_range}\n"
                "It needs to contain two numbers delimiting the range of beamsteering in degrees"
            )
        if self.horizontal_beamsteering_range[0] > self.horizontal_beamsteering_range[1]:
            raise ValueError(
                f"Invalid {ctx}.horizontal_beamsteering_range={self.horizontal_beamsteering_range}\n"
                "The second value must be bigger than the first"
            )
        if not all(map(
                lambda x: x >= -180. and x <= 180., self.horizontal_beamsteering_range
            )):
            raise ValueError(
                f"Invalid {ctx}.horizontal_beamsteering_range={self.horizontal_beamsteering_range}\n"
                "Horizontal beamsteering limit angles must be in the range [-180, 180]"
            )

        if isinstance(self.vertical_beamsteering_range, list):
            self.vertical_beamsteering_range = tuple(self.vertical_beamsteering_range)
        if not isinstance(self.vertical_beamsteering_range, tuple):
            raise ValueError(
                f"Invalid {ctx}.vertical_beamsteering_range={self.vertical_beamsteering_range}\n"
                "It needs to be a tuple"
            )
        if len(self.vertical_beamsteering_range) != 2\
            or not all(map(
                lambda x: isinstance(x, float) or isinstance(x, int), self.vertical_beamsteering_range
            )):
            raise ValueError(
                f"Invalid {ctx}.vertical_beamsteering_range={self.vertical_beamsteering_range}\n"
                "It needs to contain two numbers delimiting the range of beamsteering in degrees"
            )
        if self.vertical_beamsteering_range[0] > self.vertical_beamsteering_range[1]:
            raise ValueError(
                f"Invalid {ctx}.vertical_beamsteering_range={self.vertical_beamsteering_range}\n"
                "The second value must be bigger than the first"
            )
        if not all(map(
                lambda x: x >= 0. and x <= 180., self.vertical_beamsteering_range
            )):
            raise ValueError(
                f"Invalid {ctx}.vertical_beamsteering_range={self.vertical_beamsteering_range}\n"
                "vertical beamsteering limit angles must be in the range [0, 180]"
            )

    def get_antenna_parameters(self) -> AntennaPar:
        if self.normalization:
            # Load data, save it in dict and close it
            data = load(self.normalization_file)
            data_dict = {key: data[key] for key in data}
            self.normalization_data = data_dict
            data.close()
        else:
            self.normalization_data = None
        tpl = AntennaPar(
            self.adjacent_antenna_model,
            self.normalization,
            self.normalization_data,
            self.element_pattern,
            self.element_max_g,
            self.element_phi_3db,
            self.element_theta_3db,
            self.element_am,
            self.element_sla_v,
            self.n_rows,
            self.n_columns,
            self.element_horiz_spacing,
            self.element_vert_spacing,
            self.multiplication_factor,
            self.minimum_array_gain,
            self.downtilt,
        )

        return tpl

    def get_antenna_parameters_from_db(self) -> List[ AntennaParGen ]:
        """
        Loads antenna parameters from table.
        """
        if self.normalization:
            # Load data, save it in dict and close it
            data = load(self.normalization_file)
            data_dict = {key: data[key] for key in data}
            self.normalization_data = data_dict
            data.close()
        else:
            self.normalization_data = None

        tpl_list_from_file = []
        sub_array_p_from_file = []
        # Database file path
        database_file_path = str( Path(__file__).parent.parent.parent / self.database_file )

        # Load parameters from database
        ant_params_list = load_antenna_params_from_file( database_file_path )

        for ant_params in ant_params_list:

            # Theoretical beamforming gain
            th_bf_gain = 10 * np.log10( ant_params.num_columns * ant_params.num_rows )
            # Desired beamforming gain
            pt_bf_gain = ant_params.beamforming_gain
            # Beamforming efficiency reduction (dB)
            bf_gain_eff = th_bf_gain - pt_bf_gain

            # Gain per element compensated by beamforming efficiency
            element_max_g = ant_params.element_max_g - bf_gain_eff

            # Total TX power
            tx_power = ant_params.tx_power

            # Create antenna parameters instance
            tpl_i =  AntennaParGen(
                        self.adjacent_antenna_model,
                        self.normalization,
                        self.normalization_data,
                        self.element_pattern,
                        element_max_g,
                        self.element_phi_3db,
                        self.element_theta_3db,
                        self.element_am,
                        self.element_sla_v,
                        ant_params.num_rows,
                        ant_params.num_columns,
                        self.element_horiz_spacing,
                        self.element_vert_spacing,
                        self.multiplication_factor,
                        self.minimum_array_gain,
                        ant_params.downtilt,
                        tx_power
                        )
            tpl_list_from_file.append( tpl_i )

            # Subarray parameters
            sub_array_p_d = {
                'is_enabled': self.subarray.is_enabled,
                'n_rows': ant_params.sub_num_rows,
                'element_vert_spacing': self.subarray.element_vert_spacing,
                'eletrical_downtilt': self.subarray.eletrical_downtilt
            }
            sub_array_p_i = ParametersAntennaSubarrayImt( **sub_array_p_d )
            sub_array_p_from_file.append( sub_array_p_i )

        return tpl_list_from_file, sub_array_p_from_file
