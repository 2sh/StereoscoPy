# Stereosco.py
This is a Python script/library for converting two images into a stereoscopic 3D image: anaglyph, side-by-side (cross-eye and parallel), over/under, wiggle GIF, interlaced and checkerboard.

## Requirements
* Python3
* Pillow
* cv2 (optional for auto align)
* numpy (optional for auto align)

## Command-Line
### Help
```
python3 stereosco.py --help
```

### Cross-eyed (Right/Left)
With white 5px wide border and image division. Auto aligned, resized to be 450
pixels in width and shifted horizontally by 1 pixel.
```
python3 stereosco.py -A -R 400 0 -S 1 0 -x --div 5 --border 5 --bg 255 255 255 0 left.jpg right.jpg cross_eye.jpg
```
![alt text](/example_images/cross_eye.jpg?raw=true "Cross eyed")

### Anaglyph
For red-cyan glasses, there are various methods for creating anaglyphs available.
```
python3 stereosco.py -A -R 400 0 -S 1 0 -a left.jpg right.jpg anaglyph_wimmer.jpg
python3 stereosco.py -A -R 400 0 -S 1 0 -am dubois left.jpg right.jpg anaglyph_dubois.jpg
python3 stereosco.py -A -R 400 0 -S 1 0 -am gray left.jpg right.jpg anaglyph_gray.jpg
python3 stereosco.py -A -R 400 0 -S 1 0 -am color left.jpg right.jpg anaglyph_color.jpg
python3 stereosco.py -A -R 400 0 -S 1 0 -am half-color left.jpg right.jpg anaglyph_half_color.jpg
```
![alt text](/example_images/anaglyph_wimmer.jpg?raw=true "Wimmer Anaglyph") ![alt text](/example_images/anaglyph_dubois.jpg?raw=true "Dubois Anaglyph")
![alt text](/example_images/anaglyph_gray.jpg?raw=true "Gray Anaglyph") ![alt text](/example_images/anaglyph_color.jpg?raw=true "Color Anaglyph")
![alt text](/example_images/anaglyph_half_color.jpg?raw=true "Half-Color Anaglyph")

The Dubois anaglyph method for amber-blue glasses.
```
python3 stereosco.py -am dubois --cs amber-blue left.jpg right.jpg anaglyph_dubois_ab.jpg
```

### Wiggle GIF
Without alignment
```
python3 stereosco.py -R 400 0 -wt 400 left.jpg right.jpg simple.gif
```
![alt text](/example_images/simple.gif?raw=true "Simple")

Shifting an image moves the right image in relation to the left image. An images can be shifted after the auto align to change its center.
```
python3 stereosco.py -A -R 400 0 -S 1 0 -wt 200 left.jpg right.jpg align_shift.gif
```
![alt text](/example_images/align_shift.gif?raw=true "Aligned and shifted")

### Squashed Parallel (Left/Right) and Top/Bottom for TVs
```
python3 stereosco.py -A -R 400 0 -S 1 0 -ps left.jpg right.jpg tv_left_right.jpg
python3 stereosco.py -A -R 400 0 -S 1 0 -os left.jpg right.jpg tv_over_under.jpg
```
![alt text](/example_images/tv_left_right.jpg?raw=true "Top/Bottom") ![alt text](/example_images/tv_over_under.jpg?raw=true "Left/Right")

### Two separate image outputs
Before converting to the stereoscopic outputs, I find this (or a slow wiggle GIF) to be a nice way to check for the correct dimensions, shift and rotation by switching between the two output images in an image viewer.
```
python3 stereosco.py --shift 19 30 --crop 20% 0 0 0 --resize 1920 1080 --offset 100% --parallel left.jpg right.jpg out1.jpg out2.jpg
```

### Misc
20% cropped from the top, resized to 1920x1080 and offset to the right by 100%.
```
python3 stereosco.py --crop 20% 0 0 0 --resize 1920 1080 --offset 100% --cross-eye left.jpg right.jpg out.jpg
python3 stereosco.py -C 20% 0 0 0 -R 1920 1080 -O 100% -x left.jpg right.jpg out.jpg
```

20% cropped from left and right and resized to be 1080 high and 0 width to preserve the aspect ratio.
```
python3 stereosco.py -R 0 1080 -C 0 20% 0 20% -o left.jpg right.jpg out.jpg
```
