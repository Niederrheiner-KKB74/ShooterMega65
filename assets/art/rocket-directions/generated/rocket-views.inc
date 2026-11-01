// Static views, NOT animation frames. Local bases. Source palette indices!
// Runtime import must remap colours using merge_bank(), then relocate glyph bases.
rocket_view_base: .byte 1,4
rocket_view_w: .byte 1,1
rocket_view_h: .byte 2,2
rocket_view_pal: .byte $df,$df
