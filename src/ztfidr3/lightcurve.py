""" module focused on the LightCurve object """
import pandas
import numpy as np

ZTFCOLOR = { # ZTF
        "ztfr":dict(marker="o",ms=7,  mfc="C3"),
        "ztfg":dict(marker="o",ms=7,  mfc="C2"),
        "ztfi":dict(marker="o",ms=7, mfc="C1")
}

BAD_ZTFCOLOR = { # ZTF
        "ztfr":dict(marker="o",ms=6,  mfc="None", mec="C3"),
        "ztfg":dict(marker="o",ms=6,  mfc="None", mec="C2"),
        "ztfi":dict(marker="o",ms=6,  mfc="None", mec="C1")
}

def get_saltmodel(which="salt2.4-T21", **params):
    """Get a SALT2 model with specified parameters.

    Parameters
    ----------
    which : str, optional
        Model specification string. Can include version with "v=" syntax.
        Default is "salt2.4-T21".
    **params : dict
        Additional parameters to set on the model.

    Returns
    -------
    sncosmo.Model
        A SALT2 model with Milky Way dust effects included.

    Examples
    --------
    >>> model = get_saltmodel()
    >>> model = get_saltmodel("salt2.4", z=0.5, t0=55000)
    """
    import sncosmo
    if which is None or which in ["salt2.4"]:
        which = "salt2 v=2.4"
    if "salt" in which.lower() and "t21" in which.lower():
        which = "salt2 v=T21"

    # parsing model version
    source_name, *version = which.split("v=")
    source_name = source_name.strip()
    version = None if len(version)==0 else version[0].strip()
    source = sncosmo.get_source(source_name, version=version, copy=True)

    dust  = sncosmo.CCM89Dust()
    model = sncosmo.Model(source, effects=[dust],
                              effect_names=['mw'],
                              effect_frames=['obs'])
    model.set(**params)
    return model


class LightCurve():
    def __init__(self, data, saltdata=None):
        self._data = data
        self._saltdata = saltdata

    @classmethod
    def from_name(cls, name, release="dr3", **kwargs):
        """Create a LightCurve instance from a target name.

        Parameters
        ----------
        name : str
            The name of the target.
        release : str, optional
            Data release version. Default is "dr3".
        **kwargs : dict
            Additional keyword arguments to pass to get_target_saltdata.

        Returns
        -------
        LightCurve
            A new LightCurve instance with data and salt data loaded.
        """
        from . import io
        data = io.get_target_lightcurve(name, release=release)
        saltdata = io.get_target_saltdata(name, release=release, **kwargs)
        return cls(data, saltdata=saltdata)

    @classmethod
    def from_filename(cls, filename, saltdata=None):
        """Create a LightCurve instance from a data file.

        Parameters
        ----------
        filename : str
            Path to the light curve data file in whitespace-separated format.
        saltdata : pandas.DataFrame, optional
            SALT2 parameter data. Default is None.

        Returns
        -------
        LightCurve
            A new LightCurve instance with loaded data.
        """
        data = pandas.read_csv(filename, sep=r'\s+', comment='#')
        return cls(data, saltdata=saltdata)

    # =============== #
    #  Methods        #
    # =============== #
    def get_saltmodel(self, saltdata=None, **kwargs):
        """Get a SALT2 model with parameters from salt data.

        Parameters
        ----------
        saltdata : pandas.DataFrame, optional
            SALT2 parameter data. If None, uses the instance's saltdata.
        **kwargs : dict
            Additional keyword arguments to pass to get_saltmodel.

        Returns
        -------
        sncosmo.Model
            A SALT2 model with parameters set from saltdata.

        Raises
        ------
        ValueError
            If saltdata is not provided and not set on the instance.
        """

        if saltdata is None:
            saltdata = self.saltdata

        if saltdata is None:
            raise ValueError("saltdata is not given nor set")

        propmodel = saltdata[["z","t0","x0","x1","c","mwebv"]].to_dict()
        return get_saltmodel(**(propmodel | kwargs) )

    def get_lcdata(self, zp=None, mjdrange=None,
                       min_detection=None,
                       filters=None,
                       flagout=[1,2,4,8,16]):
        """Get light curve data with optional filtering and corrections.

        Parameters
        ----------
        zp : float, optional
            Zero point for flux calibration. If None, uses the data's ZP values.
        mjdrange : tuple of float, optional
            MJD range (min, max) to filter the light curve data.
        min_detection : float, optional
            Minimum detection significance (flux/flux_err) threshold.
        filters : str, list of str, or None, optional
            Filter selection. Options are:
            - None, '*', or 'all': no filter selection
            - str: single filter (e.g. 'ztfg')
            - list of str: multiple filters (e.g. ['ztfg', 'ztfr'])
            Default is None.
        flagout : list of int or str, optional
            Quality flags to exclude. Default is [1, 2, 4, 8, 16].
            flag == 0 means all good. Flag meanings:
            - 0: no warning
            - 1: flux_err==0, remove unphysical errors
            - 2: chi2dof>3, remove extreme outliers
            - 4: cloudy>1, BTS cut
            - 8: infobits>0, BTS cut
            - 16: mag_lim<19.3, cut applied in Dhawan 2021
            - 32: seeing>3, cut applied in Dhawan 2021
            - 64: fieldid>879, recommended IPAC cut
            - 128: moonilf>0.5, recommended IPAC cut
            - 256: has_baseline>1, has valid baseline correction
            - 512: airmass>2, recommended IPAC cut
            - 1024: flux/flux_err>=5, nominal detection

        Returns
        -------
        pandas.DataFrame
            Filtered light curve data with columns: mjd, mag, mag_err, filter,
            field_id, flag, rcid, zp, flux, error, detection, mag_lim, and phase.

        """

        from .utils import flux_to_mag

        if flagout in ["all","any","*"]:
            data = self.data[self.data["flag"]==0]
        elif flagout is None:
            data = self.data.copy()
        else:
            flag_ = np.all([(self.data.flag&i_==0) for i_ in np.atleast_1d(flagout)], axis=0)
            data = self.data[flag_]

        if zp is None:
            zp = data["ZP"].values
            coef = 1.
        else:
            coef = 10 ** (-(data["ZP"].values - zp) / 2.5)

        flux  = data["flux"] * coef
        error = data["flux_err"] * coef
        detection = flux/error

        lcdata = data[["mjd","mag","mag_err","filter","field_id", "flag", "rcid"]] # "x_pos","y_pos"
        additional = pandas.DataFrame(np.asarray([zp, flux, error, detection]).T,
                                         columns=["zp", "flux", "error", "detection"],
                                         index=lcdata.index)

        additional["mag_lim"], _ = flux_to_mag(error*5, None, zp=zp)

        lcdata = pandas.merge(lcdata, additional, left_index=True, right_index=True)

        if self.saltdata is not None:
            lcdata["phase"] = lcdata["mjd"]-self.saltdata['t0']
        else:
            lcdata["phase"] = np.NaN

        if mjdrange is not None:
            lcdata = lcdata[lcdata["mjd"].between(*mjdrange)]

        if min_detection is not None:
            lcdata = lcdata[lcdata["detection"]>min_detection]

        if filters is not None and filters not in ["*","all"]:
            lcdata = lcdata[lcdata["filter"].isin(np.atleast_1d(filters))]

        return lcdata

    # ============== #
    # Properties     #
    # ============== #
    @property
    def data(self):
        return self._data

    @property
    def saltdata(self):
        return self._saltdata
