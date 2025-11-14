# -*- coding: utf-8 -*-
from dataclasses import dataclass

from sharc.parameters.parameters_base import ParametersBase


@dataclass
class ParametersAntennaRadaltM2319(ParametersBase):
    """
    Dataclass containing the Radio altimeter parameters for the simulator
    """
    section_name: str = "RADALT-M2319"
    # Antenna pattern from ITU-R M.2319
    antenna_pattern: str = "RADALT-ITU-R-M.2319"
    # Antenna maximum gain [dBi]
    antenna_max_gain: float = 11.0
    # Antenna HPBW [degrees]
    phi_3dB: float = 40.0

    def validate(self, ctx):

        if not isinstance(self.antenna_max_gain, int) and not isinstance(self.antenna_max_gain, float):
            raise ValueError(f"{ctx}.antenna_gain needs to be a number")




    def load_parameters_from_file(self, config_file: str):
        """Load the parameters from file an run a sanity check

        Parameters
        ----------
        file_name : str
            the path to the configuration file

        Raises
        ------
        ValueError
            if a parameter is not valid
        """
        super().load_parameters_from_file(config_file)

        # Now do the sanity check for some parameters
        if self.antenna_pattern.upper() not in [ParametersAntennaRadaltM2319]:
            raise ValueError(f"ParametersAntennaRadaltM2319: \
                             invalid value for parameter antenna_pattern - {self.antenna_pattern}.")