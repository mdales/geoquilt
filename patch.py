import os
import sys

from yirgacheffe.layers import Layer
from yirgacheffe.rounding import DISTANCE_PER_DEGREE_AT_EQUATOR

try:
	folder = sys.argv[1]
	target = sys.argv[2]
except IndexError:
	print(f"usage: {sys.args[0]} [FOLDER OF GEOTIFFS] [OUTPUT TIFF NAME]")
	sys.exit(-1)

try:
	folder_contents = os.listdir(folder)
except OSError as e:
	print(f"Failed to access {folder}: {e}")
	sys.exit(-1)

# Give me the full path of all the tiffs
tiff_list = [os.path.join(folder, x) for x in folder_contents if x.endswith('.tif')]

if len(tiff_list) < 2:
	print("Need two or more layers to composite")
	sys.exit(-1)

# Give me a yirgacheffe layer object for each tiff
layer_list = [Layer.layer_from_file(filename) for filename in tiff_list]

# Find the union of all the layers
try:
	union_area = Layer.find_union(layer_list)
except ValueError:
	# This typically means that all the layers on the list are not
	# the same projection or pixel scale.
	print("Provided tiffs do not have same scale/projection:")
	mapmap = {}
	for layer in layer_list:
		try:
			mapmap[layer.pixel_scale].append(layer)
		except KeyError:
			mapmap[layer.pixel_scale] = [layer]
	for key in mapmap:
		# pixel scale is the number of degrees per pixel

		print(f"{key.xstep * DISTANCE_PER_DEGREE_AT_EQUATOR}, {key.ystep * DISTANCE_PER_DEGREE_AT_EQUATOR}:")
		for layer in mapmap[key]:
			print(f"\t{layer.name}")
	sys.exit(-1)

# make the output layer
result = Layer.empty_raster_layer(
	area=union_area,
	scale=layer_list[0].pixel_scale,
	data_type=layer_list[0].data_type,
	filename=target,
	projection=layer_list[0].projection
)

calc = layer_list[0]
for layer in layer_list[1:]:
	calc = calc + layer
calc.save(result)
