import os
import random
import time
import argparse
import bisect
from PIL import Image, ImageDraw, ImageChops
from colourlovers import clapi


parser = argparse.ArgumentParser(description="2D Procedural Landscape Generator")
parser.add_argument("-t", "--theme", type=str, help="theme for colour palette")
args = parser.parse_args()


def midpoint_displacement(start, end, roughness, vertical_displacement=None, num_of_iterations=32):
    if vertical_displacement is None:
        vertical_displacement = (start[1] + end[1]) / 2
    points = [start, end]
    iteration = 1
    while iteration <= num_of_iterations:
        points_tup = tuple(points)
        for i in range(len(points_tup) - 1):
            midpoint = list(map(lambda x: (points_tup[i][x] + points_tup[i + 1][x]) / 2, [0, 1]))
            midpoint[1] += random.choice([-vertical_displacement, vertical_displacement])
            bisect.insort(points, midpoint)
        vertical_displacement *= 2 ** (-roughness)
        iteration += 1
    return points


def draw_layers(layers, width, height, colour_palette_keyword):
    colour_dict = None
    if colour_palette_keyword:
        cl = clapi.ColourLovers()
        palettes = cl.search_palettes(request="top", keywords=colour_palette_keyword, numResults=15)
        palette = palettes[random.choice(range(len(palettes)))]
        colour_dict = {str(iter): palette.hex_to_rgb()[iter] for iter in range(len(palette.colors))}
    if colour_dict is None or len(colour_dict.keys()) < len(layers):
        colour_dict = {"0": (195, 157, 224), "1": (158, 98, 204), "2": (130, 79, 138), "3": (68, 28, 99),
                       "4": (49, 7, 82), "5": (23, 3, 38), "6": (240, 203, 163),}
    else:
        if len(colour_dict) < len(layers) + 1:
            raise ValueError("Num of colours should be bigger than the num of layers")
    landscape = Image.new("RGBA", (width, height), colour_dict[str(len(colour_dict) - 1)])
    landscape_draw = ImageDraw.Draw(landscape)
    # landscape_draw.ellipse((50, 25, 100, 75), fill=(255, 255, 255, 255))
    final_layers = []
    for layer in layers:
        sampled_layer = []
        for i in range(len(layer) - 1):
            sampled_layer += [layer[i]]
            if layer[i + 1][0] - layer[i][0] > 1:
                m = float(layer[i + 1][1] - layer[i][1]) / (layer[i + 1][0] - layer[i][0])
                n = layer[i][1] - m * layer[i][0]
                r = lambda x: m * x + n
                for j in range(int(layer[i][0] + 1), int(layer[i + 1][0])):
                    sampled_layer += [[j, r(j)]]
        final_layers += [sampled_layer]
    final_layers_enum = enumerate(final_layers)
    for final_layer in final_layers_enum:
        for x in range(len(final_layer[1]) - 1):
            landscape_draw.line((final_layer[1][x][0], height - final_layer[1][x][1],
                                 final_layer[1][x][0], height,), colour_dict[str(final_layer[0])],)
    return landscape


def generate_gradient(colour1: str, colour2: str, width: int, height: int) -> Image:
    base = Image.new('RGBA', (width, height), colour1)
    top = Image.new('RGBA', (width, height), colour2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def main():
    multiplier = 3
    width = 1920 * multiplier
    height = 1080 * multiplier
    layer_1 = midpoint_displacement([250, 0], [width+1, 300 * multiplier], 1.4, 20, 12)
    layer_2 = midpoint_displacement([0, 380 * multiplier], [width+1, 200 * multiplier], 1.2, 30, 12)
    layer_3 = midpoint_displacement([0, 470 * multiplier], [width+1, 390 * multiplier], 1, 120, 9)
    layer_4 = midpoint_displacement([0, 550 * multiplier], [width+1, 420 * multiplier], 0.9, 250, 8)
    colour_theme = None
    if args.theme:
        colour_theme = args.theme
    landscape = draw_layers([layer_4, layer_3, layer_2, layer_1], width, height, colour_theme)
    multi = generate_gradient((210,210,210,255), (0,0,0,255), width, height)
    output = ImageChops.overlay(landscape, multi)
    output = output.resize((width // multiplier, height // multiplier), resample=Image.LANCZOS)
    now = time.strftime("%Y%m%d-%H%M%S")
    filename = os.getcwd() + "\\" + now + ".png"
    output.save(filename)
    print("Generation saved at: " + filename)


if __name__ == "__main__":
    main()
