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

PROCESS_RESULTS_OPTIONS = {
    'logname'       : None,
    'logfile'       : None,
    'maxprocesses'  : 2,
    'waittime'      : 20,
    'pidfile'       : None,
}

class Command(BaseCommand):
    help = "Process 'server'.  Handles running processes."

    def handle(self, *args, **kwargs):
        '''
        Handle the process_server command.
        Arguments:
            logname - Logger's name
            logfile - Output file for your log
            maxprocesses - Maximum number of processes to start at one time.
            waittime - Time to wait between checking if we should run new 
                        processes.
            pidfile - Path to file to store PID for this process.
        '''
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
        max_processes = getattr(settings, "MAX_PROCESSES", 2) # default to 2
        wait_time = getattr(settings, "PROCESS_WAIT_TIME", 20) # default to 20 seconds
        self.logger.debug("max_processes: %d" % max_processes)
        self.logger.info("Starting processing loop")
        try:
            # Run our main loop
            processes = []
            while(True):
                to_run = max_processes - processing
                self.logger.debug("%d open slots for processes." % to_run)
                to_process = Process.objects.filter(completed=False,is_processing=False,error=False)[:to_run]
                if len(to_process) > 0:
                    self.logger.info("Starting new processes.")
                    for process in to_process:
                        processes.append(process)
                        process.start()
                sleep(wait_time)
        except KeyboardInterrupt:
            exit()
