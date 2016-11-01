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
	"""Convert a percentage to pixels.
	
	Args:
		value: The value of either pixels or percentage ending with a
			percentage sign.
		reference: The value of 100%
	
	Returns:
		The pixel value.
	"""
	try:
		if value.endswith("%"):
			return round((int(value[:-1])/100)*reference)
	except:
		pass
	return int(value)

def fix_orientation(image):
	"""Fix the orientation of an image using its exif data.
	
	Args:
		image: A PIL image.
		
	Returns:
		The reorientated PIL image.
	"""
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

def rotate(images, rotations, fill_color = (255, 255, 255, 0)):
	"""Rotate multiple images, keeping all of their sizes the same.
	
	Args:
		images: Multiple PIL images.
		rotations: The rotation degrees of each image.
		fill_color: The color surrounding the images.
	
	Returns:
		The rotated PIL images.
	"""
	images = list(images)
	width = 0
	height = 0
	for i in range(len(images)):
		if rotations[i]:
			images[i] = images[i].rotate(rotations[i], Image.BICUBIC, True)
			width = max(images[i].width, width)
			height = max(images[i].height, height)
	for i in range(len(images)):
		left = round((width-images[i].width)/2)
		top = round((height-images[i].height)/2)
		image = Image.new("RGBA", (width, height), fill_color)
		image.paste(images[i], (left, top),	images[i])
		images[i] = image
	return images

def align(images, xy):
	"""Align the second image to the first image.
	
	Args:
		images: Two PIL images.
		xy: The horizontal and vertical movement of the second image.
		
	Returns:
		The aligned PIL images.
	"""
	x, y = xy
	x_right = abs(x) if x>0 else 0
	x_left = abs(x) if x<0 else 0
	y_up = abs(y) if y>0 else 0
	y_down = abs(y) if y<0 else 0
	
	return [
		crop(images[0], (x_right, y_down, x_left, y_up)),
		crop(images[1], (x_left, y_up, x_right, y_down))]

def crop(image, box):
	"""Crop an image.
	
	Args:
		image: A PIL image.
		box: The amount to crop off each side.
			The box side order is left, top, right, bottom.
	
	Return:
		The cropped PIL image.
	"""
	left, top, right, bottom = box
	return image.crop((
		to_pixels(left, image.height),
		to_pixels(top, image.width),
		image.width-to_pixels(right, image.height),
		image.height-to_pixels(bottom, image.width)))

def resize(image, size, offset = "50%"):
	"""Resize an image.
	
	A size value that is not larger than 0 is calculated automatically
	to preserve the aspect ratio.
	
	Args:
		image: A PIL image.
		size: The width and height.
		offset: The offset from the center.
	
	Returns:
		The resized PIL image.
	"""
	width_ratio = size[0]/image.width
	height_ratio = size[1]/image.height
	
	offset_crop = None
	if width_ratio > height_ratio:
		re_size = (size[0], round(image.height * width_ratio))
		if size[1]:
			offset = to_pixels(offset, re_size[1]-size[1])
			offset_crop = (0, offset, size[0], size[1]+offset)
	elif width_ratio < height_ratio:
		re_size = (round(image.width * height_ratio), size[1])
		if size[0]:
			offset = to_pixels(offset, re_size[0]-size[0])
			offset_crop = (offset, 0, size[0]+offset, size[1])
	else:
		re_size = (size[0], size[1])
	
	image = image.resize(re_size, Image.ANTIALIAS)
	if offset_crop:
		image = image.crop(offset_crop)
	return image

def squash(image, horizontal):
	"""Squash an image to be half its width or height.
	
	Args:
		image: A PIL image.
		horizontal: If to squash the image horizontal instead of vertical.
	
	Returns:
		The squashed PIL image.
	"""
	if horizontal:
		new_size = (round(image.width/2), image.height)
	else:
		new_size = (image.width, round(image.height/2))
	return image.resize(new_size, Image.ANTIALIAS)

def create_side_by_side_image(images, horizontal = True,
		divider_width = 0, divider_color = (255, 255, 255, 0)):
	"""Create a side-by-side image from two images.
	
	Args:
		images: Two PIL images.
		horizontal: If to join the images horizontal instead of vertical.
		divider_width: Width of a divider between the two joined images.
		divider_color: Color of the divider if set (R, G, B, A).
		
	Returns:
		The side-by-side PIL image.
	"""
	if horizontal:
		width = images[0].width * 2 + divider_width
		height = images[0].height
		r_left = images[0].width + divider_width
		r_top = 0
	else:
		width = images[0].width
		height = images[0].height * 2 + divider_width
		r_left = 0
		r_top = images[0].height + divider_width
	
	output = Image.new("RGBA", (width, height), divider_color)
	output.paste(images[0], (0, 0))
	output.paste(images[1], (r_left, r_top))
	return output


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
		(0.9, 1, 0), (0, 0, 0.7)),
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
	"wimmer":
		("wim", "rgb")
}

_AG_COLOR_MATRICES = {
	"rgb": (
		(1, 0, 0),
		(0, 1, 0),
		(0, 0, 1)
	),
	"wim": (
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

ANAGLYPH_LUMA_RGB = (1/3, 1/3, 1/3)
ANAGLYPH_LUMA_REC601 = (0.299, 0.587, 0.114)
ANAGLYPH_LUMA_REC709 = (0.2126, 0.7152, 0.0722)

def create_anaglyph(images, method = "wimmer",
		color_scheme = "red-cyan", luma_coding = ANAGLYPH_LUMA_REC709):
	"""Create an anaglyph image from two images.
	
	Args:
		images: Two PIL images.
		method: The anaglyph method.
			The available methods are gray, color, half-color,
			wimmer and dubois.
		color_scheme: The anaglyph color scheme.
			The non-complementary colors of the color schemes are mainly
			to be used with the gray method.
			The available color schemes are red-green, red-blue,
			red-cyan, green-magenta, amber-blue and magenta-cyan.
		luma_coding: The luma coding for the gray and half-color methods.
	
	Returns:
		The anaglyph PIL image.
	"""
	if method == "dubois":
		try:
			matrices = _AG_DUBOIS[color_scheme]
		except:
			raise Exception("No Dubois matrices available for the specified color scheme")
	else:
		if isinstance(color_scheme, str):
			colors = _AG_COLOR_SCHEMES[color_scheme]
			m = _AG_METHODS[method]
			method_reverse = sum(colors[0]) > sum(colors[1])
			if method_reverse:
				m = (m[1], m[0])
		matrices = []
		for matrix_name, color in zip(m, colors):
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
		
		if method == "wimmer" and colors[method_reverse][i]:
			expression = "((" + expression + "/255)**(1/" + str(1 + ([0.5, 0.2, 0.3][i] * colors[method_reverse][i])) + "))*255"
		
		output_bands.append(ImageMath.eval("convert(" + expression + ", 'L')",
			lr=left_bands[0], lg=left_bands[1], lb=left_bands[2],
			rr=right_bands[0], rg=right_bands[1], rb=right_bands[2]))
	
	if len(left_bands) > 3 and len(right_bands) > 3:
		output_bands.append(ImageChops.lighter(left_bands[3], right_bands[3]))
		return Image.merge("RGBA", output_bands)
	return Image.merge("RGB", output_bands)
	
def create_interlaced_h_image(images, left_is_even):
	"""Create an horizontally interlaced image from two images.
	
	Args:
		images: Two PIL images.
		left_is_even: Set the first image to be the even line/square.
	
	Returns:
		The horizontally interlaced PIL image.
	"""
	output = images[0].copy()
	o = output.load()
	r = images[1].load()
	
	for x in range(output.width):
		for y in range(output.height):
			if y % 2 != left_is_even:
				o[x,y] = r[x,y]
	return output
	
def create_interlaced_v_image(images, left_is_even):
	"""Create an vertically interlaced image from two images.
	
	Args:
		images: Two PIL images.
		left_is_even: Set the first image to be the even line/square.
	
	Returns:
		The vertically interlaced PIL image.
	"""
	output = images[0].copy()
	o = output.load()
	r = images[1].load()
	
	for x in range(output.width):
		for y in range(output.height):
			if x % 2 != left_is_even:
				o[x,y] = r[x,y]
	return output

def create_checkerboard_image(images, left_is_even):
	"""Create a checkerboard patterened image from two images.
	
	Args:
		images: Two PIL images.
		left_is_even: Set the first image to be the even line/square.
	
	Returns:
		The checkerboard patterened PIL image.
	"""
	output = images[0].copy()
	o = output.load()
	r = images[1].load()
	
	for x in range(output.width):
		for y in range(output.height):
			if (x + y) % 2 != left_is_even:
				o[x,y] = r[x,y]
	return output

def save_as_wiggle_gif_image(output_file, images, total_duration = 200):
	"""Save multiple images as a wiggle GIF image.
	
	Args:
		output_file: The file name of the output GIF.
		images: Multiple PIL images.
		total_duration: The total duration for all the images to be
			shown before looping.
	"""
	images[0].save(output_file, format="gif", save_all=True, loop=0, duration=round(total_duration/len(images)), append_images=images[1:])


def _main():
	import sys
	import argparse
	from PIL import ImageOps
	
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
	
	parser.add_argument("-q", "--quality",
		dest='quality', metavar="VALUE", type=int, default="95",
		help="set the output image quality: 1-100 [default: %(default)s]")
	parser.add_argument("-f", "--format",
		dest='format', metavar="FORMAT", type=str,
		help="set the output image format: JPG, PNG, GIF,... If left omitted, the format to use is determined from the filename extension.")
	parser.add_argument("--bg",
		dest='bg_color', type=int,
		nargs=4, metavar=("RED", "GREEN", "BLUE", "ALPHA"), default=(255, 255, 255, 0),
		help="set the background color and transparency (alpha): 0-255 each [default: 255, 255, 255, 0]. The default is white for JPEG and transparent for PNG. This is also the color for the divider and border.")
	parser.add_argument("--border",
		dest='border', metavar="WIDTH", type=int, default=0,
		help="surround the output image with a border of a given width")
	
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
	group.add_argument("--div",
		dest='divider', metavar="WIDTH", type=int, default=0,
		help="separate the two sides with a divider of a given width")
	
	group = parser.add_argument_group('Anaglyph')
	group.add_argument("-a", "--anaglyph",
		dest='anaglyph', action='store_true',
		help="output an anaglyph image")
	group.add_argument("-m", "--anaglyph-method",
		dest='anaglyph_method', metavar="METHOD", type=str, default="wimmer",
		help="set the anaglyph method: gray, color, half-color, wimmer, dubois [default: %(default)s]. The dubois method is only available with the red-cyan, green-magenta and amber-blue color schemes.")
	group.add_argument("--cs", "--color-scheme",
		dest='color_scheme', metavar="SCHEME", type=str, default="red-cyan",
		help="set the anaglyph color scheme: red-green, red-blue, red-cyan, green-magenta, amber-blue, magenta-cyan [default: %(default)s]. The non-complementary colors are mainly to be used with the gray method.")
	group.add_argument("--lc", "--luma-coding",
		dest='luma_coding', metavar="CODING", type=str, default="rec709",
		help="set the luma coding for the anaglyph gray and half-color methods: rgb, rec601 (PAL/NTSC), rec709 (HDTV) [default: %(default)s]")
	
	group = parser.add_argument_group('Animated')
	group.add_argument("-w", "--wiggle",
		dest='wiggle', action='store_true',
		help="output a wiggle GIF image")
	group.add_argument("-t", "--duration",
		dest='duration', metavar="DURATION", type=int, default=300,
		help="set the total duration of the wiggle GIF animation in milliseconds [default: %(default)s]")
	
	group = parser.add_argument_group('Patterened')
	group.add_argument("--ih", "--interlaced-h",
		dest='interlaced_horizontal', action='store_true',
		help="output a horizontally interlaced image")
	group.add_argument("--iv", "--interlaced-v",
		dest='interlaced_vertical', action='store_true',
		help="outout a vertically interlaced image")
	group.add_argument("--cb", "--checkerboard",
		dest='checkerboard', action='store_true',
		help="output a checkerboard patterned image")
	group.add_argument("--odd",
		dest='odd', action='store_true',
		help="set the left image to be the odd line or square of the pattern instead of the even one")
	
	group = parser.add_argument_group('Preprocessing')
	group.add_argument("-T", "--rotate",
		dest='rotate', type=float,
		nargs=2, metavar=("LEFT", "RIGHT"), default=(0, 0),
		help="rotate both images in degrees")
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
	
	if any(args.rotate):
		images = rotate(images, args.rotate)
	
	if any(args.align):
		images = align(images, args.align)
	
	for i, _ in enumerate(images):
		if any(args.crop):
			images[i] = crop(images[i], args.crop)
		
		if any(args.resize):
			images[i] = resize(images[i], args.resize, args.offset)
	
	if args.anaglyph:
		if args.luma_coding == "rgb":
			luma_coding = ANAGLYPH_LUMA_RGB
		elif args.luma_coding == "rec601":
			luma_coding = ANAGLYPH_LUMA_REC601
		elif args.luma_coding == "rec709":
			luma_coding = ANAGLYPH_LUMA_REC709
		output = create_anaglyph(images, args.anaglyph_method, args.color_scheme, luma_coding)
	elif args.wiggle:
		save_as_wiggle_gif_image(image_output, images, args.duration)
		return
	elif args.interlaced_horizontal:
		output = create_interlaced_h_image(images, not args.odd)
	elif args.interlaced_vertical:
		output = create_interlaced_v_image(images, not args.odd)
	elif args.checkerboard:
		output = create_checkerboard_image(images, not args.odd)
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
			output = create_side_by_side_image(images, is_horizontal, args.divider, args.bg_color)
		else:
			images[0].save(args.image_output, format=args.format, quality=args.quality, optimize=True)
			images[1].save(args.image_output2, format=args.format, quality=args.quality, optimize=True)
			return
	if args.border:
		output = ImageOps.expand(output, args.border, args.bg_color)
	output.save(image_output, format=args.format, quality=args.quality, optimize=True)

if __name__ == '__main__':
	_main()
