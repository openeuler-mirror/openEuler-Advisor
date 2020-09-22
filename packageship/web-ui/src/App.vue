<template>
    <div id="app" v-cloak :class="{'lang-cn': $i18n.locale==='zh-cn'}">
        <i-header></i-header>
        <div class="content">
            <router-view />
        </div>
        <i-footer></i-footer>
    </div>
</template>

<script>
import header from "_c/header";
import footer from "_c/footer";
export default {
    data() {
        return {};
    },
    components: {
        "i-header": header,
        "i-footer": footer
    }
};
</script>

<style lang="less" scoped>
[v-cloak] {
    display: none !important;
}
.content {
    min-height: calc(100vh - 110px - 176px);
    @media (max-width: 1000px) {
        min-height: calc(100vh - 70px - 280px);
    }
}
</style>
