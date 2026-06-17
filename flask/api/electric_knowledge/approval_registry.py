from datetime import datetime


# 业务模块注册表（缓存）
BIZ_MODULE_REGISTRY = {
    '特性-子特性': {
        'module_path': 'electric_knowledge.front_feature_relation_data_service',
        'model_class_name': 'FEATURE_RELATION_TABLE',
        'biz_table_name': 'feature_relation_table',
        'biz_type': '特性-子特性',
        'service_add': 'addSrcFeatureRelationData',
        'service_update': 'updateSrcFeatureRelationData',
        'service_delete': 'deleteSrcFeatureRelationData',
        'has_current_status': True,
        'default_approver': '张进朋10305454',
        'admin_persons': '张进朋10305454'
    },
    '单板树': {
        'module_path': 'electric_knowledge.front_board_tree_data_service',
        'model_class_name': 'BOARD_TREE_TABLE',
        'biz_table_name': 'board_tree_table',
        'biz_type': '单板树',
        'service_add': 'addSrcBoardTreeData',
        'service_update': 'updateSrcBoardTreeData',
        'service_delete': 'deleteSrcBoardTreeData',
        'has_current_status': True,
        'default_approver': '张进朋10305454',
        'admin_persons': '张进朋10305454'
    },
}


def init_approval_config_table():
    """
    初始化APPROVAL_CONFIG_TABLE表
    将注册表配置写入数据库（仅写入不存在记录）
    """
    try:
        from electric_knowledge.data_model import db, APPROVAL_CONFIG_TABLE

        for biz_type, config in BIZ_MODULE_REGISTRY.items():
            # 检查是否已存在
            existing = db.session.query(APPROVAL_CONFIG_TABLE).filter(
                APPROVAL_CONFIG_TABLE.biz_type == biz_type,
                APPROVAL_CONFIG_TABLE.effective_flag == 'Y'
            ).first()

            if not existing:
                record = APPROVAL_CONFIG_TABLE(
                    biz_type=biz_type,
                    biz_table_name=config.get('biz_table_name', ''),
                    module_path=config['module_path'],
                    model_class_name=config['model_class_name'],
                    need_approval=True,
                    approval_flow_type='single',
                    default_approver=config.get('default_approver', ''),
                    admin_persons=config.get('admin_persons', ''),
                    description=f"{biz_type}审批配置",
                    create_time=datetime.now(),
                    update_time=datetime.now(),
                    operator_person='system',
                    effective_flag='Y'
                )
                db.session.add(record)
                print(f"[ApprovalRegistry] 新增配置: {biz_type}")

        db.session.commit()
        print("[ApprovalRegistry] 配置表初始化完成")
        return True

    except Exception as e:
        print(f"[ApprovalRegistry] 初始化失败: {str(e)}")
        return False


def get_biz_config(biz_type: str) -> dict:
    """
    获取指定业务类型的配置
    """
    return BIZ_MODULE_REGISTRY.get(biz_type)


def list_all_biz_types() -> list:
    """
    获取所有已注册的业务类型列表
    """
    return list(BIZ_MODULE_REGISTRY.keys())