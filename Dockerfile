# Base stage for the write service
FROM python:3.12-slim AS write-service-base

# Set the working directory for the write service
WORKDIR /app

# Copy the write service contents into the container
COPY write-service/requirements.txt /app/requirements.txt
COPY write-service/write-service.py /app/write-service.py

# Install dependencies for the write service
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the write service
EXPOSE 5002

# Set the command to run the write service
CMD ["python", "write-service.py"]


# Base stage for the read service
FROM python:3.12-slim AS read-service-base

# Set the working directory for the read service
WORKDIR /app

# Copy the read service contents into the container
COPY read-service/requirements.txt /app/requirements.txt
COPY read-service/read-service.py /app/read-service.py

# Install dependencies for the read service
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the read service
EXPOSE 5001

# Set the command to run the read service
CMD ["python", "read-service.py"]

# Base stage for the mds service
FROM python:3.12-slim AS mds-base

# Set the working directory for the mds service
WORKDIR /app

# Copy the mds service contents into the container
COPY mds/requirements.txt /app/requirements.txt
COPY mds/mds-service.py /app/mds-service.py

# Install dependencies for the mds service
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the mds service
EXPOSE 5006

# Set the command to run the mds service
CMD ["python", "mds.py"]

# Base stage for the wds service
FROM python:3.12-slim AS wds-base

# Set the working directory for the wds service
WORKDIR /app

# Copy the wds service contents into the container
COPY wds/requirements.txt /app/requirements.txt
COPY wds/wds-service.py /app/wds-service.py

# Install dependencies for the wds service
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the wds service
EXPOSE 5004

# Set the command to run the wds service
CMD ["python", "wds.py"]

# Base stage for the rds service
FROM python:3.12-slim AS rds-base

# Set the working directory for the rds service
WORKDIR /app

# Copy the rds service contents into the container
COPY rds/requirements.txt /app/requirements.txt
COPY rds/rds-service.py /app/rds-service.py

# Install dependencies for the rds service
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the rds service
EXPOSE 5003

# Set the command to run the rds service
CMD ["python", "rds.py"]
