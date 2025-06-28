from datetime import datetime
import pickle
import os


def save_object_to_file(save_path, file_name, file_extension, object_to_save, add_date_time_to_name):
    if save_path != "":
        if save_path[-1] != "/":
            save_path = save_path + "/"

    if add_date_time_to_name:
        now = datetime.now().strftime("_%Y_%m_%d_%H_%M_%S")
        file_full_name = save_path + file_name + now + "." + file_extension
    else:
        file_full_name = save_path + file_name + "." + file_extension

    with open(file_full_name, 'wb') as file:
        pickle.dump(object_to_save, file)
    file.close()


def load_object_from_file(file_full_name):
    if not os.path.exists(file_full_name):
        return "no file"
    with open(file_full_name, 'rb') as file:
        object_to_load = pickle.load(file)
    file.close()

    return object_to_load
