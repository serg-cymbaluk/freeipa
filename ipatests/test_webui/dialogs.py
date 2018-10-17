#
# Copyright (C) 2018  FreeIPA Contributors see COPYING for license
#

class Dialog:
    def __init__(self, ui):
        self.ui = ui

    def cancel(self):
        self.ui.dialog_button_click('cancel')


class AddRecordDialog(Dialog):
    def __init__(self, ui, form=None):
        super().__init__(ui)
        self.form = form

    def open(self):
        self.ui.assert_no_dialog()
        self.ui.facet_button_click('add')
        self.ui.assert_dialog('add')

    def add(self):
        self.ui.dialog_button_click('add')
        self.ui.wait_for_request()

    def add_and_add_another(self):
        self.ui.dialog_button_click('add_and_add_another')
        self.ui.wait_for_request()

    def add_and_edit(self):
        self.ui.dialog_button_click('add_and_edit')
        self.ui.wait_for_request()

    def fill_form(self, **kwargs):
        self.form.set_values(**kwargs)

    @property
    def is_open(self):
        return self.ui.get_dialog(name='add')
