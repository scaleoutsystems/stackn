import json
import yaml


def dump_to_file(data, name, path):
    success = True
    try:
        with open(path + '/' + name + '.json', 'w') as outfile:
            json.dump(data, outfile)
    except:
        success = False

    if not success:
        import pickle
        try:
            with open(path + name + '.pkl', 'wb') as outfile:
                pickle.dump(data, outfile)
            success = True
        except:
            success = False

    return success


def load_from_file(name, path):
    success = True
    data = None
    try:
        with open(path + '/' + name + '.json', 'r') as infile:
            data = json.load(infile)
    except:
        success = False
        pass

    if not success:
        try:
            with open(path + '/' + name + '.yaml', 'r') as infile:
                tmp = infile.read()
                data = yaml.load(tmp, Loader=yaml.FullLoader)
            success = True
        except:
            success = False
            pass

    if not success:
        import pickle
        try:
            with open(path + '/' + name + '.pkl', 'rb') as infile:
                data = pickle.load(infile)
            success = True
        except:
            success = False
            pass

    return data, success
