# XAI in Action for Effective Data Reduction on Time Series
## Submitted to CIKM 2025 Full Research track

This repository contains code and experimental result for "XAI in Action for Effective Data Reduction on Time Series"
submitted to CIKM 2025 

## Abstract 

Explainable AI (XAI) for time series is an important topic and recent efforts in this area have resulted in many new 
explanation methods. Additionally, new approaches were proposed to evaluate XAI methods, both quantitatively and 
qualitatively through domain expertise or user studies.
Despite progress in XAI for time series, its practical application for achieving measurable benefits remains unclear.
This paper bridges this gap by proposing and evaluating a novel, general methodology for
**XAI-based data reduction on time series (drXAI)**. We analyse XAI in action on the task of data reduction for time 
series classification. We first study channel selection for multivariate time series classification (MTSC). We show that
*drXAI* can reduce the data by up to 88\% on big datasets (>50 channels), significantly outperforming state-of-the-art
channel selection methods. Next, we apply the *drXAI* algorithm for time point selection in univariate time series 
classification (UTSC). We show that our XAI-based algorithm can reduce the data by up to 95\% in some cases (>4k length),
while preserving or improving the classification accuracy. Finally, we show that XAI-selection can be done using fast 
classifiers (e.g., Minirocket) and fast XAI methods (e.g., Feature Ablation): this enables the use of more complex and 
accurate algorithms such as ConvTran, which require significant memory resources for long time series.
Our experiments show that XAI can be used effectively for data reduction on the TSC task, with significant and 
measurable benefits, opening a path to applying XAI to other time series tasks.

## Results

TBD

## Code 

Code developed using Python 3.10.16, all used libraries are listed in requirements.txt

The two executable files are:

### get_selection.py
To be used to train models, explain them getting the saliency maps and related selection. <br>

Arguments:

> dataset_dir : folder where datasets are stored

> saved_models_path : folder where to save models

> explainer_results_dir : directory where to save classifiers and attributions info including related selection. Format is one file per dataset

> random_seed : random seed to be used for reproducibility

> --channel_selection : whether to perform channel selection or not (perform time point selection)

### compute_metrics.py
To be used to trained new model(s), as described in the paper, and get metrics about them

Arguments:

> explanation_dir : dir where explanation results are stored

> saved_models_path : folder where models will be saved

> dataset_dir : directory where datasets are located

> result_path : path where to store new accuracies

> --elbow_selections_path : file path where elbow selections are saved
