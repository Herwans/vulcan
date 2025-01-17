import hashlib
import json
import os
import pathlib
import re
import click
from PIL import Image

from vulcan.utils import prompt
from vulcan.utils.config import Configuration


def apply_folder_rules(element):
    altered_element = element
    for rule in Configuration().get_folder_rules():
        # 0 = Pattern
        # 1 = Replacement
        altered_element = re.sub(rule[0], rule[1], altered_element)
    altered_element = altered_element.strip()
    return altered_element


def apply_file_rules(element):
    conf = Configuration()
    sets = conf.get_extension_sets()
    file_name, file_extension = os.path.splitext(element)
    altered_element = file_name
    for rule in conf.get_file_rules():
        if len(rule) == 4:
            exclusion = rule[3].split(',')
        else:
            exclusion = []
        if (rule[2] == '*' or file_extension.lstrip(".") in sets[rule[2]]) \
                and file_extension.lstrip(".") not in exclusion:
            altered_element = altered_element.strip()
            altered_element = re.sub(rule[0], rule[1], altered_element)
    altered_element = altered_element.strip()

    if altered_element == "":
        return element
    return altered_element + file_extension


def create_meta_file(folder, current_name, new_name):
    global metadata_path, element_type
    path = f"{folder}/{current_name}"
    if os.path.exists(path):
        if os.path.isfile(path):
            element_type = "file"
            metadata_path = f"{folder}/{calculate_file_hash(path)}.json"
            if os.path.exists(metadata_path):
                click.echo("Updating meta file...")
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                click.echo("Creating meta file...")
                metadata = {"original_name": current_name}
            metadata["new_name"] = new_name
        elif os.path.isdir(path):
            element_type = "folder"
            metadata_path = f"{folder}/{current_name}/meta.json"
            prompt.line(metadata_path)
            if os.path.exists(metadata_path):
                click.echo("Updating meta file...")
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                click.echo("Creating meta file...")
                metadata = {"original_name": current_name}
            metadata["new_name"] = new_name
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        prompt.line("It's a " + element_type)


def delete_folder(path):
    elements = os.listdir(path)
    to_delete = pathlib.Path(path)
    if len(elements) == 0:
        pathlib.Path.rmdir(to_delete)
        return True
    elif len(elements) == 1 and elements[0] == "meta.json":
        os.remove(path + "/meta.json")
        pathlib.Path.rmdir(to_delete)
        return True
    return False


def calculate_file_hash(file_path, hash_algorithm='sha256'):
    try:
        with open(file_path, 'rb') as f:
            hasher = hashlib.new(hash_algorithm)
            while chunk := f.read(8192):
                hasher.update(chunk)
            return hasher.hexdigest()
    except FileNotFoundError:
        return None


def is_image_corrupted(image_path, verbose=False):
    try:
        Image.open(image_path).verify()
        return False
    except (IOError, SyntaxError) as e:
        if verbose:
            print(f"Image {image_path} is corrupted")
        return True


def is_image(image_path):
    image_extensions = Configuration().get_image_extensions()
    return os.path.splitext(image_path)[1].strip('.') in image_extensions


def is_video(video_path):
    image_extensions = Configuration().get_videos_extensions()
    return os.path.splitext(video_path)[1].strip('.') in image_extensions


def is_image_only(folder_path):
    for element in os.listdir(folder_path):
        if is_image(f"{folder_path}/{element}") is False and element != "meta.json":
            return False
    return True


def is_video_only(folder_path):
    for element in os.listdir(folder_path):
        if is_video(f"{folder_path}/{element}") is False and element != "meta.json":
            return False
    return True

