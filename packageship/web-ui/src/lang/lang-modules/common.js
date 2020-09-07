/**
 * @file  公共模块国际化配置入口
 * */

module.exports = {
    cn: {
        searchPlaceholder: '输入内容',
        navRouterConfig: [{
            path: '/download',
            name: '下载',
            children: [],
            class: []
        },
            {
                path: '/documentation/documentation',
                name: '文档',
                children: [],
                class: []
            },
            {
                path: '',
                name: '社区',
                subName: '社区玩转指引',
                subPath: '/community/community-guidance',
                subImg: '',
                children: [{
                    name: '活动',
                    path: '/community/event-list'
                },
                    {
                        name: '博客',
                        path: '/community/blog-list'
                    },
                    {
                        name: '新闻',
                        path: '/community/news-list'
                    },
                    {
                        name: '活动',
                        path: '/community/mailing-list'
                    }
                ],
                class: []
            },
            {
                path: '',
                name: 'SIG',
                subName: 'SIG玩转指引',
                subPath: '/sig/sig-guidance',
                subImg: '',
                viewAllName: '查看全部',
                viewAllPath: '/sig/sig-list',
                children: [{
                    name: 'A-Tune',
                    path: '/sig/sig-detail/1'
                },
                    {
                        name: 'Base-service',
                        path: '/sig/sig-detail/2'
                    },
                    {
                        name: 'Computing',
                        path: '/sig/sig-detail/3'
                    },
                    {
                        name: 'DB',
                        path: '/sig/sig-detail/4'
                    },
                    {
                        name: 'GNOME',
                        path: '/sig/sig-detail/5'
                    },
                    {
                        name: 'Application',
                        path: '/sig/sig-detail/6'
                    },
                    {
                        name: 'Compiler',
                        path: '/sig/sig-detail/7'
                    },
                    {
                        name: 'Container',
                        path: '/sig/sig-detail/8'
                    },
                    {
                        name: 'Desktop',
                        path: '/sig/sig-detail/9'
                    },
                    {
                        name: 'Infrastructure',
                        path: '/sig/sig-detail/10'
                    }
                ],
                class: []
            },
            {
                path: '/authentication',
                name: '认证',
                children: [],
                class: []
            },
            {
                path: '/security',
                name: '安全',
                children: [],
                class: []
            }
        ],
        PAGE_NAME: 'Package Management',
        lang: 'EN',
        search: '搜索',
        gitee: '码云',
        footer: {
            leftLogo: 'openEuler',
            mail: 'contact@openeuler.org',
            copyright: '版权所有 © 2020 openeuler 保留一切权利',
            rightList: ['品牌', '法律声明', '隐私政策']
        }
    },
    en: {
        searchPlaceholder: 'Input content',
        navRouterConfig: [{
            path: '/download',
            name: 'Download',
            children: [],
            class: []
        },
            {
                path: '/documentation/documentation',
                name: 'Documentation',
                children: [],
                class: []
            },
            {
                path: '',
                name: 'Community',
                subName: '社区玩转指引',
                subPath: '/community/community-guidance',
                subImg: '',
                children: [{
                    name: 'Events',
                    path: '/community/event-list'
                },
                    {
                        name: 'Blog',
                        path: '/community/blog-list'
                    },
                    {
                        name: 'News',
                        path: '/community/news-list'
                    },
                    {
                        name: 'Mailing',
                        path: '/community/mailing-list'
                    }
                ],
                class: []
            },
            {
                path: '',
                name: 'SIG',
                subName: 'SIG Play guide',
                subPath: '/sig/sig-guidance',
                subImg: '',
                viewAllName: 'View All',
                viewAllPath: '/sig/sig-list',
                children: [{
                    name: 'A-Tune',
                    path: '/sig/sig-detail/1'
                },
                    {
                        name: 'Base-service',
                        path: '/sig/sig-detail/2'
                    },
                    {
                        name: 'Computing',
                        path: '/sig/sig-detail/3'
                    },
                    {
                        name: 'DB',
                        path: '/sig/sig-detail/4'
                    },
                    {
                        name: 'GNOME',
                        path: '/sig/sig-detail/5'
                    },
                    {
                        name: 'Application',
                        path: '/sig/sig-detail/6'
                    },
                    {
                        name: 'Compiler',
                        path: '/sig/sig-detail/7'
                    },
                    {
                        name: 'Container',
                        path: '/sig/sig-detail/8'
                    },
                    {
                        name: 'Desktop',
                        path: '/sig/sig-detail/9'
                    },
                    {
                        name: 'Infrastructure',
                        path: '/sig/sig-detail/10'
                    }
                ],
                class: []
            },
            {
                path: '/authentication',
                name: 'Authentication',
                children: [],
                class: []
            },
            {
                path: '/security',
                name: 'Security',
                children: [],
                class: []
            }
        ],
        PAGE_NAME: 'Package Management',
        lang: '中',
        search: 'search',
        gitee: 'gitee',
        footer: {
            mail: 'contact@openeuler.org',
            copyright: 'Copyright © 2020 openEuler. All rights reserved.',
            rightList: ['TradeMark', 'Legal', 'Privacy']
        }
    }
};