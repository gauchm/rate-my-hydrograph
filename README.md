# In Defense of Metrics: Metrics Sufficiently Encode Typical Human Preferences Regarding Hydrological Model Performance

This repository contains all code, data, and analyses for the paper [**"In Defense of Metrics: Metrics Sufficiently Encode Typical Human Preferences Regarding Hydrological Model Performance"**](https://doi.org/10.1029/2022WR033918) published in WRR.

## Contents of this repository

- `website/` -- This folder contains the code to build and run the study website that we used to collect hydrograph ratings.
- `rmh-meta-stats.ipynb` -- This Jupyter notebook contains statistics about participation and demographic data.
- `rmh-stats.ipynb` -- This Jupyter notebook contains the analyses of model ranking.
- `rmh-classifier-metrics.ipynb` -- This Jupyter notebook contains the code to train a Random Forest on classifying rating outcomes.
- `rmh-metrics-vs-hydrographs.ipynb` -- This Jupyter notebook contains the code to compare a model trained on metrics vs. a model trained on raw hydrographs.
- `rmh-cycle-analyses.ipynb` -- This Jupyter notebook contains the consistency analyses.
- `data/` -- This folder contains all data used in the study, as well as csv files with the collected ratings from study phases 1 and 2.

The simulated and observed hydrographs used in this study are from the ["The Great Lakes Runoff Intercomparison Project Phase 4: the Great Lakes (GRIP-GL)"](https://doi.org/10.5194/hess-26-3537-2022). The full data repository for GRIP-GL is available [here](https://doi.org/10.20383/103.0598).

## Contact

Martin Gauch: gauch (at) ml.jku.at

## Citation

```bib
@article{gauch2022metrics,
    author = {Gauch, Martin and Kratzert, Frederik and Gilon, Oren and Gupta, Hoshin and Mai, Juliane and Nearing, Grey and Tolson, Bryan and Hochreiter, Sepp and Klotz, Daniel},
    title = {In Defense of Metrics: Metrics Sufficiently Encode Typical Human Preferences Regarding Hydrological Model Performance},
    journal = {Water Resources Research},
    year = {2023},
    volume = {59},
    number = {6},
    pages = {e2022WR033918},
    url = {https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2022WR033918},
    doi = {10.1029/2022WR033918}
}
```
