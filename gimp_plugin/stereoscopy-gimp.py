#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#	StereoscoPy for GIMP
#
#	Copyright (C) 2018 Seán Hewitt <contact@2sh.me>
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

from gimpfu import *

from PIL import Image

import stereoscopy


_anaglyph_methods = [
	("Wimmer", "wimmer"),
	("Gray", "gray"),
	("Color", "color"),
	("Half Color", "half-color"),
	("Dubois", "dubois")
]

_anaglyph_color_schemes = [
	("Red/Cyan", "red-cyan"),
	("Red/Green", "red-green"),
	("Red/Blue", "red-blue"),
	("Green/Magenta", "green-magenta"),
	("Amber/Blue", "amber-blue"),
	("Magenta/Cyan", "magenta-cyan")
]

_anaglyph_luma_coding = [
	("Rec. 709", stereoscopy.ANAGLYPH_LUMA_REC709),
	("Rec. 601", stereoscopy.ANAGLYPH_LUMA_REC601),
	("RGB", stereoscopy.ANAGLYPH_LUMA_RGB)
]


def _create_stereoscopic_image(func, name, layers):
	pdb.gimp_progress_set_text("Preparing...")
	
	width = layers[0].image.width
	height = layers[0].image.height
	
	p_images = []
	for i, layer in enumerate(layers):
		if i > 1:
			break
		
		pdb.gimp_image_undo_freeze(layer.image)
		temp = layer.copy()
		layer.image.add_layer(temp, 0)
		temp.resize(width, height, *layer.offsets)
		
		rgn = temp.get_pixel_rgn(0, 0, temp.width, temp.height, False)
		
		if temp.has_alpha:
			mode = "RGBA"
		else:
			mode = "RGB"
		
		p_image = Image.frombytes(mode, (temp.width, temp.height),
			rgn[0:temp.width, 0:temp.height])
		p_images.append(p_image)
		layer.image.remove_layer(temp)
		pdb.gimp_image_undo_thaw(layer.image)
	
	pdb.gimp_progress_set_text("Creating...")
	
	p_image = func(p_images)
	
	width, height = p_image.size
	
	pdb.gimp_progress_set_text("Displaying...")
	
	image = gimp.Image(width, height, RGB)
	image.disable_undo()
	
	layer = gimp.Layer(image, name,
		width, height, RGB_IMAGE, 100, NORMAL_MODE)
	image.add_layer(layer, 0)
	
	if p_image.mode == "RGBA":
		layer.add_alpha()
	
	rgn = layer.get_pixel_rgn(0, 0, width, height)
	rgn[0:width, 0:height] = p_image.tobytes()
	
	image.enable_undo()
	gimp.Display(image)
	gimp.displays_flush()

def create_anaglyph(image, drawable, left, right,
		method, color_scheme, luma_coding):
	method = _anaglyph_methods[method][1]
	color_scheme = _anaglyph_color_schemes[color_scheme][1]
	luma_coding = _anaglyph_luma_coding[luma_coding][1]
	
	def func(images):
		return stereoscopy.create_anaglyph(images,
			method, color_scheme, luma_coding)
	
	_create_stereoscopic_image(func, "Anaglyph", (left, right))

def create_side_by_side_image(image, drawable, left, right,
		method, squash, divider):
			
	def func(images):
		is_horizontal = method == 0 or method == 1
		
		if squash:
			for i in range(len(images)):
				images[i] = stereoscopy.squash(images[i], is_horizontal)
		
		if method == 0 or method == 3:
			images.reverse()
		
		return stereoscopy.create_side_by_side_image(images,
			is_horizontal, int(divider))
	
	_create_stereoscopic_image(func, "Side-by-side", (left, right))

def create_patterned_image(image, drawable, left, right,
		method, odd, width):
	method = [stereoscopy.PATTERN_INTERLACED_H,
		stereoscopy.PATTERN_INTERLACED_V,
		stereoscopy.PATTERN_CHECKERBOARD][method]
	
	def func(images):
		return stereoscopy.create_patterned_image(images,
			method, width, not odd)
	
	_create_stereoscopic_image(func, "Patterned", (left, right))

def create_wiggle_animation(image, drawable,
		duration):
	image = pdb.gimp_image_duplicate(image)
	
	for layer in image.layers[1:-1]:
		image.add_layer(layer.copy(), 0)
	
	image_duration = int(round(duration/len(image.layers)))
	
	for layer in image.layers:
		layer.name += " ({}ms)".format(image_duration)
	
	gimp.Display(image)
	gimp.displays_flush()

register(
	"Anaglyph",
	"Create an anaglypth",
	"Create an anaglypth",
	"Seán Hewitt",
	"Seán Hewitt",
	"2018",
	"<Image>/Filters/StereoscoPy/Anaglyph...",
	"*",
	[
		(PF_LAYER, "left", "Left image", None),
		(PF_LAYER, "right", "Right image", None),
		(PF_OPTION, "method", "Method", 0,
			[t for t,_ in _anaglyph_methods]),
		(PF_OPTION, "color_scheme", "Color Scheme", 0,
			[t for t,_ in _anaglyph_color_schemes]),
		(PF_OPTION, "luma_coding", "Luma Coding", 0,
			[t for t,_ in _anaglyph_luma_coding])
	],
	[],
	create_anaglyph)

register(
	"Side-by-side",
	"Create a side-by-side image",
	"Create a side-by-side image",
	"Seán Hewitt",
	"Seán Hewitt",
	"2018",
	"<Image>/Filters/StereoscoPy/Side-by-side...",
	"*",
	[
		(PF_LAYER, "left", "Left image", None),
		(PF_LAYER, "right", "Right image", None),
		(PF_OPTION, "method", "Method", 0, [
			"Right/Left (Cross-eye)",
			"Left/Right (Parallel, VR)",
			"Over/Under",
			"Under/Over"]),
		(PF_TOGGLE, "squash", "Squash", False),
		(PF_SPINNER, "divider", "Divider", 0, (0, 9999999, 1))
	],
	[],
	create_side_by_side_image)

register(
	"Patterned",
	"Create a patterned image",
	"Create a patterned image",
	"Seán Hewitt",
	"Seán Hewitt",
	"2018",
	"<Image>/Filters/StereoscoPy/Patterned...",
	"*",
	[
		(PF_LAYER, "left", "Left image", None),
		(PF_LAYER, "right", "Right image", None),
		(PF_OPTION, "method", "Method", 0, [
			"Interlaced horizontally",
			"Interlaced vertically",
			"Checkerboard"]),
		(PF_OPTION, "odd", "Order", 0, [
			"Even",
			"Odd"]),
		(PF_SPINNER, "width", "Width", 1, (1, 9999999, 1))
	],
	[],
	create_patterned_image)

register(
	"Wiggle",
	"Create a wiggle animation",
	"Create a wiggle animation",
	"Seán Hewitt",
	"Seán Hewitt",
	"2018",
	"<Image>/Filters/StereoscoPy/Wiggle...",
	"*",
	[
		(PF_SPINNER, "duration", "Duration (ms)", 300, (1, 9999999, 1))
	],
	[],
	create_wiggle_animation)

main()
