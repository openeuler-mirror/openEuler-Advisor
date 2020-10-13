<template>
    <div class="issue-list">
        <el-form
            :inline="true"
            class="form">
            <a class="form-button" href="https://api.openeuler.org/pkgmanage/lifeCycle/download/issues">
                <img src="@/assets/images/dowmload.svg" alt="">
                Export Excel
            </a>
        </el-form>
        <el-table
            class="pc-pkg-table"
            ref="filterTable"
            :data="issueData"
            stripe
            @filter-change="filterChange">
            <el-table-column
                prop="issue_id"
                label="Issue ID"
                width="120">
                <template slot-scope="scope">
                    <a :href="scope.row.issue_url" target="_blank">{{ scope.row.issue_id }}</a>
                </template>
            </el-table-column>
            <el-table-column
                prop="pkg_name"
                label="Package Name"
             width="140">
            </el-table-column>
            <el-table-column
                prop="issue_title"
                label="Issue Title"
                width="420">
            </el-table-column>
            <el-table-column
                    prop="issue_type"
                    label="Issue Type"
                    column-key="issue_type"
                    :filters="filterData(issueType)"
                    filter-placement="bottom-end">
                <template slot-scope="scope">
                    <span>{{ scope.row.issue_type }}</span>
                </template>
            </el-table-column>
            <el-table-column
                    prop="issue_status"
                    label="Issue Status"
                    column-key="issue_status"
                    :filters="filterData(issueStatus)">
                <template slot-scope="scope">
                    <span>{{ scope.row.issue_status }}</span>
                </template>
            </el-table-column>
            <el-table-column
                    prop="maintainer"
                    label="Maintainer">
                <template slot-scope="scope">
                    <span>{{ scope.row.maintainer }}</span>
                </template>
            </el-table-column>
        </el-table>
        <div class="mobile-pkg-table" v-for="(item, index) in issueData" :key="index">
            <ul class="pkg-line">
                <li class="detail-title">Issue ID：</li>
                <li class="detail-notice">{{ item.issue_id }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Package Name：</li>
                <li>{{ item.pkg_name }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Issue Title： </li>
                <li>{{ item.issue_title }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Issue Type：</li>
                <li>{{ item.issue_type }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Issue Status：</li>
                <li>{{ item.issue_status }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Maintainer：</li>
                <li>{{ item.maintainer }}</li>
            </ul>
        </div>


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
    import { issueList, issueType, issueStatus } from "../../api/issue";
    export default {
        name: "issue-list",
        data() {
            return {
                formData: {
                    pageNum: 1,
                    pageSize: 10,
                    issueType: '',
                    issueStatus: ''
                },
                total: 0,
                value: {
                    issueType: '',
                    issueStatus: ''
                },
                issueData: [],
                issueType: [],
                issueStatus: [],
            }
        },
        mounted() {
            this.getData(issueType, 'issueType');
            this.getData(issueStatus, 'issueStatus');
        },
        created() {
            this.initData(1, this.value);
        },
        methods: {
            getTablePage (flag, value) {
                this.formData.pageNum = flag;
                this.formData.issueType = value.issueType;
                this.formData.issueStatus = value.issueStatus;
                issueList(this.formData)
                    .then(response => {
                        if (response.total_count){
                            this.total = response.total_count;
                            this.issueData = response.data;
                        } else {
                            this.total = 0;
                            this.issueData = [];
                        }
                    })
                    .catch(data => {
                        this.$message.error(data);
                    });
            },
            initData(flag, value) {
                this.getTablePage(flag, value);
            },
            filterData(array) {
                let datas = [];
                array.forEach((item) => {
                    let o = {};
                    o.text = item;
                    o.value = item;
                    datas.push(o);
                })
                return datas;
            },
            filterChange (filterObj) {
                let value = {
                    issueStatus: '',
                    issueType: ''
                }
                if (filterObj.issue_type === undefined) {
                    value.issueStatus = filterObj.issue_status[0];
                } else {
                    value.issueType = filterObj.issue_type[0];
                }
                this.initData(1, value);
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
        },
    }
</script>

<style scoped>
    .el-table__row .cell a {
        color: #002fa7;
        text-decoration: none;
        cursor: pointer;
    }
    .safety-bulletin-pagination {
        display: block;
        margin: 60px 0 200px 0;
    }
    .mobile-safety-bulletin-pagination {
        display: none;
    }
    .form-button {
        display: inline-block;
        text-decoration: none;
        color: #000;
        height: 38px;
        line-height: 38px;
        border-radius: 4px;
        border: 1px solid rgba(0, 0, 0, 0.5);
        padding: 0 20px;
        margin-right: 20px;
        cursor: pointer;
        margin-bottom: 30px;
        float: right;
    }
    .form-button img {
        width: 19px;
        height: 15px;
        vertical-align: middle;
    }
    .form {
        display: block;
    }
    .pc-pkg-table {
        width: 100%;
        display: block;
    }
    .mobile-pkg-table {
        display: none;
    }
    @media screen and (max-width: 1000px) {
        .form {
            display: none;
        }
        .pc-pkg-table {
            display: none;
        }
        .mobile-pkg-table {
            display: block;
        }
        .safety-bulletin-pagination {
            display: none;
        }
        .mobile-safety-bulletin-pagination {
            display: block;
            margin: 40px 0 90px;
        }
        .mobile-pkg-table:nth-child(odd) {
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