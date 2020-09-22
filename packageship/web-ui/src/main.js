/**
 * @file  vue组件主入口
 * */

import Vue from 'vue';
import App from './App.vue';
import router from './router';
import ElementUI from 'element-ui';
import locale from 'element-ui/lib/locale/lang/en';
import Vue18n from 'vue-i18n';
import '@/assets/style/base.css';
import  echarts from 'echarts';


if (!localStorage.getItem('locale') || localStorage.getItem('locale') === 'zh-en') {
    import('@/assets/style/font-en.css');
} else {
    import('@/assets/style/font-cn.css');
}

Vue.use(Vue18n);
Vue.use(ElementUI, {locale});
Vue.use(echarts)
Vue.prototype.$echarts = echarts

const i18n = new Vue18n({
    locale: localStorage.getItem('locale') || 'zh-en',
    messages: {
        'zh-cn': require('@/lang/cn'), // 中文语言包
        'zh-en': require('@/lang/en') // 英文语言包
    }
});

Vue.config.productionTip = false;

new Vue({
    i18n,
    router,
    render: h => h(App)
}).$mount('#app');