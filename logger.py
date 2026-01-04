import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("lpzg.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.stream = open(console_handler.stream.fileno(), mode="w", encoding="utf-8", buffering=1)
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.info("Logger initialized")
