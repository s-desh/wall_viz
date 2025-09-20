import yaml
import tkinter as tk

with open('config.yaml', 'r') as file:
    build_config = yaml.safe_load(file)


# other internal vars
FULL = build_config["brick"]["full"]
HALF = build_config["brick"]["half"]
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

def mm_to_px(x_mm):
    return int(x_mm * px_per_mm)

def symbol_to_width(symbol):
    if symbol == FULL["symbol"]:
        return FULL["l"]
    elif symbol == HALF["symbol"]:
        return HALF["l"]
    else:
        raise ValueError(f"Unknown brick: {symbol}")

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

        self.bricks = []
        self.build_order = []

        self._build_template()

        self.counter = 0

        self.window.bind_all("<Return>", self.step) # callback with enter

        self.info_bottom = self.canvas.create_text(
            CANVAS_W//2, CANVAS_H - PAD//2,
            text="", fill="#cc3333", font=("Segoe UI", 10)
        )

        self._update_status()

    def _draw_brick(self, x_mm, y_mm, w_mm, h_mm, color, text=None):
        x0 = PAD + mm_to_px(x_mm)
        y0 = PAD + mm_to_px(y_mm)
        x1 = PAD + mm_to_px(x_mm + w_mm)
        y1 = PAD + mm_to_px(y_mm + h_mm)

        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2

        self.rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color) 
        self.text_id = self.canvas.create_text(
            cx, cy,
            text=text, fill="#000000", font=("Segoe UI", 10)
        )

        return self.rect_id, self.text_id
    
    def _build_template(self):
        '''
        Draws the wall build plan
        '''

        for row in range(int(ROWS)):
            course = stretcher_bond_row(row)

            # brick coordinates, y down is +ve
            y = (WALL_H - (row+1) * (FULL['h'] + BED))

            course_h = FULL['h'] + BED
             

            x = 0
            for col, brick_symbol in enumerate(course):
                width = symbol_to_width(brick_symbol)
                
                stride = int(max(row * (course_h) // STRIDE_H, x // STRIDE_L))
                rect_id, stride_id = self._draw_brick(x, y, width, FULL['h'], COLOR_PLANNED, stride)

                # print
                x += width
                if x < WALL_L:
                    x += HEAD
                
                self.bricks.append({
                    "id": rect_id,
                    "row": row,
                    "col": col,
                    "symbol": brick_symbol,
                    "built_color": BRICK_COLOR_MAP.get(brick_symbol),
                    "stride": stride_id
                })
                self.build_order.append(len(self.bricks) - 1)

    def step(self,_evt=None):
        '''
        Step through the build plan, and highlight built bricks
        '''
        if self.counter >= len(self.build_order):
            print("Build complete!")
            return
        idx = self.build_order[self.counter]
        brick = self.bricks[idx]
        self.canvas.itemconfig(brick["id"], fill=brick["built_color"])
        self.canvas.tag_raise(brick["stride"], brick["id"])

        self.counter += 1
        self._update_status()


    def _update_status(self):
        self.canvas.itemconfig(
            self.info_bottom,
            text=f"Built: {self.counter} / {len(self.build_order)}"
        )


if __name__ == "__main__":
    window = tk.Tk()
    app = WallViz(window)
    window.mainloop()