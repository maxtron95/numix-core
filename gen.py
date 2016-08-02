#!/usr/bin/python3

# Copyright (C) 2016
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License (version 3+) as
# published by the Free Software Foundation. You should have received
# a copy of the GNU General Public License along with this program.
# If not, see <http://www.gnu.org/licenses/>.

# Sorting out modules


from git import Git
from json import load
from os import listdir, makedirs, path, symlink
from shutil import copy2
from subprocess import PIPE, Popen, call
from io import BytesIO
from gi import require_version
require_version('Rsvg', '2.0')
try:
    from gi.repository import Rsvg
    import cairo
    use_inkscape = False
except (ImportError, AttributeError):
    ink_flag = call(['which', 'inkscape'], stdout=PIPE, stderr=PIPE)
    if ink_flag == 0:
        use_inkscape = True
    else:
        exit("Can't load cariosvg nor inkscape")
# Importing JSON
with open('data.json') as data:
    icons = load(data)

# User selects the theme
theme, themes = "", ["circle"]
while True:
    theme = input("What theme would you like to build? ").lower().strip()
    if theme in themes:
        break
    else:
        print("Please enter one of the following:", ", ".join(themes), "\n")

# User selects the platform
platform, platforms = "", ["android", "linux", "osx"]
while True:
    platform = input("What OS would you like to build for? ").lower().strip()
    if platform in platforms:
        break
    else:
        print("Please enter one of the following:", ", ".join(platforms), "\n")


def mkdir(dir):
    if not path.exists(dir):
        makedirs(dir)


def convert_svg2png(infile, outfile, w, h):
    """
        Converts svg files to png using Cairosvg or Inkscape
        @file_path : String; the svg file absolute path
        @dest_path : String; the png file absolute path
    """
    if use_inkscape:
        p = Popen(["inkscape", "-f", infile, "-e", outfile,
                   "-w" + str(w), "-h" + str(h)],
                  stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
    else:
        handle = Rsvg.Handle()
        svg = handle.new_from_file(infile)
        dim = svg.get_dimensions()

        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        ctx = cairo.Context(img)
        ctx.scale(w / dim.width, h / dim.height)
        svg.render_cairo(ctx)

        png_io = BytesIO()
        img.write_to_png(png_io)
        with open(outfile, 'wb') as fout:
            fout.write(png_io.getvalue())
        svg.close()
        png_io.close()
        img.finish()


sizes = listdir("icons")
adir = "com.numix.icons_circle/MainActivity22/app/src/main/res/drawable-xxhdpi/"
ldir = "numix-icon-theme-circle/Numix-Circle/"
odir = "numix-circle.icns/"

# The Generation Stuff
if platform == "android":
    print("\nGenerating Android theme...")
    mkdir(adir)
    for icon in icons:
        for name in icons[icon]["android"]:
            name = name.replace("_", ".")
            if path.exists("icons/48/" + icon + ".svg"):
                convert_svg2png("icons/48/" + icon + ".svg",
                                adir + name + ".png", 192, 192)
elif platform == "linux":
    print("\nGenerating Linux theme...")
    for size in sizes:
        mkdir(ldir + size + "/apps")
    for icon in icons:
        for size in sizes:
            root = icons[icon]["linux"]["root"] + ".svg"
            if path.exists("icons/" + size + "/" + icon + ".svg"):
                copy2("icons/" + size + "/" + icon + ".svg",
                      ldir + size + "/apps/" + root)
                if icons[icon]["linux"]["symlinks"]:
                    for link in icons[icon]["linux"]["symlinks"]:
                        try:
                            symlink(root,
                                    ldir + size + "/apps/" + link + ".svg")
                        except FileExistsError:
                            continue
elif platform == "osx":
    print("\nGenerating OSX theme...")
    for ext in ["icns", "pngs", "vectors"]:
        mkdir(odir + ext)
    try:
        ink_flag = call(['which', 'png2icns'], stdout=PIPE, stderr=PIPE)
        if ink_flag != 0:
            raise Exception
    except (FileNotFoundError, Exception):
        exit("You will need png2icns in order to generate OSX theme")
    for icon in icons:
        for name in icons[icon]["osx"]:
            if path.exists("icons/48/" + icon + ".svg"):
                copy2("icons/48/" + icon + ".svg",
                      odir + "vectors/" + name + ".svg")
                convert_svg2png("icons/48/" + icon + ".svg",
                                odir + "pngs/" + name + ".png", 1024, 1024)
                call(["png2icns", odir + "icns/" + name + ".icn",
                      odir + "pngs/" + name + ".png"],
                     stdout=PIPE, stderr=PIPE)
# Clean Up
print("Done!\n")
exit(0)
