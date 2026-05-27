# Docker Notes

Docker 可以把应用和运行环境打包成镜像。

Docker volume 可以把容器内部的数据持久化到宿主机目录中。对于 SQLite 数据库，如果不使用 volume，容器删除后数据可能丢失。

Dockerfile 用于定义镜像如何构建。