import request_require_schedule from '@/utils/request_require_schedule.js';
import request_fast from '@/utils/request_fast.js';

// 特性视图
export function queryFeatureViewByParams(params) {
  return request_require_schedule({
    url: '/api/feature_view/queryFeatureViewByParams',
    method: 'get',
    params,
  });
}

export function createFeatureView(data) {
  return request_require_schedule({
    url: '/api/feature_view/createFeatureView',
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    data,
  });
}

export function updateFeatureView(data) {
  return request_require_schedule({
    url: '/api/feature_view/updateFeatureView',
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    data,
  });
}

export function deleteFeatureView(data) {
  return request_require_schedule({
    url: '/api/feature_view/deleteFeatureView',
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    data,
  });
}

export function getFeatureViewOptions(params) {
  return request_require_schedule({
    url: '/api/feature_view/getFeatureViewOptions',
    method: 'get',
    params,
  });
}

export function importFeatureView(data) {
  return request_require_schedule({
    url: '/api/feature_view/importFeatureView',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export function exportFeatureView(params) {
  return request_require_schedule({
    url: '/api/feature_view/exportFeatureView',
    method: 'get',
    params,
    responseType: 'blob',
  });
}

export function countFeatureViewByDomainTeam(params) {
  return request_require_schedule({
    url: '/api/feature_view/countFeatureViewByDomainTeam',
    method: 'get',
    params,
  });
}

export function deleteFeatureViewByDomainTeam(data) {
  return request_require_schedule({
    url: '/api/feature_view/deleteFeatureViewByDomainTeam',
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    data,
  });
}

// 特性树级联选项（与特性树页面调用保持一致）
export function queryFeatureTreeFeatureFirstTypeList(params) {
  return request_fast({
    url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureFirstTypeList',
    method: 'get',
    params,
  });
}

export function queryFeatureTreeFeatureSecondTypeList(params) {
  return request_fast({
    url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureSecondTypeList',
    method: 'get',
    params,
  });
}

export function queryFeatureTreeFeatureList(params) {
  return request_fast({
    url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeFeatureList',
    method: 'get',
    params,
  });
}

export function queryFeatureTreeSubFeatureList(params) {
  return request_fast({
    url: '/api/electric_knowledge/front_feature_relation_data_service/queryFeatureTreeSubFeatureList',
    method: 'get',
    params,
  });
}
