// Optional import tables; not automatically included by Stage 2.
.const TANK_NORTH_0=0
.const TANK_NORTH_1=1
.const TANK_NORTH_2=2
.const TANK_NORTH_3=3
.const TANK_EAST_0=4
.const TANK_EAST_1=5
.const TANK_EAST_2=6
.const TANK_EAST_3=7
.const TANK_SOUTH_0=8
.const TANK_SOUTH_1=9
.const TANK_SOUTH_2=10
.const TANK_SOUTH_3=11
.const TANK_WEST_0=12
.const TANK_WEST_1=13
.const TANK_WEST_2=14
.const TANK_WEST_3=15
tank_frame_base: .byte 1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,46
tank_frame_w: .fill 16, 1
tank_frame_h: .fill 16, 2
tank_frame_pal: .fill 16, $4f
