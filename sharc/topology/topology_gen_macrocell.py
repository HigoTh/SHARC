# -*- coding: utf-8 -*-

from sharc.topology.topology import Topology
import matplotlib.pyplot as plt
import matplotlib.axes
from matplotlib.patches import Circle, Wedge

from pyproj import CRS, Transformer 
import numpy as np
import pandas as pd
from pathlib import Path


class GenTopology(Topology):
    """
    Generates a network topology based on a list of  arbitrary geographic 
    coordinates.
    """

    # Transformers between Geo coordinates (WGS84) and ECEF
    geo2ecef = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(4978))
    ecef2geo = Transformer.from_crs(CRS.from_epsg(4978), CRS.from_epsg(4326))

    # Allowed table formats
    ALLOWED_FORMATS = ['.csv', '.xlsx']

    # Table fields labels
    LAT_LABEL = 'Latitude'
    LON_LABEL = 'Longitude'
    HEIGTH_LABEL = 'Altura'
    AZ_LABEL = 'Azimute'
    COL_LABELS = [
        LAT_LABEL,
        LON_LABEL,
        HEIGTH_LABEL,
        AZ_LABEL
    ]

    def __init__( self, 
                  coords_file_path: str,
                  cell_radius: float,
                  ref_lat: float,
                  ref_lon: float,
                  ref_dist: float,
                  delimiter: str = ',' ):
        
        """
        Defines the generic macrocellular model based on reading a database.

        Parameters
        ----------
            coords_file_path : Path to coordinates file (.csv or .xlsx)
            cell_radius : Cell radius.
            delimiter : CSV file delimiter
        """
        if Path(coords_file_path).suffix not in GenTopology.ALLOWED_FORMATS:
            error_message = "The input file must be .csv or .xlsx."
            raise ValueError(error_message)
        
        self.coords_file_path = str(Path(__file__).parent.parent/coords_file_path)
        self.cell_radius = cell_radius
        self.azimuth = np.empty(0)
        self.x = np.empty(0)
        self.y = np.empty(0)
        self.z = np.empty(0)
        self.num_base_stations = -1
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.ref_dist = ref_dist

        self._delimiter = delimiter
        self.static_base_stations = False
        # Load data
        self._x_geo = np.empty(0)
        self._y_geo = np.empty(0)
        self._z_geo = np.empty(0)
        self._load_data()

    def _load_data( self ) -> None:
        """ 
        Loads geographic data from the input table.
        """

        # Load data from .csv
        if self.coords_file_path.lower().endswith('.csv'):
        
            coords_df = pd.read_csv( self.coords_file_path,
                                    delimiter=self._delimiter,
                                    usecols=GenTopology.COL_LABELS, 
                                    dtype={GenTopology.LAT_LABEL: float, 
                                           GenTopology.LON_LABEL: float, 
                                           GenTopology.AZ_LABEL: float,
                                           GenTopology.HEIGTH_LABEL: float} )
        # Load data from .xlsx
        elif self.coords_file_path.lower().endswith('.xlsx'):

            coords_df = pd.read_excel( self.coords_file_path,
                                       usecols=GenTopology.COL_LABELS, 
                                       dtype={GenTopology.LAT_LABEL: float, 
                                           GenTopology.LON_LABEL: float, 
                                           GenTopology.AZ_LABEL: float,
                                           GenTopology.HEIGTH_LABEL: float} )

        # Read and check coordinates
        x_geo, y_geo, z_geo, az_v = [], [], [], []
        for index, row in coords_df.iterrows():
            
            lat, lon, ht, az = ( row[ GenTopology.LAT_LABEL ], 
                                  row[ GenTopology.LON_LABEL ], 
                                  row[ GenTopology.HEIGTH_LABEL ], 
                                  row[ GenTopology.AZ_LABEL ] )
            # Check inputs            
            if not isinstance( lat, float ) or not ( -90.0 <= lat <= 90.0 ):
                raise ValueError(f"Latitude must be between -90° and 90°")
                        
            if not isinstance( lon, float ) or not ( -180.0 <= lon <= 180.0 ):
                raise ValueError(f"Longitude must be between -180° and 180°")
            
            if not isinstance( ht, float ) or not ( ht > 0.0 ):
                raise ValueError(f"Height must a value greater than zero.")

            if not isinstance( az, float ) or not ( 0.0 <= az <= 360.0 ):
                raise ValueError(f"Azimuth must be between 0° and 360°")

            # Append data
            x_geo.append( lat )
            y_geo.append( lon )
            z_geo.append( ht )
            az_v.append( az )

        self._x_geo = np.array( x_geo )
        self._y_geo = np.array( y_geo )
        self._z_geo = np.array( z_geo )
        self.azimuth = np.array( az_v )
        
        return

    def _compute_centroid( self ) -> None:
        """
        Calculates the centroid of input coordinates projected onto the 
        ground plane.
        """

        # Convert coords to ecef
        coords_ecef_on_ground = np.array([ 
            GenTopology.geo2ecef.transform( lat, lon, 0.0 ) 
            for (lat,lon) in zip(self._x_geo, self._y_geo) ] )
        
        # Compute centroid (centroid with zero heigth)
        centroid_ecef = np.mean( coords_ecef_on_ground, axis=0 )
        centroid_geo = self.ecef2geo.transform( *centroid_ecef )
        
        return centroid_ecef, centroid_geo

    def _compute_center( self ) -> None:
        """
        Calculates the center of input coordinates projected onto the 
        ground plane, based on the reference coordinate.
        """

        # Convert ref coords to ecef
        centroid_ecef = np.array(GenTopology.geo2ecef.transform( self.ref_lat, self.ref_lon, 0.0 ))
        # Compute centroid (centroid with zero heigth)
        centroid_geo = self.ecef2geo.transform( *centroid_ecef )
        
        return centroid_ecef, centroid_geo


    def _compute_rotation_matrix( self, centroid_geo ):
        """
        Calculates the conversion matrix between the ECEF and ENU systems.
        """
        
        # Lat, long of centroid
        phi_r, lam_r = np.radians(centroid_geo[0]), np.radians(centroid_geo[1])
        # Rotation matrix 
        # (ref:https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates)
        r_1 = [ -np.sin( lam_r ), np.cos( lam_r ), 0 ]
        r_2 = [ -np.cos( lam_r ) * np.sin( phi_r ), 
                -np.sin( lam_r ) * np.sin( phi_r ), np.cos( phi_r ) ]
        r_3 = [ np.cos( lam_r ) * np.cos( phi_r ), 
                np.sin( lam_r ) * np.cos( phi_r ), np.sin( phi_r ) ]
        rot_matrix = np.array( [ r_1, r_2, r_3] )

        return rot_matrix

    def calculate_coordinates( self, random_number_gen=np.random.RandomState()):
        """
        Calculates the planned coordinates, converting between the 
        Geo -> ECEF -> ENU systems. his method is invoked in all snapshots 
        but it can be called only once. So we set static_base_stations to True 
        to avoid unnecessary calculations.
        """

        if not self.static_base_stations:

            self.static_base_stations = True

            # Calculate the centroid of station positions
            centroid_ecef, centroid_geo = self._compute_center( )
            # Compute ECEF to ENU rotation matrix
            rot_matrix = self._compute_rotation_matrix( centroid_geo )

            # Convert reference coordinate to the local system
            ref_coords_ecef = GenTopology.geo2ecef.transform( self.ref_lat, self.ref_lon, 0.0 )
            ref_ecef_v = np.array( ref_coords_ecef ) - centroid_ecef
            ref_enu_v = np.matmul( rot_matrix, ref_ecef_v )

            x, y, z = [], [], []
            # Convert coordinates
            for i, (lat,lon,alt) in enumerate( zip(self._x_geo, self._y_geo, self._z_geo) ):

                # Geo to ECEF conversion
                coords_ecef = GenTopology.geo2ecef.transform( lat, lon, alt )

                # Centroid referenced vector
                ecef_v = np.array( coords_ecef ) - centroid_ecef

                # Convert to local ENU
                enu_v = np.matmul( rot_matrix, ecef_v )
                
                # Distance between coordinate and reference coordinate
                dist = np.sqrt((enu_v[0] - ref_enu_v[0])**2 + (enu_v[1] - ref_enu_v[1])**2)

                if dist <= self.ref_dist:

                    x.append( enu_v[0] )
                    y.append( enu_v[1] )
                    z.append( enu_v[2] )

            self.x = np.array( x )
            self.y = np.array( y )
            self.z = np.array( z )

            # Number of base stations
            self.num_base_stations = len( self.x )

        return
    
    def plot(self, ax: matplotlib.axes.Axes):

        # macro cell base stations
        ax.scatter(
            self.x, self.y, color='k', edgecolor="k",
            linewidth=8, label="Macro cell",
        )

        for (x, y, az) in zip(self.x,self.y, self.azimuth):

            # Cell coverage circle
            circle = Circle((x, y), 
                            self.cell_radius, 
                            facecolor='grey', 
                            alpha=0.4,
                            edgecolor='black')
            ax.add_patch(circle)
            ex = x + self.cell_radius * np.cos(np.deg2rad(az))
            ey = y + self.cell_radius * np.sin(np.deg2rad(az))
            ax.plot([x, ex], [y, ey], linewidth=2, linestyle='--',color='black')

        ax.set_aspect('equal')

        return

if __name__ == '__main__':

    topology = GenTopology( 'campaigns/radalt_study_database/qgis/filtered_db.csv', 
                            cell_radius=300,
                            ref_lon=-46.5919,
                            ref_lat=-23.6041,
                            ref_dist=30000,
                            delimiter='\t' )
    topology.calculate_coordinates()

    fig = plt.figure(
            figsize=(8, 8), facecolor='w',
            edgecolor='k',
        )  # create a figure object
    ax = fig.add_subplot(1, 1, 1)  # create an axes object in the figure
    topology.plot(ax)

    plt.xlabel("x-coordinate [m]")
    plt.ylabel("y-coordinate [m]")
    plt.title('Generic Network Topology')
    plt.tight_layout()
    plt.grid(True)
    plt.show()

