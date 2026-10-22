# Packed playback regression

Run `res://tests/packed_playback_test.tscn` with the rebuilt extension.
Also export it as the main scene and run the package on Android or iOS;
an editor-only run does not exercise resource loading from a packed file.
Include `*.json` in the export preset's non-resource file filter.

The fixture embeds a blue PNG that stays transparent until frame 15.
The test calls `play()` without seeking or rendering a static frame, then
checks both frame progression and the rendered center pixel. It prints
`PACKED_PLAYBACK_TEST PASS` or `FAIL`, writes
`user://packed-playback-test.png`, and exits with status 0 or 1.
