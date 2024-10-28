from typing import Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import os
import grpc
from app.pb.diceroller_pb2 import Dice, DiceResult
from app.pb.diceroller_pb2_grpc import DicerollerStub

from azure.monitor.opentelemetry import configure_azure_monitor

from opentelemetry import trace, baggage
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

from logging import getLogger
from logging.config import dictConfig

configure_azure_monitor(connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))

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
        "api-logger": {"handlers": ["default"], "level": "INFO"},
        #"azure.monitor.opentelemetry": {"handlers": ["default"], "level": "DEBUG"},
    },
}

dictConfig(log_config)
logger = getLogger("api-logger")
logger.info(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))

# trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
tracer = trace.get_tracer(__name__) 

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

@app.middleware("http")
async def ensure_w3c_header(request: Request, call_next):
    logger.info(f"Request received: {request.url}")
    logger.info(f"Middleware Headers: {request.headers}")
    response = await call_next(request)
    return response

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/grpc")
async def get_grpc(request: Request, dice: str = "1d6"):

    logger.info(f"Pre Headers: {request.headers}")
    with tracer.start_as_current_span("grpcdiceroll"):
        ctx = baggage.set_baggage("hello", "world")

        headers = {}
        W3CBaggagePropagator().inject(headers, ctx)
        TraceContextTextMapPropagator().inject(headers, ctx)
        logger.info(f"Post Headers: {headers}")
        if os.environ.get("GRPC_ENDPOINT").find(":443") > -1:
            credentials = grpc.ssl_channel_credentials()
            async with grpc.aio.secure_channel(os.environ.get("GRPC_ENDPOINT"), credentials) as channel:
                stub = DicerollerStub(channel)
                logger.info(f"Calling gRPC endpoint {os.environ.get('GRPC_ENDPOINT')}")
                response = await stub.Roll(Dice(dice=dice), metadata=[('grpc-trace-bin', headers['traceparent'].encode())])
                logger.info(f"Response from gRPC endpoint {response.input} | {response.result}")
                return { "input": response.input, "result": response.result }   
        else:
            async with grpc.aio.insecure_channel(os.environ.get("GRPC_ENDPOINT")) as channel:
                stub = DicerollerStub(channel)
                logger.info(f"Calling gRPC endpoint {os.environ.get('GRPC_ENDPOINT')}")
                response = await stub.Roll(Dice(dice=dice), metadata=[('grpc-trace-bin', headers['traceparent'].encode())])
                logger.info(f"Response from gRPC endpoint {response.input} | {response.result}")
                return { "input": response.input, "result": response.result }   

FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
