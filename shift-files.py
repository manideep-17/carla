import os
import shutil

source_folders = [
    "/home/apg/manideep/carla/out/Town10HD_Opt_28_12_2023_18_09_43/ego0/images/rgb_camera-front",
    "/home/apg/manideep/carla/out/Town10HD_Opt_28_12_2023_18_09_43/ego0/images/rgb_camera-front-left",
    "/home/apg/manideep/carla/out/Town10HD_Opt_28_12_2023_18_09_43/ego0/images/rgb_camera-front-right",

    "/home/apg/manideep/carla/out/Town10HD_Opt_28_12_2023_18_09_43/ego0/images/rgb_camera-back",
    "/home/apg/manideep/carla/out/Town10HD_Opt_28_12_2023_18_09_43/ego0/images/rgb_camera-back-left",
    "/home/apg/manideep/carla/out/Town10HD_Opt_28_12_2023_18_09_43/ego0/images/rgb_camera-back-right",
]

for source_folder in source_folders:
    print(source_folder)
    target_folder = source_folder.replace("rgb", "dvs")
    os.makedirs(target_folder, exist_ok=True)
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.startswith('d'):
                file_path = os.path.join(root, file)
                new_file_path = os.path.join(target_folder, f'{file.replace("dvs-", "")}')
                shutil.move(file_path, new_file_path)

print("Files moved successfully.")
