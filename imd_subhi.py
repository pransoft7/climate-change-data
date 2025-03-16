import imdlib as imd
import numpy as np
import geopandas as gpd
import rasterio
import rioxarray
from rasterio.mask import mask

# Define parameters
start_year = 2009
end_year = 2023
var_type = "rain"

# Load IMD RX5day Data (2009-2023)
data = imd.open_data(var_type, start_year, end_year)
rx5d = data.compute("rx5d", "A")  # "A" = Annual max 5-day rainfall

# Convert to xarray for easier processing
ds = rx5d.get_xarray()

# Remove Null Values (-4995.0)
ds_filtered = ds.where(ds != -4995.0)

# Compute Max RX5day Over 15 Years for Each Lat/Lon
rx5d_max = ds_filtered.max(dim="time", skipna=True)

# Load the Western Ghats Shapefile
shapefile_path = "./western_ghats.shp"
gdf = gpd.read_file("./Bound_G/SA_Bound_Project_WGS84.shp")

# Ensure CRS (Coordinate Reference System) Matches IMD Data
gdf = gdf.to_crs("EPSG:4326")  # Convert to Latitude/Longitude if necessary

# Convert RX5day to a GeoTIFF for Filtering
rx5d_max.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
rx5d_max.rio.write_crs("EPSG:4326", inplace=True)

# Save a Temporary Raster Before Masking
temp_raster = "./temp_rx5d_max.tif"
rx5d_max.rio.to_raster(temp_raster)

# Mask Raster Using Western Ghats Shapefile
with rasterio.open(temp_raster) as src:
    shapes = [feature["geometry"] for feature in gdf.__geo_interface__["features"]]
    
    # Apply mask to crop only the Western Ghats region
    out_image, out_transform = mask(src, shapes, crop=True)
    
    # Update metadata
    out_meta = src.meta.copy()
    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })

# Save the Final Filtered Raster TIFF
final_raster = "./western_ghats_rx5d_max.tif"
with rasterio.open(final_raster, "w", **out_meta) as dest:
    dest.write(out_image)

print(f"Filtered RX5day raster saved at: {final_raster}")
