<template>
    <div class="package-detail">
        <h1>{{ detailData.pkg_name }} Issues</h1>
        <div class="pkg-info">
            <ul class="pkg-line">
                <li class="detail-title">Version：</li>
                <li>{{ detailData.version }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Release：</li>
                <li>{{ detailData.release }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">URL：</li>
                <li>{{ detailData.url }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">License：</li>
                <li>{{ detailData.license }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Feature：</li>
                <li>{{ detailData.feature }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Maintainer：</li>
                <li>{{ detailData.maintainer }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Maintainlevel：</li>
                <li>{{ detailData.maintainlevel }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Repo URL：</li>
                <li>{{ detailData.gitee_url }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Summary：</li>
                <li>{{ detailData.summary }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Description：</li>
                <li>{{ detailData.description }}</li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Subpack：</li>
                <li><span v-for="(item, index) in detailData.subpack" :key="index">{{ item.name }} </span></li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Required：</li>
                <li><span v-for="(item, index) in detailData.buildrequired" :key="index">{{ item }} </span></li>
            </ul>
            <ul class="pkg-line">
                <li class="detail-title">Issue Num：</li>
                <li>{{ detailData.issue }}</li>
            </ul>
        </div>
        <div class="subpack" v-for="(tables, index) in detailData.subpack" :key="index">
            <p>{{ tables.name }}</p>
            <div class="package-table">
                <div class="provided">
                    <el-table
                            :data="tables.provides"
                            stripe
                            style="width: 100%">
                        <el-table-column
                                prop="name"
                                label="Symbol"
                                width="180">
                        </el-table-column>
                        <el-table-column
                                prop="requiredby"
                                label="Required by"
                                width="180">
                            <template  slot-scope="scope">
                                <span v-for="(item, index) in scope.row.requiredby" :key="index">{{ item }}</span>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
                <div class="required">
                    <el-table
                            :data="tables.requires"
                            stripe
                            style="width: 100%">
                        <el-table-column
                                prop="name"
                                label="Symbol"
                                width="180">
                        </el-table-column>
                        <el-table-column
                                prop="providedby"
                                label="Provided by"
                                width="180">
                            <template  slot-scope="scope">
                                <span v-for="(item, index) in scope.row.providedby" :key="index">{{ item }}</span>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import { packageDetail } from "../../api/repo";
    export default {
        name: "packageDetail",
        data() {
            return {
                detailData: {},
            }
        },
        mounted() {
            this.getPackageDetail();
        },
        methods: {
            getPackageDetail () {
                packageDetail({
                    pkg_name: this.$route.query.pkg_name,
                    table_name: this.$route.query.table_name
                })
                    .then(response => {
                        this.detailData = response.data;
                    })
                    .catch(data => {
                        this.$message.error(data);
                    });
            }
        }
    }
</script>
<style lang="less">
.package-table .el-table th, .has-gutter tr {
    background: rgba(0, 0, 0, 0.05);
}
.package-table .has-gutter th>.cell {
    color: #000;
    font-size: 12px;
    font-family: Roboto-Regular,Roboto;
    font-weight: 400;
}
.package-table .el-table .cell {
    font-size: 12px;
    font-family: Roboto-Light,Roboto;
    font-weight: 300;
    color: #000;
}
.package-table .el-table td {
    border: none;
}
</style>
<style scoped>
h1 {
    font-size: 36px;
    font-family: HuaweiSans-Medium;
    margin: 60px 0;
}
.package-detail {
    max-width: 1200px;
    margin: 0 auto;
}
.pkg-line .detail-title {
    font-size: 14px;
    font-family: Roboto-Bold,Roboto;
    font-weight: bold;
    margin-right: 20px;
    width: 105px;
}
.pkg-line {
    display: flex;
    justify-content: flex-start;
    margin-top: 20px;
}
.pkg-info li {
    width: 986px;
}
.subpack {
    margin-top: 60px;
}
.package-table {
    display: flex;
}
.package-table p {
    font-size: 14px;
    font-family: Roboto-Regular;
}
.table-name {
    display: flex;
}
.subpack li {
    display: inline-block;
    float: left;
    line-height: 56px;
    font-size: 14px;
}
.provided,
.required {
    max-width: 530px;
}
.provided {
    margin-right: 60px;
}
.table-title {
    width: 50%;
}
.cell span {
    display: block;
}
    @media screen and (max-width: 1000px) {
        .package-detail {
            padding: 0 30px;
        }
        h1 {
            font-size: 18px;
            font-family: FZLTCHJW;
            margin: 40px 0;
        }
        .package-table {
            display: block;
            margin-top: 20px;
        }
        .pkg-line .detail-title {
            font-size: 12px;
            font-family: Roboto-Regular;
            font-weight: 400;
            color: #000;
            width: 300px;
            margin-right: 10px;
        }
        .pkg-info li {
            font-size: 12px;
            font-family: Roboto-Regular;
            font-weight: 400;
            color: rgba(0, 0, 0, 0.5);
        }
        .provided {
            margin: 0;
        }
        .required {
            margin-top: 20px;
        }
    }
</style>