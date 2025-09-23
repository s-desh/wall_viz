import yaml
import tkinter as tk
import pandas as pd
import colorsys
import argparse

with open('config.yaml', 'r') as file:
    build_config = yaml.safe_load(file)


# other internal vars
FULL = build_config["brick"]["full"]
HALF = build_config["brick"]["half"]
QUEEN = build_config["brick"]["queen"]
HEAD = build_config["joint"]["head"]
BED  = build_config["joint"]["bed"]
WALL_L = build_config['wall']['l']
WALL_H = build_config['wall']['h']
px_per_mm=0.4
PAD = 20
CANVAS_W = int(WALL_L * px_per_mm) + PAD*2 # pad
CANVAS_H = int(WALL_H * px_per_mm) + PAD*2
COLOR_BG      = "#f7f7f7"
COLOR_PLANNED = "#e0e0e0"
ROWS = WALL_H // (FULL["h"] + BED)
COLOR_FULL    = "#d9534f"  
COLOR_HALF    = "#f0ad4e"
BRICK_COLOR_MAP = {
    FULL["symbol"]: COLOR_FULL,
    HALF["symbol"]: COLOR_HALF,
}
STRIDE_L = 800
STRIDE_H = 1300


def parse_args():
    parser = argparse.ArgumentParser(description="Wall visualizer")
    parser.add_argument(
        "--bond",
        choices=["stretcher", "english_cross"],
        default="stretcher",
        help="Bond pattern"
    )
    return parser.parse_args()

def mm_to_px(x_mm):
    return int(x_mm * px_per_mm)

def symbol_to_width(symbol):
    if symbol == FULL["symbol"]:
        return FULL["l"]
    elif symbol == HALF["symbol"]:
        return HALF["l"]
    elif symbol == QUEEN["symbol"]:
        return QUEEN["l"]
    else:
        raise ValueError(f"Unknown brick: {symbol}")

def english_cross_bond_row(row_idx):
    course = []

    # alternate stretcher and header
    first_brick = FULL if (row_idx % 2 == 0) else HALF
    course.append(first_brick['symbol'])
    
    # half followed by queen for header course
    if first_brick == HALF: 
        second_brick = QUEEN 
    elif (row_idx % 4 == 0):
        # remove head joint alignment in alternate stretcher courses
        second_brick = HALF
    else:
        second_brick = FULL
    course.append(second_brick["symbol"])

    # remaining wall, remove identical 4 bricks from start and end of row
    remaining_wall = WALL_L - 2 * (first_brick['l'] + HEAD + second_brick["l"]) - HEAD - HALF["l"]
    
    # fill remaining wall header / stretcher
    remaining_brick = first_brick
    n_full = remaining_wall // (remaining_brick['l'] + HEAD)
    course.extend([remaining_brick['symbol']]*n_full)

    # closing bricks, identical to first two
    course.extend([second_brick['symbol'], first_brick['symbol']])

    return course


def stretcher_bond_row(row_idx):
    course = []

    # alternate half / full first bricks
    first_brick = FULL if (row_idx % 2 == 0) else HALF
    course.append(first_brick['symbol'])
    
    remaining_wall = WALL_L - (first_brick['l'] + HEAD)
    
    # lay a row of full bricks
    n_full = remaining_wall // (FULL['l'] + HEAD)
    course.extend([FULL['symbol']]*n_full)

    # add half or full based on remaining space
    extra_space = remaining_wall % (FULL['l'] + HEAD)
    if extra_space > 0:
        if (extra_space % FULL['l']) == 0:
            course.append(FULL['symbol'])
        elif (extra_space % HALF['l']) == 0:
            course.append(HALF['symbol'])
        else:
            raise ValueError("Cannot fill a row!")

    return course

def hex_from_hsv(h, s=0.65, v=0.85):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

def stride_color_for(k: int) -> str:
    return hex_from_hsv((k * 0.1) % 1.0)


class WallViz:
    def __init__(self, window):
        self.window = window
        self.window.title("Wall visualizer")
        self.canvas = tk.Canvas(window, width=CANVAS_W, height=CANVAS_H, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        self.canvas.create_rectangle(
            PAD, PAD,
            PAD + mm_to_px(WALL_L),
            PAD + mm_to_px(WALL_H),
            outline="#555555", width=2
        )

        # lay build plan
        self.bricks = self._build_template()
        self.build_order = []

        
        # self.stride_starts=[(0,0),(0,5),(0,7)]
        self.stride_starts = self._stride_starts_gen()
        self.stride_counter = 0
        self.counter = 0

        self.info_bottom = self.canvas.create_text(
            CANVAS_W//2, CANVAS_H - PAD//2,
            text="", fill="#cc3333", font=("Segoe UI", 10)
        )
        
        self.window.bind_all("<Return>", self.step) # callback with enter
        self._update_status()

    def _draw_brick(self, x_mm, y_mm, w_mm, h_mm, color, text=None):
        x0 = PAD + mm_to_px(x_mm)
        y0 = PAD + mm_to_px(y_mm)
        x1 = PAD + mm_to_px(x_mm + w_mm)
        y1 = PAD + mm_to_px(y_mm + h_mm)

        self.rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color) 

        return self.rect_id
    
    def _stride_starts_gen(self):
        all_starts = []

        for _, brick in self.bricks.iterrows():
            if brick["row"] % 5 == 0:
                all_starts.append((int(brick["row"]), int(brick["col"])))
        
        remaining_bricks = set((int(r), int(c)) for r, c in 
                             zip(self.bricks['row'], self.bricks['col']))
        selected_strides = []
        
        print("Optimizing stride start coordinates ...")

        while self.bricks[self.bricks["built"]==False].shape[0]>0:
            best_start = None
            best_coverage = 0
            best_bricks = []
            for start in all_starts:
                # if start not in remaining_bricks:
                #     continue
                
                # print(start)
                buildable = self._build_order_stride(start[0], start[1], simulate=True)
                relevant_bricks = [b for b in buildable if b in remaining_bricks]
                relevant_coverage = len(relevant_bricks)

                if relevant_coverage > best_coverage:
                    best_coverage = relevant_coverage
                    best_start = start
                    best_bricks = relevant_bricks
            
            if best_start is None or best_coverage == 0:
                # print("none")
                break
                
            selected_strides.append(best_start)
            self._build_order_stride(best_start[0],best_start[1])
            remaining_bricks -= set(best_bricks)
            all_starts.remove(best_start)
        
        self.bricks["built"] = False
        # print(remaining_bricks)
        # print(selected_strides)
        print(f"Number of strides: {len(selected_strides)}")
        return selected_strides

    
    def get_brick(self, r, c):
        m = (self.bricks["row"] == r) & (self.bricks["col"] == c)
        if not m.any():
            return None
        return self.bricks.loc[m].iloc[0]   

    def set_built(self, r, c, val=True):
        m = (self.bricks["row"] == r) & (self.bricks["col"] == c)
        self.bricks.loc[m, "built"] = val
        
    def _build_order_stride(self, start_r, start_c, simulate=False):
        '''
        Generate build order for given start position 
        '''
        course_h = FULL["h"] + BED
        rows_in_stride = STRIDE_H // course_h
        r_end = min(int(ROWS), int(start_r + rows_in_stride))
        build_order= []

        start_b = self.get_brick(start_r, start_c)
        x_base = 0 if start_b is None else start_b["x0"]
        x_end = x_base + STRIDE_L
    
        # check every brick in every row of stride
        for r in range(start_r, r_end):
            
            # use unbuilt bricks within stride limits
            row_df = self.bricks[(self.bricks["row"] == r) & (self.bricks["x0"] >= x_base) & (self.bricks["built"] == False) &  (self.bricks["x1"] <= x_end)].sort_values("x0")
            if row_df.empty:
                continue
            
            # decide if brick should be built
            for i, curr in row_df.iterrows():
                left = False
                right = False
                
                # bottom row, place until stride allows
                if (r == 0):
                    build_order.append((int(curr["row"]),(int(curr["col"]))))
                    if not simulate: self.set_built(int(curr["row"]), int(curr["col"]), True)
                    continue
                
                below = self.bricks[(self.bricks["row"] == r - 1) & (self.bricks["built"] == True)]
                if below.empty:
                    continue
                          
                # check if both corners of current brick are supported by below row 
                if not below.loc[(below["x0"] <= curr["x0"]) & (below["x1"] >= curr["x0"]),:].empty: left = True
                if not below.loc[(below["x0"] <= curr["x1"]) & (below["x1"] >= curr["x1"]),:].empty: right = True

                if (left and right):
                    build_order.append((int(curr["row"]), int(curr["col"])))
                    if not simulate: self.set_built(int(curr["row"]), int(curr["col"]), True)

        return build_order
    
    def _build_template(self):
        '''
        Designs the wall build plan
        '''
        rows_data = []
        for row in range(int(ROWS)):
            if args.bond == "stretcher":
                course = stretcher_bond_row(row)
            elif args.bond == "english_cross":
                course = english_cross_bond_row(row)

            # brick coordinates, y down is +ve
            y = (WALL_H - (row+1) * (FULL['h'] + BED))
            course_h = FULL['h'] + BED
             
            x = 0
            for col, brick_symbol in enumerate(course):
                width = symbol_to_width(brick_symbol)
                
                # stride = int(row * (course_h) // STRIDE_H) + int(x // STRIDE_L)
                rect_id= self._draw_brick(x, y, width, FULL['h'], COLOR_PLANNED)

                rows_data.append({
                    "id": rect_id,
                    "row": row,
                    "col": col,
                    "symbol": brick_symbol,
                    "built_color": BRICK_COLOR_MAP.get(brick_symbol),
                    "x0": x,
                    "x1": x + width,
                    "y": y,
                    "w": width,
                    "built": False
                })

                x += width
                if x < WALL_L:
                    x += HEAD
        
        df = pd.DataFrame(rows_data)
        print(f"Design generated.")
        return df

    def step(self,_evt=None):
        '''
        Step through the build plan - through every stride, highlight built bricks
        '''

        
        if (self.stride_counter == len(self.stride_starts)) and (self.counter == len(self.build_order)):
            print("Build complete!")
            return
        
        if (self.counter == len(self.build_order)) or (len(self.build_order) == 0):
            r, c = self.stride_starts[self.stride_counter]
            self.build_order =  self._build_order_stride(r, c)
            print(f"Generated build order for Stride {self.stride_counter}")
            self.stride_counter += 1
            self.counter = 0
        
        # print(self.build_order)
        brick_idx = self.build_order[self.counter]
        brick = self.get_brick(brick_idx[0],brick_idx[1])
        color = stride_color_for(self.stride_counter)
        self.canvas.itemconfig(brick["id"], fill=color)

        self.counter += 1

        self._update_status()


    def _update_status(self):
        self.canvas.itemconfig(
            self.info_bottom,
            text=f"Built: {self.counter} / {len(self.build_order)}"
        )


if __name__ == "__main__":
    args = parse_args()
    window = tk.Tk()
    app = WallViz(window)
    window.mainloop()