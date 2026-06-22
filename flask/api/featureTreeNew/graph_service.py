from featureTreeNew.api_feature_graph import (
    build_feature_graph_from_online_seed,
    build_feature_graph_from_tree,
    feature_relation_label,
)


class FeatureGraphService:
    def generate_graph(self, seed_feature_id, scope, max_depth=2, seed_title="", seed_url=""):
        graph_data, error_message = build_feature_graph_from_tree(seed_feature_id, scope, max_depth)
        if graph_data:
            return graph_data
        graph_data, error_message = build_feature_graph_from_online_seed(
            seed_feature_id,
            seed_title,
            seed_url,
            scope,
            max_depth,
        )
        if graph_data:
            return graph_data
        raise ValueError(error_message or f"未找到特性节点：{seed_feature_id}")

    def get_relation_label(self, node_type):
        return feature_relation_label(node_type)


_feature_graph_service = FeatureGraphService()


def get_feature_graph_service():
    return _feature_graph_service
