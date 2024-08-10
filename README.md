# Distributed-Scalable-Data-Architecture

Used redis for this particualar project but do feel free to use any other database technology, you just have to change the addresses in the mds(Main Distribution Service) and also the write and read logic in wds and rds specifically.

You can easily add new data sources to read service and write service whoch house the Restful apis

Scale horizontally by adding more instances of rds and wds

Should serve as a foundation for a more complex data architecture.

What we have:
-read service - houses the read endpoint which receives a read request thru an api, sends the data as a message using rabbitmq

-read distribution service(rds) - responsible for the reading of the redis instance. receives the request from rabbitmq, reads it and sends the response to read service which then updates the frontend thru the api

write-service - same as read service but now for writing

write distribution service - same as rds, but for writing. should add tho that in wds, it writes to two redis instances, a main and a backup, the redis instances adresses are provided by the main distribution service

main distribution service(mds) - houses the addresses of the redis instances. Still under development, gonna update as soon as possible but it will be able to dynamically reassign main, backup and demonted roles based on its health assessment checks of the instances.

message service uses rabbit and its for updating the frontend ui


i should also rollout the docker instructions, with orchestration done with docker-compose or kubernetes
