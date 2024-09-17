![made-with-python](https://img.shields.io/badge/Made%20with-Python3-brightgreen)

<br />
<h1>
    <p align="center">Domebricks</p>
</h1>
<p align="center" style="color:brown">
    Alfa release of the script. Use it on your own risk, I don't guarantee correctness of any value computed.
</p>
<p align="center" style="color:brown">
    WARNING: pdf file with row templates may have length errors after printing (3-5 mm, that is critical for sure). So print first page, check with physical ruller and check scale settings of your printer if the length is wrong.
</p>
<p align="center">
    Bricks shape calculator for a dome (pompeii or pizza oven) with detailed blueprint for every row.
</p>
<p align="center">
    <a href="#geometric-shapes-for-dome-bricks">About The Project</a> •
    <a href="#installation">Installation</a> •
    <a href="#usage">How To Use</a> •
    <a href="#run-examples">Run Examples</a> •
    <a href="#output-examples">Output Examples</a> •
    <a href="#tests">Run tests</a> •
</p>

# Geometric shapes for dome bricks
This Python script calculates and prints schemes/plans needed to cut bricks for pompeii oven (actually any dome). The script allows to set initial bricks sizes, dome radius and dome height and as a result outputs svg with all info needed to cut a brick of every row of the dome (except key bricks for now).

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

## Run examples

Example with all params:
```bash
python3 domebricks.py --inner_radius 490 --height 440 --brick_width=250 --first_row_height=150 --brick_depth=123 --bricks-amount=32 --minimal-width=40
```

After finish open dome.svg (support template) in any browser and row-templates.pdf (pdf with templates for bricks)

## Output examples
Check out [dome.svg](examples/dome.svg) and [row-templates.pdf](examples/row-templates.pdf) for default run output. Also check real-life example of the dome implemented using domebricks templates - [examples](examples).

## Run tests
```bash
python -m unittest
```
