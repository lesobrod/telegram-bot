from loguru import logger

LOGGER_CONFIG = {
    "handlers": [
        {
            "sink": "test_log.log",
            "format": "{time} | {level} | {message}",
            "encoding": "utf-8",
            "level": "DEBUG",
            "rotation": "5 MB",
            "compression": "zip"
        },
    ],
}

logger.configure(**LOGGER_CONFIG)
logger.level(name="HIST-COM", no=25, color="<blue>", icon="@")
logger.level(name="HIST-HOT", no=25, color="<blue>", icon="@")
logger.add("test_com_log.log", level=25, format="{time} | {level} | {message}")


for j in range(10):
    logger.info(str(j))
    logger.log("HIST-HOT", str(j+1))
    logger.log("HIST-COM", str(j+1))

with open("test_log.log", 'r', encoding='UTF-8') as file:
    for line in file:
        data = line.split('|')
        print(data[1])
