# Wall Viz
Simple tool to visualize brick laying plans.


### Quick Start
Follow these instructions preferably on a Linux machine
1. Clone the repository with `git clone git@github.com:s-desh/wall_viz.git`
3. Skip this step if you have python installed. To install python run
```
sudo apt update
sudo apt install python3
sudo apt install python3-pip
```
2. Create a python virtual environment to install dependencies
```
cd ./wall_viz
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
3. After installation run the visualizer to only view the wall design
```
python3 main.py --bond stretcher
```
4. `--bond` allows `stretcher` and `english_cross` values and generates respective patterns.
5. Add `--plan` argument for optimizing the wall build plan and stepping through it with "enter" key. Plan generation can take upto a minute.
```
python3 main.py --bond stretcher --plan
```

### Details
- `./src` contains the code for bond pattern, configuration and other helpers.
- `./main.py` handles the main visualisation, design and planning.
- New bond patterns can be supported by adding fucntions in `./src/bonds.py`.
- A simple rule is followed to determine if a brick can be placed - if the corners of a brick are supported by bricks, a row below.

### Limitations and potential improvements
- Current approach is greedy (might not be optimal) and does not optimize on stride order that can potentially lead to fewer total strides required.
- Takes around a minute to come up with stride starts. Can by improved by, reducing the number of stride starts on which build order is simulated.
- BONUS B - Wild bond incomplete.