import json
import os
import shutil
import traceback

appdata = os.getenv('APPDATA')  # user appdata roaming directory. DO NOT MODIFY THIS LINE
# the index.json file, normally is in your .minecraft folder
assets_indexes_file = appdata + '\\.minecraft\\assets\\indexes\\1.16.json'
# the actual files for the vanilla minecraft, normally is in your .minecraft folder
# change this line and the previous line if your .minecraft folder is not in the default location as currently written
mc_sources = appdata + '\\.minecraft\\assets\\objects'
# target path where you want your files to be extracted. default is in the 'MCDefault' folder from you 'download' folder
target_path = os.getenv('USERPROFILE') + '\\Downloads\\MCDefault'


def read_json(input_file):
    d = json.load(open(input_file, "r"))
    for i in d.values():
        for keys, values in i.items():
            for key, value in values.items():
                if 'hash' in key:
                    directories = keys.split('/')
                    name = directories[len(directories) - 1]
                    path_name = target_path + '\\'
                    for j in range(len(directories) - 1):
                        path_name += directories[j] + '\\'
                        if not os.path.isdir(path_name):
                            os.makedirs(path_name)
                            print('path' + path_name + ' not exist, creating them...')
                    print('creating ' + path_name + name)
                    try:
                        copy(name, value, mc_sources, path_name)
                    except (OSError, TypeError, Exception) as e:
                        if type(e) == OSError:
                            print('ERROR: File not found or unavailable, please make sure you have the right path!')
                        elif type(e) == TypeError:
                            print('ERROR: you do not have this file in this directory yet, or you have not yet '
                                  'download this game version.')
                        else:
                            traceback.print_exc()


# from https://stackoverflow.com/questions/1724693/find-a-file-in-python
def find(filename, path):
    for root, d, files in os.walk(path):
        if filename in files:
            print('found file ' + filename + ' from ' + path)
            return os.path.join(root, filename)


def copy(filename, file, path, destination):
    file_path = find(file, path)
    print('searching for files in ' + file_path)
    shutil.copy(file_path, destination)
    if os.path.exists(destination + '\\' + filename):
        print(filename + ' already exist!')
    else:
        print("renaming file to " + filename)
        os.rename(destination + '\\' + file, destination + '\\' + filename)
    if os.path.exists(destination + '\\' + file):
        print('remove redundant file ' + file)
        os.unlink(destination + file)


if __name__ == '__main__':
    read_json(assets_indexes_file)
    print('Done!')
