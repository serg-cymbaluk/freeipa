# Authors:
#   Petr Vobornik <pvoborni@redhat.com>
#
# Copyright (C) 2013  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Cert tests
"""

from ipatests.test_webui.crypto_utils import generate_csr
from ipatests.test_webui.ui_driver import UI_driver
from ipatests.test_webui.ui_driver import screenshot
from datetime import date, timedelta
import pytest

ENTITY = 'cert'

ERR_SPACE = "invalid '{}': Leading and trailing spaces are not allowed"
ERR_MUST_INTEGER = "invalid '{}': must be an integer"
LEAST_SERIAL = "invalid '{}': must be at least 0"
INV_DATE = ("invalid '{}': does not match any of accepted formats: "
            "%Y%m%d%H%M%SZ, %Y-%m-%dT%H:%M:%SZ, %Y-%m-%dT%H:%MZ, "
            "%Y-%m-%dZ, %Y-%m-%d %H:%M:%SZ, %Y-%m-%d %H:%MZ")


def search_pkey(self, pkey):
    search_field_s = '.search-filter input[name=filter]'
    self.fill_text(search_field_s, pkey)
    self.action_button_click('find', parent=None)
    self.wait_for_request(n=2)


def check_option_negative(self, date, option):
    self.navigate_to_entity(ENTITY)
    self.select('select[name=search_option]', option)
    search_pkey(self, date)
    self.assert_last_error_dialog(INV_DATE.format(option))
    self.close_all_dialogs()


def check_space_error(self, string, option):
    self.navigate_to_entity(ENTITY)
    self.select('select[name=search_option]', option)
    search_pkey(self, string)
    self.assert_last_error_dialog(ERR_SPACE.format(option))
    self.close_all_dialogs()


def check_integer(self, string, option):
    """
    Method to check if provided value is integer.
    If not check for error dialog
    """
    self.navigate_to_entity(ENTITY)
    self.select('select[name=search_option]', option)
    search_pkey(self, string)
    self.assert_last_error_dialog(ERR_MUST_INTEGER.format(option))
    self.close_all_dialogs()


def check_minimum_serial(self, serial, option):
    self.navigate_to_entity(ENTITY)
    self.select('select[name=search_option]', option)
    search_pkey(self, serial)
    self.assert_last_error_dialog(LEAST_SERIAL.format(option))
    self.close_all_dialogs()


@pytest.mark.tier1
class test_cert(UI_driver):

    def setup(self, *args, **kwargs):
        super(test_cert, self).setup(*args, **kwargs)

        if not self.has_ca():
            self.skip('CA not configured')

    def _add_and_revoke_cert(self, reason='1'):
        hostname = self.config.get('ipa_server')
        csr = generate_csr(hostname)

        self.navigate_to_entity(ENTITY)
        self.facet_button_click('request_cert')
        self.fill_textbox('principal', 'HTTP/{}'.format(hostname))
        self.check_option('add', 'checked')
        self.fill_textarea('csr', csr)
        self.dialog_button_click('issue')
        self.assert_notification(assert_text='Certificate requested')
        self.navigate_to_entity(ENTITY)
        rows = self.get_rows()
        cert = rows[-1]

        self.navigate_to_row_record(cert)
        self.action_list_action('revoke_cert', False)
        self.select('select[name=revocation_reason]', reason)
        self.dialog_button_click('ok')
        self.navigate_to_entity(ENTITY)

        return cert

    @screenshot
    def test_read_prci(self):
        """
        Basic read: cert

        Certs don't have standard mod, add and delete methods.
        """
        self.init_app()
        self.navigate_to_entity(ENTITY)
        rows = self.get_rows()
        self.navigate_to_row_record(rows[0])
        self.navigate_by_breadcrumb("Certificates")

    @screenshot
    def test_search_revoked_on_to(self):
        """
        Try to search cert using revoked on to option
        """
        today = date.today()
        self.init_app()

        # revoke new certificate
        self._add_and_revoke_cert()

        self.select('select[name=search_option]', 'revokedon_to')
        search_pkey(self, str(today))
        rows = self.get_rows()
        assert len(rows) != 0

        # try to search with string
        check_option_negative(self, 'nonexistent', 'revokedon_to')

        # try to search using invalid date
        check_option_negative(self, '2018-02-30', 'revokedon_to')

        # try to search using date ago
        self.navigate_to_entity(ENTITY)
        self.select('select[name=search_option]', 'revokedon_to')
        search_pkey(self, str(today - timedelta(weeks=52 * 10)))
        rows = self.get_rows()
        assert len(rows) == 0

        # try to search with leading space
        check_option_negative(self, ' {}'.format(str(today)), 'revokedon_to')

        # try to search with trailing space
        check_option_negative(self, '{} '.format(str(today)), 'revokedon_to')
