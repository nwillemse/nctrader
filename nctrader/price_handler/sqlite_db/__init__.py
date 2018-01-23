#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 10:53:38 2016

@author: nwillemse
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base

engine = None
db_session = scoped_session(lambda: create_session(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_engine(uri, **kwargs):
    global engine
    engine = create_engine(uri, **kwargs)
    return engine
