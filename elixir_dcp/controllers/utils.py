import hashlib

def get_names_from_oidc(oidc_name):

    result = ['', '']
    if oidc_name is not None:
        if " " in oidc_name:
            name_list = oidc_name.split(" ")
            result[0] = name_list[0]
            if len(name_list) > 1:
                result[1] = name_list[1]
    return result


def equal_long_strings(str1: str, str2: str):

    if str1 is not None and str2 is not None:
        h1 = hashlib.sha1(str1.encode('utf-8'))
        h2 = hashlib.sha1(str2.encode('utf-8'))
        return h1.hexdigest() == h2.hexdigest()
    elif str1 is None and str2 is None:
        return True
    else:
        return False


def dict_list_lookup(dict_list, search_key: str, search_val: str, target_key: str):
    for dict in dict_list:
        if search_key in dict and target_key in dict:
            if dict[search_key] == search_val:
                return dict[target_key]
    return None



