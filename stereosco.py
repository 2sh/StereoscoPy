#!/usr/bin/env python3
#
#	Stereosco.py, stereoscopic 3D image creator
#	Copyright (C) 2016 Sean Hewitt <contact@SeanHewitt.com>
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from PIL import Image, ImageChops, ImageMath
from collections import OrderedDict

def to_pixels(value, reference):
	try:
		if value.endswith("%"):
			return round((int(value[:-1])/100)*reference)
	except:
		pass
	return int(value)

def fix_orientation(image):
	try:
		orientation = image._getexif()[274]
	except:
		return image
	
	if orientation == 3:
		return image.rotate(180, expand=True)
	elif orientation == 6:
		return image.rotate(270, expand=True)
	elif orientation == 8:
		return image.rotate(90, expand=True)
	else:
		return image

def align(images, xy):
	x, y = xy
	x_right = abs(x) if x>0 else 0
	x_left = abs(x) if x<0 else 0
	y_up = abs(y) if y>0 else 0
	y_down = abs(y) if y<0 else 0
	
	return [
		crop(images[0], (y_down, x_left, y_up, x_right)),
		crop(images[1], (y_up, x_right, y_down, x_left))]
	
def crop(image, trbl):
	top, right, bottom, left = trbl
	return image.crop((
		to_pixels(left, image.size[1]),
		to_pixels(top, image.size[0]),
		image.size[0]-to_pixels(right, image.size[1]),
		image.size[1]-to_pixels(bottom, image.size[0])))

def resize(image, size, offset="50%"):
	width_ratio = size[0]/image.size[0]
	height_ratio = size[1]/image.size[1]
	
	offset_crop = None
	if width_ratio > height_ratio:
		re_size = (size[0], round(image.size[1] * width_ratio))
		if size[1]:
			offset = to_pixels(offset, re_size[1]-size[1])
			offset_crop = (0, offset, size[0], size[1]+offset)
	elif width_ratio < height_ratio:
		re_size = (round(image.size[0] * height_ratio), size[1])
		if size[0]:
			offset = to_pixels(offset, re_size[0]-size[0])
			offset_crop = (offset, 0, size[0]+offset, size[1])
	else:
		re_size = (size[0], size[1])
	
	image = image.resize(re_size, Image.ANTIALIAS)
	if offset_crop:
		image = image.crop(offset_crop)
	return image

def squash(image, horizontal=True):
	if horizontal:
		new_size = (round(image.size[0]/2), image.size[1])
	else:
		new_size = (image.size[0], round(image.size[1]/2))
	return image.resize(new_size, Image.ANTIALIAS)

def join(images, horizontal=True):
	if horizontal:
		size = (images[0].size[0]*2, images[0].size[1])
		pos = (images[0].size[0], 0)
	else:
		size = (images[0].size[0], images[0].size[1]*2)
		pos = (0, images[0].size[1])
	
	output = Image.new("RGBA", size)
	output.paste(images[0], (0, 0))
	output.paste(images[1], pos)
	return output

def create_anaglyph(images, matrices):
	left_bands = images[0].split()
	right_bands = images[1].split()
	
	output_bands = list()
	for i in range(0, 9, 3):
		output_bands.append(ImageMath.eval(("convert(" +
			"(float(lr)*{0[0]})+(float(lg)*{0[1]})+(float(lb)*{0[2]})+" +
			"(float(rr)*{1[0]})+(float(rg)*{1[1]})+(float(rb)*{1[2]}), 'L')")
				.format(matrices[0][i:i+3], matrices[1][i:i+3]),
			lr=left_bands[0], lg=left_bands[1], lb=left_bands[2],
			rr=right_bands[0], rg=right_bands[1], rb=right_bands[2]))
	
	if len(left_bands) > 3 and len(right_bands) > 3:
		output_bands.append(ImageChops.lighter(left_bands[3], right_bands[3]))
		return Image.merge("RGBA", output_bands)
	return Image.merge("RGB", output_bands)

ANAGLYPH_MATRICES = OrderedDict([
	("true", (
		(0.299, 0.587, 0.114,  0, 0, 0,  0, 0, 0),
		(0, 0, 0,  0, 0, 0,  0.299, 0.587, 0.114))),
	("gray", (
		(0.299, 0.587, 0.114,  0, 0, 0,  0, 0, 0),
		(0, 0, 0,  0.299, 0.587, 0.114,  0.299, 0.587, 0.114))),
	("color", (
		(1, 0, 0,  0, 0, 0,  0, 0, 0),
		(0, 0, 0,  0, 1, 0,  0, 0, 1))),
	("half-color", (
		(0.299, 0.587, 0.114,  0, 0, 0,  0, 0, 0),
		(0, 0, 0,  0, 1, 0,  0, 0, 1))),
	("optimized", (
		(0, 0.7, 0.3,  0, 0, 0,  0, 0, 0),
		(0, 0, 0,  0, 1, 0,  0, 0, 1))),
	("dubois-red-cyan", (
		(0.456, 0.500, 0.175,  -0.040, -0.038, -0.016,  -0.015, -0.021, -0.005),
		(-0.043, -0.088, -0.002,  0.378, 0.734, -0.018,  -0.072, -0.113, 1.226))),
	("dubois-red-cyan2", (
		(0.437, 0.449, 0.164,  -0.062, -0.062, -0.024,  -0.048, -0.050, -0.017),
		(-0.011, -0.032, -0.007,  0.377, 0.761, 0.009,  -0.026, -0.093, 1.234))),
	("dubois-green-magenta", (
		(-0.062, -0.158, -0.039,  0.284, 0.668, 0.143,  -0.015, -0.027, 0.021),
		(0.529, 0.705, 0.024,  -0.016, -0.015, -0.065,  0.009, 0.075, 0.937))),
	("dubois-amber-blue", (
		(1.062, -0.205, 0.299,  -0.026, 0.908, 0.068,  -0.038, -0.173, 0.022),
		(-0.016, -0.123, -0.017,  0.006, 0.062, -0.017,  0.094, 0.185, 0.911)))
])

def save_as_wiggle_gif_image(output_file, images, total_duration=200):
	images[0].save(output_file, save_all=True, loop=0, duration=round(total_duration/len(images)), append_images=images[1:])

def create_patterened_image(images, pattern=1, left_is_even=True):
	output = images[0].copy()
	o = output.load()
	r = images[1].load()
	
	for x in range(output.size[0]):
		for y in range(output.size[1]):
			if pattern == 0:
				if (x + y) % 2 != left_is_even:
					o[x,y] = r[x,y]
			elif pattern == 1:
				if y % 2 != left_is_even:
					o[x,y] = r[x,y]
			elif pattern == 2:
				if x % 2 != left_is_even:
					o[x,y] = r[x,y]
	return output


def main():
	import argparse
	parser = argparse.ArgumentParser(description="Convert 2 images into a stereoscopic 3D image")

	parser.add_argument("image_left",
		metavar="LEFT", type=str, help="left image")
	parser.add_argument("image_right",
		metavar="RIGHT", type=str, help="right image")
	parser.add_argument("image_output",
		metavar="OUT", type=str, help="output image")
	parser.add_argument("image_output2",
		metavar="OUT2", nargs='?', type=str,
		help="optional second output image for split left and right")
	
	group = parser.add_argument_group('Side-by-side')
	group.add_argument("-X", "--cross-eye",
		dest='is_cross_eye', action='store_true',
		help="cross-eye output: Right/Left")
	group.add_argument("-P", "--parallel",
		dest='is_parallel',  action='store_true',
		help="Parallel output: Left/Right")
	group.add_argument("-O", "--over-under",
		dest='is_over_under', action='store_true',
		help="Over/under output: Left is over and right is under")
	group.add_argument("-U", "--under-over",
		dest='is_under_over', action='store_true',
		help="Under/Over output: Left is under and right is over")
	
	group.add_argument("-S", "--squash",
		dest='is_squash', action='store_true',
		help="Squash the two sides to make an image of size equal to that of the sides")
	
	group = parser.add_argument_group('Encoded')
	group.add_argument("-A", "--anaglyph",
		dest='anaglyph', nargs="?", type=str, metavar="METHOD", const="dubois-red-cyan", 
		help="Anaglyph output with a choice of the following methods: " +
			", ".join(ANAGLYPH_MATRICES.keys()) + " (default method: %(const)s)")
	
	group = parser.add_argument_group('Animated')
	group.add_argument("-W", "--wiggle",
		dest='wiggle', nargs="?", type=int, metavar="DURATION", const=200, 
		help="Wiggle GIF image with total duration in milliseconds (default: %(const)s)")
	
	group = parser.add_argument_group('Patterened')
	group.add_argument("-I", "--interlaced-h",
		dest='interlaced_horizontal', nargs="?", type=str, metavar="EVEN/ODD", const="even",
		help="Horizontally interlaced output with the left image being either the even or odd line (default: %(const)s)")
	group.add_argument("-V", "--interlaced-v",
		dest='interlaced_vertical', nargs="?", type=str, metavar="EVEN/ODD", const="even",
		help="Vertically interlaced output with the left image being either the even or odd line (default: %(const)s)")
	group.add_argument("-C", "--checkerboard",
		dest='checkerboard', nargs="?", type=str, metavar="EVEN/ODD", const="even",
		help="Checkerboard output with the left image being either the even or odd square (default: %(const)s)")
	
	group = parser.add_argument_group('Preprocessing')
	
	group.add_argument("-a", "--align",
		dest='align', type=int,
		nargs=2, metavar=("X", "Y"), default=(0, 0),
		help="Align right image in relation to left image")
	
	group.add_argument("-c", "--crop",
		dest='crop', type=str,
		nargs=4, metavar=("TOP", "RIGHT", "BOTTOM", "LEFT"), default=(0, 0, 0, 0),
		help="Crop both images in either pixels or percentage")
	
	group.add_argument("-r", "--resize",
		dest='resize', type=int,
		nargs=2, metavar=("WIDTH", "HEIGHT"), default=(0, 0),
		help="Resize both images to WIDTHxHEIGHT: A side with 0 is calculated automatically to preserve aspect ratio")
	group.add_argument("-o", "--offset",
		dest='offset', type=str, default="50%",
		help="Resize offset from top or left in either pixels or percentage (default: %(default)s)")
	
	args = parser.parse_args()

	images = [Image.open(args.image_left), Image.open(args.image_right)]
	
	for i, _ in enumerate(images):
		images[i] = fix_orientation(images[i])
		
		if images[i].mode != "RGB" or images[i].mode != "RGBA":
			images[i] = images[i].convert("RGBA")
		
	if any(args.align):
		images = align(images, args.align)
		
	for i, _ in enumerate(images):
		if any(args.crop):
			images[i] = crop(images[i], args.crop)
		
		if any(args.resize):
			images[i] = resize(images[i], args.resize, args.offset)
	
	if args.anaglyph:
		output = create_anaglyph(images, ANAGLYPH_MATRICES[args.anaglyph])
		output.save(args.image_output)
	elif args.wiggle:
		save_as_wiggle_gif_image(args.image_output, images, args.wiggle)
	elif args.interlaced_horizontal:
		output = create_interweaved_image(images, 1, args.interlaced_horizontal!="odd")
		output.save(args.image_output)
	elif args.interlaced_vertical:
		output = create_patterened_image(images, 2, args.interlaced_vertical!="odd")
		output.save(args.image_output)
	elif args.checkerboard:
		output = create_patterened_image(images, 0, args.checkerboard!="odd")
		output.save(args.image_output)
	else:
		if not (args.is_cross_eye or args.is_parallel or
			args.is_over_under or args.is_under_over):
			args.is_cross_eye = True
			
		is_horizontal = args.is_cross_eye or args.is_parallel
		
		if args.is_squash:
			for i, _ in enumerate(images):
				images[0] = squash(images[0], is_horizontal)

		if args.is_cross_eye or args.is_under_over:
			images.reverse()

		if args.image_output2 is None:
			output = join(images, is_horizontal)
			output.save(args.image_output)
		else:
			images[0].save(args.image_output)
			images[1].save(args.image_output2)

if __name__ == '__main__':
	main()
