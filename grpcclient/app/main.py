from typing import Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import os
import grpc
from app.pb.diceroller_pb2 import Dice, DiceResult
from app.pb.diceroller_pb2_grpc import DicerollerStub

from azure.monitor.opentelemetry import configure_azure_monitor

from logging import getLogger
from logging.config import dictConfig

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",

        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "api-logger": {"handlers": ["default"], "level": "DEBUG"},
        #"azure.monitor.opentelemetry": {"handlers": ["default"], "level": "DEBUG"},
    },
}

dictConfig(log_config)
logger = getLogger("api-logger")
logger.info(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))

configure_azure_monitor(connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/grpc")
async def get_grpc(dice: str = "1d6"):
    #async with grpc.aio.insecure_channel(os.environ.get("GRPC_ENDPOINT")) as channel:
    if os.environ.get("GRPC_ENDPOINT").find(":443") > -1:
        credentials = grpc.ssl_channel_credentials()
        async with grpc.aio.secure_channel(os.environ.get("GRPC_ENDPOINT"), credentials) as channel:
            stub = DicerollerStub(channel)
            logger.info(f"Calling gRPC endpoint {os.environ.get('GRPC_ENDPOINT')}")
            response = await stub.Roll(Dice(dice=dice))
            logger.info(f"Response from gRPC endpoint {response.input} | {response.result}")
            return { "input": response.input, "result": response.result }   
    else:
        async with grpc.aio.insecure_channel(os.environ.get("GRPC_ENDPOINT")) as channel:
            stub = DicerollerStub(channel)
            logger.info(f"Calling gRPC endpoint {os.environ.get('GRPC_ENDPOINT')}")
            response = await stub.Roll(Dice(dice=dice))
            logger.info(f"Response from gRPC endpoint {response.input} | {response.result}")
            return { "input": response.input, "result": response.result }   

