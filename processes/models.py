import datetime
import traceback

from StringIO import StringIO

from django.db import models
from django.utils.encoding import smart_str, smart_unicode

from processes.fields import UUIDField
from processes.exceptions import ProcessError

try:
    import threading
except ImportError:
    import dummy_threading as threading

class ProcessManager(models.Manager):
    '''
    ProcessManager for Process objects.
    '''

    def processing(self):
        '''
        Filters for objects with the processing flag set to True.
        '''
        return self.filter(processing=True)

    def complete(self):
        '''
        Filters for objects with the completed flag set to True.
        '''
        return self.filter(completed=True)

    def error(self):
        '''
        Filters for objects with the error flag set to True.
        '''
        return self.filter(error=True)

    def to_run(self):
        '''
        Filters for objects which do not have processing, completed, or error
        flags set to True, and orders by created date.
        '''
        qs = self.filter(processing=False,completed=False,error=False)
        return qs.order_by('created')

    def has_run(self):
        '''
        Filters for objects which have any of the processing, completed, or
        error flags set to True.
        '''
        myQ = models.Q(processing=True)
        myQ = myQ|models.Q(completed=True)
        myQ = myQ|models.Q(error=True)
        return self.filter(myQ)


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

    objects = ProcessManager()

    class Meta:
        abstract = True

    def __str__(self):
        return smart_str(self.uuid)

    def __unicode__(self):
        return smart_unicode(self.uuid)

    def __init__(self, *args, **kwargs):
        '''
        Initialize both Model and Thread superclasses in the correct order.
        '''
        models.Model.__init__(self, *args, **kwargs)
        # Clearly order is important here as we do not have self.uuid until the
        # Model's __init__() has been run.
        threading.Thread.__init__(self, name=self.uuid)

    def save(self, *args, **kwargs):
        '''
        Save method overridden to add created and modified times.
        '''
        if not self.id:
            self.created = datetime.datetime.now()
            self.modified = datetime.datetime.now()
        else:
            self.modified = datetime.datetime.now()
        models.Model.save(self, *args, **kwargs)

    def setLogger(self, logger):
        self.logger = logger

    def run(self):
        '''
        Run the process.  This function first sets self.processing to be True
        so we can see which processes are running by querying the database,
        then attempts to run the setup, run_process, and teardown methods.

        If there are any ProcessErrors thrown, the error flag is set and the
        error_msg attribute is set to the ProcessError msg attribute.  If a 
        debug attribute is included in the ProcessError, then the debug_msg
        attribute is set to the included debug message, otherwise a stack
        trace is produced and saved to debug_msg.

        If any other errors occur, the error_msg attribute is set to 'Unknown
        Error!' and a stack trace is produced and saved to the debug_msg
        attribute.

        In either case, both error_msg and debug_msg are logged.

        If no exceptions are encountered, the completed flag is set to true.

        Once all of these conditions have been evaluated, the processing flag
        is reset to False, and the object is saved again.
        '''
        self.processing = True
        self.save()
        try:
            self.setup()
            self.run_process()
            self.teardown()
        except ProcessError, e:
            self.error = True
            self.error_msg = e.msg
            if e.debug:
                self.debug_msg = e.debug
            else:
                s = StringIO()
                traceback.print_exc(file=s)
                s.seek(0)
                self.debug_msg = s.read()
            self.logger.error("error_msg: %s" % self.error_msg)
            self.logger.error("debug_msg: %s" % self.debug_msg)
        except:
            self.error = True
            self.error_msg = "Unknown error!"
            s = StringIO()
            traceback.print_exc(file=s)
            s.seek(0)
            self.debug_msg = s.read()
            self.logger.error("error_msg: %s" % self.error_msg)
            self.logger.error("debug_msg: %s" % self.debug_msg)
        else:
            self.completed = True
        finally:
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
        '''
        pass

    def run_process(self):
        '''
        Run the process.  This method must be overridden.
        '''
        raise NotImplementedError("You must override this function in order for your process to run.")

