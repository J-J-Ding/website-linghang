import { MessagePlugin } from 'tdesign-vue-next';

export const pubFormatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const pubDownloadExampleFile = (filePath, fileName) => {
    try {
        const exampleFilePath = filePath;
        // 创建下载链接
        const link = document.createElement('a');
        link.href = exampleFilePath;
        link.download = fileName; // 指定下载文件名
        document.body.appendChild(link);
        link.click();
        // 清理
        document.body.removeChild(link);
        MessagePlugin.success(`${fileName}下载成功，请查看下载文件`);
    } catch (error) {
        console.error(`${fileName}下载失败`, error);
        MessagePlugin.error(`${fileName}下失败，请联系管理员`);
    }
};

export const pubCalculateTableHeight = (offset = 205) => {
    return `${window.innerHeight - offset}px`;
};

export const pubBuildTreeWithText = (data, parentLabels = []) => {
    return (data || []).map(node => {
        // 当前路径 labels
        const currentLabels = [...parentLabels, node.label];

        // 构造新节点
        const newNode = {
            label: node.label,
            value: node.value,
            text: currentLabels.join('$')  // 路径文本
        };

        // 如果有子节点，递归处理
        if (node.children && node.children.length > 0) {
            newNode.children = pubBuildTreeWithText(node.children, currentLabels);
        }

        return newNode;
    });
};

export const pubFilterTreeOptionFun = (searchText, node) => {
    if (!searchText) return true;

    const label = node.data?.text || '';
    if (searchText.startsWith('$')) {
        // 处理 $ 开头的层级搜索
        const searchPartList = searchText.slice(1).split('$');
        const labelPartList = label.split('$');
        // 如果层级数量不够，直接不匹配
        if (labelPartList.length < searchPartList.length) {
            return false;
        }
        // 逐级匹配：第 i 级 label 包含第 i 个 searchPart
        return searchPartList.every((keyword, index) => {
            return labelPartList[index].indexOf(keyword) >= 0;
        });
    } else {
        // 原始模糊匹配整个 label
        return label.indexOf(searchText) >= 0;
    }
};
