const staticHeaders = {
    'X-Auth-Value': null,
    'X-Emp-No': null,
    'X-Tenant-Id': null,
    'X-Lang-Id': null
    // 'X-Auth-Value': null,
    // 'X-Emp-No': null
};

export class Utils {
  static getCookie(name) {
    const cookieString = document.cookie;
    const cookieMap = new Map();
    const cookies = cookieString.split('; ');
    cookies.forEach((cookie) => {
        const [cookieName, cookieValue] = cookie.split('=');
        // 解码 cookie 值
        const decodedValue = decodeURIComponent(cookieValue || '');
        cookieMap.set(cookieName, decodedValue);
    });
    return cookieMap.get(name) || null;
  }

  static getHeader() {
    const userId = Utils.getCookie('PORTALSSOUser') || Utils.getCookie('ZTEDPGSSOUser');
    const tocken = Utils.getCookie('PORTALSSOCookie') || Utils.getCookie('ZTEDPGSSOCookie');
    console.log('获取浏览器用户token/cookie: ', tocken);
    const header = {
      'X-Auth-Value': tocken || staticHeaders['X-Auth-Value'],
      'X-Emp-No': userId || staticHeaders['X-Emp-No'],
    };
    return header;
  }

  static getRDCHeader() {
    const userId = Utils.getCookie('PORTALSSOUser') || Utils.getCookie('ZTEDPGSSOUser');
    const tocken = Utils.getCookie('PORTALSSOCookie') || Utils.getCookie('ZTEDPGSSOCookie');
    const id = Utils.getCookie('X_Tenant_Id')  || Utils.getCookie('iAuthTenantId_prod'); // '10001';
    const language = Utils.getCookie('ZTEDPGSSOLanguage');
    const appcode = 'd09fddc101a14bb3bfa0fbd02ed1932a';
    const type = 'application/json';
    console.log('获取浏览器用户token/cookie: ', tocken);
    const header = {
      'X-Auth-Value': tocken || staticHeaders['X-Auth-Value'],
      'X-Emp-No': userId || staticHeaders['X-Emp-No'],
      'X-Tenant-Id': id || staticHeaders['X-Tenant-Id'],
      'X-Lang-Id': language || staticHeaders['X-Lang-Id'],
      'appCode': appcode,
      'Content-Type': type,
    };
    return header;
  }

  static getBaseUrl() {
    // 获取当前页面的协议、主机名和端口
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // 构建基础URL
    return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
  };
}
