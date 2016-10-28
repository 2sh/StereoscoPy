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
		crop(images[0], (x_right, y_down, x_left, y_up)),
		crop(images[1], (x_left, y_up, x_right, y_down))]

def crop(image, box):
	left, top, right, bottom = box
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

def create_side_by_side_image(images, horizontal=True, divider=0, border=0, bg_color=(255, 255, 255, 0)):
	if horizontal:
		width = images[0].size[0] * 2 + divider
		height = images[0].size[1]
		r_left = images[0].size[0] + divider
		r_top = 0
	else:
		width = images[0].size[0]
		height = images[0].size[1] * 2 + divider
		r_left = 0
		r_top = images[0].size[1] + divider
	
	width += 2 * border
	height += 2 * border
	r_left += border
	r_top += border
	
	output = Image.new("RGBA", (width, height), bg_color)
	output.paste(images[0], (border, border))
	output.paste(images[1], (r_left, r_top))
	return output

AG_LUMA_CODING_RGB = (1/3, 1/3, 1/3)
AG_LUMA_CODING_REC601 = (0.299, 0.587, 0.114)
AG_LUMA_CODING_REC709 = (0.2126, 0.7152, 0.0722)

_AG_COLOR_SCHEMES = {
	"red-green": (
		(1, 0, 0), (0, 1, 0)),
	"red-blue": (
		(1, 0, 0), (0, 0, 1)),
	"red-cyan": (
		(1, 0, 0), (0, 1, 1)),
	"green-magenta": (
		(0, 1, 0), (1, 0, 1)),
	"amber-blue": (
		(1, 1, 0), (0, 0, 1)),
	"magenta-cyan": (
		(1, 0, 1), (0, 1, 1))
}

_AG_METHODS = {
	"gray":
		("lum", "lum"),
	"color":
		("rgb", "rgb"),
	"half-color":
		("lum", "rgb"),
	"optimized": # wimmer
		("opt", "rgb")
}

_AG_COLOR_MATRICES = {
	"rgb": (
		(1, 0, 0),
		(0, 1, 0),
		(0, 0, 1)
	),
	"opt": (
		(0, 0.7, 0.3),
		(0.5, 0, 0.5), # ?
		(0.5, 0.5, 0) # ?
	)
}

_AG_DUBOIS = {
	"red-cyan": (
		((0.456, 0.500, 0.175), (-0.040, -0.038, -0.016), (-0.015, -0.021, -0.005)),
		((-0.043, -0.088, -0.002), (0.378, 0.734, -0.018), (-0.072, -0.113, 1.226))),
	"green-magenta": (
		((-0.062, -0.158, -0.039), (0.284, 0.668, 0.143), (-0.015, -0.027, 0.021)),
		((0.529, 0.705, 0.024), (-0.016, -0.015, -0.065), (0.009, 0.075, 0.937))),
	"amber-blue": (
		((1.062, -0.205, 0.299), (-0.026, 0.908, 0.068), (-0.038, -0.173, 0.022)),
		((-0.016, -0.123, -0.017), (0.006, 0.062, -0.017), (0.094, 0.185, 0.911)))
}

def create_anaglyph(images, method="optimized", color_scheme="red-cyan", luma_coding=AG_LUMA_CODING_RGB):
	if method == "dubois":
		try:
			matrices = _AG_DUBOIS[color_scheme]
		except:
			raise Exception("No Dubois matrices available for the specified color scheme")
	else:
		if isinstance(color_scheme, str):
			colors = _AG_COLOR_SCHEMES[color_scheme]
		matrices = []
		for matrix_name, color in zip(_AG_METHODS[method], colors):
			matrix = []
			if matrix_name == "lum":
				color_matrix = (luma_coding,)*3
			else:
				color_matrix = _AG_COLOR_MATRICES[matrix_name]
			for color_band, intensity in zip(color_matrix, color):
				matrix.append((
					color_band[0] * intensity,
					color_band[1] * intensity,
					color_band[2] * intensity))
			matrices.append(tuple(matrix))
	
	left_bands = images[0].split()
	right_bands = images[1].split()
	output_bands = list()
	for i in range(3):
		expression = (
			"(float(lr)*{lm[0]}+float(lg)*{lm[1]}+float(lb)*{lm[2]}+" +
			 "float(rr)*{rm[0]}+float(rg)*{rm[1]}+float(rb)*{rm[2]})"
			).format(lm=matrices[0][i], rm=matrices[1][i])
		
		if method == "optimized" and colors[0][i]:
			expression = "((" + expression + "/255)**(1/" + str(1 + (0.5 * colors[0][i])) + "))*255"
		
		output_bands.append(ImageMath.eval("convert(" + expression + ", 'L')",
			lr=left_bands[0], lg=left_bands[1], lb=left_bands[2],
			rr=right_bands[0], rg=right_bands[1], rb=right_bands[2]))
	
	if len(left_bands) > 3 and len(right_bands) > 3:
		output_bands.append(ImageChops.lighter(left_bands[3], right_bands[3]))
		return Image.merge("RGBA", output_bands)
	return Image.merge("RGB", output_bands)

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

def save_as_wiggle_gif_image(output_file, images, total_duration=200):
	images[0].save(output_file, format="gif", save_all=True, loop=0, duration=round(total_duration/len(images)), append_images=images[1:])

def main():
	import sys
	import argparse
	
	parser = argparse.ArgumentParser(description="Convert 2 images into a stereoscopic 3D image", usage="%(prog)s [OPTION]... LEFT RIGHT [OUT] [OUT2]")
	
	parser.add_argument("image_left",
		metavar="LEFT", type=str,
		help="left input image")
	parser.add_argument("image_right",
		metavar="RIGHT", type=str,
		help="right input image.")
	parser.add_argument("image_output",
		metavar="OUT", type=str, nargs='?',
		help="output file. If left omitted, output to STDOUT, in which case the output format is required.")
	parser.add_argument("image_output2",
		metavar="OUT2", type=str, nargs='?',
		help="output an optional second image for split left and right")
	
	parser.add_argument("-Q", "--quality",
		dest='quality', metavar="VALUE", type=int, default="95",
		help="set the output image quality: 1-100 [default: %(default)s]")
	parser.add_argument("-F", "--format",
		dest='format', metavar="FORMAT", type=str,
		help="set the output image format: JPG, PNG, GIF,... If left omitted, the format to use is determined from the filename extension.")
	parser.add_argument("-B", "--bg-color",
		dest='bg_color', type=int,
		nargs=4, metavar=("RED", "GREEN", "BLUE", "ALPHA"), default=(255, 255, 255, 0),
		help="set the background color and transparency (alpha): 0-255 each [default: 255, 255, 255, 0]. The default is white for JPEG and transparent for PNG. This is also the color for the divider and border.")
	
	group = parser.add_argument_group('Side-by-side')
	group.add_argument("-x", "--cross-eye",
		dest='cross_eye', action='store_true',
		help="output an image for cross-eyed viewing, right/left")
	group.add_argument("-p", "--parallel",
		dest='parallel',  action='store_true',
		help="output an image for parallel viewing, left/right")
	group.add_argument("-o", "--over-under",
		dest='over_under', action='store_true',
		help="output an over/under image, left is over")
	group.add_argument("-u", "--under-over",
		dest='under_over', action='store_true',
		help="output an under/over image, left is under")
	
	group.add_argument("-s", "--squash",
		dest='squash', action='store_true',
		help="squash the sides to be half their width (cross-eye, parallel) or height (over/under, under/over)")
	group.add_argument("-d", "--divider",
		dest='divider', metavar="WIDTH", type=int, default=0,
		help="separate the two sides with a divider of a given width")
	group.add_argument("-b", "--border",
		dest='border', metavar="WIDTH", type=int, default=0,
		help="surround the output image with a border of a given width")
	
	group = parser.add_argument_group('Encoded')
	group.add_argument("-a", "--anaglyph",
		dest='anaglyph', type=str, nargs='?', metavar="METHOD", const="optimized",
		help="output an anaglyph image: gray, color, half-color, optimized, dubois [default: %(const)s]. The dubois method is only available with the red-cyan, green-magenta and amber-blue color schemes.")
	group.add_argument("--cs", "--color-scheme",
		dest='color_scheme', metavar="SCHEME", type=str, default="red-cyan",
		help="set the anaglyph color scheme: red-green, red-blue, red-cyan, green-magenta, amber-blue, magenta-cyan [default: %(default)s]. The non-complementary colors are mainly to be used with the gray method.")
	group.add_argument("--lc", "--luma-coding",
		dest='luma_coding', metavar="CODING", type=str, default="rec709",
		help="set the luma coding for the gray and half-color methods: rgb, rec601 (PAL/NTSC), rec709 (HDTV) [default: %(default)s]")
	
	group = parser.add_argument_group('Animated')
	group.add_argument("-w", "--wiggle",
		dest='wiggle', type=int, nargs='?', metavar="DURATION", const=200,
		help="output a wiggle GIF image with total duration in milliseconds [default: %(const)s]")
	
	group = parser.add_argument_group('Patterened')
	group.add_argument("-i", "--interlaced-h",
		dest='interlaced_horizontal', type=str, nargs='?', metavar="EVEN/ODD", const="even",
		help="output a horizontally interlaced image with the left image being either the even or odd line [default: %(const)s]")
	group.add_argument("-v", "--interlaced-v",
		dest='interlaced_vertical', type=str, nargs='?', metavar="EVEN/ODD", const="even",
		help="outout a vertically interlaced image with the left image being either the even or odd line [default: %(const)s]")
	group.add_argument("-c", "--checkerboard",
		dest='checkerboard', type=str, nargs='?', metavar="EVEN/ODD", const="even",
		help="output a checkerboard patterned image with the left image being either the even or odd square [default: %(const)s]")
	
	group = parser.add_argument_group('Preprocessing')
	group.add_argument("-A", "--align",
		dest='align', type=int,
		nargs=2, metavar=("X", "Y"), default=(0, 0),
		help="align the right image in relation to the left image")
	
	group.add_argument("-C", "--crop",
		dest='crop', type=str,
		nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"), default=(0, 0, 0, 0),
		help="crop both images in either pixels or percentage")
	
	group.add_argument("-R", "--resize",
		dest='resize', type=int,
		nargs=2, metavar=("WIDTH", "HEIGHT"), default=(0, 0),
		help="resize both images to WIDTHxHEIGHT. A value of 0 is calculated automatically to preserve the aspect ratio.")
	group.add_argument("-O", "--offset",
		dest='offset', type=str, default="50%",
		help="set the resize offset from top or left in either pixels or percentage [default: %(default)s]")
	
	args = parser.parse_args()
	
	if args.image_output:
		image_output = args.image_output
	else:
		if args.format is None:
			print("Either specify the output file name or the format to be used for outputting to STDOUT.", file=sys.stderr)
			exit()
		image_output = sys.stdout.buffer
	
	images = [Image.open(args.image_left), Image.open(args.image_right)]
	
	for i, _ in enumerate(images):
		images[i] = fix_orientation(images[i])
		
		if images[i].mode != "RGB" or images[i].mode != "RGBA":
			images[i] = images[i].convert("RGBA")
		
		if i > 0 and images[0].size != images[i].size:
			print("Given images are not the same size!", file=sys.stderr)
			exit()
	
	if any(args.align):
		images = align(images, args.align)
	
	for i, _ in enumerate(images):
		if any(args.crop):
			images[i] = crop(images[i], args.crop)
		
		if any(args.resize):
			images[i] = resize(images[i], args.resize, args.offset)
	
	if args.anaglyph:
		if args.luma_coding == "rgb":
			luma_coding = AG_LUMA_CODING_RGB
		elif args.luma_coding == "rec601":
			luma_coding = AG_LUMA_CODING_REC601
		elif args.luma_coding == "rec709":
			luma_coding = AG_LUMA_CODING_REC709
		output = create_anaglyph(images, args.anaglyph, args.color_scheme, luma_coding)
	elif args.wiggle:
		save_as_wiggle_gif_image(image_output, images, args.wiggle)
		return
	elif args.interlaced_horizontal:
		output = create_interweaved_image(images, 1, args.interlaced_horizontal!="odd")
	elif args.interlaced_vertical:
		output = create_patterened_image(images, 2, args.interlaced_vertical!="odd")
	elif args.checkerboard:
		output = create_patterened_image(images, 0, args.checkerboard!="odd")
	else:
		if not (args.cross_eye or args.parallel or
			args.over_under or args.under_over):
			args.cross_eye = True
		
		is_horizontal = args.cross_eye or args.parallel
		
		if args.squash:
			for i, _ in enumerate(images):
				images[i] = squash(images[i], is_horizontal)
		
		if args.cross_eye or args.under_over:
			images.reverse()
		
		if args.image_output2 is None:
			output = create_side_by_side_image(images, is_horizontal, args.divider, args.border, args.bg_color)
		else:
			images[0].save(args.image_output, format=args.format, quality=args.quality, optimize=True)
			images[1].save(args.image_output2, format=args.format, quality=args.quality, optimize=True)
			return
	output.save(image_output, format=args.format, quality=args.quality, optimize=True)

if __name__ == '__main__':
	main()
