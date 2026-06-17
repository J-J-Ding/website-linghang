根据您提出的需求，修改端口支持数量需要涉及以下模块的调整：

---

### **一、涉及模块及修改方案**

#### 1. **PortApi 模块（核心 API 与硬件抽象）**

- **修改点**：
  | 修改项 | 文件 | 修改内容 |
  |-----------------------|-----------------------|-------------------------------------------------------------------------|
  | 端口数组扩容 | `sspPortApi.c` | 将`g_stPortInfo`数组长度改为`SSP_DEVICE_PHY_NUM_MAX_NEW` |
  | 端口 ID 校验逻辑 | `sspPortApi.c` | 更新`usPortId`的有效范围判断条件（如`SSP_DEVICE_PHY_MIN`/`MAX`） |
  | 信号量参数适配 | `sspPortApi.c` | 调整`sspSemMuxCreate`参数以匹配新端口数量 |
  | 硬件抽象层配置 | `sspHwAdapterApi.h/c` | 更新硬件驱动中端口最大值宏（如`HW_PORT_MAX`） |

- **关键代码示例**：

  ```c
  // sspPortApi.c
  #define SSP_DEVICE_PHY_NUM_MAX_NEW 64  // 新增宏定义

  SSP_PORT_INFO_S g_stPortInfo[SSP_DEVICE_PHY_NUM_MAX_NEW];  // 数组扩容

  SSP_PORT_INFO_S* sspPortInfoGet(UINT16 usPortId) {
      if ((usPortId >= SSP_DEVICE_PHY_MIN) && (usPortId <= SSP_DEVICE_PHY_MAX_NEW)) {
          return &g_stPortInfo[usPortId - 1];
      }
      return NULL;
  }
  ```

#### 2. **PortInit 模块（初始化与状态管理）**

- **修改点**：
  | 修改项 | 文件 | 修改内容 |
  |-----------------------|-----------------------|-------------------------------------------------------------------------|
  | 动态端口上下文管理 | `sspPortInit.c` | 使用动态数组`g_pstPortCtxArray`替代固定大小变量 |
  | 初始化函数适配 | `sspPortInit.c` | 在`sspPortInfoInit()`中动态分配内存并初始化端口上下文 |
  | 任务调度策略优化 | `sspPortInit.c` | 根据端口数量动态调整任务优先级和堆栈大小 |

- **关键代码示例**：

  ```c
  // sspPortInit.c
  static SSP_PORT_CTX_S *g_pstPortCtxArray = NULL;
  static UINT16 g_usPortCount = 0;

  INT32 sspPortInfoInit() {
      g_usPortCount = SSP_DEVICE_CLIENT_MAX - SSP_DEVICE_CLIENT_MIN + 1;
      g_pstPortCtxArray = malloc(g_usPortCount * sizeof(SSP_PORT_CTX_S));
      // ... 初始化逻辑 ...
  }

  INT32 SSP_PORT_Init(VOID) {
      if (g_usPortCount > 128) {
          ucPriority -= 2;  // 降低任务优先级
          ulStackSize *= 2;  // 扩大堆栈
      }
      // ... 创建任务 ...
  }
  ```

#### 3. **PortGhao 模块（光传输带宽调整）**

- **修改点**：
  | 修改项 | 文件 | 修改内容 |
  |-----------------------|-----------------------|-------------------------------------------------------------------------|
  | 带宽计算逻辑 | `portGhaoBandwidth.c` | 更新带宽计算公式中的端口数量参数 |
  | 协议转换适配 | `portGhaoProtocol.c` | 根据新端口数量调整协议转换表 |

- **关键代码示例**：
  ```c
  // portGhaoBandwidth.c
  void calculateBandwidth(UINT16 totalPorts) {
      // 使用新的端口总数进行计算
      float bandwidthPerPort = TOTAL_BANDWIDTH / totalPorts;
      // ... 其他逻辑 ...
  }
  ```

---

### **二、修改要点总结**

| **模块**     | **修改内容**                                         | **波及分析**                                                         | **风险分析**                                           |
| ------------ | ---------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------ |
| **PortApi**  | 端口数组扩容、ID 校验逻辑更新、信号量参数适配        | 影响所有使用端口信息的 API（如`sspPortInfoGet`、`SSP_PORT_InfoSet`） | 数组越界或信号量不足可能导致系统崩溃或功能异常         |
| **PortInit** | 动态端口上下文管理、初始化函数适配、任务调度策略优化 | 影响端口初始化流程和全局状态管理                                     | 内存泄漏或任务优先级设置不当可能引发资源竞争或性能下降 |
| **PortGhao** | 带宽计算逻辑更新、协议转换适配                       | 影响光传输系统的带宽分配和协议兼容性                                 | 带宽计算错误或协议不匹配可能导致数据传输异常           |

---

### **三、风险控制建议**

1. **硬件一致性验证**  
   确保所有模块中定义的端口数量宏（如`SSP_DEVICE_PHY_NUM_MAX_NEW`）与硬件实际支持的端口数严格一致。

2. **边界测试**  
   对新增端口 ID 进行全链路测试，覆盖最大/最小值场景（如`SSP_PORT_InfoSet`、`sspPortSpeedAndNegSet`等）。

3. **资源容量评估**

   - 若端口数量显著增加，需重新计算信号量、堆栈大小和内存分配策略。
   - 引入读写锁（`pthread_rwlock_t`）替代互斥量，提升高并发场景下的性能。

4. **依赖模块同步更新**  
   检查其他模块（如`sspTrunkOuterApi`）是否依赖端口数量定义，避免因参数不一致引发错误。

5. **日志与监控**  
   在关键操作（如内存分配、任务创建）中添加详细日志，便于故障排查。

---

通过以上修改，可确保端口数量扩展后的系统稳定性、性能和兼容性。
