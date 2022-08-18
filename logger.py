import logging
import re
import time
import traceback
import os
import sys
from logging.handlers import RotatingFileHandler

class LoggerConfig:
    def __init__(self, file_path, max_log_file_size_mb, min_log_level):
        self.file_path = file_path
        self.max_log_file_size_mb = max_log_file_size_mb
        self.min_log_level = min_log_level

TRACE_LEVEL = logging.DEBUG - 1

class Logger:

    _num_of_bytes_in_1_mb = 1048576
    _stack_trace_line_regex = re.compile(
        r"File\s\"(?P<file>[^\"]+)\"\,\sline\s(?P<line>\d+)")
    _logger_format = '%(asctime)s %(location)s, %(name)s %(levelname)s %(message)s'

    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        format=_logger_format,
        datefmt='%Y/%m/%d %H:%M:%S')

    logging.addLevelName(TRACE_LEVEL, 'TRACE')
    logging.TRACE = TRACE_LEVEL

    def __init__(self, logger_type, logger_config, max_backup_files=10):
        self._log_enabled = len(logger_config.file_path) > 0 and os.path.isdir(
            os.path.dirname(logger_config.file_path))
        
        rotating_file_handler = RotatingFileHandler(filename=logger_config.file_path,
                                                    maxBytes=self._num_of_bytes_in_1_mb *
                                                    int(
                                                        logger_config.max_log_file_size_mb),
                                                    backupCount=max_backup_files,
                                                    mode="w")

        rotating_file_handler.setFormatter(
            logging.Formatter(self._logger_format))

        self._logger = logging.getLogger(logger_type)
        self._logger.level = self._log_name_to_level(
            logger_config.min_log_level.lower())
        self._logger.handlers = [rotating_file_handler]
        self._logger.propagate = False

        self.is_trace_enabled = self._logger.level >= TRACE_LEVEL

    def trace(self, msg):
        self._logger.log(TRACE_LEVEL, msg, extra={
                         "location": self._get_location()})

    def debug(self, msg):
        self._logger.debug(msg, extra={"location": self._get_location()})

    def info(self, msg):
        self._logger.info(msg, extra={"location": self._get_location()})

    def warning(self, msg):
        self._logger.warning(msg, extra={"location": self._get_location()})

    def error(self, msg, err=None):
        err_message = err.message if err is not None and hasattr(
            err, 'message') else ''
        self._logger.exception("{err} {message}, stacktrace: {st}".format(err=err_message, message=msg, st=self.get_current_stacktrace()),
                               extra={"location": self._get_location()})

    def fatal(self, msg):
        if self._log_enabled:
            self._logger.fatal("{message}, stacktrace: {st}".format(message=msg, st=self.get_current_stacktrace()),
                               extra={"location": self._get_location()})

    def is_debug_enabled(self):
        return self._logger.level <= logging.DEBUG

    @staticmethod
    def _log_name_to_level(name):
        if name == "trace":
            return TRACE_LEVEL
        if name == "debug":
            return logging.DEBUG
        elif name == "info":
            return logging.INFO
        elif name == "warning" or name == "warn":
            return logging.WARNING
        elif name == "error":
            return logging.ERROR
        elif name == "fatal":
            return logging.FATAL
        else:
            raise ValueError("invalid log level {}".format(name))

    @staticmethod
    def get_current_stacktrace():
        return "".join(traceback.format_stack())

    @staticmethod
    def get_last_error_stacktrace():
        stack_trace = traceback.format_stack()[:-2]
        stack_trace.extend(traceback.format_tb(sys.exc_info()[2]))
        stack_trace.extend(traceback.format_exception_only(
            sys.exc_info()[0], sys.exc_info()[1]))

        exception_str = "Traceback (most recent call last):\n" + \
            "".join(stack_trace)
        return exception_str.rstrip()

    def _get_location(self):
        try:
            row = traceback.format_stack(limit=3)[0]
            match = self._stack_trace_line_regex.search(row)
            if match is None:
                self._logger.warning("failed to format stack trace, row={row}".format(
                    row=row), extra={"st": ""})
                return ""

            fields = match.groupdict()
            line = fields["line"]
            file = fields["file"]

            separator = '/' if '/' in file else '__'
            file = file.split(separator)[-1]

            return "{file}:{line}".format(file=file, line=line)
        except Exception as err:
            return "failed to  get stacktrace with: {err}".format(err=err)
