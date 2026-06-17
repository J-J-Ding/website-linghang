export class RDC {
  static getRDCParams(key, name) {
    return {
      type: 'string',
      workItemTypeKey: key,
      textData: {
          pickListDataScopeConfig: {
              canInputAnyValue: false,
              referencePickListName: name,
              useRemoteDataSource: false
          },
          textDataScopeConfig: null
      },
      remoteDataSource: '',
    };
  }
  static getRDCCustomers(key, name) {
    return {
      workItemTypeKey: key,
      key: name,
      eventId: "",
      remoteDataConfig: "",
      currentValue: ""
    };
  }
}
