from pathlib import Path
from functools import partial
import argparse
import iris
import iris.quickplot as qplt
import matplotlib.colors as mcol
import matplotlib.pyplot as plt
from geovista import GeoPlotter
from iris.experimental.geovista import cube_to_polydata
from iris.experimental import stratify
import numpy as np

from aeolus.io import create_dummy_cube
from aeolus.lfric import (
    add_equally_spaced_height_coord,
    fix_time_coord,
    load_lfric_raw,
    simple_regrid_lfric,
)
from aeolus.model import lfric
from aeolus.coord import (
    isel,
)
from aeolus.calc import zonal_mean


def load_cubes(filename: str):
    # Load cubes.
    cubes = iris.load(filename)

    return cubes


def dump_cube_info(cube):
    # Output information on a single cube

    print(cube)

    for coord in cube.coords():
        print(coord.name())
        print(len(coord.points))
        print(coord.points)

    print(cube.mesh)
    print("Time: " + str(cube.coord("time")))


def plot_cube_2d(cube):
    # Make a simple contour plot of a cube

    contour = qplt.contour(cube)
    plt.clabel(contour, inline=False)

    plt.show()


def plot_cube_mesh(cube):
    # Use GeoPlotter to make a globe plot of a cube

    mesh = cube_to_polydata(cube)

    p = GeoPlotter()
    p.add_mesh(mesh)
    p.show()


def reduce_to_1d(cube):
    # Sample the cube at a particular point to make it 1D for plotting

    if not cube.mesh:
        print("Not a mesh cube")
        return cube

    for coord in cube.coords():
        print(coord.name())


def extract_first_time_slice(cube):
    i = 0

    for slice_t in cube.slices(["time"]):
        print(i, type(slice_t))
        i += 1

    return cube.slices(["time"]).begin()


def plot_cubes_nstep(
    all_cubes, cubes_1d: [str], cubes_2d: [str], timestep: int, layer: int
):
    # Run the cube loop and plot cubes in 1 or 2D at desired timestep/layer

    for cube in all_cubes:
        if cube.name() in cubes_1d:
            plot_cube_mesh(cube[timestep])
        if cube.name() in cubes_2d:
            plot_cube_mesh(cube[timestep, layer])


def generate_latlon_cube(
    n_divisions_lat: int,
    n_divisions_lon: int,
    lat_min: float = -90.0,
    lat_max: float = 90.0,
    lon_min: float = -180.0,
    lon_max: float = 180.0,
) -> iris.cube.Cube:
    # Make a mock cube with a regular latlon grid
    latitude = iris.coords.DimCoord(
        np.linspace(lat_min, lat_max, n_divisions_lat),
        standard_name="latitude",
        units="degrees",
    )
    longitude = iris.coords.DimCoord(
        np.linspace(lon_min, lon_max, n_divisions_lon),
        standard_name="longitude",
        units="degrees",
    )
    cube = iris.cube.Cube(
        np.zeros((n_divisions_lat, n_divisions_lon), np.float32),
        dim_coords_and_dims=[(latitude, 0), (longitude, 1)],
    )

    return cube


def cube_in_list(cubelist, cube_name):
    # Because Iris throws an exception when if can't find a cube by a name, this is
    # a helper to check it's in the list

    for cube in cubelist:
        if cube.name() == cube_name:
            return True

    return False


def plot_air_pot_temp(air_pot_cube):
    # Plot air temperature

    print(air_pot_cube)
    if not air_pot_cube.coord("level_height").has_bounds():
        air_pot_cube.coord("level_height").guess_bounds()
    if not air_pot_cube.coord("time").has_bounds():
        air_pot_cube.coord("time").guess_bounds()
    cube_slice = air_pot_cube[-1].extract(iris.Constraint(level_height=123_456))

    print(cube_slice)

    lats = cube_slice.coord("latitude").points
    lons = cube_slice.coord("longitude").points

    fig, ax = plt.subplots(constrained_layout=True)
    im = ax.pcolormesh(lons, lats, cube_slice.data)
    fig.colorbar(im)

    ax.set_title(
        f"{cube_slice.name()} / {cube_slice.units}"
        f"\n@ {cube_slice.coord('level_height').points[0]} "
        f"{cube_slice.coord('level_height').units}",
        loc="right",
    )

    ax.set_ylim(-90, 90)
    ax.set_xlim(-180, 180)
    ax.set_ylabel("Latitude / deg")
    ax.set_xlabel("Longitude / deg")

    fig.show()
    fig.savefig("air_pot_temp.png")


def plot_horizontal_wind_vecs(east_cube, north_cube):
    # Make a vector plot of winds

    cube_east_slice = isel(east_cube[-1], "level_height", 20)
    cube_north_slice = isel(north_cube[-1], "level_height", 20)

    lats = cube_east_slice.coord("latitude").points
    lons = cube_east_slice.coord("longitude").points

    print(cube_east_slice)
    print(cube_north_slice)

    fig, ax = plt.subplots(constrained_layout=True)
    ax.streamplot(
        lons,
        lats,
        cube_east_slice.data,
        cube_north_slice.data,
    )
    ax.set_title(
        f"Horizontal flow @ {east_cube.coord('level_height').points[20]} "
        f"{east_cube.coord('level_height').units}",
        loc="right",
    )
    ax.set_ylim(-90, 90)
    ax.set_xlim(-180, 180)
    ax.set_ylabel("Latitude / deg")
    ax.set_xlabel("Longitude / deg")

    fig.savefig("horiz_vec.png")


def plot_zonal_winds(east_winds_cube):
    # Make the zonal map

    u_zm = zonal_mean(east_winds_cube[-1])

    fig, ax = plt.subplots(constrained_layout=True)

    p0 = ax.contourf(
        u_zm.coord("latitude").points,
        u_zm.coord("level_height").points,
        u_zm.data,
        cmap="RdBu_r",
        norm=mcol.CenteredNorm(),
    )
    cb0 = fig.colorbar(p0, ax=ax)
    cb0.ax.set_ylabel("Wind Speed / $m$ $s^{-1}$")

    ax.set_ylabel("Level Height / m")
    ax.set_xlabel("Latitude / deg")

    ax.set_title("Zonal mean eastward wind")
    fig.savefig("zonal_plot_height.png")


def plot_isobaric_winds(
    eastward_wind_cube,
    air_pressure_cube,
    max_pressure=1e5,
    pressure_res=1e2,
    debug=False,
):
    # Interpolate wind speeds to isobaric
    INTERPOLATOR = partial(
        stratify.stratify.interpolate,
        interpolation=stratify.stratify.INTERPOLATE_LINEAR,
        extrapolation=stratify.stratify.EXTRAPOLATE_LINEAR,
    )
    lfric.pres = air_pressure_cube.name()
    (pres_lev := np.arange(max_pressure, 0, -(pressure_res)))

    cube_plev = stratify.relevel(
        eastward_wind_cube,
        air_pressure_cube,
        np.atleast_1d(pres_lev),
        axis=lfric.z,
        interpolator=INTERPOLATOR,
    )
    cube_plev.coord(air_pressure_cube.name()).attributes = {}
    cube_plev = iris.util.squeeze(cube_plev)
    if debug:
        print(cube_plev)

    u_p_zm = zonal_mean(cube_plev[-1])

    fig, ax = plt.subplots(constrained_layout=True)
    p0 = ax.contourf(
        u_p_zm.coord("latitude").points,
        u_p_zm.coord(air_pressure_cube.name()).points,
        u_p_zm.data,
        cmap="RdBu_r",
        norm=mcol.CenteredNorm(),
    )
    cb0 = fig.colorbar(p0, ax=ax)
    cb0.ax.set_ylabel("Wind Speed / $m$ $s^{-1}$")

    ax.set_ylim(max_pressure, pressure_res)
    ax.set_yscale("log")

    ax.set_ylabel("Pressure / Pa")
    ax.set_xlabel("Latitude / deg")

    ax.set_title("Zonal mean eastward wind")

    fig.savefig("zonal_wind_isobaric.png")


def regrid_cubes(filename):
    # Following the aeolus method of re-gridding cubes to latlon

    # This has to be a Path
    in_file = Path.cwd() / filename

    # This is to get rid of time?
    drop_coord = ["forecast_period"]

    # Callback functions that fix dimensions and add height
    _add_levs = partial(add_equally_spaced_height_coord, model_top_height=3.29689e6)
    _fix_time = partial(fix_time_coord, downgrade_to_scalar=True)

    def _combi_callback(cube, field, filename):
        return _fix_time(
            _add_levs(cube, field, filename), field, filename, downgrade_to_scalar=True
        )

    cubes_raw = load_lfric_raw(in_file, callback=_combi_callback, drop_coord=drop_coord)

    # Rename the full level air pressure cube so that we can pick it out later
    for cube in cubes_raw:
        if cube.name() == "air_pressure" and cube.coords("full_levels"):
            cube.rename("air_pressure_full_levels")

    # Check that we've done that
    print(cubes_raw)

    # Try re-gridding the cubes
    ref_cube = create_dummy_cube(nlat=48, nlon=96, pm180=True)
    #    generate_latlon_cube(10,20)

    print(ref_cube)

    # Now re-grid them
    cubes_regr = simple_regrid_lfric(
        cubes_raw, tgt_cube=ref_cube, ref_cube_constr="air_potential_temperature"
    )

    print(cubes_regr)

    # Let's make a simple latlon plot
    if cube_in_list(cubes_regr, "air_potential_temperature"):
        plot_air_pot_temp(cubes_regr.extract_cube("air_potential_temperature"))

    # Make a wind vector plot
    if cube_in_list(cubes_regr, "eastward_wind") and cube_in_list(
        cubes_regr, "northward_wind"
    ):
        plot_horizontal_wind_vecs(
            cubes_regr.extract_cube("eastward_wind"),
            cubes_regr.extract_cube("northward_wind"),
        )

    if cube_in_list(cubes_regr, "eastward_wind"):
        plot_zonal_winds(cubes_regr.extract_cube("eastward_wind"))
        if cube_in_list(cubes_regr, "air_pressure_full_levels"):
            plot_isobaric_winds(
                cubes_regr.extract_cube("eastward_wind"),
                cubes_regr.extract_cube("air_pressure_full_levels"),
            )


def main(
    filename: str,
    dump_info: bool = False,
    timestep: int = 0,
    layer: int = 0,
    norun: bool = False,
    no_regrid: bool = False,
):
    cubes = load_cubes(filename)

    print(cubes)

    if dump_info:
        dump_cube_info(cubes[0])

        for cube in cubes:
            if "temperature" in cube.name():
                print(cube.name)
            if "wind" in cube.name():
                print(cube.name)

    # Plot the cubes
    cubes_1d = ["surface_upward_longwave_flux", "grid_surface_temperature"]
    cubes_2d = [
        "snow_layer_thickness",
        "air_pressure",
        "air_potential_temperature",
        "temperature_in_radiation_layers",
        "eastward_wind",
    ]
    if not norun:
        # Make simple plots
        plot_cubes_nstep(cubes, cubes_1d, cubes_2d, timestep, layer)

    # Call the re-gridding routine
    if not no_regrid:
        regrid_cubes(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="simple_iris_plotter",
        description="Simple plotting scripts for Iris cubes",
    )
    parser.add_argument(
        "--infile",
        "-i",
        default="lfric_diag.nc",
        help="Input file name [default=lfric_diag]",
    )
    parser.add_argument(
        "--dumpinfo",
        "-d",
        default=False,
        action="store_true",
        help="Dump information about the cubes",
    )
    parser.add_argument(
        "--timestep", "-t", default=1, type=int, help="Which timestep to plot"
    )
    parser.add_argument(
        "--layer", "-l", default=0, type=int, help="Which layer to plot"
    )
    parser.add_argument(
        "--norun",
        "-n",
        default=False,
        action="store_true",
        help="Don't run the plot production",
    )
    parser.add_argument(
        "--noregrid",
        "-g",
        default=False,
        action="store_true",
        help="Don't run the re-gridding",
    )

    args = parser.parse_args()

    main(
        args.infile, args.dumpinfo, args.timestep, args.layer, args.norun, args.noregrid
    )
