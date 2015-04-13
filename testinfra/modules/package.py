# -*- coding: utf8 -*-
# Copyright © 2015 Philippe Pepiot
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

import pytest

from testinfra.modules.base import Module


class Package(Module):
    """Test packages status and version"""

    def __init__(self, name):
        self.name = name
        super(Package, self).__init__()

    @property
    def is_installed(self):
        raise NotImplementedError

    @property
    def version(self):
        raise NotImplementedError

    def __repr__(self):
        return "<package %s>" % (self.name,)

    @classmethod
    def as_fixture(cls):
        @pytest.fixture(scope="session")
        def f(Command, SystemInfo):
            if SystemInfo.type == "freebsd":
                return FreeBSDPackage
            elif SystemInfo.type in ("openbsd", "netbsd"):
                return OpenBSDPackage
            elif Command.run_test("which apt-get").rc == 0:
                return DebianPackage
            else:
                raise NotImplementedError
        f.__doc__ = cls.__doc__
        return f


class DebianPackage(Package):

    @property
    def is_installed(self):
        return self.run_test((
            "dpkg-query -f '${Status}' -W %s | "
            "grep -qE '^(install|hold) ok installed$'"), self.name).rc == 0

    @property
    def version(self):
        return self.check_output((
            "dpkg-query -f '${Status} ${Version}' -W %s | "
            "sed -n 's/^install ok installed //p'"), self.name)


class FreeBSDPackage(Package):

    @property
    def is_installed(self):
        EX_UNAVAILABLE = 69
        return self.run_expect(
            [0, EX_UNAVAILABLE], "pkg query %%n %s", self.name).rc == 0

    @property
    def version(self):
        return self.check_output("pkg query %%v %s", self.name)


class OpenBSDPackage(Package):

    @property
    def is_installed(self):
        return self.run_test("pkg_info -e %s", "%s-*" % (self.name,)).rc == 0

    @property
    def version(self):
        out = self.check_output("pkg_info -e %s", "%s-*" % (self.name,))
        # OpenBSD: inst:zsh-5.0.5p0
        # NetBSD: zsh-5.0.7nb1
        return out.split(self.name + "-", 1)[1]