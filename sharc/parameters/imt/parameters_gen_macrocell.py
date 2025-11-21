from dataclasses import dataclass

from sharc.parameters.parameters_base import ParametersBase


@dataclass
class ParametersGenMacrocell(ParametersBase):
    """
    Data class for gen_macrocell topology parameters.
    """
    # Coordinates file path [.csv or .xlsx]
    coord_file_path: str = None
    # Cell radius [m]
    cell_radius: int = 100
    # Reference latitude coordinate [°]
    ref_lat: float = None
    # Reference longitude coordinate
    ref_lon: float = None
    # Reference distance [m]
    ref_dist: float = 30000.0
    # Database (.csv or .xlsx) columns delimiter
    delimiter: str = '\t'
    
    def validate(self, ctx):

        if not isinstance(self.coord_file_path, str):
            raise ValueError(f"{ctx}.coord_file_path should be a string")

        if not self.coord_file_path.lower().endswith(('.csv', '.xlsx')):
            raise ValueError(f"{ctx}.coord_file_path should be a .csv or .xlsx file")

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