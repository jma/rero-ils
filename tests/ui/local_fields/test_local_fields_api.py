# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Local fields Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.local_fields.api import LocalField


def test_local_fields_es(client, local_field_martigny):
    """Test."""
    local_field = LocalField.get_local_fields_by_resource('doc', 'doc1')
    assert len(local_field) == 1

    local_field = LocalField.get_local_fields_by_resource(
        'doc', 'doc1', 'org2')
    assert len(local_field) == 0
