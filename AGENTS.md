# AGENTS.md - 智能代理开发指南

本文档为AI代理（如Sisyphus等）在本项目中的开发提供指导，包含构建命令、代码风格指南、测试运行方式等。

## 项目概述

**技术栈**:
- **前端**: Vue 3 + TypeScript + Vite + TDesign UI + Pinia + Vue Router
- **后端**: Flask (Python) + Gunicorn + PostgreSQL
- **AI框架**: LangChain + LangGraph + OpenAI + Dashscope
- **构建工具**: Vite 5.1.0, Vue-tsc, ESLint, Prettier, Stylelint
- **版本控制**: Git + Husky + Commitlint + Commitizen

**项目结构**:
- `/tdesign/` - 前端应用（Vue 3 + TypeScript）
- `/flask/api/` - 后端API服务（Flask）
- `/flask/api/graphdb_service/` - 图数据库服务
- `/flask/doc/` - 文档和设计

## 构建命令

### 前端开发（在 `/tdesign/` 目录下运行）

```bash
# 开发模式
npm run dev              # 启动开发服务器（端口3002）
npm run dev:mock         # 启动mock数据模式
npm run dev:linux        # Linux环境开发模式

# 构建生产版本
npm run build            # 类型检查 + 构建release版本
npm run build:test       # 构建test版本
npm run build:site       # 构建site版本
npm run build:type       # 仅运行类型检查（vue-tsc）

# 预览构建结果
npm run preview          # 预览构建后的应用

# 代码质量检查
npm run lint             # ESLint检查（不允许警告）
npm run lint:fix         # ESLint自动修复
npm run stylelint        # Stylelint检查样式
npm run stylelint:fix    # Stylelint自动修复

# Git钩子准备
npm run prepare          # 配置Husky git hooks
```

### 后端启动

```bash
# 启动Flask后端（在 /flask/api 目录）
gunicorn -w 4 -b 0.0.0.0:3001 --timeout 360 --access-logfile - --error-logfile - app:app

# PostgreSQL数据库管理
sudo systemctl start postgresql
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

### 完整项目启动流程

1. **启动数据库**: `sudo systemctl start postgresql`
2. **启动后端**: `cd flask/api && gunicorn -w 4 -b 0.0.0.0:3001 --timeout 360 app:app`
3. **启动前端**: `cd tdesign && npm run dev`

**端口说明**:
- 前端开发服务器: `3002`
- 后端API服务: `3001`
- 前端代理API: `3000`

## 代码风格指南

### Prettier格式化规则

配置位置: `/tdesign/.prettierrc.js`

```javascript
// 关键规则
printWidth: 120,           // 行宽120字符
tabWidth: 2,               // 2空格缩进
useTabs: false,            // 使用空格而非Tab
semi: true,                // 必须使用分号
singleQuote: true,         // 单引号（JS），双引号（JSX）
jsxSingleQuote: false,     // JSX使用双引号
trailingComma: 'all',      // 尾随逗号
arrowParens: 'always',     // 箭头函数参数总是使用括号
endOfLine: 'lf',           // LF换行符
vueIndentScriptAndStyle: false, // Vue script/style内不缩进
```

### ESLint代码质量规则

配置位置: `/tdesign/.eslintrc`

**扩展规则集**:
- `@typescript-eslint/recommended` - TypeScript推荐规则
- `eslint-config-airbnb-base` - Airbnb代码风格
- `plugin:vue/vue3-recommended` - Vue 3推荐规则
- `plugin:prettier/recommended` - Prettier集成

**关键规则**:
```javascript
"simple-import-sort/imports": "error",    // 自动排序import
"simple-import-sort/exports": "error",    // 自动排序export
"vue/component-name-in-template-casing": [2, "kebab-case"], // 组件名kebab-case
"vue-scoped-css/enforce-style-type": ["error", {"allows": ["scoped"]}], // 必须scoped样式
"@typescript-eslint/no-unused-vars": [    // 未使用变量规则
  "error",
  {"argsIgnorePattern": "^_", "varsIgnorePattern": "^_"}
],
```

**禁用的规则**:
- `no-console` - 允许console
- `no-continue` - 允许continue
- `no-plusplus` - 允许++
- `no-shadow` - 允许变量遮蔽
- `@typescript-eslint/no-explicit-any` - 允许any类型

### TypeScript配置

配置位置: `/tdesign/tsconfig.json`

```json
{
  "target": "esnext",
  "module": "esnext",
  "strict": true,                    // 严格模式启用
  "noImplicitAny": true,             // 禁止隐式any
  "baseUrl": "./",
  "paths": { "@/*": ["src/*"] },     // 路径别名
  "allowJs": true,                   // 允许JavaScript文件
  "jsx": "preserve",                 // Vue JSX模式
  "types": ["vite/client"]           // Vite类型支持
}
```

### Vue组件规范

1. **组件命名**: 使用kebab-case（如 `my-component.vue`）
2. **样式**: 必须使用scoped样式
3. **模板**: 组件名在模板中使用kebab-case
4. **TypeScript**: 组件使用`<script setup lang="ts">`
5. **Props/Emits**: 使用TypeScript接口定义类型

### 导入排序规则

使用`simple-import-sort`插件自动排序：

1. 第三方库（`vue`, `pinia`, `axios`等）
2. 项目内部模块（`@/components`, `@/utils`等）
3. 相对路径导入（`./`, `../`等）
4. 样式文件（`.css`, `.less`等）

### 命名约定

- **组件文件**: kebab-case（`user-profile.vue`）
- **组件名**: kebab-case（`<user-profile />`）
- **TypeScript文件**: kebab-case或camelCase（`userService.ts`）
- **CSS类名**: kebab-case（`.user-profile-header`）
- **未使用变量**: 以下划线开头（`_unusedVar`）

## Git工作流

### 提交规范（Commitlint）

配置位置: `/tdesign/commitlint.config.js`

**允许的提交类型**:
- `feat` - 新功能
- `fix` - 修复bug
- `docs` - 文档更新
- `style` - 代码格式调整（不影响功能）
- `refactor` - 代码重构
- `perf` - 性能优化
- `test` - 测试相关
- `build` - 构建系统或外部依赖
- `ci` - CI配置
- `chore` - 其他杂项
- `revert` - 回滚提交
- `types` - 类型定义更新

**提交信息格式**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

示例:
```
feat(auth): 添加JWT认证功能

- 实现JWT令牌生成和验证
- 添加登录/注册API端点
- 集成到前端认证流程

Closes #123
```

### Git Hooks（Husky + lint-staged）

配置位置: `/tdesign/package.json` 的 `lint-staged` 部分

```json
"lint-staged": {
  "*.{js,jsx,vue,ts,tsx}": [
    "prettier --write",
    "npm run lint:fix"
  ],
  "*.{html,vue,css,sass,less}": [
    "npm run stylelint:fix"
  ]
}
```

**工作流程**:
1. 提交前自动运行Prettier格式化
2. 运行ESLint自动修复
3. 运行Stylelint自动修复
4. 检查提交信息格式

### Commitizen辅助提交

```bash
# 使用交互式提交
npx cz

# 或使用git commit（会被Husky拦截并提示）
git commit -m "feat: 添加新功能"
```

## 开发环境配置

### Vite开发服务器

配置位置: `/tdesign/vite.config.ts`

```typescript
server: {
  port: 3002,                    // 开发服务器端口
  host: '0.0.0.0',               // 允许外部访问
  proxy: {                       // API代理
    '/api': 'http://127.0.0.1:3000/'
  },
  allowedHosts: [                // 允许的主机名
    'wsit.zx.zte.com.cn',
    'icit.zx.zte.com.cn',
    '.localhost',
    '.local',
    '.lan'
  ]
}
```

### 环境变量

项目使用Vite环境变量模式：

- `.env.development` - 开发环境
- `.env.test` - 测试环境
- `.env.release` - 生产环境

**常用环境变量**:
```bash
VITE_BASE_URL=/              # 基础URL
VITE_API_URL_PREFIX=/api     # API前缀
```

### Mock数据

项目使用`vite-plugin-mock`支持Mock数据：

- Mock文件位置: `/tdesign/mock/`
- 启用方式: `npm run dev:mock`
- 配置: `vite.config.ts`中的`viteMockServe`

## 测试运行（目前占位）

目前测试系统尚未完全实现：

```bash
npm run test             # Placeholder - 无测试
npm run test:coverage    # Placeholder - 无覆盖率测试
```

## AI代理开发建议

### 代码生成策略

1. **遵循现有模式**: 查看`src/components/`中的现有组件作为参考
2. **TypeScript优先**: 所有新代码必须使用TypeScript
3. **组件规范**: 新组件必须遵循Vue 3 + `<script setup>`模式
4. **样式处理**: 使用Less + scoped样式
5. **状态管理**: 使用Pinia进行状态管理

### 文件组织

```
src/
├── components/          # 公共组件
├── views/              # 页面组件
├── store/              # Pinia状态管理
├── router/             # 路由配置
├── utils/              # 工具函数
├── types/              # TypeScript类型定义
├── style/              # 全局样式
└── api/                # API接口定义
```

### 错误处理模式

1. **API调用**: 使用`axios` + `try/catch`
2. **表单验证**: 使用TDesign表单组件内置验证
3. **类型安全**: 充分利用TypeScript类型系统
4. **用户反馈**: 使用TDesign的Message/Notification组件

## 项目约束

### 硬性要求

1. **Node版本**: >=18.0.0
2. **TypeScript**: 严格模式必须启用
3. **Vue样式**: 必须使用scoped样式
4. **提交规范**: 必须遵循Commitlint规范
5. **代码格式**: 提交前必须通过Prettier格式化

### 避免的操作

1. **禁止**: 使用`@ts-ignore`或`as any`绕过类型检查
2. **禁止**: 在组件中使用非scoped样式
3. **禁止**: 绕过Git Hooks提交
4. **避免**: 直接修改`dist/`目录中的文件

## 快速参考

### 常见任务

```bash
# 创建新组件
cd tdesign/src/components
touch my-component.vue

# 运行类型检查
npm run build:type

# 修复所有代码问题
npm run lint:fix && npm run stylelint:fix

# 查看项目状态
git status
npm run lint
```

### 故障排除

1. **类型错误**: 运行`npm run build:type`查看详细错误
2. **构建失败**: 检查Node版本和依赖安装
3. **样式问题**: 确保使用scoped样式
4. **Git提交失败**: 检查提交信息格式和代码检查结果

---

*文档最后更新: 2026-03-07*
*适用于: AI代理开发人员、新团队成员*