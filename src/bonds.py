from src.config import WallConfig

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

# def wild_bond_row(cfg, row_idx):
#     row_idx += 1
    
#     course = []

#     # alternate half / full first bricks
#     if (row_idx % 2 != 0) and (row_idx % 3 != 0):
#         first_brick = cfg.full
#     elif row_idx % 2 == 0:
#         first_brick = cfg.half
#     else:
#         first_brick = cfg.full 
    
#     course.append(first_brick['symbol'])

#     remaining_wall = cfg.wall_l - (first_brick['l'] + cfg.head)

#     while remaining_wall > 0:
#         # lay a row of full bricks
#         n_full = min(6, remaining_wall // (cfg.full['l'] + cfg.head))
#         course.extend([cfg.full['symbol']]*n_full)
    