from typing import Union

from fastapi import FastAPI, Request

import os
import grpc
from app.pb.diceroller_pb2 import Dice, DiceResult
from app.pb.diceroller_pb2_grpc import DicerollerStub

app = FastAPI()


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
            response = await stub.Roll(Dice(dice=dice))
            
            return { "input": response.input, "result": response.result }   
    else:
        async with grpc.aio.insecure_channel(os.environ.get("GRPC_ENDPOINT")) as channel:
            stub = DicerollerStub(channel)
            response = await stub.Roll(Dice(dice=dice))
            
            return { "input": response.input, "result": response.result }   

