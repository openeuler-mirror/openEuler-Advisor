/**
 * @file  vue构建相关配置文件
 * */

const path = require('path');

const resolve = dir => {
    return path.join(__dirname, dir);
};

const BASE_URL = process.env.NODE_ENV === 'production' ? '/' : '/';

module.exports = {
    publicPath: BASE_URL,

    pluginOptions: {
        'style-resources-loader': {
            preProcessor: 'less',
            patterns: [
                path.resolve(__dirname, './src/assets/style/vars.less')
            ]
        }
    },

    chainWebpack: config => {
        config.resolve.alias
            .set('@', resolve('src'))
            .set('_c', resolve('src/components'))
            .set('_libs', resolve('src/libs'));
    },

    // 设为false打包时不生成.map文件
    productionSourceMap: false,

    // 这里写你调用接口的基础路径，来解决跨域，如果设置了代理，那你本地开发环境的axios的baseUrl要写为 '' ，即空字符串
    devServer: {
        proxy: {
            '/api': {
                target: 'https://api.openeuler.org/pkgmanage/',
                ws: true,
                changeOrigin: true,
                pathRewrite: {
                    '^/api': ''
                }
            }
        }

    }
};