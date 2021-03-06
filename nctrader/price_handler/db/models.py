# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 10:53:38 2018

@author: nwillemse
"""
# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import (BigInteger, Integer, Column, String, Float, DateTime,
                        Time, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship
from . import Base


class Asset(Base):
    """
    """
    __tablename__ = 'asset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange_id = Column(Integer, ForeignKey('exchange.id'), nullable=False)
    data_vendor_id = Column(Integer, ForeignKey('data_vendor.id'), nullable=False)
    ticker = Column(String(50), nullable=False)
    exchange_ticker = Column(String(50))
    name = Column(String(50))
    type = Column(String(25))
    sector = Column(String(25))
    currency = Column(String(10))
    big_point_value = Column(Integer)
    minimum_tick_size = Column(Float)
    tick_value = Column(Float)
    margin = Column(Float)

    created_date = Column(DateTime, default=datetime.now)
    last_updated_date = Column(DateTime, default=datetime.now)

    UniqueConstraint(exchange_id, data_vendor_id, ticker, name='asset_u1')
    data_vendor = relationship("DataVendor", back_populates="assets")
    exchange = relationship("Exchange", back_populates="assets")
    bar_data = relationship("BarData", back_populates="assets")
    tick_data = relationship("TickData", back_populates="assets")

    def __repr__(self):
        return ('<Asset(id:%s exchange_id:%s data_vendor_id:%s ticker:%s type:%s created_date:%s last_updated_date:%s)>' % \
                (self.id, self.exchange_id, self.data_vendor_id, self.ticker, self.type, self.created_date, self.last_updated_date)
            )


class Exchange(Base):
    """
    """
    __tablename__ = 'exchange'

    id = Column(Integer, primary_key=True, autoincrement=True)
    abbrev = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False, unique=True)
    city = Column(String(50))
    country = Column(String(50))
    currency = Column(String(10))
    timezone_offset = Column(Time)

    created_date = Column(DateTime, default=datetime.now)
    last_updated_date = Column(DateTime, default=datetime.now)

    assets = relationship("Asset", order_by=Asset.id, back_populates="exchange")

    def __repr__(self):
        return ('<Exchange(id:%s abbrev:%s name:%s city:%s country:%s currency:%s timezone_offset:%s created_date:%s last_updated_date:%s)>' % \
                (self.id, self.abbrev, self.name, self.city, self.country, self.currency, self.timezone_offset, self.created_date, self.last_updated_date)
            )


class DataVendor(Base):
    """
    """
    __tablename__ = 'data_vendor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    website_url = Column(String(50))
    support_email = Column(String(50))

    created_date = Column(DateTime, default=datetime.now)
    last_updated_date = Column(DateTime, default=datetime.now)

    assets = relationship("Asset", order_by=Asset.id, back_populates="data_vendor")

    def __repr__(self):
        return ('<DataVendor(id:%s name:%s website:%s support_email:%s created_date:%s last_updated_date:%s)>' % \
                (self.id, self.name, self.website_url, self.support_email, self.created_date, self.last_updated_date)
            )


class BarData(Base):
    """
    """
    __tablename__ = 'bar_data'
    asset_id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    bar_size = Column(String(10), nullable=False, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)

    volume = Column(BigInteger)
    open_interest = Column(BigInteger)

    created_date = Column(DateTime, default=datetime.now)
    last_updated_date = Column(DateTime, default=datetime.now)

    assets = relationship("Asset", order_by=Asset.id, back_populates="bar_data")

    def __repr__(self):
        return ('<BarData(asset_id:%s bar_size:%s timestamp:%s open_price:%s high_price:%s low_price:%s close_price:%s created_date:%s last_updated_date:%s)>' % \
                (self.asset_id, self.bar_size, self.timestamp, self.open_price, self.high_price, self.low_price, self.close_price, self.created_date, self.last_updated_date)
            )


class TickData(Base):
    """
    """
    __tablename__ = 'tick_data'
    asset_id = Column(Integer, ForeignKey('asset.id'), primary_key=True)

    timestamp = Column(DateTime, primary_key=True)
    bid_price = Column(Float, nullable=False)
    ask_price = Column(Float, nullable=False)

    created_date = Column(DateTime, default=datetime.now)
    last_updated_date = Column(DateTime, default=datetime.now)

    assets = relationship("Asset", order_by=Asset.id, back_populates="tick_data")

    def __repr__(self):
        return ('<TickData(asset_id:%s timestamp:%s bid_price:%s ask_price:%s created_date:%s last_updated_date:%s)>' % \
                (self.asset_id, self.timestamp, self.bid_price, self.ask_price, self.created_date, self.last_updated_date)
            )
