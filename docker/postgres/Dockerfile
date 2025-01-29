FROM postgres:15

COPY init.sql /docker-entrypoint-initdb.d/

ENV POSTGRES_DB=amarshop_db
ENV POSTGRES_USER=db_admin
ENV POSTGRES_PASSWORD=123456

EXPOSE 5432