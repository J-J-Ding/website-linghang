<template>
  <div>
    <template v-for="item in list" :key="item.path">
      <template v-if="!item.children || !item.children.length || item.meta?.single">
        <t-menu-item 
          v-if="getHref(item)" 
          :name="item.path" 
          :value="getPath(item)" 
          :class="getMenuItemClass(item)"
          @click="openHref(getHref(item)[0])"
        >
          <template #icon>
            <component :is="menuIcon(item)" class="t-icon"></component>
          </template>
          {{ renderMenuTitle(item.title) }}
        </t-menu-item>
        <t-menu-item 
          v-else 
          :name="item.path" 
          :value="getPath(item)" 
          :to="item.path"
          :class="getMenuItemClass(item)"
        >
          <template #icon>
            <component :is="menuIcon(item)" class="t-icon"></component>
          </template>
          {{ renderMenuTitle(item.title) }}
        </t-menu-item>
      </template>
      <t-submenu v-else :name="item.path" :value="item.path" :title="renderMenuTitle(item.title)">
        <template #icon>
          <component :is="menuIcon(item)" class="t-icon"></component>
        </template>
        <menu-content v-if="item.children" :nav-data="item.children" />
      </t-submenu>
    </template>
  </div>
</template>

<script setup lang="tsx">
import type { PropType } from 'vue';
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { useLocale } from '@/locales/useLocale';
import { getActive } from '@/router';
import type { MenuRoute } from '@/types/interface';

type ListItemType = MenuRoute & { icon?: string };

const { navData } = defineProps({
  navData: {
    type: Array as PropType<MenuRoute[]>,
    default: () => [],
  },
});

const route = useRoute();
const active = computed(() => getActive());

const { locale } = useLocale();
const list = computed(() => {
  return getMenuList(navData);
});

// 判断是否是最后一级菜单项（叶子节点）
const isLastLevelMenuItem = (item: ListItemType): boolean => {
  // 如果有 meta.single 标记，认为是最后一级
  if (item.meta?.single) return true;
  
  // 如果没有子菜单或子菜单为空，认为是最后一级
  if (!item.children || item.children.length === 0) return true;
  
  // 其他情况不是最后一级
  return false;
};

// 获取菜单项的CSS类
const getMenuItemClass = (item: ListItemType) => {
  const classes = [];
  
  // 只有最后一级菜单项才添加激活样式
  if (isLastLevelMenuItem(item)) {
    const isActive = isActiveMenuItem(item);
    if (isActive) {
      classes.push('last-level-active');
    }
  }
  
  return classes;
};

// 判断菜单项是否激活
const isActiveMenuItem = (item: ListItemType): boolean => {
  if (!isLastLevelMenuItem(item)) return false;
  
  const currentPath = route.path;
  const itemPath = item.path;
  
  // 精确匹配
  if (currentPath === itemPath) return true;
  
  // 处理重定向情况
  if (item.meta?.single && item.redirect) {
    return currentPath === item.redirect;
  }
  
  return false;
};

const menuIcon = (item: ListItemType) => {
  if (typeof item.icon === 'string') return <t-icon name={item.icon} />;
  const RenderIcon = item.icon;
  return RenderIcon;
};

const renderMenuTitle = (title: string | Record<string, string>) => {
  if (typeof title === 'string') return title;
  return title[locale.value];
};

const getMenuList = (list: MenuRoute[], basePath?: string): ListItemType[] => {
  if (!list || list.length === 0) {
    return [];
  }
  // 如果meta中有orderNo则按照从小到大排序
  list.sort((a, b) => {
    return (a.meta?.orderNo || 0) - (b.meta?.orderNo || 0);
  });
  return list
    .map((item) => {
      const path = basePath && !item.path.includes(basePath) ? `${basePath}/${item.path}` : item.path;

      return {
        path,
        title: item.meta?.title,
        icon: item.meta?.icon,
        children: getMenuList(item.children, path),
        meta: item.meta,
        redirect: item.redirect,
      };
    })
    .filter((item) => item.meta && item.meta.hidden !== true);
};

const getHref = (item: MenuRoute) => {
  const { frameSrc, frameBlank } = item.meta;
  if (frameSrc && frameBlank) {
    return frameSrc.match(/(http|https):\/\/([\w.]+\/?)\S*/);
  }
  return null;
};

const getPath = (item: ListItemType) => {
  const activeLevel = active.value.split('/').length;
  const pathLevel = item.path.split('/').length;
  if (activeLevel > pathLevel && active.value.startsWith(item.path)) {
    return active.value;
  }

  if (active.value === item.path) {
    return active.value;
  }

  return item.meta?.single ? item.redirect : item.path;
};

const openHref = (url: string) => {
  window.open(url);
};
</script>

<style scoped>
/* 最后一级菜单的激活样式 - 蓝色 */
.last-level-active {
  color: #0052D9 !important;
  background-color: rgba(24, 144, 255, 0.1) !important;
  border-left: 3px solid #0052D9 !important;
  font-weight: 500 !important;
}

/* 暗色主题下的激活样式 */
:global(.t-menu--dark) .last-level-active {
  background-color: rgba(24, 144, 255, 0.2) !important;
  color: #0052D9 !important;
}

/* 悬停效果 */
:deep(.t-menu__item:hover) {
  color: #0052D9 !important;
  background-color: rgba(24, 144, 255, 0.05) !important;
}

/* 过渡效果 */
:deep(.t-menu__item) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>