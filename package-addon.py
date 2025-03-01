#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
import zipfile

# 定义源目录和目标目录
SOURCE_DIR = "custom_components/cleveroom"
DEST_DIR = "releases/cleveroom"
RELEASE_LIBS = "releases/libs"

# 删除目标目录（如果存在）
if os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)

# 将源目录复制到目标目录
shutil.copytree(SOURCE_DIR, DEST_DIR)

# 读取并修改目标目录中的 manifest.json 文件
dest_manifest_path = os.path.join(DEST_DIR, "manifest.json")
if os.path.exists(dest_manifest_path):
    # 读取目标目录中的manifest.json
    with open(dest_manifest_path, 'r') as f:
        manifest_data = json.load(f)

    # 获取版本号
    VERSION = manifest_data.get("version")
    if not VERSION:
        raise ValueError("无法从 manifest.json 中获取版本号")

    # 将requirements节点改成空数组
    manifest_data["requirements"] = []

    # 保存修改后的manifest.json
    with open(dest_manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
else:
    raise FileNotFoundError(f"目标目录中未找到 manifest.json 文件: {dest_manifest_path}")

# 创建klwiot目录（如果不存在）
klwiot_dir = os.path.join(DEST_DIR, "klwiot")
if not os.path.exists(klwiot_dir):
    os.makedirs(klwiot_dir)

# 将libs作为子文件夹复制到klwiot目录下
libs_dest_dir = os.path.join(klwiot_dir, "libs")
if os.path.exists(libs_dest_dir):
    shutil.rmtree(libs_dest_dir)
shutil.copytree(RELEASE_LIBS, libs_dest_dir)

# 定义输出文件名
OUTPUT_FILE = f"releases/cleveroom-{VERSION}.zip"


# 创建目标目录的 zip 归档，排除 _MACOS、隐藏文件、__pycache__ 和 .DS_Store
def should_exclude(file):
    return ('_MACOS' in file or
            file.startswith('.') or
            '__pycache__' in file or
            '.DS_Store' in file)


with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
    original_dir = os.getcwd()
    os.chdir(DEST_DIR)

    for root, dirs, files in os.walk('.'):
        # 过滤掉应该排除的目录
        dirs[:] = [d for d in dirs if not should_exclude(d)]

        for file in files:
            if not should_exclude(file):
                file_path = os.path.join(root, file)
                arcname = file_path
                zipf.write(file_path, arcname)

    os.chdir(original_dir)

# 删除目标目录
shutil.rmtree(DEST_DIR)

# 打印操作完成的消息
print(f"完成: {OUTPUT_FILE}")