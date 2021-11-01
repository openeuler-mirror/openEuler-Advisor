# openEuler-Advisor

## 1. Introduction

openEuler-Advisor aims to provide automatic inspection and suggestions on routine work of the openEuler artifact repository.

Important directories and scripts in the current project:

(1) **upstream-info**: This directory contains upstream information of the software components in the artifact repository of openEuler.

(2) **advisors**: This directory provides some automation scripts, including:

2.1. **oa_upgradable.py**: a Python script based on **upstream-info**, which is used to query the upstream community version information and the recommended version of a software package.

2.2. **simple_update_robot.py**: a Python script used to automatically upgrade software packages in src-openeuler, including downloading a source package of the recommended version, modifying the spec file, compiling the OBS locally, and creating PRs and issues.

2.3. **check_missing_file.py**: a Python script used to inspect each repository in src-openeuler. If the spec file does not exist in a repository, you can directly create one.

2.4. **check_source_url.py**: a Python script used to check the source address of each software package in src-openeuler. If the address is invalid or incorrect, an issue is automatically created to notify address modification.

2.5. **create_repo.py** and **create_repo_with_srpm**: Python scripts that provide the function of creating repositories in batches.

2.6. **which_archived.py**: a script used to check whether the upstream community of the software in the artifact repository has been archived so that the maintenance team can adjust the package maintenance policy in a timely manner.

2.7. **check_repeated_repo.py**: a script used to check for duplicate software packages in src-openeuler.

2.8. **psrtool.py**: a script used to query the SIG to which a software package belongs and the list of software packages managed by a SIG.

2.9. **tc_reminder.py**: a script used to automatically create prompt information for TC members in openEuler.

2.10. **review_tool.py**: a script used to generate the code review list of RPs in a specified software repository PR to standardize the PR review process.

2.11. **issue_report.py**: a tool for automatically generating issue and CVE management tables (CSV files) and result reports (Markdown files). It provides the function of generating issue and CVE lists based on the openEuler version.

(3) **prow**: This directory stores the script for connecting to the CI/CD framework PROW.

## 2. Follow-up Plan

1. The @solarhu team is developing a tool to query the dependencies of all components in openEuler.

2. Optimize the **simple_update_robot.py** script to improve the automatic upgrade processing capability.

3. Optimize **upstream-info** to cover all software in the openEuler artifact repository, and integrate all YAML files in the openEuler community into **upstream-info** for unified management.

4. Optimize the upstream community code management protocol supported by **oa_upgradable.py** and add the support from fossil.


## 3. Tool Instructions

### 3.1 YAML File Specifications

The name of the YAML file in each src-openEuler repository must be the same as the repository name. For example, the name of the YAML file stored in the glibc repository is **glibc.yaml**, and the file is stored in the root directory of the repository.
In a YAML file, only the **version_control**, **src_repo**, **tag_prefix**, and **separator** fields need to be manually set. Other fields are automatically generated.

#### 3.1.1 Description of the Fields in the YAML File

##### 1. version_control

Version control protocol used by the upstream repository. Currently, svn, git, hg, github, gnome, metacpan, pypi are supported.

##### 2. src_repo

Actual address of the upstream repository. You can use version_control and src_repo to download the corresponding code.

##### 3. tag_prefix

Version prefix in the tag of the upstream repository. If the git protocol is used, you can run the git tag command to display all tags. If the tag provided by the upstream is v1_0_1, **tag_prefix** must be set to **^v**. The correct version information can be obtained by matching **tag_prefix**.

##### 4. separator

Version separator in the tag. If the tag is v1_0_1 and **separator** is set to **_**, the correct version number 1.0.1 can be obtained by parsing the code.

#### 3.1.2. Requirements and Examples of the Fields

##### 1. src_repo

1) If **version_control** is set to **svn**, **src_repo** requires a complete SVN repository address. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/amanda.yaml.
2) If **version_control** is set to **git**, **src_repo** requires a complete GIT repository address. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/mdadm.yaml.

3) If **version_control** is set to **hg**, **src_repo** requires a complete HG repository address. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/nginx.yaml.
4) If **version_control** is set to **github**, **src_repo** requires only proj/repo and does not require a complete URL. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/asciidoc.yaml.
5) If **version_control** is set to **gnome**, **src_repo** requires only $proj and does not require a complete URL. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/gnome-terminal.yaml. Note that many projects on gitlab.gnome.org require access permissions, which cannot be used as the upstream code repositories.
6) If **version_control** is set to **metacpan**, **src_repo** requires only $proj and does not require a complete URL. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/perl-Authen-SASL.yaml. Pay attention to the naming specifications on metacpan.
7) If **version_control** is set to **pypi**, **src_repo** requires only $proj and does not require a complete URL. For the example, see https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/python-apipkg. Pay attention to the naming rules on PyPI.

##### 2. tag_prefix

The tag rule varies depending on the project. For example, if the tag is v1.1, set tag_prefix to ^v.

##### 3. separator

The domain separator in the tag varies according to the project. Some projects use hyphens ("-") and some use underscores ("_"). The default value is period ("."). You are advised to add double quotation marks ("").

#### 3.1.3 Method for Verifying the Upstream Code Repository Information of Open Source Software

##### 1) Common methods for code configuration management

  git, svn, and hg can obtain the code repository information without downloading the complete code repository. The method is as follows:

\- git:

```
git ls-remote --tags $repo_url
```

\- svn:

    svn ls -v $repo_url/tags

\- hg:

    curl $repo_url/json-tags

##### 2) Common methods to use code hosting websites

\- GitHub

   curl https://api.github.com/repos/$user/$repo/release

   A list of complete release information in JSON format can be obtained. Not all projects support this function.

   curl https://api.github.com/repos/$user/$repo/tags

   A list of complete tag information in JSON format can be obtained. Not all projects support this function, and this information has been found to be wrong for some projects.

\- metacpan

   curl https://fastapi.metacpan.org/release/$repo

   The latest version information in JSON format can be obtained.

\- pypi

   curl https://pypi.org/pypi/$repo/json

   The information about the latest version of the project can be obtained.

- Use of tag_prefix and tag_pattern

  The tag information of some software uses prefixes, such as release-1.2.3 or v1.2.3.

  If **tag_prefix** is set, the same prefix is deleted from all tag strings.

  For example, a piece of software has two tags: 1.2.3 and release-1.2.2. If **tag_prefix** is set to release-, the processed tags are 1.2.3 and 1.2.2.

  **tag_pattern** is used for more complex forms and is not recommended.

- Use of separator

  If separator is set, a character can be replaced with a period (.).

  For some software, the separator for tag domain division is not period (.). In this case, you can set a separator to standardize the version tags.

  If the separator for tag domain division is period (.), setting separator does not affect the result.

### 3.2 Introduction to Advisors
#### 3.2.1 Environment Configuration
##### a. Install necessary software packages.
```
 pip3 install python-rpm-spec (ver>=0.10)
 pip3 install PyYAML (ver>=5.3.1)
 pip3 install requests (ver>=2.24.0)
 yum install rpmdevtools (ver>=8.3)
 pip3 install beautifulsoup4 (ver>=4.9.3)
 yum install yum-utils (ver>=1.1.31)
 yum install libabigail (ver>=1.6)
```

##### b. Configure JSON files.
```
 Run the ~/.gitee_personal_token.json command to create a JSON file.
 JSON file format: {"user":"gitee_user_name","access_token":"token_password"}
	
 Entry for setting the Gitee token password: https://gitee.com/profile/personal_access_tokens
```

##### c. Configure the Gitee SSH.
```
 If Gitee SSH is not configured, see https://gitee.com/help/articles/4181.
```

##### d. Configure the OBS.
```
 If OBS is not configured, see https://www.openeuler.org/en/.
```

##### e. Configure the Python environment.
```
 To use this tool in the development state, configure the Python environment path: source ./develop_env.sh.	
```

#### 3.2.2 Usage Description
##### a. simple_update_robot.py
```
Automatic upgrade of a single software package: python3 simple_update_robot.py -u pkg pkg_name branch_name [-n new_version]
Example: python3 simple_update_robot.py -u pkg snappy master
	
Manual upgrade of a single software package: python3 simple_update_robot.py pkg_name branch_name [-fc] [-d] [-s] [-n new_version] [-b] [-p]
Example: python3 simple_update_robot.py snappy openEuler-20.03-LTS -fc -d -s -n 1.8.1
	
Upgrade of a repository containing multiple software packages: python3 simple_update_robot.py -u repo repo_name branch_name
Example: python3 simple_update_robot.py -u repo src-openeuler master
	
Users can configure an automatic upgrade YAML file in the local working directory, for example, upgrade-example.yaml.
 repositories:

 - name: A-Tune
 - name: python-py
 - name: python-ply
   If you want to specify an upgrade version for some software packages, you can configure as follows:
    repositories:
 - name: A-Tune
   u_ver: x.y.z
 - name: python-py
 - name: python-ply
   Then use a tool to automatically upgrade upgrade-example: python3 simple_update_robot.py -u repo upgrade-example master.
```

##### b. oa_upgradable.py 
```
Query the upstream community information and recommended version of the software package: python3 oa_upgradable.py pkg_name
Example: python3 oa_upgradable.py glibc
```

##### c. issue_report.py
> ```
> Operating environment: Python 3.8 or later
>  Tool use:
>  
>  ```bash
>  python3 issue_report.py -milestone "openEuler 20.03-LTS" "openEuler 20.09" -branch "openEuler-21.03" "openEuler-20.09" -outpath /Users/lilu/Downloads 
>  ```
> Parameter description:
> 
> > -milestone: milestone of the openEuler version. Multiple milestone names can be entered. For example, "openEuler-21.03" and "openEuler 21.03-RC1".
> > -branch: branch name of the src-openEuler repositories. Multiple branch names can be entered. For example, "openEuler-21.03" and "openEuler-20.09".
> > -outpath:path where the version management report and version release report are generated.
> ```

#### 3.2.3 Advisors Consultant
If you have any other questions, send an email to licihua@huawei.com/zwfeng@huawei.com/shanshishi@huawei.com.