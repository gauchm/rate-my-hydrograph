# Data for Rate My Hydrograph

This folder contains the observations and model simulations used in this study (see folders `objective_1`/`objective_2`).
These data originate from the [GRIP-GL project](https://doi.org/10.5194/hess-26-3537-2022).

The csv files contain the data we collected in this study:

- `rmh-stage1.csv` -- The main results from the study. This file contains one line for each rating. See below for an explanation of the different columns.
- `rmh-stage2.csv` -- Ratings from the second phase of the study. This file has the same structure as the file for stage 1.
- `rmh-users.csv` -- One entry for each participant in the study.

## Columns

### Rating information
- `basin` -- The basin that the hydrographs came from.
- `model_a` -- The first model in the comparison.
- `model_b` -- The second model in the comparison.
- `num_{a_better, b_better, equal_good, equal_bad}` -- The participant's rating. These are just 0 or 1, and for each rating exactly one of them is 1.
- `{start, end}_date` -- The date range of the compared hydrographs.
- `task` -- What users were told to focus on for their rating (overall/high flow/low flow).
- `objective` -- The GRIP-GL study (which is where our hydrographs come from) had two "objectives", the first one being basins with no human influence, and the second one being most-downstream basins. This column indicates from which objective the simulations/observations were taken.
- `y_scale` -- Whether the user gave their rating when they looked at the hydrographs with a linear or a log scale.
- `{x, y}_zoomed` -- Indicates whether the user had zoomed in along the x or y axis when they gave their rating.
- `{x, y}_range_{start, end}` -- Indicates the x/y axis range the user had zoomed to when they gave their rating.
- `last_modified` -- Time when the rating was given.

### Participant information
- `user_id` -- The id of the participant who gave the rating.
- `creation_time` -- Time when the participant who gave the rating was created.
- `occupation` -- Main area of occupation for this participant.
- `focus_areas` -- List of the participant's focus areas.
- `country` -- The participant's country of residence.
- `gender` -- The participant's self-reported gender.
- `years_experience` -- The participant's years of experience related to hydrology.

