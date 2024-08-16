from argparse import ArgumentParser
from os import mkdir
from os import name as os_name
from os import path, remove, scandir, system

import imageio.v3 as imageio
from cv2 import COLOR_RGB2BGR, cvtColor, imwrite

from blendNorms import blend_normals
from getMacroNorm import create_macro_normal_map
from getMicroNorm import create_micro_normal_map
from print_colored import print_colored

CLEAR = "cls" if os_name == "nt" else "clear"


def imgs2normals(
    input_dir: str,
    output_dir: str | None,
    blending_factor: float,
) -> bool:
    found_images: bool = False
    if not output_dir:
        output_dir = input_dir
    input_directory = path.abspath(input_dir)
    output_directory = path.abspath(output_dir)
    if not path.exists(output_directory):
        mkdir(output_directory)

    for input_img in scandir(input_directory):
        if input_img.is_dir():
            continue
        if True not in [
            input_img.name.lower().endswith(ext) for ext in [".png", ".jpg", ".tga"]
        ]:
            continue

        found_images = True

        system(CLEAR)
        print("Processing image: " + input_img.path)
        base_img = imageio.imread(input_img.path)
        base_img = cvtColor(base_img, COLOR_RGB2BGR)

        system(CLEAR)
        print_colored("blue", "Generating micro details normal map...")
        try:
            micro_normal_map = create_micro_normal_map(base_img)
        except Exception as e:
            print_colored("red", str(e))
            return False

        system(CLEAR)
        print_colored("blue", "Generating macro details normal map...")
        try:
            macro_normal_map = create_macro_normal_map(input_img.path)
        except Exception as e:
            print_colored("red", str(e))
            return False

        system(CLEAR)
        print_colored("blue", "Blending micro and macro normal maps...")
        try:
            blended_img = blend_normals(
                micro_normal_map, macro_normal_map, alpha=blending_factor
            )
        except Exception as e:
            print_colored("red", str(e))
            return False

        system(CLEAR)
        print_colored("blue", "Saving image...")
        try:
            output_path = path.join(
                output_directory,
                "normal_"
                + path.basename(input_img.path).replace(
                    path.basename(input_img.path).split(".")[-1], "png"
                ),
            )
            imwrite(output_path, blended_img)
        except Exception as e:
            print_colored("red", str(e))
            return False
    return found_images


def convert2dds(_input_path: str, _output_path: str | None, output_format: str = "dds"):
    print_colored("blue", "Converting image to specified format...")
    if not _output_path:
        _output_path = path.dirname(_input_path)
    input_path = path.abspath(_input_path)
    output_path = path.abspath(_output_path)
    if not path.exists(output_path):
        mkdir(output_path)

    initial_image = imageio.imread(input_path)
    if not path.isfile(output_path):
        output_path = path.join(
            output_path,
            path.basename(input_path).replace(input_path.split(".")[-1], output_format),
        )
    else:
        output_path = output_path.replace(output_path.split("r")[-1], output_format)
    imageio.imwrite(output_path, initial_image)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "input_directory", type=str, help="Input directory with the images"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Specify the output directory (default: same as input directory)",
    )
    parser.add_argument(
        "-b",
        "--blend",
        type=float,
        default=0.5,
        help="Set the blending factor between micro and macro normal maps (default: 0.5)",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="dds",
        help="Set the output format for the final normal map (default: dds)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = args.input_directory
    output_dir = args.output
    blending_factor = args.blend
    output_format = args.format
    imgs2normals(input_dir, output_dir, blending_factor)
    for normal in scandir(output_dir):
        if normal.is_dir():
            continue
        if normal.name.lower().endswith(".png") and normal.name.lower().startswith(
            "normal_"
        ):
            if output_format != "png":
                convert2dds(normal.path, output_dir, output_format)
                remove(normal.path)
    print_colored("green", "Done!")


if __name__ == "__main__":
    main()
