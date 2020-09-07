<template>
    <div class="package-info">
        <el-form
                :inline="true"
                class="form">
            <div class="form-inputs">
                <el-form-item label="Product Version">
                    <el-select class="pc-select" v-model="formData.tableName" @change="initData(1, value)">
                        <el-option v-for="(item, index) in productV" :key="index"
                                   :label="item"
                                   :value="item">
                        </el-option>
                    </el-select>
                    <el-select class="mobile-select" v-model="formData.tableName" @change="initData(1, value)" placeholder="Product Version">
                        <el-option v-for="(item, index) in productV" :key="index"
                                   :label="item"
                                   :value="item">
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="Search">
                    <el-input
                            v-model="formData.queryPkgName"
                            class="pc-search"
                            placeholder="Search Name">
                        <i slot="suffix" class="icon-search" @click="initData(1, value)"></i>
                    </el-input>
                    <el-input
                            v-model="formData.queryPkgName"
                            class="mobile-search"
                            placeholder="Search Name">
                        <i slot="suffix" class="icon-search" @click="initData(1, value)"></i>
                    </el-input>
                </el-form-item>
            </div>
            <div class="form-btns">
                <a class="form-button" @click="centerDialogVisible = true">
                    <img src="@/assets/images/column.svg" alt="">
                    Custom Display Column
                </a>
                <a class="form-button" :href="excelUrl">
                    <img src="@/assets/images/dowmload.svg" alt="">
                    Export Excel
                </a>
            </div>
        </el-form>
        <el-dialog
                title="Display Column"
                class="column-button"
                :visible.sync="centerDialogVisible"
                width="80%"
                center>
            <div class="col-button">
                <el-checkbox-group v-model="checked">
                    <el-checkbox-button v-for="item in checkList" :label="item" :key="item">{{item}}</el-checkbox-button>
                </el-checkbox-group>
            </div>
            <span slot="footer" class="dialog-footer">
                <el-button type="primary" @click="columnFilter">OK</el-button>
                <el-button @click="centerDialogVisible = false">Clear</el-button>
            </span>
        </el-dialog>
        <template>
            <el-table
                    class="pc-pkg-table"
                    :data="tableData"
                    stripe
                    @filter-change="filterChange">
                <template v-for="(item, index) in filterTable(tableTitle)">
                    <el-table-column
                            :key="index"
                            v-if="item.label === 'Name'"
                            :label="item.label"
                            :prop="item.column_name">
                        <template slot-scope="scope" >
                            <a @click="go(scope.row.name, formData.tableName)">{{ scope.row.name }}</a>
                        </template>
                    </el-table-column>
                    <el-table-column
                        :key="index"
                        v-if="item.label === 'Maintainer'"
                        :label="item.label"
                        :prop="item.column_name"
                        :column-key="item.column_name"
                        :filters="filterData(pkgMaintainer)"
                        filter-placement="bottom-end">
                        <template slot-scope="scope">
                            <span>{{ scope.row.maintainer }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column
                            :key="index"
                            v-if="item.label === 'Maintenance Level'"
                            :label="item.label"
                            :prop="item.column_name"
                            :column-key="item.column_name"
                            :filters="filterData(pkgMainLevel)"
                            filter-placement="bottom-end">
                        <template slot-scope="scope">
                            <span>{{ scope.row.maintainlevel }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column
                        :key="index"
                        v-if="(item.label !== 'Maintainer') && (item.label !== 'Name') && (item.label !== 'Maintenance Level')"
                        :label="item.label"
                        :prop="item.column_name">
                    </el-table-column>
                </template>
            </el-table>
            <div class="mobile-pkg-table" v-for="(item, index) in tableData" :key="index">
                <ul class="pkg-line">
                    <li class="detail-title">Name：</li>
                    <li class="detail-notice"><a @click="go(item.name, formData.tableName)">{{ item.name }}</a></li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Version：</li>
                    <li>{{ item.version }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Release：</li>
                    <li>{{ item.release }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">URL：</li>
                    <li>{{ item.url }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">License：</li>
                    <li>{{ item.rpm_license }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Feature：</li>
                    <li>{{ item.feature }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Maintainer：</li>
                    <li>{{ item.maintainer }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Maintainlevel：</li>
                    <li>{{ item.maintainlevel }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Repo URL：</li>
                    <li>{{ item.gitee_url }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Summary：</li>
                    <li>{{ item.summary }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Description：</li>
                    <li>{{ item.description }}</li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Subpack：</li>
                    <li><span v-for="(item, index) in item.subpack" :key="index">{{ item.name }} </span></li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Required：</li>
                    <li><span v-for="(item, index) in item.buildrequired" :key="index">{{ item }} </span></li>
                </ul>
                <ul class="pkg-line">
                    <li class="detail-title">Issue Num：</li>
                    <li class="detail-notice">{{ item.issue }}</li>
                </ul>
            </div>
        </template>
        <el-pagination
                class="safety-bulletin-pagination"
                :current-page.sync="formData.pageNum"
                :page-size="formData.pageSize"
                layout="total, prev, pager, next, jumper"
                @current-change="initData"
                :total="total">
        </el-pagination>
        <el-pagination
                class="mobile-safety-bulletin-pagination"
                :current-page.sync="formData.pageNum"
                :page-size="formData.pageSize"
                layout="prev, pager, next"
                @current-change="initData"
                :total="total">
        </el-pagination>
    </div>
</template>

<script>
    import { productVersion } from "../../api/repo";
    import { packages } from "../../api/repo";
    import { maintainer } from "../../api/repo";
    import { tableCol } from "../../api/repo";


    export default {
        name: "package-info",
        data() {
            return {
                search: '',
                showOtherTag: null,
                centerDialogVisible: false,
                checkList: ["Name", "Version", "Release", "Url", "License", "Feature", "Maintainer", "Maintenance Level", "Release Time", "Used time", "Maintain Status", "Latest Version", "Latest Version Release Time", "Issue"],
                checked: [],
                pkgMaintainer: [],
                pkgMainLevel: ['1', '2', '3', '4'],
                formData: {
                    pageNum: 1,
                    pageSize: 10,
                    tableName: "bringInRely",
                    queryPkgName: "",
                    maintainner: '',
                    maintainlevel:''
                },
                pkgName: "",
                total: 0,
                productV: [],
                tableTitle: [],
                tableData: [],
                excelUrl: "",
                value: {
                    maintainner: "",
                    maintainlevel: ""
                }
            }
        },
        mounted() {
            this.getData(productVersion, 'productV');
            this.getData(tableCol, "tableTitle");
            this.getData(maintainer, "pkgMaintainer");
        },
        created () {
            this.initData(1, this.value);
        },
        methods: {
            filterTable(data) {
                let newTableTitle = data.filter(item => item.default_selected);
                return newTableTitle;
            },
            filterData(array) {
                let datas = [];
                array.forEach((item) => {
                    let titleData = {};
                    titleData.text = item;
                    titleData.value = item;
                    datas.push(titleData);
                })
                return datas;
            },
            filterChange (filterObj) {
                let value = {
                    maintainner: "",
                    maintainlevel: ""
                }
                if (filterObj.maintainner === undefined) {
                    value.maintainlevel = filterObj.maintainlevel[0];
                } else {
                    value.maintainner = filterObj.maintainner[0];
                }
                this.initData(1, value);
            },
            defaultColumn(data) {
                let titles = data;
                let columnTitleList = [
                    'Name',
                    'Version',
                    'Release',
                    'Maintainer',
                    'Maintenance Level',
                    'Release Time',
                    'Maintainer Status',
                    'Issue',
                    'Used Time'
                ];
                titles.forEach(title => {
                    let label = title.label;
                    if (columnTitleList.includes(label)) {
                        title.default_selected = true;
                    }
                })
                return titles
            },
            columnFilter() {
                this.centerDialogVisible = false;
                let title = this.tableTitle;
                title.forEach(item => item.default_selected = false);
                for (let i = 0; i < this.checked.length; i++) {
                    let item = this.checked[i];
                    for (let j = 0; j < title.length; j++) {
                        let n = title[j];
                        if (item === n.label) {
                            n.default_selected = true;
                        }
                    }
                }
                title = this.defaultColumn(title);
                this.tableTitle = title;
            },
            getTablePage (flag, value) {
                this.formData.pageNum = flag;
                this.formData.maintainner = value.maintainner;
                this.formData.maintainlevel = value.maintainlevel;
                packages(this.formData)
                    .then(response => {
                        if(response.total_count){
                            this.total = response.total_count;
                            this.tableData = response.data;
                            this.excelUrl = "https://api.openeuler.org/pkgmanagedebug/lifeCycle/download/packages?table_name=" + this.formData.tableName;
                        } else {
                            this.total = 0;
                            this.tableData = [];
                        }
                    })
                    .catch(response => {
                        this.$message.error('error', response);
                    });
            },
            initData(flag) {
                this.getTablePage(flag, this.value);
            },
            go (pkg_name, table_name){
                this.$router.push({
                    path: '/package-detail',
                    query: {pkg_name, table_name}
                })
            },
            getData(func, verb) {
                func()
                    .then(response => {
                        this[verb] = response.data;
                    })
                    .catch(response => {
                        this.$message.error(response);
                    });
            },
        }
    }
</script>

<style lang="less">
    .package-info .el-form-item:nth-child(2) {
        margin-left: 50px;
    }
    .package-info .el-button+.el-button {
        margin-left: 20px;
    }
    .column-button .el-checkbox-button__inner,
    .column-button .el-checkbox-button:first-child .el-checkbox-button__inner,
    .column-button .el-checkbox-button:last-child .el-checkbox-button__inner {
        border: 1px solid;
        padding: 8px 20px;
        color: #000;
        box-shadow: 0px 4px 20px 0px rgba(0, 0, 0, 0.1);
        border-radius: 16px;
        border: 1px solid rgba(0, 0, 0, 0.1);
    }
    .column-button .el-dialog__body {
        text-align: center;
    }
    .column-button .el-checkbox-button {
        display: inline-block;
        margin: 30px 20px 0;
    }
    .package-container label {
        font-size: 18px;
        font-family: Roboto-Regular,Roboto;
        font-weight: 400;
        color: #000;
        line-height: 40px;
    }
    .package-container .el-input__inner {
        line-height: 40px;
        border: 1px solid rgba(0, 0, 0, 0.5);
    }
    .package-container .el-input__inner:hover {
        border: 1px solid #002FA7;
    }
    .package-container .el-select:hover .el-input__inner {
        border: 1px solid #002FA7;
    }
    .package-container .el-table th, .has-gutter tr {
        background: rgba(0, 0, 0, 0.05);
    }
    .package-container .has-gutter th>.cell {
        color: #000;
        font-size: 16px;
        font-family: Roboto-Regular,Roboto;
        font-weight: 400;
        word-break: normal;
    }
    .package-container .el-table .cell {
        font-size: 14px;
        font-family: Roboto-Light,Roboto;
        font-weight: 300;
        color: rgba(0,0,0,0.85);
    }
    .package-container .el-table td {
        border: none;
    }
    .package-container .el-checkbox-button.is-checked .el-checkbox-button__inner {
        background-color: #fff;
        box-shadow: 0px 4px 20px 0px rgba(0, 0, 0, 0.1);
        border: 1px solid #002FA7;
        color: #000;
    }
    .package-info .el-button--primary {
        background-color: #002FA7;
        border-color: #002FA7;
    }
    .package-info .el-button--primary.is-active, .el-button--primary:active {
        color: #fff;
        background: #002FA7;
        border-radius: 4px;
    }
    .package-info .el-button--primary:focus, .el-button--primary:hover {
        background: #002FA7;
    }
    @media screen and (max-width: 1000px) {
        .package-info .el-form--inline .el-form-item__label {
            display: none;
        }
    }
</style>
<style scoped>
    h1 {
        font-size: 36px;
        font-family: HuaweiSans-Medium;
        margin: 60px 0;
    }
    .form-btns {
        display: inline-block;
        text-align: right;
    }
    .form-button {
        display: inline-block;
        text-decoration: none;
        color: #000;
        height: 40px;
        line-height: 40px;
        border-radius:4px;
        border: 1px solid rgba(0, 0, 0, 0.5);
        padding: 0 20px;
        margin-right: 20px;
        cursor: pointer;
    }
    .form-button img {
        width: 19px;
        height: 15px;
        vertical-align: middle;
    }
    .el-table .cell a {
        color: #002FA7;
        cursor: pointer;
    }
    .safety-bulletin-pagination {
        display: block;
        margin: 60px 0 200px 0;
    }
    .mobile-safety-bulletin-pagination {
        display: none;
    }
    .package-info form {
        display: flex;
        justify-content: space-between;
    }
    .pc-search,
    .pc-select {
        display: block;
    }
    .mobile-search,
    .mobile-select {
        display: none;
    }
    .pc-pkg-table {
        width: 100%;
        display: block;
    }
    .mobile-pkg-table {
        display: none;
    }
    .icon-search {
        cursor: pointer;
    }
    @media screen and (max-width: 1000px) {
        .pc-select,
        .pc-search {
            display: none;
        }
        .mobile-select,
        .mobile-search {
            display: block;
            width: 315px;
        }
        .form-btns {
            display: none;
        }
        .safety-bulletin-pagination {
            display: none;
        }
        .pc-pkg-table {
            display: none;
        }
        .mobile-pkg-table {
            display: block;
        }
        .mobile-safety-bulletin-pagination {
            display: block;
            margin: 40px 0 90px;
        }
        .package-info .el-form-item:nth-child(2) {
            margin:0 0 40px;
        }
        .mobile-pkg-table:nth-child(even) {
            background: rgba(0, 0, 0, 0.05);
        }
        .mobile-pkg-table {
            padding: 20px;
        }
        .mobile-pkg-table:last-child {
            padding-bottom: 0;
        }
        .pkg-line li {
            display: inline;
            font-size: 12px;
            line-height: 16px;
        }
        .pkg-line {
            margin-bottom: 10px;
        }
        .pkg-line li:first-child {
            font-family: Roboto-Regular;
            font-weight: 400;
        }
        .pkg-line li:last-child {
            font-family: Roboto-Light;
            font-weight: 300;
            color: rgba(0, 0, 0, 0.5);
        }
        .mobile-pkg-table .pkg-line .detail-notice {
            color: #002FA7;
        }
    }
</style>