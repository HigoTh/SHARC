# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from dataclasses import fields, field
import pandas as pd
from typing import List
import numpy as np
import math

from sharc.parameters.parameters_base import ParametersBase
from sharc.parameters.database.parameters_database_imt_antenna import AntennaParamsFromFile
from sharc.parameters.database.parameters_database_gen_topology import GenTopologyParamsFromFile
from sharc.parameters.database.parameters_database_topology_countries import TopologyCountriesParamsFromFile

ALLOWED_FORMATS = ['.csv', '.xlsx']
ALLOWED_DELIMITERS = ['\t',',','|']

@dataclass
class Database:

    # Database file name
    database_file_name: str = "./database.csv"

    # Database dataframe
    database_df_full: float = field(default_factory=pd.DataFrame, init=False)

    # Database chunk dataframe
    database_df: float = field(default_factory=pd.DataFrame, init=False)

    # Database delimiter
    delimiter: str = ","

    def __post_init__(self):

        self.database_df_full = None

    def load_parameters_from_database(self):
        """
        Load parameters from database file.
        """

        # Get the field names of the AntennaParamsFromFile class
        col_labels_types_imt_ant = {f.name.lower(): f.type for f in fields(AntennaParamsFromFile)}
        # Get the field names of the GenTopologyParamsFromFile class
        col_labels_types_gen_topology = {f.name.lower(): f.type for f in fields(GenTopologyParamsFromFile)}
        # Get the field name of the TopologyCountriesParamsFromFile class
        col_labels_types_topology_countries = {f.name.lower(): f.type for f in fields(TopologyCountriesParamsFromFile)}

        # Columns names and types
        col_labels_types = {**col_labels_types_imt_ant, 
                            **col_labels_types_gen_topology,
                            **col_labels_types_topology_countries}

        # Read file
        self.database_df_full = None
        if self.database_file_name.endswith('.csv'):

            self.database_df_full = pd.read_csv(self.database_file_name,delimiter=self.delimiter)
            
        elif self.database_file_name.endswith('.xlsx'):

            self.database_df_full = pd.read_excel(self.database_file_name)
        else:
            raise ValueError( 'File format must be .csv or .xlsx' )

        self.database_df_full.columns = self.database_df_full.columns.str.lower()
        # Check if all required columns exist in the DataFrame
        missing_columns = [ f for f in col_labels_types.keys()
                        if f not in self.database_df_full ]
        if missing_columns:
            raise ValueError(
                f"Missing columns in the file: {missing_columns}. "
                f"Expected columns: {missing_columns}"
            )
        
        # Filter only columns that exist in the class
        self.database_df_full = self.database_df_full[col_labels_types.keys()]

        return self

@dataclass
class ParametersDatabase(ParametersBase):
    """Dataclass containing the parameters for database loading
    """
    section_name: str = "database"

    # Database file name
    database_file_name: str = None

    # Database load flag
    database_loaded: bool = False

    # Database
    database: Database = field(init=False)

    # Database delimiter
    delimiter: str = ","

    # Number of parts into which the base is divided.
    num_subsets: int = 1

    # Chunks size
    chunks_size: int = 100

    # IMT antenna parameters
    db_imt_antenna_params_full: List[AntennaParamsFromFile] = field(init=False)

    # IMT antenna parameters
    db_imt_antenna_params: List[AntennaParamsFromFile] = field(init=False)

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

        if self.database_file_name:

            self.database_file_name = str(Path(self.database_file_name).expanduser().resolve(strict=False))
            self.delimiter = self.delimiter.encode().decode("unicode_escape")

            # Check inputs
            if not os.path.isfile(self.database_file_name):
                raise ValueError(f"ParametersDatabase: \
                                Could not find the database file {self.database_file_name}")

            if os.path.splitext(self.database_file_name)[1] not in ALLOWED_FORMATS:
                raise ValueError(f"ParametersDatabase: The database format must be .csv or .xlsx.")

            if self.delimiter.upper() not in ALLOWED_DELIMITERS:
                raise ValueError(f"ParametersGeneral: Invalid database delimiter")
            
            # Load database
            self.database = Database(self.database_file_name, self.delimiter).load_parameters_from_database()
            self.database_loaded = True
            # Get IMT antenna parameters
            self.get_imt_antenna_parameters()

            # Chunk size
            self.chunks_size = math.ceil(len(self.database.database_df_full) / self.num_subsets)

            # Point to the first subset
            self.point_to_ith_subset(0)

        return

    def get_imt_antenna_parameters(self):

        # Load antenna parameters
        col_labels_types_imt_ant = {f.name.lower(): f.type for f in fields(AntennaParamsFromFile)}
        # Filter only columns that exist in the class
        ant_params_df = self.database.database_df_full[col_labels_types_imt_ant.keys()]
        # Convert each line to a AntennaParamsFromFile object
        self.db_imt_antenna_params_full = [AntennaParamsFromFile(**row) for row in ant_params_df.to_dict('records')]

        return
    
    def point_to_ith_subset(self, blk_i: int):

        self.database.database_df = self.database.database_df_full.iloc[blk_i*self.chunks_size:(blk_i+1)*self.chunks_size - 1]
        self.db_imt_antenna_params = self.db_imt_antenna_params_full[blk_i*self.chunks_size:(blk_i+1)*self.chunks_size - 1]

        return
