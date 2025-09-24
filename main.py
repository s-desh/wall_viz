import yaml
import tkinter as tk
import pandas as pd

from dataclasses import dataclass
from typing import Dict, Any
from helpers import (symbol_to_width, load_config, 
                    parse_args, mm_to_px, stride_color_for, 
                    make_bond_fn, get_brick, set_built) 
from config import WallConfig


def generate_wall_design(cfg: WallConfig, bond_fn):
    '''
    Designs the wall build, store properties in dataframe
    '''
    rows_data = []
    for row in range(int(cfg.rows)):
        course = bond_fn(cfg, row)

        # brick coordinates, y down is +ve
        y = (cfg.wall_h - (row+1) * (cfg.course_h))
            
        x = 0
        for col, brick_symbol in enumerate(course):
            width = symbol_to_width(cfg, brick_symbol)
            
            rows_data.append({
                "row": row,
                "col": col,
                "symbol": brick_symbol,
                "x0": x,
                "x1": x + width,
                "y": y,
                "w": width,
                "h": cfg.full["h"],
                "built": False
            })

            x += width
            if x < cfg.wall_l:
                x += cfg.head
    
    df = pd.DataFrame(rows_data)
    print(f"Design generated.")
    return df

class WallViz:
    '''
    Handle UI/interaction and build planning
    '''
    def __init__(self, window, cfg: WallConfig):
        self.cfg = cfg
        self.window = window
        self.window.title("Wall visualizer")
        self.canvas = tk.Canvas(window, width=cfg.canvas_w, height=cfg.canvas_h, bg=cfg.color_bg, highlightthickness=0)
        self.canvas.pack()

        self.canvas.create_rectangle(
            cfg.pad, cfg.pad,
            cfg.pad + mm_to_px(cfg,cfg.wall_l),
            cfg.pad + mm_to_px(cfg,cfg.wall_h),
            outline="#555555", width=2
        )

        # lay build plan
        bond_fn = make_bond_fn(cfg)
        self.bricks = generate_wall_design(cfg, bond_fn)

        # draw planned bricks and store ids
        ids = []
        for _, b in self.bricks.iterrows():
            ids.append(self._draw_brick(b.x0, b.y, b.w, b.h, cfg.color_planned))
        self.bricks["id"] = ids

        self.build_order = []

        # self.stride_starts=[(0,0),(0,5),(0,7)]
        self.stride_starts = self.plan_strides()
        self.stride_counter = 0
        self.counter = 0

        self.info_bottom = self.canvas.create_text(
            cfg.canvas_w//2, cfg.canvas_h - cfg.pad//2,
            text="", fill="#cc3333", font=("Segoe UI", 10)
        )
        
        self.window.bind_all("<Return>", self.step) # callback with enter
        self._update_status()

    def _draw_brick(self, x_mm, y_mm, w_mm, h_mm, color, text=None):
        x0 = cfg.pad + mm_to_px(self.cfg, x_mm)
        y0 = cfg.pad + mm_to_px(self.cfg, y_mm)
        x1 = cfg.pad + mm_to_px(self.cfg, x_mm + w_mm)
        y1 = cfg.pad + mm_to_px(self.cfg, y_mm + h_mm)

        self.rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color) 

        return self.rect_id
    
    def plan_strides(self):
        '''
        Plan stride starts
        '''
        
        if not args.plan:
            print("Add --plan to plan and step through the build")
            return
        
        all_starts = []

        for _, brick in self.bricks.iterrows():
            # potential stride starts every 5th row - tunable
            if brick["row"] % 5 == 0:
                all_starts.append((int(brick["row"]), int(brick["col"])))
        
        remaining_bricks = set((int(r), int(c)) for r, c in 
                             zip(self.bricks['row'], self.bricks['col']))
        selected_strides = []
        
        print("Optimizing stride start coordinates ...")

        while self.bricks[self.bricks["built"]==False].shape[0] > 0:
            best_start = None
            best_coverage = 0
            best_bricks = []
            for start in all_starts:
                # if start not in remaining_bricks:
                #     continue
                
                # print(start)
                buildable = self.generate_build_order(start[0], start[1], simulate=True)
                relevant_bricks = [b for b in buildable if b in remaining_bricks]
                relevant_coverage = len(relevant_bricks)

                # greedy approach, add stride coordinate that lays most bricks
                if relevant_coverage > best_coverage:
                    best_coverage = relevant_coverage
                    best_start = start
                    best_bricks = relevant_bricks
            
            if best_start is None or best_coverage == 0:
                # print("none")
                break
                
            selected_strides.append(best_start)
            self.generate_build_order(best_start[0], best_start[1])
            # self.generate_build_order(best_start[0], best_start[1])
            remaining_bricks -= set(best_bricks)
            all_starts.remove(best_start)
        
        self.bricks["built"] = False
        print(f"Number of strides: {len(selected_strides)}")
        return selected_strides

    def generate_build_order(self,start_r, start_c, simulate=False):
        '''
        Generate build order within stride for given start position 
        '''
        rows_in_stride = cfg.stride_h // cfg.course_h
        r_end = min(int(cfg.rows), int(start_r + rows_in_stride))
        build_order= []

        start_b = get_brick(self.bricks,start_r, start_c)
        x_base = 0 if start_b is None else start_b["x0"]
        x_end = x_base + cfg.stride_l

        # check every brick in every row of stride
        for r in range(start_r, r_end):
            
            # slice unbuilt bricks within stride limits
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
                    if not simulate: set_built(self.bricks, int(curr["row"]), int(curr["col"]), True)
                    continue
                
                below = self.bricks[(self.bricks["row"] == r - 1) & (self.bricks["built"] == True)]
                if below.empty:
                    continue
                            
                # check if both corners of current brick are supported by below row 
                if not below.loc[(below["x0"] <= curr["x0"]) & (below["x1"] >= curr["x0"]),:].empty: left = True
                if not below.loc[(below["x0"] <= curr["x1"]) & (below["x1"] >= curr["x1"]),:].empty: right = True

                if (left and right):
                    build_order.append((int(curr["row"]), int(curr["col"])))
                    if not simulate: set_built(self.bricks, int(curr["row"]), int(curr["col"]), True)

        return build_order


    def step(self,_evt=None):
        '''
        Step through the build plan - through every stride, highlight built bricks
        '''
        if not args.plan:
            print("Add --plan to plan and step through the build")
            return

        if (self.stride_counter == len(self.stride_starts)) and (self.counter == len(self.build_order)):
            print("Build complete!")
            return
        
        if (self.counter == len(self.build_order)) or (len(self.build_order) == 0):
            r, c = self.stride_starts[self.stride_counter]
            self.build_order =  self.generate_build_order(r, c)
            self.stride_counter += 1
            self.counter = 0
        
        # print(self.build_order)
        brick_idx = self.build_order[self.counter]
        brick = get_brick(self.bricks, brick_idx[0],brick_idx[1])
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
    cfg = load_config("config.yaml", args)
    window = tk.Tk()
    app = WallViz(window, cfg)
    window.mainloop()