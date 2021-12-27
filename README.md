# GRIP Tools

System configuration files relevant to GRIP system deployment.

## Executable

`bin` directory includes scripts relevant to installation, setting up redis/kafka services, and adding some message-passing scripts.

## Configurations

Configuration files for:

- Kafka
- Redis
- ElasticSearch
- Crontab job

## Systemd

Systemd files for running services.

**NOTE**: this is likely to be deprecated since we containerized the services and the background services can be managed by Docker.
