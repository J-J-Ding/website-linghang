def has_empty_value(d):
    return any(
        value is None or 
        value == '' or 
        (isinstance(value, (list, dict, set)) and not value)
        for value in d.values()
    )
def handle_factor_value_src(factor_value_src_description):
    if '0101' in factor_value_src_description:
        return "business_model_rate_table,network_element_business_model_rate"
    elif '0103' in factor_value_src_description:
        return "business_model_table,network_element_business_model"
    elif '0301' in factor_value_src_description:
        return "feature_relation_table,feature_name"
    else:
        return None
    