from dataclasses import dataclass

from sharc.parameters.parameters_base import ParametersBase


@dataclass
class ParametersGenMacrocell(ParametersBase):

    coord_file_path: str = None
    cell_radius: float = None

    def validate(self, ctx):

        if not isinstance(self.coord_file_path, str):
            raise ValueError(f"{ctx}.coord_file_path should be a string")

        if not self.coord_file_path.lower().endswith(('.csv', '.xlsx')):
            raise ValueError(f"{ctx}.coord_file_path should be a .csv or .xlsx file")

        if not isinstance(self.cell_radius, int):
            raise ValueError(f"{ctx}.cell_radius should be a number")
