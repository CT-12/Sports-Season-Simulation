FROM postgres:latest

ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=baseball_stats

COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
