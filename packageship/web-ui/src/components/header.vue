<template>
    <div class="nav-fill">
        <div class="nav-wrapper">
            <div class="nav-bar">
                <img
                        src="@/assets/images/openeuler.png"
                        alt=""
                        class="nav-logo"
                        @click="go('/')"
                />
                <img
                        src="@/assets/images/logo-mobile.png"
                        alt=""
                        class="nav-logo nav-logo-mobile"
                        @click="go('/')"
                />
                <div
                        :class="{ mask: menuMobileFlag }"
                        @click="menuMobileFlag = false"
                ></div>
                <ul class="nav-other">
                    <li>
                        <img src="@/assets/images/Gitee.png" alt="" />
                        <span>{{ $t("common.gitee") }}</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                toggleSubMenu: [],
                menuActivePath: "",
                menuMobileFlag: false,
                searchData: "",
                searchFlag: false
            };
        },
        mounted() {},
        methods: {
            go(path) {
                if (path) {
                    this.$router.push(path);
                    this.menuMobileFlag = false;
                }
            },
            showSub(toggleClass) {
                toggleClass.push("show-sub-menu");
            },
            hideSub(toggleClass) {
                toggleClass.pop();
            },
            toggleLang() {
                const locale = this.$i18n.locale === "zh-cn" ? "zh-en" : "zh-cn";
                window.localStorage.setItem("locale", locale);
                window.location.reload(true);
            },
            menuActiveFn(item) {
                let $route = this.$route;
                return (
                    $route.path === item.path ||
                    $route.path === item.subPath ||
                    $route.path === item.viewAllPath ||
                    item.children.some(item => item.path === $route.path)
                );
            },
            toggleMenuMobile() {
                this.searchFlag = false;
                this.menuMobileFlag = !this.menuMobileFlag;
            },
            toggleSub(item) {
                if (item.path) {
                    this.$router.push(item.path);
                    this.menuMobileFlag = false;
                    return;
                }
                if (item.class.length) {
                    item.class.pop();
                } else {
                    item.class.push("arrow-active");
                }
                console.log(item.class);
            },
            subMenuMobileFn(item) {
                let $route = this.$route;
                return (
                    item.class.indexOf("arrow-active") > 0 ||
                    $route.path === item.path ||
                    $route.path === item.subPath ||
                    $route.path === item.viewAllPath ||
                    item.children.some(item => item.path === $route.path)
                );
            },
            toggleSearchMobile() {
                this.menuMobileFlag = false;
                this.searchFlag = !this.searchFlag;
            }
        }
    };
</script>
<style lang="less" scoped>
    .el-input {
        width: 80%;
        margin: 9px;
    }
</style>
<style lang="less" scoped>
    @keyframes fade-in {
        0% {
            opacity: 0;
            top: -110px;
        }
        100% {
            opacity: 1;
            top: 0;
        }
    }
    @keyframes slide-down {
        0% {
            display: block;
            opacity: 0;
            top: -352px;
        }
        50% {
            opacity: 0;
        }
        100% {
            opacity: 1;
            top: 110px;
            display: block;
        }
    }
    .menu-active {
        border-bottom: 5px solid @primary-color;
    }
    .menu-mobile-active {
        display: block !important;
    }
    .show {
        display: block !important;
    }
    .search-active {
        color: #0041bd;
    }
    .mask {
        position: fixed;
        top: 72px;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.4);
    }
    .nav-fill {
        height: 110px;
        @media (max-width: 1000px) {
            height: 70px;
        }
        .nav-wrapper {
            background-color: #fff;
            animation: fade-in;
            animation-duration: 0.5s;
            height: 110px;
            width: 100%;
            position: fixed;
            z-index: 999;
            box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.2);
            @media (max-width: 1000px) {
                height: 70px;
            }
            .nav-bar {
                width: 1200px;
                height: 100%;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
                @media (max-width: 1000px) {
                    width: 100%;
                    padding: 0 15px;
                }
                ul li {
                    display: inline-block;
                }
                .nav-logo {
                    flex-shrink: 0;
                    width: 193px;
                    margin-right: 25px;
                    cursor: pointer;
                }
                .nav-logo-mobile {
                    display: none;
                    width: 142px;
                }
                .nav-other-mobile {
                    display: none;
                    height: 100%;
                    .menu-icon-active {
                        color: #0041bd;
                    }
                    li {
                        height: 100%;
                        line-height: 70px;
                        vertical-align: middle;
                        margin-left: 20px;
                        cursor: pointer;
                    }
                    .lang {
                        font-size: 16px;
                    }
                    .search {
                        font-size: 25px;
                    }
                    .menu {
                        font-size: 22px;
                    }
                }
                .nav-menu-mobile {
                    display: none;
                    max-height: calc(100vh - 70px);
                    overflow-y: scroll;
                    background-color: #fff;
                    position: fixed;
                    top: 70px;
                    left: 0;
                    width: 100%;
                    padding: 10px 30px;
                    z-index: 998;
                    & > li {
                        display: block;
                        border-bottom: 1px solid rgba(0, 0, 0, 0.09);
                        padding: 10px 0;
                        a {
                            border: none;
                            font-size: 16px;
                            font-family: FZLTHJW;
                            height: 26px;
                            line-height: 26px;
                            display: inline-block;
                            width: 100%;
                            position: relative;
                            .arrow-active {
                                color: #0041bd;
                                transform: rotate(90deg);
                            }
                            i {
                                position: absolute;
                                right: 7px;
                                top: 5px;
                            }
                        }
                        .sub-menu {
                            margin-left: 15px;
                            display: none;
                            .sub-menu-color-active {
                                color: #0041bd;
                            }
                            li {
                                display: block;
                                height: 26px;
                                line-height: 26px;
                                font-size: 14px;
                                font-family: FZLTXIHJW;
                                color: rgba(0, 0, 0, 0.7);
                                margin: 6px 0;
                            }
                        }
                    }
                }
                .nav-menu {
                    height: 100%;
                    flex: 3;
                    .ff-h();
                    color: @text-dark;
                    .fz20();
                    display: flex;
                    align-items: center;
                    @media (max-width: 1000px) {
                        display: none;
                    }
                    .show-sub-menu {
                        .sub-menu {
                            animation: slide-down;
                            animation-duration: 0.5s;
                            top: 110px;
                            display: block;
                        }
                    }
                    .sub-menu {
                        background-color: #fff;
                        position: absolute;
                        left: -100%;
                        height: 242px;
                        width: 364px;
                        display: none;
                        border: 1px solid @primary-color;
                        box-shadow: 0 6px 30px 0 rgba(0, 0, 0, 0.1);
                        border-radius: 5px;
                        .sub-menu-wrapper {
                            height: 100%;
                            display: flex;

                            .sub-menu-left {
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                flex: 3;
                                background-color: rgba(0, 0, 0, 0.05);
                                height: 100%;
                                &:hover {
                                    cursor: pointer;
                                    color: @primary-color2;
                                }
                                .sub-menu-img {
                                    width: 100%;
                                    flex: 3;
                                }
                                .sub-menu-name {
                                    text-align: center;
                                    flex: 1;
                                }
                            }
                            .sub-menu-right {
                                display: inline-block;
                                flex: 2;
                            }
                            .community-sub-menu {
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: space-around;
                                li {
                                    line-height: 20px;
                                    &:hover {
                                        cursor: pointer;
                                        color: @primary-color2;
                                    }
                                }
                            }
                        }
                    }
                    .sig-menu {
                        width: 572px;
                        .sub-menu-left {
                            flex: 2 !important;
                        }
                        .sig-sub-menu {
                            padding-left: 30px;
                            flex: 3 !important;
                            .sub-menu-head {
                                height: 60px;
                                line-height: 60px;
                                a {
                                    margin-left: 10px;
                                    &:hover {
                                        cursor: pointer;
                                        color: @primary-color;
                                    }
                                }
                            }
                            .sig-menu-content {
                                height: 182px;
                                display: flex;
                                flex-direction: column;
                                align-items: flex-start;
                                justify-content: flex-start;
                                flex-wrap: wrap;
                                li {
                                    line-height: 20px;
                                    margin-bottom: 15px;
                                    &:hover {
                                        cursor: pointer;
                                        color: @primary-color;
                                    }
                                }
                            }
                        }
                    }
                    & > li {
                        position: relative;
                        padding: 0 25px;
                        height: 100%;
                        line-height: 110px;
                        @media (max-width: 1000px) {
                            line-height: 70px;
                        }
                        & > a {
                            display: inline-block;
                            height: 100%;
                            cursor: pointer;
                            &:hover {
                                border-bottom: 5px solid @primary-color;
                            }
                        }
                    }
                }
                .nav-other {
                    flex: 1;
                    height: 100%;
                    .fz16();
                    color: @text-dark;
                    .ff-xih();
                    display: flex;
                    justify-content: flex-end;
                    @media (max-width: 1000px) {
                        display: none;
                    }
                    li {
                        margin-left: 36px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        span {
                            margin-top: 10px;
                        }
                    }
                }
                .search-mobile {
                    display: none;
                    text-align: center;
                    position: fixed;
                    top: 70px;
                    left: 0;
                    width: 100%;
                    background-color: #fff;
                }
                @media (max-width: 1000px) {
                    .nav-logo {
                        display: none;
                    }
                    .nav-logo-mobile {
                        display: inline-block;
                    }
                    .nav-other-mobile {
                        display: inline-block;
                    }
                }
            }
        }
    }
</style>
