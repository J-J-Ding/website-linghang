export const deepClone = (obj) => {
  const _obj = JSON.stringify(obj);
  const objClone = JSON.parse(_obj);
  return objClone;
};