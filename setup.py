#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as f:
	long_description = f.read()

setuptools.setup(
	name="stereoscopy",
	version="1.0.1",
	
	author="Seán Hewitt",
	author_email="contact@2sh.me",
	
	description="StereoscoPy, stereoscopic 3D image creator",
	long_description=long_description,
	long_description_content_type="text/markdown",
	
	url="https://github.com/2sh/StereoscoPy",
	
	packages=["stereoscopy"],
	
	install_requires=["Pillow"],
	extras_require={
		"auto_align": ["opencv-python", "numpy"]
	},
	python_requires='>=3',
	classifiers=(
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
		"Operating System :: OS Independent",
		"Topic :: Multimedia :: Graphics"
	),
	
	entry_points={"console_scripts":["StereoscoPy=stereoscopy:_main"]}
)
