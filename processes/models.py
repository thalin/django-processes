import subprocess
import datetime

from django.db import models
from django.utils.encoding import smart_str, smart_unicode

from processes.fields import UUIDField
from processes.exceptions import ProcessError

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
    debug_msg = models.TextField(editable=False, blank=True)
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return smart_str(self.uuid)

    def __unicode__(self):
        return smart_unicode(self.uuid)

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        # Clearly order is important here as we do not have self.uuid until the
        # Model's __init__() has been run.
        threading.Thread.__init__(self, name=self.uuid)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = datetime.datetime.now()
            self.modified = datetime.datetime.now()
        else:
            self.modified = datetime.datetime.now()
        models.Model.save(self, *args, **kwargs)

    def set_logger(self, logger):
        self.logger = logger

    def run(self):
        self.processing = True
        self.save()
        try:
            self.setup()
            self.run_process()
        except ProcessError, e:
            self.error = True
            self.error_msg = e.msg
            if e.debug:
                self.debug_msg = e.debug
            self.logger.error(self.error_msg)
        else:
            self.completed = True
        finally:
            self.teardown()
            self.processing = False
            self.save()

    def setup(self):
        '''
        Set up the environment.
        '''
        pass

    def teardown(self):
        '''
        Tear down the environment.
        This method should never produce an error.
        '''
        pass

    def run_process(self):
        '''
        Run the process.  This method must be overridden.
        '''
        raise NotImplementedError("You must override this function in order for your process to run.")

