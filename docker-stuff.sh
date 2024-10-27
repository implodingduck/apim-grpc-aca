source .env

cp -a pb grpcbackend/app/
cp -a pb grpcclient/app/

docker-compose down
docker-compose build
docker-compose up -d
docker logs -f apim-grpc-aca_grpcbackend_1