import asyncio
import logging

import grpc
from app.pb.diceroller_pb2 import Dice, DiceResult
from app.pb.diceroller_pb2_grpc import DicerollerServicer, add_DicerollerServicer_to_server
import rolldice


class Diceroller(DicerollerServicer):
    async def Roll(
        self,
        request: Dice,
        context: grpc.aio.ServicerContext,
    ) -> DiceResult:
        logging.info(f"Rolling the dice: {request.dice}")
        result, explanation = rolldice.roll_dice(request.dice)
        return DiceResult(input=request.dice, result=f"{result} ({explanation})")


async def serve() -> None:
    server = grpc.aio.server()
    add_DicerollerServicer_to_server(Diceroller(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())