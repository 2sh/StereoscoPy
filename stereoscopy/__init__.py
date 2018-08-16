#!/usr/bin/env python3
#
#	StereoscoPy, stereoscopic 3D image creator
#
#	Copyright (C) 2016-2018 Seán Hewitt <contact@2sh.me>
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
import math

try:
	import cv2
	import numpy
	_is_advanced_available = True
except ImportError:
	_is_advanced_available = False

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
		return image.transpose(Image.ROTATE_180)
	elif orientation == 6:
		return image.transpose(Image.ROTATE_270)
	elif orientation == 8:
		return image.transpose(Image.ROTATE_90)
	else:
		return image

def _get_rotation_coordinates(matrix, size):
	xs = [0]
	ys = [0]
	for x, y in [(0, size[1]), (size[0], 0), size]:
		xs.append(matrix[0][0]*x + matrix[0][1]*y)
		ys.append(matrix[1][0]*x + matrix[1][1]*y)
	return xs, ys

def transform(images, matrices, shrink=False):
	"""Transform the images.
	
	The images are transformed by their matrices and either expanded or shruk
	to the same size.
	
	Args:
		images: The PIL images.
		matrices: The matrices for each image.
		shrink: Whether the image is shrunk into or expanded around the
			resulting picture.
	
	Returns:
		The transformed images.
	"""
	output = []
	
	output_width = 0
	output_height = 0
	matrices = list(matrices)
	for i, image in enumerate(images):
		matrix = []
		for row in matrices[i]:
			matrix.append(list(row))
		matrices[i] = matrix
		
		aspect_ratio = image.width / image.height
		
		xs, ys = _get_rotation_coordinates(matrix, image.size)
		
		min_x = min(xs)
		max_x = max(xs)
		min_y = min(ys)
		max_y = max(ys)
		
		expanded_width = max_x - min_x
		expanded_height = max_y - min_y
		
		a, b, h = matrix[0]
		c, d, k = matrix[1]
		
		h += min_x+(expanded_width-image.width)/2
		k += min_y+(expanded_height-image.height)/2
		
		margin_x = abs((d*h-b*k)/(a*d-b*c))
		margin_y = abs((a*k-c*h)/(a*d-b*c))
		
		if shrink:
			rotated_aspect_ratio = expanded_width / expanded_height
			
			if aspect_ratio < 1:
				total_height = image.width / rotated_aspect_ratio
			else:
				total_height = image.height
			angle = math.acos(matrix[0][0])
			height = total_height / (aspect_ratio * abs(math.sin(angle)) + abs(math.cos(angle)))
			
			width = math.floor(height * aspect_ratio) - margin_x*2
			height = math.floor(height) - margin_y*2
			
			height_from_width = width/aspect_ratio
			if height_from_width < height:
				height = height_from_width
			elif height_from_width > height:
				width = height * aspect_ratio
			
			output_width = min(output_width, width) if output_width else width
			output_height = min(output_height, height) if output_height else height
		else:
			width = expanded_width + margin_x*2
			height = expanded_height + margin_y*2
			
			height_from_width = width/aspect_ratio
			if height_from_width > height:
				height = height_from_width
			elif height_from_width < height:
				width = height * aspect_ratio
			
			output_width = max(output_width, width)
			output_height = max(output_height, height)
	
	if shrink:
		output_width = math.floor(output_width)
		output_height = math.floor(output_height)
	else:
		output_width = math.ceil(output_width)
		output_height = math.ceil(output_height)
	
	for i, image in enumerate(images):
		matrix = matrices[i]
		x = (output_width - image.size[0]) / 2
		y = (output_height - image.size[1]) / 2
		
		matrix[0][2] -= matrix[0][0] * x + matrix[0][1] * y
		matrix[1][2] -= matrix[1][0] * x + matrix[1][1] * y
	
		output.append(
			image.transform((output_width, output_height),
				Image.AFFINE, data=matrix[0]+matrix[1], resample=Image.BICUBIC))
	return output

def xy_and_angle_to_matrix(xy, angle, size):
	"""Create a 3x3 transformation matrix
	
	Args:
		xy: a tuple of the x and y dimensions.
		angle: the angle in degrees.
	
	Returns:
		The transformation matrix
	"""
	x, y = (xy if xy else (0, 0))
	angle = math.radians(angle)
	c = math.cos(angle)
	s = math.sin(angle)
	h = c*x + s*y
	k = -s*x + c*y
	
	xs, ys = _get_rotation_coordinates(((c, s),(-s, c)), size)
	
	min_x = min(xs)
	max_x = max(xs)
	min_y = min(ys)
	max_y = max(ys)
	
	expanded_size = (max_x-min_x, max_y-min_y)
	
	h -= min_x+(expanded_size[0]-size[0])/2
	k -= min_y+(expanded_size[1]-size[1])/2
	
	return ((c, s, h), (-s, c, k), (0, 0, 1))

def combine_matrices(matrix1, matrix2):
	"""Combine the two matrices through multiplication.
	
	Args:
		matrix1: The first matrix.
		matrix2: The second matrix.
	
	Returns:
		A matrix, combined from the two input matrices.
	"""
	m2_columns = list(zip(*matrix2))
	return tuple([tuple([sum(a * b for a, b in zip(m1_row, m2_col))
		for m2_col in m2_columns]) for m1_row in matrix1])

def find_alignments(images, iterations=20, threshold=1e-10):
	"""Find the alignment between two images.
	
	Args:
		images: Two PIL images.
		iterations: The amount of iterations.
		threshold: The accuracy threshold.
	
	Returns:
		The alignment matrix for each image.
	"""
	ii = images
	tn_size = 500
	ratio = max(images[0].size)/tn_size
	
	images = list(images)
	for i in range(len(images)):
		images[i] = images[i].convert("L")
		#Runs on smaller image for speed
		images[i].thumbnail((tn_size, tn_size), Image.BILINEAR)
		images[i] = numpy.array(images[i])
	
	criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iterations, threshold)
	
	m = numpy.eye(2, 3, dtype=numpy.float32)
	_, m = cv2.findTransformECC(images[0], images[1], m, cv2.MOTION_EUCLIDEAN, criteria)
	
	m[0,2] *= ratio
	m[1,2] *= ratio
	
	m[0,1] /= 2
	m[0,2] /= 2
	m[1,0] /= 2
	m[1,2] /= 2
	
	l = ((m[0,0], -m[0,1], -m[0,2]), (-m[1,0], m[1,1], -m[1,2]), (0, 0, 1))
	r = ((m[0,0], m[0,1], m[0,2]), (m[1,0], m[1,1], m[1,2]), (0, 0, 1))
	
	return [l, r]

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

def create_side_by_side_image(images, horizontal = True, divider_width = 0):
	"""Create a side-by-side image from two images.
	
	Args:
		images: Two PIL images.
		horizontal: If to join the images horizontal instead of vertical.
		divider_width: Width of a divider between the two joined images.
		
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
		
	if divider_width:
		mode = "RGBA"
	else:
		mode = images[0].mode
	
	output = Image.new(mode, (width, height))
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
	
	left, right = images
	if method == "wimmer" and color_scheme == "red-cyan":
		left = left.copy()
		right = right.copy()
		
		for i in left.load(), left.load():
			for y in range(left.height):
				for x in range(left.width):
					c = list(i[x, y])
					
					if c[0] > c[1] and c[0] > c[1]:
						c[1] = round(c[0]*0.3+c[1]*0.7)
						c[2] = round(c[0]*0.3+c[2]*0.7)
					
					i[x, y] = tuple(c)
	
	left_bands = left.split()
	right_bands = right.split()
	output_bands = list()
	for i in range(3):
		expression = (
			"(float(lr)*{lm[0]}+float(lg)*{lm[1]}+float(lb)*{lm[2]}+" +
			 "float(rr)*{rm[0]}+float(rg)*{rm[1]}+float(rb)*{rm[2]})"
			).format(lm=matrices[0][i], rm=matrices[1][i])
		
		if method == "wimmer" and colors[method_reverse][i]:
			expression = ("((" + expression + "/255)**(1/" +
				str(1 + (0.3 * colors[method_reverse][i])) +
				"))*255")
		
		output_bands.append(ImageMath.eval("convert(" + expression + ", 'L')",
			lr=left_bands[0], lg=left_bands[1], lb=left_bands[2],
			rr=right_bands[0], rg=right_bands[1], rb=right_bands[2]))
	
	if len(left_bands) > 3 and len(right_bands) > 3:
		output_bands.append(ImageChops.lighter(left_bands[3], right_bands[3]))
		return Image.merge("RGBA", output_bands)
	return Image.merge("RGB", output_bands)

PATTERN_CHECKERBOARD = 0
PATTERN_INTERLACED_H = 1
PATTERN_INTERLACED_V = 2

def create_patterned_image(images, pattern=PATTERN_INTERLACED_H, width=1, left_is_even=True):
	"""Create a patterned image from two images.
	
	Args:
		images: Two PIL images.
		pattern: the pattern number.
		width: the width of a line/square.
		left_is_even: Set the first image to be the even line/square.
	
	Returns:
		The patterned PIL image.
	"""
	output = images[0].copy()
	o = output.load()
	r = images[1].load()
	
	is_even = True
	two_width = width * 2
	for y in range(output.height):
		for x in range(output.width):
			if pattern == PATTERN_INTERLACED_H:
				is_even = (y % two_width) < width
			elif pattern == PATTERN_INTERLACED_V:
				is_even = (x % two_width) < width
			elif pattern == PATTERN_CHECKERBOARD:
				is_even = ((y % two_width) < width) == ((x % two_width) < width)
			if is_even != left_is_even:
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
	images[0].save(output_file, format="gif", save_all=True, loop=0,
		duration=round(total_duration/len(images)), append_images=images[1:])


def _main():
	import sys
	import argparse
	from PIL import ImageOps
	
	parser = argparse.ArgumentParser(
		description="Convert 2 images into a stereoscopic 3D image",
		usage="%(prog)s [OPTION]... LEFT RIGHT [OUT] [OUT2]")
	
	parser.add_argument("image_left",
		metavar="LEFT", type=str,
		help="left input image")
	parser.add_argument("image_right",
		metavar="RIGHT", type=str,
		help="right input image.")
	parser.add_argument("image_output",
		metavar="OUT", type=str, nargs='?',
		help="output file. If left omitted, output to STDOUT, in which case the output format is required")
	parser.add_argument("image_output2",
		metavar="OUT2", type=str, nargs='?',
		help="output an optional second image for split left and right")
	
	parser.add_argument("-q", "--quality",
		dest='quality', metavar="VALUE", type=int, default="95",
		help="set the output image quality: 1-100 [default: %(default)s]")
	parser.add_argument("-f", "--format",
		dest='format', metavar="FORMAT", type=str,
		help="set the output image format: JPG, PNG, GIF,... If left omitted, the format to use is determined from the filename extension")
	parser.add_argument("--bg",
		dest='bg_color', type=int,
		nargs=4, metavar=("RED", "GREEN", "BLUE", "ALPHA"), default=None,
		help="set the background color and transparency (alpha): 0-255 each. This is also the color for the divider and border")
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
		help="set the anaglyph method: gray, color, half-color, wimmer, dubois [default: %(default)s]. The dubois method is only available with the red-cyan, green-magenta and amber-blue color schemes")
	group.add_argument("--cs", "--color-scheme",
		dest='color_scheme', metavar="SCHEME", type=str, default="red-cyan",
		help="set the anaglyph color scheme: red-green, red-blue, red-cyan, green-magenta, amber-blue, magenta-cyan [default: %(default)s]. The non-complementary colors are mainly to be used with the gray method")
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
	
	group = parser.add_argument_group('Patterned')
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
		help="set the left image to be the odd line/square of the pattern instead of the even one")
	group.add_argument("--pw", "--pattern-width",
		dest='pattern_width', metavar="WIDTH", type=int, default=1,
		help="set the width of a line/square of the pattern [default: %(default)s]")
	
	group = parser.add_argument_group('Preprocessing')
	if _is_advanced_available:
		group.add_argument("-A", "--auto-align",
			dest='auto_align', action='store_true',
			help="auto align the right image to the left image. The aspect ratio is preserved")
	
	group.add_argument("-T", "--rotate",
		dest='rotate', type=float,
		nargs=2, metavar=("LEFT", "RIGHT"), default=(0, 0),
		help="rotate both images in degrees counter clockwise. The aspect ratio is preserved")
	group.add_argument("-S", "--shift",
		dest='shift', type=float,
		nargs=2, metavar=("X", "Y"), default=(0, 0),
		help="shift the right image in relation to the left image. The aspect ratio is preserved")
	group.add_argument("-X", "--expand",
		dest='expand', action='store_true',
		help="set to expand the images around the aligned/rotated pictures. The default is to shrink the images into the pictures, excluding the empty and non-overlapping areas")
	
	group.add_argument("-C", "--crop",
		dest='crop', type=str,
		nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"), default=(0, 0, 0, 0),
		help="crop both images in either pixels or percentage")
	
	group.add_argument("-R", "--resize",
		dest='resize', type=int,
		nargs=2, metavar=("WIDTH", "HEIGHT"), default=(0, 0),
		help="resize both images to WIDTHxHEIGHT. The dimension with a value of 0 is calculated automatically to preserve the aspect ratio")
	group.add_argument("-O", "--offset",
		dest='offset', type=str, default="50%",
		help="set the resize offset from top or left in either pixels or percentage [default: %(default)s]")
	
	args = parser.parse_args()
	
	if args.image_output:
		args.image_output = args.image_output
	else:
		if args.format is None:
			print("Either specify the output file name or the format to be used for outputting to STDOUT.", file=sys.stderr)
			exit()
		args.image_output = sys.stdout.buffer
	
	images = [Image.open(args.image_left), Image.open(args.image_right)]
	
	for i, _ in enumerate(images):
		images[i] = fix_orientation(images[i])
		
		if images[i].mode != "RGB" or images[i].mode != "RGBA":
			images[i] = images[i].convert("RGBA")
		
		if i > 0 and images[0].size != images[i].size:
			print("Given images are not the same size!", file=sys.stderr)
			exit()
	
	if any(args.shift) or any(args.rotate) or args.auto_align:
		if args.auto_align:
			matrices = find_alignments(images)
		else:
			matrices = [((1, 0, 0), (0, 1, 0), (0, 0, 1))]*2
		
		for i in range(2):
			if i == 0:
				xy = -args.shift[0], -args.shift[1]
			else:
				xy = args.shift
		
			matrix = xy_and_angle_to_matrix(xy, args.rotate[i], images[i].size)
			matrices[i] = combine_matrices(matrices[i], matrix)
		
		images = transform(images, matrices, not args.expand)
	
	for i, _ in enumerate(images):
		if any(args.crop):
			images[i] = crop(images[i], args.crop)
		
		if any(args.resize):
			images[i] = resize(images[i], args.resize, args.offset)
	
	do_save = True
	if args.anaglyph:
		if args.luma_coding == "rgb":
			luma_coding = ANAGLYPH_LUMA_RGB
		elif args.luma_coding == "rec601":
			luma_coding = ANAGLYPH_LUMA_REC601
		elif args.luma_coding == "rec709":
			luma_coding = ANAGLYPH_LUMA_REC709
		images = [create_anaglyph(images, args.anaglyph_method, args.color_scheme, luma_coding)]
	elif args.interlaced_horizontal:
		images = [create_patterned_image(images, PATTERN_INTERLACED_H, args.pattern_width, not args.odd)]
	elif args.interlaced_vertical:
		images = [create_patterned_image(images, PATTERN_INTERLACED_V, args.pattern_width, not args.odd)]
	elif args.checkerboard:
		images = [create_patterned_image(images, PATTERN_CHECKERBOARD, args.pattern_width, not args.odd)]
	elif args.wiggle:
		do_save = False
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
			images = [create_side_by_side_image(images, is_horizontal, args.divider)]
	
	for i, _ in enumerate(images):
		if i == 0:
			image_output = args.image_output
		elif args.image_output2:
			image_output = args.image_output2
		else:
			break
		
		if args.border:
			images[i] = ImageOps.expand(images[i], args.border)
		
		if args.bg_color and images[i].mode == "RGBA":
			background_image = Image.new("RGBA", images[i].size, tuple(args.bg_color))
			images[i] = Image.alpha_composite(background_image, images[i])
		
		if do_save:
			images[i].save(image_output, format=args.format, quality=args.quality, optimize=True)
	
	if args.wiggle:
		save_as_wiggle_gif_image(args.image_output, images, args.duration)
