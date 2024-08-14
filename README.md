# Distributed-Scalable-Data-Architecture

Used redis for this particualar project but do feel free to use any other database technology, you just have to change the addresses in the mds(Main Distribution Service) and also the write and read logic in wds and rds respectively.

You can easily add new data sources to read service and write service which house the Restful apis

Scale horizontally by adding more instances of rds and wds

Should serve as a foundation for a more complex data architecture.

What we have:
  -read service - houses the read endpoint which receives a read request thru an api, sends the data as a message using rabbitmq

  -read distribution service(rds) - responsible for the reading of the redis instance. receives the request from rabbitmq, reads it and sends the response to read service which then updates the frontend thru the api. periodically checks the  instances addresses.

  -write-service - same as read service but now for writing

  -write distribution service - same as rds, but for writing. should add tho that in wds, it writes to two redis instances, a main and a backup, the redis instances adresses are provided by the main distribution service. periodically checks the instances addresses

  -main distribution service(mds) - houses the addresses of the redis instances. dynamically reassigns main and backup roles based on availability of backup instances and connection health.

  -rabbitmq message queues for processing reading and writing requests

But yes, understand how everything works and you are going to find it easy. I should be rolling out new updates really soon in another branch. The goal is a high frequency data architecture with extremely high performance.

will rolout the docker compose or kubernetes soon.

the terminal.sh is a bash automated script for running all of tgem in different terminals using one script.
