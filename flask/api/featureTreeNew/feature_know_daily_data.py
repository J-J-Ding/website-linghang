from featureTreeNew.api_feature_tree import (
    FEATURE_TREE_SCOPE_CONFIG,
    FEATURE_TREE_SOURCE_URLS,
    infer_feature_node_type,
    parse_feature_title_meta,
)


def is_valid_feature_page_title_format(title):
    return bool(parse_feature_title_meta(title))


def get_feature_node_type(title, level=1):
    return infer_feature_node_type(title, level)
