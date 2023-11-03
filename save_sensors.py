import os
import carla
from carla import ColorConverter
import numpy as np
import pygame
import cv2
import traceback

VIEW_WIDTH = 1280
VIEW_HEIGHT = 960
BB_COLOR = (248, 64, 24)
OCCLUDED_COLOR = (0 , 0 , 0)

class ClientSideBoundingBoxes(object):
    """
    This is a module responsible for creating 3D bounding boxes and drawing them
    client-side on pygame surface.
    """

    @staticmethod
    def get_bounding_boxes(vehicles, camera):
        """
        Creates 3D bounding boxes based on carla vehicle list and camera.
        """
        bounding_boxes = [ClientSideBoundingBoxes.get_bounding_box(vehicle, camera) for vehicle in vehicles]
        # filter objects behind camera
        bounding_boxes = [bb for bb in bounding_boxes if all(bb[:, 2] > 0)]
        return bounding_boxes

    @staticmethod
    def get_bounding_box(vehicle, camera):
        """
        Returns 3D bounding box for a vehicle based on camera view.
        """

        bb_cords = ClientSideBoundingBoxes._create_bb_points(vehicle)
        cords_x_y_z = ClientSideBoundingBoxes._vehicle_to_sensor(bb_cords, vehicle, camera)[:3, :]
        
        cords_y_minus_z_x = np.concatenate([cords_x_y_z[1, :], -cords_x_y_z[2, :], cords_x_y_z[0, :]])
        
        calibration = np.identity(3)
        calibration[0, 2] = VIEW_WIDTH / 2.0
        calibration[1, 2] = VIEW_HEIGHT / 2.0
        calibration[0, 0] = calibration[1, 1] = VIEW_WIDTH / (2.0 * np.tan(70 * np.pi / 360.0))

        bbox = np.transpose(np.dot(calibration, cords_y_minus_z_x))
        camera_bbox = np.concatenate([bbox[:, 0] / bbox[:, 2], bbox[:, 1] / bbox[:, 2], bbox[:, 2]], axis=1)
        return camera_bbox
    


    @staticmethod
    def _create_bb_points(vehicle):
        """
        Returns 3D bounding box for a vehicle.
        """

        cords = np.zeros((8, 4))
        extent = vehicle.bounding_box.extent
        cords[0, :] = np.array([extent.x, extent.y, -extent.z, 1])
        cords[1, :] = np.array([-extent.x, extent.y, -extent.z, 1])
        cords[2, :] = np.array([-extent.x, -extent.y, -extent.z, 1])
        cords[3, :] = np.array([extent.x, -extent.y, -extent.z, 1])
        cords[4, :] = np.array([extent.x, extent.y, extent.z, 1])
        cords[5, :] = np.array([-extent.x, extent.y, extent.z, 1])
        cords[6, :] = np.array([-extent.x, -extent.y, extent.z, 1])
        cords[7, :] = np.array([extent.x, -extent.y, extent.z, 1])
        return cords
    
    @staticmethod
    def _vehicle_to_sensor(cords, vehicle, sensor):
        """
        Transforms coordinates of a vehicle bounding box to sensor.
        """

        world_cord = ClientSideBoundingBoxes._vehicle_to_world(cords, vehicle)
        sensor_cord = ClientSideBoundingBoxes._world_to_sensor(world_cord, sensor)
        return sensor_cord

    @staticmethod
    def _vehicle_to_world(cords, vehicle):
        """
        Transforms coordinates of a vehicle bounding box to world.
        """

        bb_transform = carla.Transform(vehicle.bounding_box.location)
        bb_vehicle_matrix = ClientSideBoundingBoxes.get_matrix(bb_transform)
        vehicle_world_matrix = ClientSideBoundingBoxes.get_matrix(vehicle.get_transform())
        bb_world_matrix = np.dot(vehicle_world_matrix, bb_vehicle_matrix)
        world_cords = np.dot(bb_world_matrix, np.transpose(cords))
        return world_cords

    @staticmethod
    def _world_to_sensor(cords, sensor):
        """
        Transforms world coordinates to sensor.
        """

        sensor_world_matrix = ClientSideBoundingBoxes.get_matrix(sensor.get_transform())
        world_sensor_matrix = np.linalg.inv(sensor_world_matrix)
        sensor_cords = np.dot(world_sensor_matrix, cords)
        return sensor_cords

    @staticmethod
    def get_matrix(transform):
        """
        Creates matrix from carla transform.
        """

        rotation = transform.rotation
        location = transform.location
        c_y = np.cos(np.radians(rotation.yaw))
        s_y = np.sin(np.radians(rotation.yaw))
        c_r = np.cos(np.radians(rotation.roll))
        s_r = np.sin(np.radians(rotation.roll))
        c_p = np.cos(np.radians(rotation.pitch))
        s_p = np.sin(np.radians(rotation.pitch))
        matrix = np.matrix(np.identity(4))
        matrix[0, 3] = location.x
        matrix[1, 3] = location.y
        matrix[2, 3] = location.z
        matrix[0, 0] = c_p * c_y
        matrix[0, 1] = c_y * s_p * s_r - s_y * c_r
        matrix[0, 2] = -c_y * s_p * c_r - s_y * s_r
        matrix[1, 0] = s_y * c_p
        matrix[1, 1] = s_y * s_p * s_r + c_y * c_r
        matrix[1, 2] = -s_y * s_p * c_r + c_y * s_r
        matrix[2, 0] = s_p
        matrix[2, 1] = -c_p * s_r
        matrix[2, 2] = c_p * c_r
        return matrix
    
    @staticmethod
    def get_bounding_boxes_parked_vehicles(bboxes, camera):
        """
        Creates 3D bounding boxes based on carla vehicle list and camera.
        """
        bounding_boxes = [ClientSideBoundingBoxes.get_bounding_box_parked_vehicle(vehicle, camera) for vehicle in bboxes]
        # filter objects behind camera
        bounding_boxes = [bb for bb in bounding_boxes if all(bb[:, 2] > 0)]
        return bounding_boxes
    
    @staticmethod
    def get_bounding_box_parked_vehicle(bbox, camera):
        """
        Returns 3D bounding box for a vehicle based on camera view.
        """
        print(bbox, "*****")
        bb_cords = ClientSideBoundingBoxes._bounding_box_to_world(bbox)

        cords_x_y_z = ClientSideBoundingBoxes._world_to_sensor(bb_cords, camera)[:3, :]
        cords_y_minus_z_x = np.concatenate([cords_x_y_z[1, :], -cords_x_y_z[2, :], cords_x_y_z[0, :]])
        calibration = np.identity(3)
        calibration[0, 2] = VIEW_WIDTH / 2.0
        calibration[1, 2] = VIEW_HEIGHT / 2.0
        calibration[0, 0] = calibration[1, 1] = VIEW_WIDTH / (2.0 * np.tan(70 * np.pi / 360.0))
        bbox = np.transpose(np.dot(calibration, cords_y_minus_z_x))
        camera_bbox = np.concatenate([bbox[:, 0] / bbox[:, 2], bbox[:, 1] / bbox[:, 2], bbox[:, 2]], axis=1)
        return camera_bbox
    
    @staticmethod
    def _bounding_box_to_world(bbox):
        extent = bbox.extent

        cords = np.zeros((8, 4))
        cords[0, :] = np.array([extent.x, extent.y, -extent.z, 1])
        cords[1, :] = np.array([-extent.x, extent.y, -extent.z, 1])
        cords[2, :] = np.array([-extent.x, -extent.y, -extent.z, 1])
        cords[3, :] = np.array([extent.x, -extent.y, -extent.z, 1])
        cords[4, :] = np.array([extent.x, extent.y, extent.z, 1])
        cords[5, :] = np.array([-extent.x, extent.y, extent.z, 1])
        cords[6, :] = np.array([-extent.x, -extent.y, extent.z, 1])
        cords[7, :] = np.array([extent.x, -extent.y, extent.z, 1])

        world_matrix = ClientSideBoundingBoxes.get_matrix(bbox)

        world_cords = np.dot(world_matrix, np.transpose(cords))

        return world_cords
    
    @staticmethod
    def _create_bb_points_parked(vehicle):
        """
        Returns 3D bounding box for a vehicle.
        """

        cords = np.zeros((8, 4))
        if isinstance(vehicle, carla.BoundingBox):
            extent = vehicle.extent
        else:
            extent = vehicle.bounding_box.extent
        cords[0, :] = np.array([extent.x, extent.y, -extent.z, 1])
        cords[1, :] = np.array([-extent.x, extent.y, -extent.z, 1])
        cords[2, :] = np.array([-extent.x, -extent.y, -extent.z, 1])
        cords[3, :] = np.array([extent.x, -extent.y, -extent.z, 1])
        cords[4, :] = np.array([extent.x, extent.y, extent.z, 1])
        cords[5, :] = np.array([-extent.x, extent.y, extent.z, 1])
        cords[6, :] = np.array([-extent.x, -extent.y, extent.z, 1])
        cords[7, :] = np.array([extent.x, -extent.y, extent.z, 1])
        return cords

edges = [[0,1], [1,3], [3,2], [2,0], [0,4], [4,5], [5,1], [5,7], [7,6], [6,4], [6,2], [7,3]]

def saveAllSensors(out_root_folder, sensor_datas, sensor_types, world):

    #TODO have it find the snapshot object dynamically instead of using the hardcoded 0 index
    (sensor_data, sensor, vehicle) = sensor_datas[0]
    saveSnapshot(out_root_folder, sensor_data)
    sensor_datas.pop(0)

    depth_camera = {}
    rgb_camera = {}
    is_camera = {}
    sematic_seg_camera = {}
    ray_cast = {}

    for i in range(len(sensor_datas)):
        (sensor_data, sensor, vehicle) = sensor_datas[i]
        sensor_name = sensor_types[i]
        
        if(sensor_name.find('dvs') != -1):
            dvs_callback(sensor_data[i], os.path.join(out_root_folder, sensor_name))

        if(sensor_name.find('optical_flow') != -1):
            optical_camera_callback(sensor_data[i], os.path.join(out_root_folder, sensor_name))

        if(sensor_name.find('instance_segmentation_camera') != -1):
            is_camera[sensor_name] = sensor_data
            saveISImage(sensor_data, os.path.join(out_root_folder, sensor_name))
            pass

        if(sensor_name.find('semantic_segmentation_camera') != -1):
            sematic_seg_camera[sensor_name] = sensor_data
            # saveSegImage(sensor_data, os.path.join(out_root_folder, sensor_name))

        if(sensor_name.find('depth_camera') != -1):
            depth_camera[sensor_name] = sensor_data
            original_string = sensor_name
            new_string = original_string.replace("depth", "rgb")
            if sensor_name in depth_camera and new_string in rgb_camera :
                print("from depth")

        if(sensor_name.find('rgb_camera') != -1):
            try:
                rgb_camera[sensor_name] = (sensor_data[i], os.path.join(out_root_folder, sensor_name))
                original_string = sensor_name
                print("from rgb")
                saveRgbImage(sensor_data, os.path.join(out_root_folder, sensor_name), world, sensor, vehicle, ray_cast["ray_cast_semantic-front"], ray_cast["ray_cast_semantic-front-2"], is_camera["instance_segmentation_camera-front"])
            except Exception as error:
                print("An exception occurred in rgb_camera:", error)
                traceback.print_exc()
            # print("sensor_name" , sensor_name)
            # if( depth_camera[sensor_name] )
            # saveDepthImage(sensor_data[i], os.path.join(out_root_folder, sensor_name))

        if(sensor_name.find('imu') != -1):
            saveImu(sensor_data[i], os.path.join(out_root_folder, sensor_name), sensor_name)

        if(sensor_name.find('gnss') != -1):
            saveGnss(sensor_data[i], os.path.join(out_root_folder, sensor_name), sensor_name)

        if(sensor_name == 'sensor.lidar.ray_cast' or sensor_name == 'sensor.lidar.ray_cast_semantic' or sensor_name.find('ray_cast_semantic') != -1):
            print(sensor_name, "---")
            ray_cast[sensor_name] = sensor_data
        # if(sensor_name.find('lidar') != -1):
            # saveLidar(sensor_data, os.path.join(out_root_folder, sensor_name))
    return

def saveSnapshot(output, filepath):
    return

def saveSteeringAngle(value, filepath):
    with open(filepath + "/steering_norm.txt", 'a') as fp:
        fp.writelines(str(value) + ", ")
    with open(filepath + "/steering_true.txt", 'a') as fp:
        fp.writelines(str(70*value) + ", ")

def saveGnss(output, filepath, sensor_name):
    with open(filepath + "/" + sensor_name + ".txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")

def saveImu(output, filepath, sensor_name):
    with open(filepath + "/" + sensor_name + ".txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")

def saveLidar(output, filepath):
    pass
    try:
        hit_actors = set()
        print(output)
        # print(output.raw_data)
        for detection in output:
            if detection.object_idx is not 0:
                hit_actors.add(detection.object_idx)
        print("Hit actors:", hit_actors)
        pass
    except Exception as error:
        print("An exception occurred:", error)
        traceback.print_exc()
    # output.save_to_disk(filepath + '/%05d'%output.frame)
    # with open(filepath + "/lidar_metadata.txt", 'a') as fp:
    #     fp.writelines(str(output) + ", ")
    #     fp.writelines(str(output.transform) + "\n")

def build_projection_matrix(w, h, fov):
    focal = w / (2.0 * np.tan(fov * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = w / 2.0
    K[1, 2] = h / 2.0
    return K

def get_image_point(loc, K, w2c):
    # Calculate 2D projection of 3D coordinate

    # Format the input coordinate (loc is a carla.Position object)
    point = np.array([loc.x, loc.y, loc.z, 1])
    # transform to camera coordinates
    point_camera = np.dot(w2c, point)

    # New we must change from UE4's coordinate system to an "standard"
    # (x, y ,z) -> (y, -z, x)
    # and we remove the fourth componebonent also
    point_camera = [point_camera[1], -point_camera[2], point_camera[0]]

    # now project 3D->2D using the camera matrix
    point_img = np.dot(K, point_camera)
    # normalize
    point_img[0] /= point_img[2]
    point_img[1] /= point_img[2]

    return point_img[0:2]

def get_2d_bounding_box(points):
    sorted_points = sort_points_clockwise(points)

    min_x = min(point[0] for point in sorted_points)
    min_y = min(point[1] for point in sorted_points)
    max_x = max(point[0] for point in sorted_points)
    max_y = max(point[1] for point in sorted_points)

    return int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y)

def get_bounding_box_center(bounding_box):
    x, y, w, h = bounding_box
    center_x = x + w // 2
    center_y = y + h // 2
    return center_x, center_y

def sort_points_clockwise(points):
    center = np.mean(points, axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    sorted_indices = np.argsort(angles)
    return points[sorted_indices]

def draw_bounding_box(image, bounding_box, color=(0, 255, 0), thickness=2):
    x, y, w, h = bounding_box
    cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)

def draw_bounding_box_center(image, center, color=(0, 0, 0), radius=5):
    cv2.circle(image, center, radius, color, -1)

def draw_bounding_box_corners(image, points, color=(0, 0, 255), thickness=2):
    for i in range(4):
        cv2.line(image, tuple(points[i]), tuple(points[(i + 1) % 4]), color, thickness)


def saveRgbImage(output, filepath, world, sensor, vehicle, raycast_detection, raycast_detection2, instance_seg):

    try:
        print("saving rgb")
        # bounding_box_set = world.get_level_bbs(carla.CityObjectLabel.TrafficLight)
        # bounding_box_set.extend(world.get_level_bbs(carla.CityObjectLabel.TrafficSigns))

        

        # world_2_camera = np.array(sensor.get_transform().get_inverse_matrix())
        # K = build_projection_matrix(output.width, output.height, output.fov)
        img = np.frombuffer(output.raw_data, dtype=np.uint8).reshape(
        (output.height, output.width, 4))

        instance_data = np.frombuffer(instance_seg.raw_data, dtype=np.uint8).reshape(
        (instance_seg.height, instance_seg.width, 4))

        hit_actors = set()
        for detection in raycast_detection:
            if detection.object_idx is not 0:
                hit_actors.add(detection.object_idx)
        
        for detection in raycast_detection2:
            if detection.object_idx is not 0:
                hit_actors.add(detection.object_idx)

        print(print(dir(carla.CityObjectLabel)))
        
        print(carla.CityObjectLabel.Car)
        bbs = world.get_level_bbs(carla.CityObjectLabel.Car)
        print(bbs)
        bounding_boxes = ClientSideBoundingBoxes.get_bounding_boxes_parked_vehicles(bbs, sensor)
        
        for bbox in bounding_boxes:
            points = [(int(bbox[i, 0]), int(bbox[i, 1])) for i in range(8)]
            cv2.line(img, points[0], points[1], BB_COLOR, 1)
            cv2.line(img, points[0], points[1], BB_COLOR, 1)
            cv2.line(img, points[1], points[2], BB_COLOR, 1)
            cv2.line(img, points[2], points[3], BB_COLOR, 1)
            cv2.line(img, points[3], points[0], BB_COLOR, 1)
            cv2.line(img, points[4], points[5], BB_COLOR, 1)
            cv2.line(img, points[5], points[6], BB_COLOR, 1)
            cv2.line(img, points[6], points[7], BB_COLOR, 1)
            cv2.line(img, points[7], points[4], BB_COLOR, 1)
            cv2.line(img, points[0], points[4], BB_COLOR, 1)
            cv2.line(img, points[1], points[5], BB_COLOR, 1)
            cv2.line(img, points[2], points[6], BB_COLOR, 1)
            cv2.line(img, points[3], points[7], BB_COLOR, 1)
        
        # for vehicle in world.get_actors().filter('*vehicle*'):
        #     if vehicle.id in hit_actors:
        #     # if 1==1:
        #         bounding_boxes = ClientSideBoundingBoxes.get_bounding_boxes([vehicle], sensor)
        #         for bbox in bounding_boxes:
        #             points = [(int(bbox[i, 0]), int(bbox[i, 1])) for i in range(8)]
        #             bounding_box = get_2d_bounding_box(np.array(points, dtype=np.int32))
        #             center = get_bounding_box_center(bounding_box)

        #             # Draw each bounding box and its center on the image
        #             # draw_bounding_box(img, bounding_box)
        #             # draw_bounding_box_center(img, center)
        #             # draw_bounding_box_corners(img, points)
        #             center_x, center_y = center
        #             print(center_x, center_y, "--center of bb")
        #             if not (0 <= center_x < instance_data.shape[0] and 0 <= center_y < instance_data.shape[1]):
        #                 print("Nope")
        #             else:
        #                 tag = instance_data[center_y,center_x, 2]
        #                 print("Tag", tag)
        #                 if tag == 15 or tag == 14:
        #                     cv2.line(img, points[0], points[1], BB_COLOR, 1)
        #                     cv2.line(img, points[0], points[1], BB_COLOR, 1)
        #                     cv2.line(img, points[1], points[2], BB_COLOR, 1)
        #                     cv2.line(img, points[2], points[3], BB_COLOR, 1)
        #                     cv2.line(img, points[3], points[0], BB_COLOR, 1)
        #                     cv2.line(img, points[4], points[5], BB_COLOR, 1)
        #                     cv2.line(img, points[5], points[6], BB_COLOR, 1)
        #                     cv2.line(img, points[6], points[7], BB_COLOR, 1)
        #                     cv2.line(img, points[7], points[4], BB_COLOR, 1)
        #                     cv2.line(img, points[0], points[4], BB_COLOR, 1)
        #                     cv2.line(img, points[1], points[5], BB_COLOR, 1)
        #                     cv2.line(img, points[2], points[6], BB_COLOR, 1)
        #                     cv2.line(img, points[3], points[7], BB_COLOR, 1)
                            
                    
                    

                    # if 0 <= center_x < semantic_data.shape[1] and 0 <= center_y < semantic_data.shape[0]:
                    #     r_value = semantic_data[center_y, center_x]
                    #     print(r_value, "rvalue")
                    #     # tag = tag_mapping.get(r_value, 'Unknown')
                    #     # print(f"Tag: {tag}")
                    # else:
                    #     print("Center coordinates are out of bounds.")

                    # Get the R value at the center coordinates
                    # r_value = semantic_data[center_y, center_x, 2]
                    # print(r_value)
                    # cv2.line(img, points[0], points[1], BB_COLOR, 1)
                    # cv2.line(img, points[0], points[1], BB_COLOR, 1)
                    # cv2.line(img, points[1], points[2], BB_COLOR, 1)
                    # cv2.line(img, points[2], points[3], BB_COLOR, 1)
                    # cv2.line(img, points[3], points[0], BB_COLOR, 1)
                    # cv2.line(img, points[4], points[5], BB_COLOR, 1)
                    # cv2.line(img, points[5], points[6], BB_COLOR, 1)
                    # cv2.line(img, points[6], points[7], BB_COLOR, 1)
                    # cv2.line(img, points[7], points[4], BB_COLOR, 1)
                    # cv2.line(img, points[0], points[4], BB_COLOR, 1)
                    # cv2.line(img, points[1], points[5], BB_COLOR, 1)
                    # cv2.line(img, points[2], points[6], BB_COLOR, 1)
                    # cv2.line(img, points[3], points[7], BB_COLOR, 1)
        
        # for vehicle in world.get_actors().filter('*pedestrian*'):
        #     if vehicle.id in hit_actors:
        #         bounding_boxes = ClientSideBoundingBoxes.get_bounding_boxes([vehicle], sensor)
        #         for bbox in bounding_boxes:
        #             points = [(int(bbox[i, 0]), int(bbox[i, 1])) for i in range(8)]
        #             cv2.line(img, points[0], points[1], BB_COLOR, 1)
        #             cv2.line(img, points[0], points[1], BB_COLOR, 1)
        #             cv2.line(img, points[1], points[2], BB_COLOR, 1)
        #             cv2.line(img, points[2], points[3], BB_COLOR, 1)
        #             cv2.line(img, points[3], points[0], BB_COLOR, 1)
        #             cv2.line(img, points[4], points[5], BB_COLOR, 1)
        #             cv2.line(img, points[5], points[6], BB_COLOR, 1)
        #             cv2.line(img, points[6], points[7], BB_COLOR, 1)
        #             cv2.line(img, points[7], points[4], BB_COLOR, 1)
        #             cv2.line(img, points[0], points[4], BB_COLOR, 1)
        #             cv2.line(img, points[1], points[5], BB_COLOR, 1)
        #             cv2.line(img, points[2], points[6], BB_COLOR, 1)
        #             cv2.line(img, points[3], points[7], BB_COLOR, 1)
                

        output_file = os.path.join(
        filepath, f'{output.frame}.png')
        cv2.imwrite(output_file, img)
        
        return

        bounding_boxes = ClientSideBoundingBoxes.get_bounding_boxes(world.get_actors().filter('*vehicle*'), sensor, depth)
        for bbox in bounding_boxes:
            occluded = False
            points = [(int(bbox[i, 0]), int(bbox[i, 1])) for i in range(8)]
            # for point in points:
            #     x, y = point

            #     print(x, y)
            #     if x <= 1280 and x >= 0 and y >= 0 and y <= 960:
            #         depth_value = depth[y, x]  # Get depth value at this pixel
                    
            #         # Check if the depth value of the point is greater than the depth value in the depth image
            #         if (depth_value < bbox[2, 2]).any():
            #             occluded = True
            #             break
            if not occluded:
                cv2.line(img, points[0], points[1], BB_COLOR, 1)
                cv2.line(img, points[0], points[1], BB_COLOR, 1)
                cv2.line(img, points[1], points[2], BB_COLOR, 1)
                cv2.line(img, points[2], points[3], BB_COLOR, 1)
                cv2.line(img, points[3], points[0], BB_COLOR, 1)

                cv2.line(img, points[4], points[5], BB_COLOR, 1)
                cv2.line(img, points[5], points[6], BB_COLOR, 1)
                cv2.line(img, points[6], points[7], BB_COLOR, 1)
                cv2.line(img, points[7], points[4], BB_COLOR, 1)

                cv2.line(img, points[0], points[4], BB_COLOR, 1)
                cv2.line(img, points[1], points[5], BB_COLOR, 1)
                cv2.line(img, points[2], points[6], BB_COLOR, 1)
                cv2.line(img, points[3], points[7], BB_COLOR, 1)
            else:
                cv2.line(img, points[0], points[1], OCCLUDED_COLOR, 1)
                cv2.line(img, points[0], points[1], OCCLUDED_COLOR, 1)
                cv2.line(img, points[1], points[2], OCCLUDED_COLOR, 1)
                cv2.line(img, points[2], points[3], OCCLUDED_COLOR, 1)
                cv2.line(img, points[3], points[0], OCCLUDED_COLOR, 1)

                cv2.line(img, points[4], points[5], OCCLUDED_COLOR, 1)
                cv2.line(img, points[5], points[6], OCCLUDED_COLOR, 1)
                cv2.line(img, points[6], points[7], OCCLUDED_COLOR, 1)
                cv2.line(img, points[7], points[4], OCCLUDED_COLOR, 1)

                cv2.line(img, points[0], points[4], OCCLUDED_COLOR, 1)
                cv2.line(img, points[1], points[5], OCCLUDED_COLOR, 1)
                cv2.line(img, points[2], points[6], OCCLUDED_COLOR, 1)
                cv2.line(img, points[3], points[7], OCCLUDED_COLOR, 1)

        # for npc in world.get_actors().filter('*pedestrian*'):

        #     # Filter out the ego vehicle
        #     if npc.id != vehicle.id:

        #         bb = npc.bounding_box
        #         dist = npc.get_transform().location.distance(vehicle.get_transform().location)

        #         # Filter for the vehicles within 50m
        #         if dist < 50:

        #         # Calculate the dot product between the forward vector
        #         # of the vehicle and the vector between the vehicle
        #         # and the other vehicle.get_transform(). We threshold this dot product
        #         # to limit to drawing bounding boxes IN FRONT OF THE CAMERA
        #             forward_vec = output.transform.get_forward_vector()
        #             ray = npc.get_transform().location - vehicle.get_transform().location

        #             if forward_vec.dot(ray) > 1:
        #                 p1 = get_image_point(bb.location, K, world_2_camera)
        #                 verts = [v for v in bb.get_world_vertices(npc.get_transform())]
        #                 for edge in edges:
        #                     p1 = get_image_point(verts[edge[0]], K, world_2_camera)
        #                     p2 = get_image_point(verts[edge[1]],  K, world_2_camera)
        #                     cv2.line(img, (int(p1[0]),int(p1[1])), (int(p2[0]),int(p2[1])), (255,255,255, 255), 1)   
        
        output_file = os.path.join(
        filepath, f'{output.frame}.png')
        cv2.imwrite(output_file, img)
        # output.save_to_disk(filepath + '/%05d'%output.frame)
        # with open(filepath + "/rgb_camera_metadata.txt", 'a') as fp:
        #     fp.writelines(str(output) + ", ")
        #     fp.writelines(str(output.transform) + "\n")
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)
        traceback.print_exc()

def saveISImage(output, filepath):
    try:
        output.save_to_disk(filepath + '/%05d'%output.frame)
        with open(filepath + "/rgb_camera_metadata.txt", 'a') as fp:
            fp.writelines(str(output) + ", ")
            fp.writelines(str(output.transform) + "\n")
        # image_data = np.frombuffer(output.raw_data, dtype=np.uint8).reshape(
        # (output.height, output.width, 4))
        # # print(image)
        # red_channel = image_data[:, :, 2]  # Red channel
        # green_channel = image_data[:, :, 1]  # Green channel
        # blue_channel = image_data[:, :, 0]  # Blue channel
        # unique_instance_ids = set()
        # # Iterate through the image and identify vehicles and pedestrians
        # for y in range(image_data.shape[0]):
        #     for x in range(image_data.shape[1]):
        #         red_value = red_channel[y, x]
        #         green_value = green_channel[y, x]
        #         blue_value = blue_channel[y, x]

        #         # Calculate instance ID
        #         instance_id = (green_value << 8) | blue_value
        #         unique_instance_ids.add(instance_id)
        #         # # Check for vehicles (semantic tag 10) and pedestrians (other semantic tag)
        #         # if red_value == 10:  # Semantic tag for vehicles
        #         #     print(f"Vehicle ID: {instance_id}")
        #         # else:  # Assuming other semantic tags represent pedestrians
        #         #     print(f"Pedestrian ID: {instance_id}")
        # print(unique_instance_ids)
        
    except Exception as error:
        # handle the exception
        print("An exception occurred:", error)

def dvs_callback(data, filepath):
    timestamp = data.timestamp
    dvs_events = np.frombuffer(data.raw_data, dtype=np.dtype([
        ('x', np.uint16), ('y', np.uint16), ('t', np.int64), ('pol', np.bool)]))
    dvs_img = np.zeros((data.height, data.width, 3), dtype=np.uint8)
    dvs_img[dvs_events[:]['y'], dvs_events[:]
            ['x'], dvs_events[:]['pol'] * 2] = 255
    surface = pygame.surfarray.make_surface(dvs_img.swapaxes(0, 1))
    # output_folder = os.path.join(
    #     'out', 'dvs')
    # os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(filepath, f'{data.frame}.png')
    pygame.image.save(surface, output_file)

def optical_camera_callback(image, filepath):
    width = image.width
    height = image.height

    # Convert the raw data to a numpy array of 32-bit floats
    image_data = np.frombuffer(image.raw_data, dtype=np.float32)

    # Reshape the image data to the correct shape (height, width, 2)
    image_data = image_data.reshape((height, width, 2))

    # Extract the magnitude of the optical flow vectors
    magnitude = np.sqrt(np.sum(image_data ** 2, axis=2))

    # Normalize the magnitude values to the range [0, 255] for visualization
    normalized_magnitude = cv2.normalize(
        magnitude, None, 0, 255, cv2.NORM_MINMAX)

    # Convert the magnitude values to 8-bit BGR format (for visualization)
    bgr_image = cv2.applyColorMap(
        normalized_magnitude.astype(np.uint8), cv2.COLORMAP_JET)

    # output_folder = os.path.join(
    #     'out', 'optical')
    # os.makedirs(output_folder, exist_ok=True)
    filename = os.path.join(filepath, f"{image.frame}.png")
    cv2.imwrite(filename, bgr_image)

def saveDepthImage(output, filepath):
    output.convert(carla.ColorConverter.Depth)
    output.save_to_disk(filepath + '/%05d'%output.frame)
    with open(filepath + "/depth_camera_metadata.txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")

def saveSegImage(output, filepath):
    output.convert(carla.ColorConverter.CityScapesPalette)
    output.save_to_disk(filepath + '/%05d'%output.frame)

    image_data = np.array(output.raw_data)
    image_data = image_data.reshape((output.height, output.width, 4))
    semantic_image = image_data[:, :, :3]

    with open(filepath + "/seg_camera_metadata.txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")

def saveDvsImage(output, filepath):
    output.convert(carla.ColorConverter.CityScapesPalette)
    output.save_to_disk(filepath + '/%05d'%output.frame)
    with open(filepath + "/seg_camera_metadata.txt", 'a') as fp:
        fp.writelines(str(output) + ", ")
        fp.writelines(str(output.transform) + "\n")