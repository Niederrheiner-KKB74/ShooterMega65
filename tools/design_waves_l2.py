#!/usr/bin/env python3
"""Stage 9: enemy waves of level 2 (levels/level2.json, canyon and refinery, map by ChatGPT, PR #17).

Same flight paths and formations as level 1 (tools/design_waves_l1.py), in a new order and denser: the player
arrives with the upgrades of level 1. The map, the shops, the boss and the level end stay as they are.

    python3 tools/design_waves_l2.py            # rewrites levels/level2.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_waves_l1 as w1  # noqa: E402

LEVEL = w1.ROOT / 'levels/level2.json'

# (row, [(formation, mirror, x or None), ...]); quiet before the shops (188, 368) and the boss (358)
WAVES = [
    (14, [('side6', False, None), ('side6', True, None)]),
    (22, [('snake8', False, None)]),
    (30, [('cross4', False, None), ('cross4', True, None)]),
    (38, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (46, [('loop6', False, None), ('loop6', True, None)]),
    (54, [('hover4', False, None)]),
    (61, [('strafe5', False, None), ('strafe5', True, None)]),
    (69, [('stop3', False, None)]),
    (77, [('uturn6', False, None), ('uturn6', True, None)]),
    (85, [('ring5', False, None)]),
    # canyon (96-183): planes along the river, helicopters over the banks
    (94, [('zigzag6', False, None), ('zigzag6', True, None)]),
    (102, [('hover4', False, None), ('hover4', True, None)]),
    (110, [('swoop8', False, None)]),
    (117, [('sweep3', False, None), ('weave4', True, None)]),
    (125, [('side6', True, None)]),
    (132, [('v_lead', False, 60), ('v_wing', False, 28), ('v_lead', True, 60), ('v_wing', True, 28)]),
    (140, [('ring5', False, None), ('ring5', True, None)]),
    (148, [('loop6', False, None)]),
    (155, [('cross4', True, None), ('strafe5', False, None)]),
    (163, [('stop3', False, None), ('stop3', True, None)]),
    (171, [('snake8', True, None)]),
    # mid shop at row 188
    (198, [('swoop6', False, None), ('swoop6', True, None)]),
    (206, [('uturn6', False, None)]),
    (213, [('hover4', False, None), ('hover4', True, None)]),
    (221, [('weave4', False, None), ('weave4', True, None)]),
    (229, [('side6', False, None), ('strafe5', True, None)]),
    (237, [('sweep3', False, None), ('sweep3', True, None)]),
    (245, [('zigzag6', False, None), ('zigzag6', True, None)]),
    (253, [('ring5', True, None)]),
    (260, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (268, [('loop6', False, None), ('loop6', True, None)]),
    (276, [('stop3', False, None), ('cross4', True, None)]),
    # refinery (280-374)
    (284, [('snake8', False, None)]),
    (291, [('hover4', False, None), ('hover4', True, None)]),
    (299, [('uturn6', False, None), ('uturn6', True, None)]),
    (307, [('sweep3', True, None), ('strafe5', False, None)]),
    (315, [('side6', False, None), ('side6', True, None)]),
    (323, [('ring5', False, None), ('weave4', True, None)]),
    (331, [('swoop6', False, None), ('swoop6', True, None)]),
    (339, [('stop3', False, None), ('stop3', True, None)]),
    (346, [('zigzag6', False, None)]),
    # boss at row 358
]

TANK_ROWS = [20, 34, 50, 64, 80, 98, 108, 120, 134, 146, 160, 172, 200, 212, 226, 240, 252, 266, 278, 290,
             302, 314, 328, 342]

GUN_ROWS = [(26, 'flak'), (58, 'flak'), (88, 'heavy_flak'), (106, 'flak'), (122, 'flak'), (138, 'heavy_flak'),
            (152, 'flak'), (168, 'flak'), (202, 'flak'), (218, 'heavy_flak'), (232, 'flak'), (248, 'flak'),
            (262, 'heavy_flak'), (286, 'flak'), (296, 'heavy_flak'), (310, 'flak'), (320, 'flak'),
            (330, 'heavy_flak'), (340, 'flak'), (348, 'heavy_flak')]


if __name__ == '__main__':
    w1.design(LEVEL, WAVES, TANK_ROWS, GUN_ROWS)
