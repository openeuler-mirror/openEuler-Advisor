/**
 * @file  路由配置入口文件
 * */

import Vue from 'vue';
import Router from 'vue-router';
import routes from './routers';

Vue.use(Router);

const router = new Router({
    routes,
    mode: 'history'
});

const originalPush = Router.prototype.push;

Router.prototype.push = function push(location) {
    return originalPush.call(this, location).catch(err => err);
}

router.beforeEach((to, from, next) => {
    next();
});

export default router;