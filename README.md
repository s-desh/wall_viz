# Wall Viz
Simple tool to visualize brick laying plans.


### Quick Start
Follow these instructions preferably on a Linux machine
1. Clone the repository with `git clone git@github.com:s-desh/wall_viz.git`
2. Create a python virtual environment to install dependencies
```
pip -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. After installation run the visualizer to only view the wall design
```
python3 main.py --pattern stretcher
```
4. `--pattern` allows `stretcher` and `english_cross` values and generates respective patterns.
5. Add `--plan` argument for optimizing the wall build plan and stepping through it with "enter" key. Plan generation can take upto a minute.