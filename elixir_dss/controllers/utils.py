def dict_list_lookup(dict_list, search_key: str, search_val: str, target_key: str):
    for dict in dict_list:
        if search_key in dict and target_key in dict:
            if dict[search_key] == search_val:
                return dict[target_key]
    return None
