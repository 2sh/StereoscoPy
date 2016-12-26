# Stereosco.py
This is a Python script/library for converting two images into a stereoscopic 3D image: anaglyph, side-by-side (cross-eye and parallel), over/under, wiggle GIF, interlaced and checkerboard.

##Requirements
* Python3
* Pillow

##Command-Line
###Help
```
python3 stereosco.py --help
```

###Cross-eyed (Right/Left)
20% cropped from the top, resized to 1920x1080 and offset to the right by 100%.
```
python3 stereosco.py --crop 20% 0 0 0 --resize 1920 1080 --offset 100% --cross-eye left.jpg right.jpg out.jpg
python3 stereosco.py -C 20% 0 0 0 -R 1920 1080 -O 100% -x left.jpg right.jpg out.jpg
```

###Squashed Parallel (Left/Right)
```
python3 stereosco.py -R 1920 1080 -sp left.jpg right.jpg out.jpg
```

###Anaglyph
```
python3 stereosco.py -a left.jpg right.jpg out.jpg
```

Dubois anaglyph method for amber-blue glasses
```
python3 stereosco.py -am dubois --cs amber-blue left.jpg right.jpg out.jpg
```

###Over/under (Left/Right)
20% cropped from left and right and resized to be 1080 high, preserving the aspect ratio.
```
python3 stereosco.py -R 0 1080 -C 0 20% 0 20% -o left.jpg right.jpg out.jpg
```

###Wiggle GIF
Shift the right image to be 5 to the left and 30 down, and set the wiggle duration to 400 milliseconds
```
python3 stereosco.py -R 800 0 -S -5 30 -wt 400 left.jpg right.jpg out.gif
```

###Two separate image outputs
Before converting to the stereoscopic outputs, I find this (or a slow wiggle GIF) to be a nice way to check for the correct dimensions, shift and rotation by switching between the two output images in an image viewer.
```
python3 stereosco.py --shift 19 30 --crop 20% 0 0 0 --resize 1920 1080 --offset 100% --parallel left.jpg right.jpg out1.jpg out2.jpg
```
