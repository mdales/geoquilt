import os
import sys

import numpy as np
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
	print("Provided tiffs do not have same scale/projection")
	sys.exit(-1)

for layer in layer_list:
	layer.set_window_for_union(union_area)

# make the output layer
result = Layer.empty_raster_layer(
	area=union_area,
	scale=layer_list[0].pixel_scale,
	data_type=layer_list[0].datatype,
	filename=target,
	projection=layer_list[0].projection
)

def nansum(a, b):
	return np.nansum(np.dstack((a, b)),2)

calc = layer_list[0]
for layer in layer_list[1:]:
	calc = calc.numpy_apply(nansum, layer)
calc.save(result)
