import sys
import os
import math
import argparse
import io
import re

from PIL import Image

pre = """
<?xml version="1.0" encoding="UTF-8"?><vehicle data_version="2" is_advanced="tru
e" is_static="false" bodies_id="2"><editor_placement_offset x="0" y="0" z="0"/><
authors/><bodies><body unique_id="2"><initial_local_transform 00="1" 01="0" 02="
0" 03="0" 10="0" 11="1" 12="0" 13="0" 20="0" 21="0" 22="1" 23="0" 30="0" 31="0" 
32="0" 33="1"/><local_transform 00="1" 01="0" 02="0" 03="0" 10="0" 11="1" 12="0"
 13="0" 20="0" 21="0" 22="1" 23="0" 30="0" 31="0" 32="0" 33="1"/><components>
"""
 
component = """
<c d="sign_na" t="0"><o r="1,0,0,0,1,0,0,0,1" bc="FFFFFFFF" ac="FFFFFFFF" sc="6"
 custom_name=""><vp x="%i" y="%i" z="%i"/><logic_slots><slot value="false"/></lo
gic_slots>%s</o></c>
"""

post = """</components></body></bodies><logic_node_links/></vehicle>"""

def generate(image, savegame, width, height, background):
	# Load image from stdin or disk
	if image == "-":
		orig = Image.open(io.BytesIO(sys.stdin.buffer.read()))
	else:
		orig = Image.open(image)
	
	# Add background color for transparent images
	if orig.mode in ('RGBA', 'LA') or (orig.mode == 'P' and 'transparency' in orig.info):
		if orig.mode == 'P':
			orig = orig.convert('RGBA')
		im = Image.new('RGBA', orig.size, background)
		im.paste(orig, (0, 0), orig)
	else:
		im = orig

	# Convert to RGB, pad to multiple of 9 and mirror for easier generation
	im = im.convert('RGB')
	
	w, h = math.ceil(im.width / 9) * 9, math.ceil(im.height / 9) * 9
	bg = Image.new('RGB', (w, h), background)
	x, y = (w - im.width) // 2, (h - im.height) // 2
	bg.paste(im, (x, y))
	
	im = bg.transpose(Image.FLIP_LEFT_RIGHT)
	
	# Resize to final size
	if width or height:
		if width and height:
			w, h = width * 9, height * 9
		else:
			factor = height * 9 / im.height if height else width * 9 / im.width
			w, h = im.width * factor, im.height * factor

		w, h = math.ceil(w / 9) * 9, math.ceil(h / 9) * 9
		im = im.resize((w, h), Image.LANCZOS)

	# Santiy check
	assert im.width % 9 == 0
	assert im.height % 9 == 0

	# Generate XML
	text = pre
	pixels = im.getdata()
	blocks_x = im.width // 9
	blocks_y = im.height // 9

	for block_x in range(0, blocks_x):
		for block_y in range(0, blocks_y):
			colors = ""
			for pixel_x in range(0, 9):
				for pixel_y in range(0, 9):
					pixel_pos = block_x * 9 + pixel_x + (block_y * 9 + pixel_y) * im.width
					pixel = pixels[pixel_pos]
					game_pos = pixel_x + 9 * pixel_y
					colors += '<cc%i r="%i" g="%i" b="%i" a="255"/>' % ((game_pos,) + pixel)
			text += component % (block_x, 0, block_y, colors)

	text += post
	text = text.replace("\n", "")	
	
	# Save to stdout or disk
	if savegame == '-':
		sys.stdout.write(text + "\n")
		sys.stdout.flush()
	else:
		open(savegame, "w").write(text)

def hex_rgba_color(s):
	if re.match(r"0[xX][a-f0-9A-F]{6}", s):
		color = int(s, 16)
		return (color >> 16 & 0xff, color >> 8 & 0xFF, color & 0xFF, 0xFF)
	else:
		raise argparse.ArgumentTypeError("Please use format 0xRRGGBB")

def main():
	parser = argparse.ArgumentParser(description='Generate Stormworks savegame with paintable signs from image.')
	parser.add_argument('image', metavar='IMAGE', help='the input image to be processed, "-" for stdin')
	parser.add_argument('savegame', metavar='SAVEFILE', help='savegame filename to write to, "-" for stdout')
	parser.add_argument('--width', type=int, help='resize horizontally to number of blocks')
	parser.add_argument('--height', type=int, help='resize vertically to number of blocks')
	parser.add_argument('--background', type=hex_rgba_color, dest='background',
		help='use background for transparent and padded images, format: 0xRRGGBB')

	args = parser.parse_args()
	generate(args.image, args.savegame, args.width, args.height, args.background)

if __name__ == '__main__':
	main()
