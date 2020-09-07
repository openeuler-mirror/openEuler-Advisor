/**
 * @file  路由配置文件
 * */

export default [{
        path: '/',
        component: () => import('@/views/home/home.vue')
    },
    {
        path: '/package-detail',
        component: () => import('@/views/package/package-detail.vue')
    },
    {
        path: '*',
        component: () => import('@/views/404.vue')
    }
];