import subprocess
import datetime

from django.db import models

from processes.fields import UUIDField

try:
    import threading
except ImportError:
    import dummy_threading as threading

class Process(models.Model, threading.Thread):
    '''
    This model represents a process.  To use this you must inherit from this
    class, and at least override the run_process method.

    You may also override the setup and teardown methods which are run before
    and after the run_process method, respectively.
    '''
    uuid = UUIDField(auto=True)
    processing = models.BooleanField(editable=False, default=False)
    completed = models.BooleanField(editable=False, default=False)
    error = models.BooleanField(editable=False, default=False)
    error_msg = models.TextField(editable=False, blank=True)
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self, name=self.uuid)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.datetime.now()
            self.modified = datetime.datetime.now()
        else:
            self.modified = datetime.datetime.now()
        models.Model.save(self, *args, **kwargs)

    def run(self):
        self.processing = True
        self.save()
        try:
            self.setup()
            self.run_process()
            self.teardown()
        except ProcessError, e:
            self.error = True
            self.error_message = e.msg
        else:
            self.processing = False
            self.completed = True
            self.save()

    def setup(self):
        pass

    def teardown(self):
        pass

    def run_process(self):
        raise NotImplementedError("You must override this function in order for your process to run.")
