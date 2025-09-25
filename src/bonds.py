from src.config import WallConfig
import random


def symbol_to_width(cfg, symbol):
    if symbol == cfg.full["symbol"]:
        return cfg.full["l"]
    elif symbol == cfg.half["symbol"]:
        return cfg.half["l"]
    elif symbol == cfg.queen["symbol"]:
        return cfg.queen["l"]
    else:
        raise ValueError(f"Unknown brick: {symbol}")


def stretcher_bond_row(cfg, row_idx):
    course = []

    # alternate half / full first bricks
    first_brick = cfg.full if (row_idx % 2 == 0) else cfg.half
    course.append(first_brick['symbol'])
    
    remaining_wall = cfg.wall_l - (first_brick['l'] + cfg.head)
    
    # lay a row of full bricks
    n_full = remaining_wall // (cfg.full['l'] + cfg.head)
    course.extend([cfg.full['symbol']]*n_full)

    # add half or full based on remaining space
    extra_space = remaining_wall % (cfg.full['l'] + cfg.head)
    if extra_space > 0:
        if (extra_space % cfg.full['l']) == 0:
            course.append(cfg.full['symbol'])
        elif (extra_space % cfg.half['l']) == 0:
            course.append(cfg.half['symbol'])
        else:
            raise ValueError("Cannot fill a row!")

    return course

def english_cross_bond_row(cfg: WallConfig, row_idx):
    course = []

    # alternate stretcher and header
    first_brick = cfg.full if (row_idx % 2 == 0) else cfg.half
    course.append(first_brick['symbol'])
    
    # half followed by queen for header course
    if first_brick == cfg.half: 
        second_brick = cfg.queen 
    elif (row_idx % 4 == 0):
        # remove head joint alignment in alternate stretcher courses
        second_brick = cfg.half
    else:
        second_brick = cfg.full
    course.append(second_brick["symbol"])

    # remaining wall, remove identical 4 bricks from start and end of row
    remaining_wall = cfg.wall_l - 2 * (first_brick['l'] + cfg.head + second_brick["l"]) - cfg.head - cfg.half["l"]
    
    # fill remaining wall header / stretcher
    remaining_brick = first_brick
    n_full = remaining_wall // (remaining_brick['l'] + cfg.head)
    course.extend([remaining_brick['symbol']]*n_full)

    # closing bricks, identical to first two
    course.extend([second_brick['symbol'], first_brick['symbol']])

    return course

def wild_bond_row(cfg, row):
    prev_course_x1 = []

    for row_idx in range(int(2)):
        row_idx += 1
        
        course = []
        built_x1 = []
        first_brick = cfg.full if (row_idx % 2 == 0) else cfg.half
        
        course.append(first_brick['symbol'])
        built_x1.append(first_brick['l'])

        remaining_wall = cfg.wall_l - (first_brick['l'] + cfg.head)
        consec_full = 1 if first_brick is cfg.full else 0

        while remaining_wall > (cfg.full["l"] + cfg.head):
            placed = False
            full_cap = random.randint(1, 6)
            
            if consec_full < full_cap:
                next_x2_full = built_x1[-1] + cfg.head + cfg.full["l"]
                if (next_x2_full not in prev_course_x1) and (remaining_wall >= (cfg.full["l"] + cfg.head)):
                    course.append(cfg.full["symbol"])
                    built_x1.append(next_x2_full)
                    remaining_wall -= (built_x1[-1] - built_x1[-2])
                    consec_full += 1
                    placed = True

            
            if not placed and course[-1] != cfg.half["symbol"]:
                next_x2_half = built_x1[-1] + cfg.head + cfg.half["l"]
                if (next_x2_half not in prev_course_x1) and (remaining_wall >= (cfg.half["l"] + cfg.head)):
                    course.append(cfg.half["symbol"])
                    built_x1.append(next_x2_half)
                    remaining_wall -= (built_x1[-1] - built_x1[-2])
                    consec_full = 0
                    placed = True

            if not placed:
                continue

        print(course)
        
        prev_course_x1 = built_x1
  
    return course
    
    