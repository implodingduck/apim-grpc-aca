# apim-grpc-aca

Generating gRPC code:
```
python -m grpc_tools.protoc -I./protos --python_out=./pb --pyi_out=./pb --grpc_python_out=./pb ./protos/diceroller.proto
```

## Random notes
* May need to change `import diceroller_pb2 as diceroller__pb2` to `import app.pb.diceroller_pb2 as diceroller__pb2` in `pb/diceroller_pb2_grpc.py`
* In the APIM, be sure to enable Http/2 in the `Protocols + ciphers` section