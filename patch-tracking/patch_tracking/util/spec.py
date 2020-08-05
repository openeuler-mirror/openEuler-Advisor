"""
functionality of modify the spec file
"""

import re


class Spec:
    """
    functionality of update spec file
    """
    def __init__(self, content):
        self._lines = content.splitlines()
        self.version = "0.0"
        self.release = {"num": 0, "lineno": 0}
        self.source_lineno = 0
        self.patch = {"threshold": 6000, "max_num": 0, "lineno": 0}
        self.changelog_lineno = 0

        # 规避空文件异常
        if len(self._lines) == 0:
            self._lines.append("")

        # 查找配置项最后一次出现所在行的行号
        for i, line in enumerate(self._lines):
            match_find = re.match(r"[ \t]*Version:[ \t]*([\d.]+)", line)
            if match_find:
                self.version = match_find[1]
                continue

            match_find = re.match(r"[ \t]*Release:[ \t]*([\d.]+)", line)
            if match_find:
                self.release["num"] = int(match_find[1])
                self.release["lineno"] = i
                continue

            match_find = re.match(r"[ \t]*%changelog", line)
            if match_find:
                self.changelog_lineno = i
                continue

            match_find = re.match(r"[ \t]*Source([\d]*):", line)
            if match_find:
                self.source_lineno = i
                continue

            match_find = re.match(r"[ \t]*Patch([\d]+):", line)
            if match_find:
                num = int(match_find[1])
                self.patch["lineno"] = 0
                if num > self.patch["max_num"]:
                    self.patch["max_num"] = num
                self.patch["lineno"] = i
                continue

        if self.patch["lineno"] == 0:
            self.patch["lineno"] = self.source_lineno

        if self.patch["max_num"] < self.patch["threshold"]:
            self.patch["max_num"] = self.patch["threshold"]
        else:
            self.patch["max_num"] += 1

    def update(self, log_title, log_content, patches):
        """
            Update items in spec file
        """
        self.release["num"] += 1
        self._lines[self.release["lineno"]
                    ] = re.sub(r"[\d]+", str(self.release["num"]), self._lines[self.release["lineno"]])

        log_title = "* " + log_title + " " + self.version + "-" + str(self.release["num"])
        log_content = "- " + log_content
        self._lines.insert(self.changelog_lineno + 1, log_title + "\n" + log_content + "\n")

        patch_list = []
        for patch in patches:
            patch_list.append("Patch" + str(self.patch["max_num"]) + ": " + patch)
            self.patch["max_num"] += 1
        self._lines.insert(self.patch["lineno"] + 1, "\n".join(patch_list))

        return self.__str__()

    def __str__(self):
        return "\n".join(self._lines)


if __name__ == "__main__":
    SPEC_CONTENT = """Name: diffutils
Version: 3.7
Release: 3

Source: ftp://ftp.gnu.org/gnu/diffutils/diffutils-%{version}.tar.xz

Patch: diffutils-cmp-s-empty.patch

%changelog
* Mon Nov 11 2019 shenyangyang<shenyangyang4@huawei.com> 3.7-3
- DESC:delete unneeded comments

* Thu Oct 24 2019 shenyangyang<shenyangyang4@huawei.com> 3.7-2
- Type:enhancement
"""

    s = Spec(SPEC_CONTENT)
    s.update("Mon Nov 11 2019 patch-tracking", "DESC:add patch files", [
        "xxx.patch",
        "yyy.patch",
    ])

    print(s)

    SPEC_CONTENT = """"""

    s = Spec(SPEC_CONTENT)
    s.update("Mon Nov 11 2019 patch-tracking", "DESC:add patch files", [
        "xxx.patch",
        "yyy.patch",
    ])

    print(s)
