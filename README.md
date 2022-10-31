![made-with-python](https://img.shields.io/badge/Made%20with-Python3-brightgreen)

<br />
<h1>
    <p align="center">Domebricks</p>
</h1>
<p align="center" style="color:brown">
    Pre-alfa release of the script. Use it on your own risk, I don't guarantee correctness of any value computed.
</p>
<p align="center">
    Python3 script compute bricks geometry for dome (pompeii oven).
</p>
<p align="center">
    <a href="#about-the-project">About The Project</a> •
    <a href="#installation">Installation</a> •
    <a href="#usage">How To Use</a> •
    <a href="#run-examples">Run Examples</a> •
    <a href="#output-examples">Output Examples</a> •
    <a href="#tests">Run tests</a> •
</p>

## About The Project
Domebricks is a Python script for computing and printing schemes/plans needed to cut bricks for pompeii oven (actually any dome). This script allows to set initial bricks sizes, dome radius and dome height and as a result outputs svg with all info needed to cut any brick of any row of the dome (except key bricks for now).

## Installation
Download from GitHub:
```bash
wget https://raw.githubusercontent.com/nmb10/domebricks/main/domebricks.py
```

## Usage
```bash
usage: domebricks.py [-h] [--scale SCALE] [--brick_width BRICK_WIDTH] [--brick_height BRICK_HEIGHT]
                     [--brick_depth BRICK_DEPTH] [--inner_radius INNER_RADIUS] [--height HEIGHT]
                     [--first_row_height FIRST_ROW_HEIGHT] [--seam SEAM]

optional arguments:
  -h, --help            Show this help message and exit
  --scale SCALE         Scale of the svg.
  --brick_width BRICK_WIDTH
                        Brick width (mm.)
  --brick_height BRICK_HEIGHT
                        Brick height (mm.)
  --brick_depth BRICK_DEPTH
                        Brick depth (mm.)
  --inner_radius INNER_RADIUS
                        Inner surface radius (mm.)
  --height HEIGHT       Dome height (mm.)
  --first_row_height FIRST_ROW_HEIGHT
                        First row outer height (mm)
  --seam SEAM           Masonry seam (mm.)
```
All params are optional.

## Run Examples
```bash
domebricks.py
```
After finish open dome.svg in any browser

Example with all params:
```bash
domebricks.py --scale=3.78 --brick_width=250 --brick_height=65 --brick_depth=125 --inner_radius=503 --height=440 --first_row_height=125 --seam=4
```

## Output examples
Check out [example.svg](example.svg) for default run output.

## Run tests
```bash
python -m unittest
```
