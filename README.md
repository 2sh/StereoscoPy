# Stereosco.py
This is a Python script/library for converting two images into a stereoscopic 3D image.
The stereoscopic output methods are currently anaglyph, side-by-side (cross-eye and parallel), over/under and wiggle GIF.

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
python3 stereosco.py DSC_0611.JPG DSC_0610.JPG --crop 20% 0 0 0 --resize 1920 1080 --offset 100% --cross-eye
python3 stereosco.py DSC_0611.JPG DSC_0610.JPG -c 20% 0 0 0 -r 1920 1080 -o 100% -X
```

###Squashed Parallel (Left/Right)
```
python3 stereosco.py DSC_0611.JPG DSC_0610.JPG -c 20% 0 0 0 -r 1920 1080 -o 100% -SP
```

###Anaglyph
```
python3 stereosco.py DSC_0596.JPG DSC_0597.JPG out.jpg -c 20% 40% 15% 40% -r 1920 1080 -A color
```

###Over/under (Left/Right)
20% cropped from left and right and resized to be 1400 wide, preserving the aspect ratio.
```
python3 stereosco.py DSC_5616.JPG DSC_5615.JPG out.jpg -r 1400 0 -c 0 20% 0 20% -O
```

###Wiggle GIF
Align the right image to be 5 to the left and 30 down, and set the wiggle duration to 200 milliseconds
```
python3 stereosco.py image_left.jpg image_right.jpg out.gif -r 800 0 -a -5 30 -W 200
```

###Two separate image outputs
Before converting to the stereoscopic outputs, I find this to be a quick way to check for the correct dimensions, and rotational angles and alignment by switching between the two output images in an image viewer.
```
python3 stereosco.py in_left.jpg in_right.jpg out_left.jpg out_right.jpg -a 19 30 --crop 20% 0 0 0 --resize 1920 1080 --offset 100% -P
```