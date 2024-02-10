import numpy as np
import os
from tqdm import tqdm

input_directories = [
    # '/home/apg/manideep/carla/out/egoD1/ego0/annotations/dvs/dvs_camera-back/npz',
    # '/home/apg/manideep/carla/out/egoD1/ego0/annotations/dvs/dvs_camera-back-left/npz',
    # '/home/apg/manideep/carla/out/egoD1/ego0/annotations/dvs/dvs_camera-back-right/npz',
    # '/home/apg/manideep/carla/out/egoD1/ego0/annotations/dvs/dvs_camera-front/npz',
    # '/home/apg/manideep/carla/out/egoD1/ego0/annotations/dvs/dvs_camera-front-left/npz',
    '/home/apg/manideep/carla/out/egoD1/ego0/annotations/dvs/dvs_camera-front-right/npz',
]

for input_directory in input_directories:
    result = input_directory.split('/')[-2]
    compiled_output_file_path = f'/home/apg/manideep/carla/out/compiled-{result}.npz'

    compiled_data = {}
    all_files = sorted([filename for filename in os.listdir(input_directory) if filename.endswith(".npz")],
                       key=lambda x: int(x.split('-')[0]))

    for filename in tqdm(all_files, desc=f"Processing files in {result}"):
        if filename.endswith(".npz"):
            file_path = os.path.join(input_directory, filename)
            file_number = str(filename.split('-')[0])
            loaded_data = np.load(file_path)
            dvs_events = loaded_data['dvs_events']
            compiled_data[file_number] = dvs_events

    np.savez_compressed(compiled_output_file_path, **compiled_data)
