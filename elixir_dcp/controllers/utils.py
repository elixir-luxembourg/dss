

def get_names_from_oidc(oidc_name):
    result = ['', '']

    if oidc_name is not None:
        if " " in oidc_name:
            name_list = oidc_name.split(" ")
            result[0] = name_list[0]
            if len(name_list) > 1:
                result[1] = name_list[1]
    return result
