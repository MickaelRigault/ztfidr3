from . import io



class Sample():
    """
    """
    def __init__(self, data, release="dr3"):
        """ """
        self._data = data
        self._release = release
        # this is store for speed
        self._specfile = io.get_spec_datafile(release=release)

    @classmethod
    def load(cls, release="dr3"):
        """ """
        data = io.get_data(release=release)
        return cls(data)

    def get_target_lightcurve(self, name):
        """ """
        if name not in self.data.index:
            raise ValueError(f"Target {name} not found in data")
        return io.get_target_lightcurve(name, release=self.release)

    def get_target_spectrum(self, name):
        """ """
        if name not in self.data.index:
            raise ValueError(f"Target {name} not found in data")

        return self.specfile[self.specfile["name"] == name]

    # =============== #
    #   Properties    #
    # =============== #
    @property
    def data(self):
        """ """
        return self._data

    @property
    def release(self):
        """ """
        return self._release

    @property
    def specfile(self):
        """ """
        return self._specfile
