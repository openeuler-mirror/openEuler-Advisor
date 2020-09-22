<template>
    <div class="depend">
        <div class="depend-type">
            <span>Type</span>
            <div class="type-btns">
                <button :class="{'active': currentButton === 'Install'}" @click="clickButton($event)">Install Depend</button>
                <button :class="{'active': currentButton === 'Build'}" @click="clickButton($event)">Build Depend</button>
                <button :class="{'active': currentButton === 'Self'}" @click="clickButton($event)">Self Build Depend</button>
                <button :class="{'active': currentButton === 'Bedepend'}" @click="clickButton($event)">Bedepend</button>
            </div>
       </div>
        <div class="depend-search">
            <el-form
                    :inline="true"
                    class="form">
                <el-form-item label="Search">
                    <el-input
                            v-model="formData.queryPkgName"
                            class="pc-search"
                            placeholder="Search">
                        <i slot="suffix" class="icon-search"></i>
                    </el-input>
                    <el-input
                            v-model="formData.queryPkgName"
                            class="mobile-search"
                            placeholder="Search">
                        <i slot="suffix" class="icon-search"></i>
                    </el-input>
                </el-form-item>
                <el-form-item label="Product Version">
                    <el-select class="pc-select" v-model="formData.tableName" @change="initData(1)">
                        <el-option v-for="(item, index) in productV" :key="index"
                                   :label="item"
                                   :value="item">
                        </el-option>
                    </el-select>
                    <el-select class="mobile-select" v-model="formData.tableName" @change="initData(1)" placeholder="Product Version">
                        <el-option v-for="(item, index) in productV" :key="index"
                                   :label="item"
                                   :value="item">
                        </el-option>
                    </el-select>
                </el-form-item>
            </el-form>
        </div>
        <div class="depend-diagram">
            <div id="package-diagram"></div>
        </div>
    </div>
</template>

<script>
    export default {
        name: "depend-info",
        data () {
            return {
                formData: {
                    queryPkgName: "",
                    tableName: ""
                },
                productV: [],
                currentButton: 'Install'
            }
        },
        mounted() {
            this.drawLine()
        },
        methods: {
            initData() {

            },
            clickButton(event) {
                let text = event.currentTarget.innerHTML
                text = text.split(' ', 1)[0]
                this.currentButton = text
            },
            drawLine() {

            }
        }
    }
</script>

<style scoped>
.type-btns {
    display: inline-block;
}
.pc-search,
.pc-select {
    display: block;
}
.mobile-search,
.mobile-select {
    display: none;
}
#package-diagram {
    width: 600px;
    height: 600px;
}
@media screen and (max-width: 1000px) {
    .pc-search,
    .pc-select {
        display: none;
    }
    .mobile-search,
    .mobile-select {
        display: block;
        width: 315px;
    }
}
</style>