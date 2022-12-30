from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import glob
import io
import os
import pandas as pd
import subprocess
import sys
import tensorflow as tf
import xml.etree.ElementTree as xet
import hashlib

from collections import namedtuple
from object_detection.utils import dataset_util
from PIL import Image
from tqdm import tqdm


tmp_csv = ".tmpFile.csv"


def txt_to_csv(txt_dir, csv_output_file):
    csv_lines = []
    for txt_file in tqdm(glob.glob(os.path.join(txt_dir, "*.txt"))):
        with open(txt_file, "r") as f:
            file_lines = f.readlines()

        for line in file_lines:
            class_xmin_ymin_xmax_ymax = line.strip("\t\n\r").split()
            csv_line = (os.path.splitext(os.path.basename(os.path.normpath(txt_file)))[0] + ".jpg",
                        class_xmin_ymin_xmax_ymax[0],
                        int(float(class_xmin_ymin_xmax_ymax[1])),
                        int(float(class_xmin_ymin_xmax_ymax[2])),
                        int(float(class_xmin_ymin_xmax_ymax[3])),
                        int(float(class_xmin_ymin_xmax_ymax[4])))
            csv_lines.append(csv_line)

    column_names = ["filename", "class", "xmin", "ymin", "xmax", "ymax"]
    txt_df = pd.DataFrame(csv_lines, columns=column_names)
    txt_df.to_csv(csv_output_file, index=False)


def xml_to_csv(xml_dir, csv_output_file):
    csv_lines = []
    for xml_file in tqdm(glob.glob(os.path.join(xml_dir, "*.xml"))):
        tree = xet.parse(xml_file)
        root = tree.getroot()
        for xml_member in root.findall("object"):
            csv_line = (root.find("filename").text,
                        xml_member[0].text,
                        int(xml_member[4][0].text),
                        int(xml_member[4][1].text),
                        int(xml_member[4][2].text),
                        int(xml_member[4][3].text))
            csv_lines.append(csv_line)

    column_names = ["filename", "class", "xmin", "ymin", "xmax", "ymax"]
    xml_df = pd.DataFrame(csv_lines, columns=column_names)
    xml_df.to_csv(csv_output_file, index=False)


def label_dict_from_pbtxt(pbtxt_path):
    with open(pbtxt_path, "r", encoding="utf-8-sig") as f:
        file_lines = f.readlines()

    name_key = "name:"
    file_lines = [line.rstrip("\n").strip() for line in file_lines if "id:" in line or name_key in line]

    ids = [int(line.replace("id:", "")) for line in file_lines if line.startswith("id")]
    names = [line.replace(name_key, "").replace("\"", "").replace("\'", "").strip() for line in file_lines
             if line.startswith(name_key)]

    label_dict = {}
    for i in range(len(ids)):
        label_dict[names[i]] = ids[i]

    return label_dict


def create_tf_example(filename_object_group, img_dir_path, class_dict):
    with tf.io.gfile.GFile(os.path.join(img_dir_path, "{}".format(filename_object_group.filename)), "rb") as f:
        encoded_jpg = f.read()

    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = filename_object_group.filename.encode("utf8")
    source_id = str(int(hashlib.sha256(filename).hexdigest(), 16) % 2**64).encode('utf8')
    image_format = b"jpg"
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for index, row in filename_object_group.object.iterrows():
        xmins.append(row["xmin"] / width)
        xmaxs.append(row["xmax"] / width)
        ymins.append(row["ymin"] / height)
        ymaxs.append(row["ymax"] / height)

        if row["xmin"] <= row["xmax"] <= width is False:
            print("bad x coordinates:", row["filename"])
            sys.exit(0)

        if row["ymin"] <= row["ymax"] <= width is False:
            print("bad y coordinates:", row["filename"])
            sys.exit(0)

        classes_text.append(str(row["class"]).encode("utf8"))
        classes.append(class_dict[str(row["class"])])

    tf_example = tf.train.Example(features=tf.train.Features(
        feature={
            "image/height": dataset_util.int64_feature(height),
            "image/width": dataset_util.int64_feature(width),
            "image/filename": dataset_util.bytes_feature(filename),
            "image/source_id": dataset_util.bytes_feature(source_id),
            "image/encoded": dataset_util.bytes_feature(encoded_jpg),
            "image/format": dataset_util.bytes_feature(image_format),
            "image/object/bbox/xmin": dataset_util.float_list_feature(xmins),
            "image/object/bbox/xmax": dataset_util.float_list_feature(xmaxs),
            "image/object/bbox/ymin": dataset_util.float_list_feature(ymins),
            "image/object/bbox/ymax": dataset_util.float_list_feature(ymaxs),
            "image/object/class/text": dataset_util.bytes_list_feature(classes_text),
            "image/object/class/label": dataset_util.int64_list_feature(classes), }))

    return tf_example


def main():
    parser = argparse.ArgumentParser(
        description="Create a TFRecord file for use with the TensorFlow Object Detection API.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--txt_or_xml",
        choices=["txt", "xml"],
        required=True,
        type=str,
        help="Indicate whether parsing XML or TXT files")
    parser.add_argument(
        "--label_dir",
        required=True,
        type=str,
        help="Directory containing the XML or TXT files with the image label information")
    parser.add_argument(
        "--img_dir",
        required=True,
        type=str,
        help="Directory containing the images")
    parser.add_argument(
        "--pbtxt",
        required=True,
        type=str,
        help="PBTXT file containing the class ids and display names")
    parser.add_argument(
        "--tfrecord",
        required=True,
        type=str,
        help="TFRecord file to create")

    args = parser.parse_args()

    label_dict = label_dict_from_pbtxt(args.pbtxt)
    tfrecord_writer = tf.compat.v1.python_io.TFRecordWriter(args.tfrecord)
    img_dir_path = os.path.join(args.img_dir)

    if args.txt_or_xml == "txt":
        txt_to_csv(args.label_dir, tmp_csv)
    elif args.txt_or_xml == "xml":
        xml_to_csv(args.label_dir, tmp_csv)

    examples = pd.read_csv(tmp_csv)

    try:
        subprocess.run(["rm", "-rf", tmp_csv],
                       stdout=subprocess.PIPE,
                       universal_newlines=True,
                       check=True)
    except subprocess.CalledProcessError as error:
        print(error)
        sys.exit(1)

    gb = examples.groupby("filename")
    data = namedtuple("data", ["filename", "object"])
    filename_object_groups = [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]

    for filename_object_group in tqdm(filename_object_groups):
        tf_example = create_tf_example(filename_object_group, img_dir_path, label_dict)
        tfrecord_writer.write(tf_example.SerializeToString())

    tfrecord_writer.close()
    tfrecord_path = os.path.join(os.getcwd(), args.tfrecord)
    print("Successfully created the TFRecord: " + tfrecord_path)


if __name__ == "__main__":
    main()
