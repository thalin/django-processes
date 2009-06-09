# Standard module imports
import logging

# Standard module partial imports
from time import sleep
from sys import exit
from os import getpid

# 3rd party module partial imports
from django.core.management.base import BaseCommand
from django.conf import settings

# Process model
from processes.models import Process
from processes.exceptions import ProcessError

PROCESS_RESULTS_OPTIONS = {
    'logname'       : None,
    'logfile'       : None,
    'maxprocesses'  : 2,
    'waittime'      : 20,
    'pidfile'       : None,
}

def ProcessSort(x, y):
    """
    Comparison function to sort() a list of processes by created date.
    """
    if x.created > y.created:
        return 1
    elif x.created == y.created:
        return 0
    else: # x.created < y.created
        return -1

class Command(BaseCommand):
    help = "Process 'server'.  Handles running processes."

    def parse_options(self, *args, **kwargs):
        """
        Parse options for our command handler.
        Arguments:
            logname - Logger's name
            logfile - Output file for your log
            maxprocesses - Maximum number of processes to start at one time.
            waittime - Time to wait between checking if we should run new 
                        processes.
            pidfile - Path to file to store PID for this process.
        Sets:
            self.waittime
            self.maxprocesses
            self.logger
        Writes:
            pidfile
        """
        # Parse options
        options = PROCESS_RESULTS_OPTIONS.copy()
        for x in args:
            if "=" in x:
                k, v = x.split('=', 1) 
            else:
                k, v = x, True 
            options[k.lower()] = v

        # Set up our logger
        if options['logname'] is not None:
            self.logger = logging.getLogger(options['logname'])
        elif hasattr(settings, "LOG_NAME"):
            self.logger = logging.getLogger(settings.LOG_NAME)
        else:
            self.logger = logging.getLogger()
        if options['logfile'] is not None:
            ch = logging.FileHandler(options['logfile'])
        elif hasattr(settings, "LOG_FILENAME"):
            ch = logging.FileHandler(settings.LOG_FILENAME)
        else:
            ch = logging.StreamHandler()
        if settings.DEBUG:
            self.logger.setLevel(logging.DEBUG)
            ch.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
            ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        # Write out pidfile
        if options['pidfile'] is not None:
            pidfile = open(options['pidfile'], 'w')
            pidfile.write("%d\n" % getpid())
            pidfile.close()
        self.max_processes = getattr(settings, "MAX_PROCESSES", 4) # default to 2
        self.wait_time = getattr(settings, "PROCESS_WAIT_TIME", 20) # default to 20 seconds
        self.logger.debug("max_processes: %d" % self.max_processes)

    def handle(self, *args, **kwargs):
        '''
        Handle the process_server command.
        '''
        self.parse_options(*args, **kwargs)
        self.logger.info("Starting processing loop")
        try:
            # Run our main loop
            subclasses = Process.__subclasses__() # Find process subclasses
            while(True):
                processing = 0
                for pclass in subclasses: # Find number of currently running processes
                    processing += pclass.objects.filter(processing=True).count()
                to_run = self.max_processes - processing # Figure out how many new processes to run
                self.logger.debug("%d open slots for processes." % to_run)
                if to_run > 0:
                    self.logger.debug("Finding new processes.")
                    processes = []
                    for pclass in subclasses: # Build process queue
                        processes.extend([procs for procs in pclass.objects.filter(completed=False,processing=False,error=False)])
                    processes.sort(cmp=ProcessSort) # Sort by created date
                    if len(processes) > 0:
                        self.logger.debug("Starting new processes.")
                        for process in processes[:to_run]: # Start new processes
                            process.setLogger(self.logger)
                            process.start()
                sleep(self.wait_time)
        except KeyboardInterrupt:
            exit()
