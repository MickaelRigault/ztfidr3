# ztfcosmoidr
Access ZTF Internal data-release. 

This package is currently maintained for the internal data-release 3. 
Data associated with this package is only available to the ZTF Cosmo Science working group.


# Installation
```bash
git clone https://github.com/MickaelRigault/ztfidr3.git
cd ztfidr3
pip install .
```

# Data Access
The `Sample` object is a top layer made to ease access to any target. 

```python
sample = ztfidr3.Sample.load_release("dr3")

# access top level datatable
data = sample.data

# select a target
name = "ZTF19abpxcaf"

# get its lightcurve
lc = sample.get_target_lightcurve(name, as_dataframe=False)
figlc  = lc.show()

# get its spectra (could be a list of 0, 1 or n entries)
spectra = sample.get_target_spectra(name)
figspec = spectra[0].show()
```
