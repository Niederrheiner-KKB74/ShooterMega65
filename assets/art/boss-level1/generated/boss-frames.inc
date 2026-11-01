// Local indices and glyph bases. Choose/remap a boss bank before runtime import.
.const BOSS_BODY = 0
.const BOSS_CORE_EXPOSED = 1
.const BOSS_ROTOR_0 = 2
.const BOSS_ROTOR_1 = 3
.const BOSS_ROTOR_2 = 4
.const BOSS_TURRET_NW_SOUTH = 5
.const BOSS_TURRET_NW_SOUTHEAST = 6
.const BOSS_TURRET_NW_DESTROYED = 7
.const BOSS_TURRET_NE_SOUTH = 8
.const BOSS_TURRET_NE_SOUTHEAST = 9
.const BOSS_TURRET_NE_DESTROYED = 10
.const BOSS_TURRET_SW_SOUTH = 11
.const BOSS_TURRET_SW_SOUTHEAST = 12
.const BOSS_TURRET_SW_DESTROYED = 13
.const BOSS_TURRET_SE_SOUTH = 14
.const BOSS_TURRET_SE_SOUTHEAST = 15
.const BOSS_TURRET_SE_DESTROYED = 16
.const BOSS_MUZZLE_0 = 17
.const BOSS_MUZZLE_1 = 18
boss_base_lo: .byte 1,55,65,75,85,95,98,101,104,107,110,113,116,119,122,125,128,131,134
boss_base_hi: .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
boss_w: .byte 6,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1
boss_h: .byte 8,4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,2,2
