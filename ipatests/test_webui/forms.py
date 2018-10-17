#
# Copyright (C) 2018  FreeIPA Contributors see COPYING for license
#

class FormField:

    def __init__(self):
        self.name = None

    def set_name(self, name):
        self.name = name

    def set_value(self, value, context=None):
        raise NotImplementedError()


class TextBox(FormField):
    def set_value(self, value, context=None):
        self.ui.fill_textbox(self.name, value, context)


class TextArea(FormField):
    def set_value(self, value, context=None):
        self.ui.fill_textarea(self.name, value, context)


class Password(FormField):
    def set_value(self, value, context=None):
        self.ui.fill_password(self.name, value, context)


class Radio(FormField):
    def set_value(self, value, context=None):
        self.ui.check_option(self.name, value, context)


class CheckBox(FormField):
    def set_value(self, value, context=None):
        self.ui.check_option(self.name, value, context)


class Select(FormField):
    def set_value(self, value, context=None):
        self.ui.select('select[name=%s]' % self.name, value, context)


class ComboBox(FormField):
    def set_value(self, value, context=None):
        self.ui.select_combobox(self.name, value, context)


class MultiValue(FormField):
    def set_value(self, value, context=None):
        self.ui.fill_multivalued(self.name, value, context)


class FormMeta(type):
    def __init__(cls, name, bases, attrs):
        super(FormMeta, cls).__init__(name, bases, attrs)
        for name, field in attrs.items():
            if isinstance(field, FormField):
                field.set_name(name)
                cls._fields[name] = field


class Form(metaclass=FormMeta):
    _fields = {}

    def __init__(self, ui):
        self.ui = ui
        for field in self._fields.values():
            field.ui = ui

    def set_values(self, **values):
        context = self.ui.get_form()

        for key, value in values.items():
            field = self._fields.get(key)
            if not field:
                continue
            field.set_value(value, context)
            self.ui.wait()
