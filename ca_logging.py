import logging

# Create a custom log
log = logging.getLogger(__name__)

log.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
format_log = '%(levelname)-10s | %(threadName)-10s | %(message)s'
c_format = logging.Formatter(format_log)
f_format = logging.Formatter('%(asctime)s |'+format_log)
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the log
log.addHandler(c_handler)
log.addHandler(f_handler)

if __name__ == "__main___":
    log.debug('This is a debug')
    log.info('This is an info')
