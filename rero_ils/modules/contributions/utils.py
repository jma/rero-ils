# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Contributions utilities."""

from __future__ import absolute_import, print_function

from flask import current_app


def get_contribution_localized_value(contribution, key, language):
    """Get the 1st localized value for given key among MEF source list.

    :params contribution: Contribution data.
    :params key: Key to find a translated form.
    :param language: Language to use.
    :resturns: Valu from key in language if found otherwise the value of key.
    """
    order = current_app.config.get(
        'RERO_ILS_CONTRIBUTIONS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))
    for source in source_order:
        value = contribution.get(source, {}).get(key)
        if value:
            return value
    return contribution.get(key)
