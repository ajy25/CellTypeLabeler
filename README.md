# CellTypeLabeler

Simple app for labeling cell types based on an image with expert labels.


## Usage

1. Install the dependencies found in `requirements.txt`. 

2. Replace the example `location.csv` file with your CSV file containing two columns, 
`'x'` and `'y'`. It must be named `location.csv`. The first column must 
be an index with no name—please examine the example `location.csv`.

3. Run the app via `python app.py`. You can optionally upload a labeled image 
to facilitate point labeling. The labeled image corresponding to the 
points in the example `location.csv` can be found in `example/annotation_img.png`. 
