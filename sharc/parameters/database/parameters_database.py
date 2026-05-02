# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from dataclasses import fields, field
import pandas as pd
from typing import List, Dict, Type, Any, Optional
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
    """Database loader and holder for simulation parameters."""

    database_file_name: str = "./database.csv"
    delimiter: str = ","
    expected_columns: Optional[Dict[str, Type]] = None

    # DataFrames: full database and current subset
    database_df_full: pd.DataFrame = field(default_factory=pd.DataFrame, init=False)
    database_df: pd.DataFrame = field(default_factory=pd.DataFrame, init=False)


    def __post_init__(self) -> None:
        """Initialize empty DataFrames."""
        self.database_df_full = pd.DataFrame()
        self.database_df = pd.DataFrame()

    def load_parameters_from_database(self) -> "Database":
        """Load parameters from the database file (CSV or Excel) and validate columns.

        Returns
        -------
        Database
            Self instance for method chaining.

        Raises
        ------
        ValueError
            If file format is not supported, file is missing, or required columns are absent.
        FileNotFoundError
            If the database file does not exist.
        """
        self._validate_file_exists()
        self._read_file_based_on_extension()
        self._normalize_column_names()
        self._validate_required_columns()
        self._filter_to_expected_columns()
        return self

    # ----------------------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------------------
    def _validate_file_exists(self) -> None:
        """Check if the database file exists."""
        path = Path(self.database_file_name).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Database file not found: {path}")
        self.database_file_name = str(path)

    def _read_file_based_on_extension(self) -> None:
        """Read CSV or Excel file based on file extension."""
        file_path = self.database_file_name
        if file_path.lower().endswith('.csv'):
            self.database_df_full = pd.read_csv(file_path, delimiter=self.delimiter)
        elif file_path.lower().endswith('.xlsx'):
            self.database_df_full = pd.read_excel(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {file_path}. Must be .csv or .xlsx"
            )

    def _normalize_column_names(self) -> None:
        """Convert all column names to lowercase for consistency."""
        self.database_df_full.columns = self.database_df_full.columns.str.lower()

    def _validate_required_columns(self) -> None:
        """Raise an error if any expected column is missing from the DataFrame."""
        expected_cols = set(self.expected_columns.keys())
        actual_cols = set(self.database_df_full.columns)
        missing = expected_cols - actual_cols
        if missing:
            raise ValueError(
                f"Missing required columns in database file: {sorted(missing)}"
            )

    def _filter_to_expected_columns(self) -> None:
        """Keep only the columns that are expected (defined in the parameter classes)."""
        expected_cols = list(self.expected_columns.keys())
        self.database_df_full = self.database_df_full[expected_cols]

@dataclass
class ParametersDatabase(ParametersBase):
    """Dataclass containing the parameters for database loading."""

    section_name: str = "database"

    # Database file name
    database_file_name: Optional[str] = None

    # Database load flag
    database_loaded: bool = False

    # Database instance
    database: Database = field(init=False)

    # Database delimiter (only for CSV)
    delimiter: str = ","

    # Number of parts into which the base is divided
    num_subsets: int = 1

    # Chunk size (automatically computed)
    chunks_size: int = 100

    # Full IMT antenna parameters list
    db_imt_antenna_params_full: List[AntennaParamsFromFile] = field(init=False)

    # Current subset IMT antenna parameters
    db_imt_antenna_params: List[AntennaParamsFromFile] = field(init=False)

    # Flags for topology/antenna data sources
    from_db_topology_countries: bool = False
    from_db_topology_gen_macrocell: bool = False
    from_db_antenna_params: bool = False

    def load_parameters_from_file(self, config_file: str) -> None:
        """Load parameters from a configuration file and run sanity checks.

        Parameters
        ----------
        config_file : str
            Path to the configuration file.

        Raises
        ------
        ValueError
            If any parameter is invalid.
        """
        super().load_parameters_from_file(config_file)
        if self.database_file_name:
            self._load_database_from_file()
        else:
            raise ValueError(
                f"ParametersDatabase: Database file name not defined."
            )

    @classmethod
    def from_direct_params(cls, database_file_name: str, delimiter: str = ",", **kwargs):
        """Cria instância diretamente a partir de parâmetros, sem YAML."""
        instance = cls(**kwargs)
        instance.database_file_name = database_file_name
        instance.delimiter = delimiter
        instance._load_database_from_file()
        return instance

    # ----------------------------------------------------------------------
    # Private helper methods
    # ----------------------------------------------------------------------
    def _load_database_from_file(self):

        self._validate_and_prepare_database_file()
        expected = self._get_expected_columns()
        self._load_database(expected)
        self._prepare_antenna_parameters()
        self._setup_chunking_and_first_subset()
        
    def _validate_and_prepare_database_file(self) -> None:
        """Resolve the database file path and validate its existence and format."""
        self.database_file_name = str(Path(self.database_file_name).expanduser().resolve(strict=False))
        self.delimiter = self.delimiter.encode().decode("unicode_escape")

        db_path = Path(self.database_file_name)

        if not db_path.is_file():
            raise ValueError(
                f"ParametersDatabase: Could not find the database file {self.database_file_name}"
            )

        if db_path.suffix.lower() not in ALLOWED_FORMATS:
            raise ValueError(
                f"ParametersDatabase: The database format must be one of {ALLOWED_FORMATS}."
            )

        if self.delimiter.upper() not in ALLOWED_DELIMITERS:
            raise ValueError(f"ParametersGeneral: Invalid database delimiter '{self.delimiter}'")

    def _load_database(self, expected: Dict[str, Type]) -> None:
        """Instantiate and load the database from the file."""
        self.database = Database(self.database_file_name, self.delimiter, expected_columns=expected).load_parameters_from_database()
        self.database_loaded = True

    def _prepare_antenna_parameters(self) -> None:
        """Build the full list of IMT antenna parameters from the database."""
        if self.from_db_antenna_params:
            col_labels_types_imt_ant = {f.name.lower(): f.type for f in fields(AntennaParamsFromFile)}
            # Keep only columns that exist in the AntennaParamsFromFile class
            ant_params_df = self.database.database_df_full[col_labels_types_imt_ant.keys()]
            self.db_imt_antenna_params_full = [
                AntennaParamsFromFile(**row) for row in ant_params_df.to_dict("records")
            ]

    def _setup_chunking_and_first_subset(self) -> None:
        """Compute chunk size and point to the first subset."""
        total_rows = len(self.database.database_df_full)
        self.chunks_size = math.ceil(total_rows / self.num_subsets)
        self.point_to_ith_subset(0)

    def _get_expected_columns(self) -> Dict[str, Type]:
        """Return a mapping of expected column names to their required types,
        based on the active flags."""
        col_sets = []
        if self.from_db_antenna_params:
            col_sets.append({f.name.lower(): f.type for f in fields(AntennaParamsFromFile)})
        if self.from_db_topology_gen_macrocell:
            col_sets.append({f.name.lower(): f.type for f in fields(GenTopologyParamsFromFile)})
        if self.from_db_topology_countries:
            col_sets.append({f.name.lower(): f.type for f in fields(TopologyCountriesParamsFromFile)})

        expected = {}
        for cs in col_sets:
            expected.update(cs)
        return expected

    # ----------------------------------------------------------------------
    # Public subset selection
    # ----------------------------------------------------------------------
    def point_to_ith_subset(self, blk_i: int) -> None:
        """Select the i-th subset of the database and antenna parameters.

        Parameters
        ----------
        blk_i : int
            Subset index (0-based).
        """
        start = blk_i * self.chunks_size
        end = (blk_i + 1) * self.chunks_size
        self.database.database_df = self.database.database_df_full.iloc[start:end]
        if self.from_db_antenna_params:
            self.db_imt_antenna_params = self.db_imt_antenna_params_full[start:end]