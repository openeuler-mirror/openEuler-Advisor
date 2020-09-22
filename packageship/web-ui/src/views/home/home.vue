<template>
    <div class="home">
        <h1>Package Management</h1>

        <div class="switcher">
            <a :class="{'active': isInfoShow }" @click="showInfo">Package Info</a>
            <a :class="{'active': isListShow }" @click="showList">Issue List</a>
            <a :class="{'active': isDependShow }" @click="showDepend">Depend Info</a>
        </div>
        <div class="package-container">
            <package-Info v-if="isInfoShow" />
            <issue-list v-if="isListShow" />
            <depend-info v-if="isDependShow" />
        </div>
    </div>
</template>

<script>
import InfoList from "./package-info";
import IssueList from "./issue-list"
import DependInfo from "./depend-info"

export default {
    name: "Home",
    components: {
        "package-Info": InfoList,
        "issue-list": IssueList,
        "depend-info": DependInfo
    },
    mounted() {
    },
    data() {
        return {
            isInfoShow: true,
            isListShow: false,
            isDependShow: false
        }
    },
    methods: {
        showInfo() {
            this.isInfoShow = true;
            this.isListShow = false;
            this.isDependShow = false

        },
        showList() {
            this.isListShow = true;
            this.isInfoShow = false;
            this.isDependShow = false
        },
        showDepend() {
            this.isInfoShow = false;
            this.isListShow = false;
            this.isDependShow = true
        }

    }
};
</script>

<style lang="less">

</style>

<style scoped>
    h1 {
        font-size: 36px;
        font-family: HuaweiSans-Medium;
        margin: 60px 0;
    }
    .home {
        width: 1200px;
        margin: 0 auto;
    }
    .switcher a {
        font-size: 24px;
        font-family: HuaweiSans-Medium;
        color: rgba(0, 0, 0, 0.5);
        margin-right: 40px;
        cursor: pointer;
        padding-bottom: 10px;
        margin-bottom: 30px;
    }
    .switcher .active {
        color: #000;
        display: inline-block;
        border-bottom: 4px solid #002fa7;

    }
    @media screen and (max-width: 1000px) {
        .home {
            width: 100%;
            padding: 0 30px;
        }
        h1 {
            font-size: 18px;
            font-family: FZLTCHJW;
            margin: 40px 0;
        }
        .switcher a {
            font-size: 16px;
            margin-right: 20px;
        }
    }
</style>
