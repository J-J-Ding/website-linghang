import axios from 'axios';
import { useUserStore } from '@/store';
import { MessagePlugin } from 'tdesign-vue-next';


const user = useUserStore();

const service = axios.create({
    // baseURL: "http://10.239.69.183:8385",
    baseURL: "/boardChat",
    timeout: 300000,
    withCredentials: true
});


service.interceptors.request.use(
    config => {
        if (user.userInfo) {
            config.headers['X-Emp-No'] = user.userInfo.name
          }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);


service.interceptors.response.use(
    response => {
        // 关键：如果是blob响应，直接返回完整的响应对象
        if (response.config.responseType === 'blob' || response.data instanceof Blob) {
            console.log('Blob响应，返回完整响应对象');
            return response; // 返回完整的axios响应对象
        }
        const res = response.data
        if (res.code !== 200 && res.code !== undefined) {
            console.log(res)
            MessagePlugin.error(res.message);
            return Promise.reject(res)
        } else {
            return res
        }
    },
    error => {
        MessagePlugin.error(error.message);
        return Promise.reject(error);
    }
);

export default service;
