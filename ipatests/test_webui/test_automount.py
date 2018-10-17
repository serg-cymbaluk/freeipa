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
Automount tests
"""

import pytest

from ipatests.test_webui.dialogs import AddRecordDialog
from ipatests.test_webui.forms import Form, Radio, TextArea, TextBox
from ipatests.test_webui.ui_driver import UI_driver, UIUtils, screenshot

LOC_ENTITY = 'automountlocation'
MAP_ENTITY = 'automountmap'
KEY_ENTITY = 'automountkey'

LOC_PKEY = 'itestloc'
LOC_DATA = {
    'pkey': LOC_PKEY,
    'add': [
        ('textbox', 'cn', LOC_PKEY),
    ],
}

MAP_PKEY = 'itestmap'
MAP_DATA = {
    'pkey': MAP_PKEY,
    'add': [
        ('textbox', 'automountmapname', MAP_PKEY),
        ('textarea', 'description', 'map desc'),
    ],
    'mod': [
        ('textarea', 'description', 'map desc mod'),
    ]
}

KEY_PKEY = 'itestkey'
KEY_DATA = {
    'pkey': KEY_PKEY,
    'add': [
        ('textbox', 'automountkey', KEY_PKEY),
        ('textbox', 'automountinformation', '/itest/key'),
    ],
    'mod': [
        ('textbox', 'automountinformation', '/itest/key2'),
    ]
}


class LocationForm(Form):
    cn = TextBox()


class MapForm(Form):
    DIRECT = 'add'
    INDIRECT = 'add_indirect'

    method = Radio()
    automountmapname = TextBox()
    description = TextArea()
    # Indirect map fields
    key = TextBox()
    parentmap = TextBox()


class MapEditForm(Form):
    description = TextArea()


@pytest.fixture()
def location_dialog(ui):
    return AddRecordDialog(ui, form=LocationForm(ui))


@pytest.fixture()
def location(ui, location_dialog):
    class _Location:
        def __init__(self, cn):
            self.cn = cn

        def __enter__(self):
            ui.navigate_to_entity(LOC_ENTITY)
            ui.delete_record(self.cn)
            location_dialog.open()
            location_dialog.fill_form(cn=self.cn)
            location_dialog.add()
            ui.navigate_to_record(self.cn)
            return self

        def __exit__(self, *args):
            ui.delete_record(self.cn)
            return False

    return _Location


@pytest.fixture()
def map_dialog(ui):
    return AddRecordDialog(ui, form=MapForm(ui))


@pytest.mark.tier1
class TestAutomount(UI_driver):

    @pytest.fixture(autouse=True)
    def init(self, ui: UIUtils):
        ui.init_app()

    @screenshot
    def test_crud(self, ui: UIUtils, map_dialog):
        """
        Basic CRUD: automount
        """

        # location
        ui.basic_crud(LOC_ENTITY, LOC_DATA,
                      default_facet='maps',
                      delete=False,
                      breadcrumb='Automount Locations')

        # map
        ui.navigate_to_record(LOC_PKEY)

        ui.basic_crud(MAP_ENTITY, MAP_DATA,
                      parent_entity=LOC_ENTITY,
                      search_facet='maps',
                      default_facet='keys',
                      delete=False,
                      navigate=False,
                      breadcrumb=LOC_PKEY)

        # key
        ui.navigate_to_record(MAP_PKEY)

        ui.basic_crud(KEY_ENTITY, KEY_DATA,
                      parent_entity=MAP_ENTITY,
                      search_facet='keys',
                      navigate=False,
                      breadcrumb=MAP_PKEY)

        # delete
        ui.navigate_by_breadcrumb(LOC_PKEY)
        ui.delete_record(MAP_PKEY)

        ## test indirect maps
        direct_pkey = 'itest-direct'
        indirect_pkey = 'itest-indirect'

        map_dialog.open()
        map_dialog.fill_form(
            method=MapForm.DIRECT,
            automountmapname=direct_pkey,
            description='foobar'
        )
        map_dialog.add()

        map_dialog.open()
        map_dialog.fill_form(
            method=MapForm.INDIRECT,
            automountmapname=indirect_pkey,
            description='foobar',
            key='baz',
            parentmap=direct_pkey
        )
        map_dialog.add()

        ui.assert_record(direct_pkey)
        ui.assert_record(indirect_pkey)

        # delete
        ui.delete_record(direct_pkey)
        ui.delete_record(indirect_pkey)
        ui.navigate_by_breadcrumb('Automount Locations')
        ui.delete_record(LOC_PKEY)

    @screenshot
    def test_add_location_dialog(self, ui: UIUtils, location_dialog):
        """
        Test 'Add Automember Location' dialog behaviour
        """
        dialog = location_dialog

        ui.navigate_to_entity(LOC_ENTITY)
        ui.assert_facet(LOC_ENTITY, 'search')

        dialog.open()
        dialog.fill_form(cn='loc1')
        dialog.add_and_add_another()
        dialog.fill_form(cn='loc2')
        dialog.add()

        ui.assert_record('loc1')
        ui.assert_record('loc2')

        dialog.open()
        dialog.fill_form(cn='loc3')
        dialog.add_and_edit()

        self.assert_facet(LOC_ENTITY, facet="details")

        dialog.open()
        dialog.fill_form(cn='loc4')
        dialog.cancel()

        assert not dialog.is_open

        ui.delete_record(['loc1', 'loc2', 'loc4'])

    @screenshot
    def test_add_map_dialog(self, ui: UIUtils, location, map_dialog):
        """
        Test 'Add Automember Map' dialog behaviour
        """

        dialog = map_dialog

        with location('loc1'):
            dialog.open()
            dialog.fill_form(
                method=MapForm.DIRECT,
                automountmapname='map1',
                description='First description'
            )
            dialog.add_and_add_another()
            dialog.fill_form(
                method=MapForm.INDIRECT,
                automountmapname='map2',
                description='Second description',
                key='key1',
                parentmap='map1'
            )
            dialog.add_and_add_another()
            dialog.fill_form(
                method=MapForm.INDIRECT,
                automountmapname='map3',
                description='Third description',
                key='key2',
                parentmap='map2'
            )
            dialog.add()

            dialog.open()
            dialog.fill_form(
                method=MapForm.DIRECT,
                automountmapname='map3',
                description='Fourth description'
            )
            dialog.cancel()

            ui.delete_record(['map1', 'map2', 'map3'])
