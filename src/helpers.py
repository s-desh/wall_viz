from src.config import WallConfig
from src.bonds import stretcher_bond_row, english_cross_bond_row, wild_bond_row

import colorsys
import argparse
import yaml

BOND = {
    "stretcher": stretcher_bond_row,
    "english_cross": english_cross_bond_row,
    "wild": wild_bond_row
}


def load_config(yaml_path: str, args=None) -> WallConfig:
    with open(yaml_path, "r") as f:
        build_config = yaml.safe_load(f)

    if args is None:
        args = parse_args()

    return WallConfig(
        brick=build_config["brick"],
        joint=build_config["joint"],
        wall=build_config["wall"],
        bond=args.bond,
        plan=args.plan,
    )

def parse_args():
    parser = argparse.ArgumentParser(description="Wall visualizer")
    parser.add_argument(
        "--bond",
        choices=["stretcher", "english_cross", "wild"],
        default="stretcher",
        help="Bond pattern"
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Enable stride planning, else only design"
    )
    return parser.parse_args()

def mm_to_px(cfg: WallConfig, x_mm):
    return int(x_mm * cfg.px_per_mm)

def symbol_to_width(cfg, symbol):
    if symbol == cfg.full["symbol"]:
        return cfg.full["l"]
    elif symbol == cfg.half["symbol"]:
        return cfg.half["l"]
    elif symbol == cfg.queen["symbol"]:
        return cfg.queen["l"]
    else:
        raise ValueError(f"Unknown brick: {symbol}")


def hex_from_hsv(h, s=0.65, v=0.85):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

def stride_color_for(k: int) -> str:
    return hex_from_hsv((k * 0.1) % 1.0)

def make_bond_fn(cfg: WallConfig):
    try:
        bond_fn = BOND[cfg.bond]
    except KeyError:
        raise ValueError(
            f"Unsupported bond type '{cfg.bond}'. "
            )
    return bond_fn


def get_brick(df, r, c):
    m = (df["row"] == r) & (df["col"] == c)
    if not m.any():
        return None
    return df.loc[m].iloc[0]

def set_built(df, r, c, val=True):
    m = (df["row"] == r) & (df["col"] == c)
    df.loc[m, "built"] = val
    