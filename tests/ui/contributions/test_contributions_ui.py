# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Tests UI view for patrons."""


from flask import url_for


def test_contributions_detailed_view(client, contribution_person_data,
                                     document_ref):
    """Test contribution detailed view."""
    # check redirection
    res = client.get(url_for(
        'invenio_records_ui.cont', viewcode='global', pid_value='cont_pers'))
    assert res.status_code == 200

# TODO: add search view
