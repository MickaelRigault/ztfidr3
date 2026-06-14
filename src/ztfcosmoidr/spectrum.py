import os
import pandas
import numpy as np

from .io import IDR_PATH

def read_specfile(filepath):
    """ Read spectroscopic data from a file.

    Parses a spectrum file with header information (lines starting with '#')
    and data columns. Header lines are expected to have 'key: value' format.

    Parameters
    ----------
    filepath : str
        Path to the spectrum file to read.

    Returns
    -------
    data : np.ndarray
        2D array of spectroscopic data (float type).
        lbda, flux[, ...]
    head_dict : dict
        Dictionary containing header information parsed from lines starting with '#'.
    """
    alldata = open(filepath).read().splitlines()
    # header parsing
    head_data = [line for line in alldata if line.startswith("#")]
    head_dict = {key.replace("#", "").strip(): value.strip() for head_ in head_data for key, value in [head_.split(":")] }

    # data parsing
    data_in = [line for line in alldata if not line.startswith("#")]
    data = np.asarray([line.split() for line in data_in], dtype="float")
    return data, head_dict


class Spectrum:
    def __init__(self, data, header):
        """Initialize a Spectrum object.

        Parameters
        ----------
        data : pandas.DataFrame
            DataFrame containing spectroscopic data columns (lbda, flux, etc.).
        header : dict
            Dictionary containing header information from the spectrum file.
        """
        self._data = data
        self._header = header

    @classmethod
    def from_filename(cls, filename, release=None):
        """Create a Spectrum object from a spectrum file.

        Parameters
        ----------
        filename : str
            Path to the spectrum file or basename of the file.
        release : str, optional
            Release name to locate the file in the IDR_PATH directory structure.
            If provided, the file is searched in IDR_PATH/release/spectra/.
            Required if filename is not an absolute path that exists.

        Returns
        -------
        Spectrum
            A new Spectrum instance initialized with data and header from the file.

        Raises
        ------
        FileNotFoundError
            If the file is not found and no release is provided, or if the file
            is still not found after constructing the path with the release.
        ValueError
            If the data shape is not 2D with 2, 3, or 4 columns.
        """
        # this file does not exist, maybe it is just the basename
        if not os.path.isfile(filename):
            if release is None:
                raise FileNotFoundError(f"File not found: {filename} and no release given, cannot fetch it.")
            filename = os.path.join(IDR_PATH, release, "spectra", filename)
            if not os.path.isfile(filename):
                raise FileNotFoundError(f"File not found: {filename}")

        data, header = read_specfile(filename)

        # parse input data depending on its dimension.
        columns = ["lbda", "flux"]
        if data.shape[-1] == 2:
            pass # all good already.
        elif data.shape[-1] == 3:
            columns += ["variance"]
        elif data.shape[-1] == 4:
            columns += ["variance_corr"]
        else:
            raise ValueError(f"Unexpected data shape: {data.shape}")

        data = pandas.DataFrame(data, columns=columns)
        return cls(data, header)

    # =============== #
    #   Methods       #
    # =============== #
    def get_phase(self, t0, redshift=None):
        """Calculate the phase of the observation.

        Parameters
        ----------
        t0 : float
            Reference time (e.g., time of explosion).
            phase is defined as time-t0.

        redshift : float, optional
            Redshift value to set the phase in rest-frame. If None
            phase is return in obs-frame

        Returns
        -------
        float
            Phase value (mjd - t0), or NaN if observation date is not available.
        """
        mjd = self.obsdate
        if mjd is None:
            return np.nan

        phase = mjd - t0
        if redshift is not None:
            phase /= (1+redshift)

        return phase

    # ------- #
    # PLOTS   #
    # ------- #
    def show(self, ax=None, **kwargs):
        """Plot the spectrum.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Matplotlib axes object to plot on. If None, a new figure and axes
            are created with figsize (7, 3).
        **kwargs
            Additional keyword arguments passed to ax.plot().

        Returns
        -------
        matplotlib.figure.Figure
            The matplotlib figure object containing the plot.
        """
        if ax is None:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(7,3))
        else:
            fig = ax.figure

        line, *_ = ax.plot(self.lbda, self.flux, **kwargs)
        if self.variance is not None:
            err = np.sqrt(self.variance)
            _ = ax.fill_between(self.lbda, self.flux-err, self.flux+err, alpha=0.3, color=line.get_color())

        ax.set_xlabel("wavelength", fontsize="large")
        ax.set_ylabel("flux", fontsize="large")
        return fig
    # =============== #
    #    Properties   #
    # =============== #
    @property
    def data(self):
        """Get the spectroscopic data.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing the spectroscopic data (lbda, flux, variance, etc.).
        """
        return self._data

    @property
    def header(self):
        """Get the header information.

        Returns
        -------
        dict
            Dictionary containing metadata from the spectrum file.
        """
        return self._header

    @property
    def lbda(self):
        """Get the wavelength array.

        Returns
        -------
        pandas.Series
            Wavelength values from the spectroscopic data.
        """
        return self.data["lbda"]

    @property
    def flux(self):
        """Get the flux array.

        Returns
        -------
        pandas.Series
            Flux values from the spectroscopic data.
        """
        return self.data["flux"]

    @property
    def variance(self):
        """Get the variance array if available.

        Returns
        -------
        pandas.Series or None
            Variance values if present in the data, otherwise None.
        """
        return self.data.get("variance", None)

    @property
    def obsdate(self):
        """Get the observation date (MJD).

        Returns
        -------
        float or None
            Modified Julian Date (MJD) of the observation if available,
            otherwise None.
        """
        mjd = self.header.get("MJD_OBS", None)
        if mjd is None:
            return mjd

        mjd = float(mjd)
        return mjd

    @property
    def instrument(self):
        """Get the instrument name.

        Returns
        -------
        str
            Instrument identifier from the header, or 'unknown' if not specified.
        """
        return self.header.get("INSTRUME", "unknown")
