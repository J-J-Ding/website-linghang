import axios from 'axios';
import { useUserStore } from '@/store';
import { MessagePlugin } from 'tdesign-vue-next';
import { Utils } from "@/utils/utils";
const user = useUserStore();
// const token = tokenManager.getToken();
const headerParams = Utils.getHeader();
const service = axios.create({
    // baseURL: "http://10.239.69.183:3030",
    baseURL: "",
    timeout: 600000,
    withCredentials: true
});


service.interceptors.request.use(
    config => {
        if (user?.userInfo) {
            // const headerParams = Utils.getHeader();        
            // 使用可选链和空值合并
            // config.headers['X-Emp-No'] = headerParams?.['X-Emp-No'] ?? '';
            // config.headers['X-Auth-Value'] = headerParams?.['X-Auth-Value'] ?? '';
        }
        return config;
    },
    error => Promise.reject(error)
);


service.interceptors.response.use(
    response => {
        const res = response.data
        // 兼容两种响应格式：{code: 200} 和 {status: 'success'}
        if (res.code !== 200 && res.code !== undefined && res.status !== 'success') {
            console.log(res)
            MessagePlugin.error(res.message);
            return Promise.reject(res)
        } else {
            return res
        }
    },
    error => {
        // 处理 HTTP 错误响应
        if (error.response && error.response.data) {
            MessagePlugin.error(error.response.data.message || error.message);
            // 返回错误响应数据，保持错误状态码信息
            return Promise.reject({
                ...error.response.data,
                status: error.response.status
            });
        }
        MessagePlugin.error(error.message);
        return Promise.reject(error);
    }
);

export default service;
