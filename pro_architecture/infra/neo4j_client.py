import os
from neo4j import GraphDatabase
from config import S

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            S.NEO4J_URI,
            auth=(S.NEO4J_USER, S.NEO4J_PASSWORD),
            connection_timeout=10,
            max_connection_pool_size=5,
            max_connection_lifetime=30,
        )
    return _driver

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
