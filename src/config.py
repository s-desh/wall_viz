from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class WallConfig:
    brick: Dict[str, Dict[str, Any]]
    joint: Dict[str, int]
    wall: Dict[str, int]

    # default
    px_per_mm: float = 0.4
    pad: int = 20
    stride_l: int = 800
    stride_h: int = 1300
    color_bg: str = "#f7f7f7"
    color_planned: str = "#e0e0e0"
    color_full: str = "#d9534f"
    color_half: str = "#f0ad4e"

    bond: str = "stretcher"   # "stretcher" or "english_cross"
    plan: bool = False

    @property
    def full(self) -> Dict[str, Any]:
        return self.brick["full"]

    @property
    def half(self) -> Dict[str, Any]:
        return self.brick["half"]

    @property
    def queen(self) -> Dict[str, Any]:
        return self.brick["queen"]

    @property
    def head(self) -> int:
        return self.joint["head"]

    @property
    def bed(self) -> int:
        return self.joint["bed"]

    @property
    def wall_l(self) -> int:
        return self.wall["l"]

    @property
    def wall_h(self) -> int:
        return self.wall["h"]
    
    @property
    def course_h(self) -> int:
        return (self.full["h"] + self.bed)

    @property
    def rows(self) -> int:
        return self.wall_h // (self.full["h"] + self.bed)

    @property
    def canvas_w(self) -> int:
        return int(self.wall_l * self.px_per_mm) + self.pad * 2

    @property
    def canvas_h(self) -> int:
        return int(self.wall_h * self.px_per_mm) + self.pad * 2

    @property
    def color_map(self) -> Dict[str, str]:
        return {
            self.full["symbol"]: self.color_full,
            self.half["symbol"]: self.color_half,
        }