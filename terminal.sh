#!/bin/bash

# Open new GNOME terminal tab and run mds.py
gnome-terminal --tab -- bash -c "cd /path/to/Distributed-Scalable-Data-Architecture/mds && python3 mds.py && echo 'mds.py has completed'; exec bash"

# Wait for 5 seconds to give mds.py time to start
sleep 5

# Retry mechanism to ensure mds.py is fully up before starting rds.py and wds.py
max_retries=10
counter=0
mds_ready=false

while [ $counter -lt $max_retries ]; do
    echo "Checking if mds.py is ready... Attempt $(($counter + 1))"
    if nc -zv localhost 5006; then
        echo "mds.py is ready!"
        mds_ready=true
        break
    else
        echo "mds.py is not ready yet, waiting 5 seconds..."
        sleep 5
    fi
    counter=$(($counter + 1))
done

if [ "$mds_ready" = true ]; then
    # Open new GNOME terminal tab and run rds.py
    gnome-terminal --tab -- bash -c "cd /path/to/Distributed-Scalable-Data-Architecture/rds && python3 rds.py && echo 'rds.py has completed'; exec bash"

    # Open new GNOME terminal tab and run wds.py
    gnome-terminal --tab -- bash -c "cd /path/to/Distributed-Scalable-Data-Architecture/wds && python3 wds.py && echo 'wds.py has completed'; exec bash"
else
    echo "mds.py did not start successfully after $max_retries attempts. Exiting script."
    exit 1
fi

# Wait for rds.py and wds.py to fully complete
wait

# Open new GNOME terminal tab and run read-service.py
gnome-terminal --tab -- bash -c "cd /path/to/Distributed-Scalable-Data-Architecture/read-service && python3 read-service.py && echo 'read-service.py has completed'; exec bash"

# Wait for read-service.py to fully complete
wait

# Open new GNOME terminal tab and run write-service.py
gnome-terminal --tab -- bash -c "cd /path/to/Distributed-Scalable-Data-Architecture/write-service && python3 write-service.py && echo 'write-service.py has completed'; exec bash"


# Wait for write-service.py to fully complete
wait

echo "All services have been started in separate terminal tabs."
