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

"""API for manipulating patron transactions."""

from datetime import datetime, timezone
from functools import partial

from flask import current_app

from .models import PatronTransactionIdentifier
from ..api import IlsRecord, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..organisations.api import Organisation
from ..patron_transaction_events.api import PatronTransactionEvent, \
    PatronTransactionEventsSearch
from ..providers import Provider

# provider
PatronTransactionProvider = type(
    'PatronTransactionProvider',
    (Provider,),
    dict(identifier=PatronTransactionIdentifier, pid_type='pttr')
)
# minter
patron_transaction_id_minter = partial(
    id_minter, provider=PatronTransactionProvider)
# fetcher
patron_transaction_id_fetcher = partial(
    id_fetcher, provider=PatronTransactionProvider)


class PatronTransactionsSearch(IlsRecordsSearch):
    """Patron Transactions Search."""

    class Meta:
        """Search only on patron transaction index."""

        index = 'patron_transactions'


class PatronTransaction(IlsRecord):
    """Patron Transaction class."""

    minter = patron_transaction_id_minter
    fetcher = patron_transaction_id_fetcher
    provider = PatronTransactionProvider

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create patron transaction record."""
        record = super(PatronTransaction, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        PatronTransactionEvent.create_event_from_patron_transaction(
            patron_transaction=record, dbcommit=dbcommit, reindex=reindex,
            delete_pid=delete_pid, update_parent=False)
        return record

    @property
    def loan_pid(self):
        """Return the loan pid of the the overdue patron transaction."""
        from ..notifications.api import Notification
        if self.notification_pid:
            notif = Notification.get_record_by_pid(self.notification_pid)
            return notif.loan_pid
        return None

    @property
    def document_pid(self):
        """Return the document pid of the the overdue patron transaction."""
        from ..notifications.api import Notification
        if self.notification_pid:
            notif = Notification.get_record_by_pid(self.notification_pid)
            return notif.document_pid
        return None

    @property
    def patron_pid(self):
        """Return the patron pid of the patron transaction."""
        return self.replace_refs()['patron']['pid']

    @property
    def total_amount(self):
        """Return the total_amount of the patron transaction."""
        return self.get('total_amount')

    @property
    def notification_pid(self):
        """Return the notification pid of the patron transaction."""
        if self.get('notification'):
            return self.replace_refs()['notification']['pid']
        return None

    @property
    def notification(self):
        """Return the notification of the patron transaction."""
        from ..notifications.api import Notification
        if self.get('notification'):
            pid = self.replace_refs()['notification']['pid']
            return Notification.get_record_by_pid(pid)
        return None

    @property
    def notification_transaction_library_pid(self):
        """Return the transaction library of the notification."""
        notif = self.notification
        if notif:
            location = notif.transaction_location
            if location:
                return location.library_pid

    @property
    def notification_transaction_user_pid(self):
        """Return the transaction user pid of the notification."""
        notif = self.notification
        if notif:
            return notif.transaction_user_pid
        return None

    @property
    def status(self):
        """Return the status of the patron transaction."""
        return self.get('status')

    @classmethod
    def create_patron_transaction_from_notification(
            cls, notification=None, dbcommit=None, reindex=None,
            delete_pid=None):
        """Create a patron transaction from notification."""
        record = {}
        if notification.get('notification_type') == 'overdue':
            data = build_patron_transaction_ref(notification, {})
            data['creation_date'] = datetime.now(timezone.utc).isoformat()
            data['type'] = 'overdue'
            data['status'] = 'open'
            record = cls.create(
                data,
                dbcommit=dbcommit,
                reindex=reindex,
                delete_pid=delete_pid
            )
        return record

    @property
    def currency(self):
        """Return patron transaction currency."""
        organisation_pid = self.organisation_pid
        return Organisation.get_record_by_pid(organisation_pid).get(
            'default_currency')

    @property
    def events(self):
        """Shortcut for events of the patron transaction."""
        # events = []
        results = PatronTransactionEventsSearch().filter(
            'term', parent__pid=self.pid
        ).source().scan()
        for result in results:
            yield PatronTransactionEvent.get_record_by_pid(result.pid)

    def get_number_of_patron_transaction_events(self):
        """Get number of patron transaction events."""
        results = PatronTransactionEventsSearch().filter(
            'term', parent__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        events = self.get_number_of_patron_transaction_events()
        if events:
            links['events'] = events
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete


def build_patron_transaction_ref(notification, data):
    """Create $ref for a patron transaction."""
    from ..notifications.api import calculate_overdue_amount
    schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
    data_schema = {
        'base_url': current_app.config.get(
            'RERO_ILS_APP_BASE_URL'
        ),
        'schema_endpoint': current_app.config.get(
            'JSONSCHEMAS_ENDPOINT'
        ),
        'schema': schemas['pttr']
    }
    data['$schema'] = '{base_url}{schema_endpoint}{schema}'\
        .format(**data_schema)
    base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
    url_api = '{base_url}/api/{doc_type}/{pid}'
    for record in [
        {'resource': 'notification', 'pid': notification.pid},
        {'resource': 'patron', 'pid': notification.patron_pid},
        {'resource': 'organisation', 'pid': notification.organisation_pid}
    ]:
        data[record['resource']] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='{}s'.format(record['resource']),
                pid=record['pid'])
            }
    data['total_amount'] = calculate_overdue_amount(notification)
    return data