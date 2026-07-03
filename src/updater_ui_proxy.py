"""Thread-aware Tkinter variables, widgets, and dialogs."""


class ThreadAwareVariable:
    def __init__(self, variable, app, snapshot_key):
        self.variable = variable
        self.app = app
        self.snapshot_key = snapshot_key

    def get(self):
        if not self.app._is_ui_thread():
            snapshot = getattr(self.app, "_update_selection", None) or {}
            if self.snapshot_key in snapshot:
                return snapshot[self.snapshot_key]
            return self.app._call_ui(self.variable.get, wait=True)
        return self.variable.get()

    def set(self, value):
        return self.app._call_ui(lambda: self.variable.set(value), wait=True)

    def trace_add(self, *args, **kwargs):
        return self.app._call_ui(
            lambda: self.variable.trace_add(*args, **kwargs), wait=True
        )

    def __getattr__(self, name):
        return getattr(self.variable, name)


class ThreadAwareWidget:
    ASYNC_METHODS = {
        "config", "configure", "insert", "delete", "see", "set",
        "selection_clear", "selection_set", "state",
    }

    def __init__(self, widget, app):
        self.widget = widget
        self.app = app

    def __getattr__(self, name):
        attribute = getattr(self.widget, name)
        if not callable(attribute):
            return attribute

        def call(*args, **kwargs):
            return self.app._call_ui(
                lambda: getattr(self.widget, name)(*args, **kwargs),
                wait=name not in self.ASYNC_METHODS,
            )

        return call

    def __getitem__(self, key):
        return self.app._call_ui(lambda: self.widget[key], wait=True)

    def __setitem__(self, key, value):
        return self.app._call_ui(
            lambda: self.widget.__setitem__(key, value), wait=True
        )


class MessageboxProxy:
    def __init__(self, original):
        self.original = original
        self.app = None

    def set_app(self, app):
        self.app = app

    def __getattr__(self, name):
        original_method = getattr(self.original, name)

        def call(*args, **kwargs):
            if self.app is None or self.app._is_ui_thread():
                return original_method(*args, **kwargs)
            return self.app._call_ui(
                lambda: original_method(*args, **kwargs), wait=True
            )

        return call
