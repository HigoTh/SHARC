from dataclasses import dataclass

from sharc.parameters.parameters_base import ParametersBase


@dataclass
class ParametersGenMacrocell(ParametersBase):
    """
    Data class for gen_macrocell topology parameters.
    """
    # Cell radius [m]
    cell_radius: int = 100
    # Reference latitude coordinate [°]
    ref_lat: float = None
    # Reference longitude coordinate
    ref_lon: float = None
    # Reference distance [m]
    ref_dist: float = 30000.0
    
    def validate(self, ctx):

        if not isinstance(self.cell_radius, int):
            raise ValueError(f"{ctx}.cell_radius should be a number")
        
        if (not isinstance(self.cell_radius, float) and not isinstance(
                self.cell_radius, int)) or self.cell_radius < 0:
            raise ValueError(f"{ctx}.cell_radius must be non-negative")

        if (not isinstance(self.ref_dist, float) and not isinstance(
                self.ref_dist, int)) or self.ref_dist < 0:
            raise ValueError(f"{ctx}.ref_dist must be non-negative")

        if not isinstance( self.ref_lon, float ) or not ( -180.0 <= self.ref_lon <= 180.0 ):
            raise ValueError(f"{ctx}.ref_lon must be between -180° and 180°")
        
        if not isinstance( self.ref_lat, float ) or not ( -90.0 <= self.ref_lat <= 0.0 ):
            raise ValueError(f"{ctx}.ref_lat must be between -90 and 90")            