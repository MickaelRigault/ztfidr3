"""access ztf dr3 internal data-release"""

import os

import numpy as np
import pandas

IDR_PATH = os.getenv("ZTFIDRPATH")
if np.any([IDR_PATH.endswith(test_case) for test_case in ["/dr2", "/dr2/"]]):
    IDR_PATH = IDR_PATH.replace("/dr2", "").replace("//", "/")

# ============ #
# Top level    #
# ============ #
def get_master_list(release="dr3"):
    """return the master list of ZTF objects"""
    return pandas.read_csv(
        os.path.join(IDR_PATH, release, "tables/object_lists/master_list.csv")
    )

def get_data(release="dr3"):
    """ """
    # so far data is quite empty but more will come.
    masterlist = get_master_list(release).set_index("ztfname")
    return masterlist

# ============ #
# Lightcurves  #
# ============ #
# from ztfidr3.io import IDR_PATH
def get_target_lightcurve(target, release="dr3", test_exist=True, load=True):
    """Get the target lightcurve for a ZTF object.

    Parameters
    ----------
    target : str
        The name or identifier of the target object.
    release : str, optional
        The data release version (default is "dr2").
    test_exist : bool, optional
        If True, check if the file exists before loading (default is True).
    load : bool, optional
        If True, load and return the data as a pandas DataFrame.
        If False, return only the file path (default is True).

    Returns
    -------
    pandas.DataFrame or str or None
        If load is True, returns a pandas DataFrame containing the lightcurve data.
        If load is False, returns the file path as a string.
        If test_exist is True and file does not exist, returns None.
    """
    fullpath = os.path.join(IDR_PATH, release, "lightcurves", f"{target}_LC.csv")
    if test_exist:
        if not os.path.isfile(fullpath):
            warnings.warn(f"No lc file for {target} ; {fullpath}")
            return None

    if not load:
        return fullpath

    return pandas.read_csv(fullpath, sep='\s+', comment='#')

# ============ #
#   Spectra    #
# ============ #
def parse_spectrum_file(filename):
    """Parse a spectrum file.

    Parse a ZTF spectrum file with format: name_mjd_instrument.ascii

    Parameters
    ----------
    filename : str
        Path to spectrum file

    Returns
    -------
    tuple
        Tuple of (name, mjd, instrument) extracted from the filename
    """

    import re

    # Parse filename to extract metadata
    basename = os.path.basename(filename)
    match = re.match(r"([^_]+)_([^_]+)_([^.]+)\.ascii", basename)

    if not match:
        return "failed", 0, "failed"
        #raise ValueError(f"Filename does not match expected format: {basename}")

    return match.groups()

def get_spec_datafile(release="dr3"):
    """Return the spectral data file.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing spectral data with columns ["name", "mjd", "instrument"]
        and mjd cast as float type.
    """
    from glob import glob

    path_to_spec = os.path.join(IDR_PATH, release, "spectra")
    all_spectra = glob(os.path.join(path_to_spec, "*.ascii"))
    specdata = [parse_spectrum_file(filename) for filename in all_spectra]
    specdata = pandas.DataFrame(specdata, columns=["name", "mjd", "instrument"]).astype({"mjd": "float"})
    specdata["basename"] = [os.path.basename(filename) for filename in all_spectra]
    return specdata
