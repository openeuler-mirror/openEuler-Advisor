'''
Database entity model mapping
'''
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from packageship.libs.dbutils.sqlalchemy_helper import DBHelper


class src_pack(DBHelper.BASE):  # pylint: disable=C0103,R0903
    '''
    functional description:Source package model
    modify record:
    '''

    __tablename__ = 'src_pack'

    id = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    version = Column(String(200), nullable=True)

    license = Column(String(500), nullable=True)

    sourceURL = Column(String(200), nullable=True)

    downloadURL = Column(String(200), nullable=True)

    Maintaniner = Column(String(50), nullable=True)

    MaintainLevel = Column(String(20), nullable=True)


class bin_pack(DBHelper.BASE):  # pylint: disable=C0103,R0903
    '''
    functional description:Binary package data
    modify record:
    '''
    __tablename__ = 'bin_pack'

    id = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    version = Column(String(200), nullable=True)

    srcIDkey = Column(Integer, ForeignKey('src_pack.id'))

    src_pack = relationship('src_pack', backref="bin_pack")


class pack_requires(DBHelper.BASE):  # pylint: disable=C0103,R0903
    '''
    functional description:
    modify record:
    '''

    __tablename__ = 'pack_requires'

    id = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    # depProIDkey = Column(Integer, ForeignKey(
    #     'pack_provides.id'), nullable=True)

    depProIDkey = Column(Integer)
    srcIDkey = Column(Integer, ForeignKey('src_pack.id'), nullable=True)

    binIDkey = Column(Integer, ForeignKey('bin_pack.id'), nullable=True)


class pack_provides(DBHelper.BASE):  # pylint: disable=C0103,R0903
    '''
    functional description:
    modify record:
    '''
    __tablename__ = 'pack_provides'

    id = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    binIDkey = Column(Integer, ForeignKey('bin_pack.id'))


class maintenance_info(DBHelper.BASE):  # pylint: disable=C0103,R0903
    '''
        Maintain data related to person information
    '''
    __tablename__ = 'maintenance_info'

    id = Column(Integer, primary_key=True)

    name = Column(String(500), nullable=True)

    version = Column(String(500), nullable=True)

    maintaniner = Column(String(100), nullable=True)

    maintainlevel = Column(String(100), nullable=True)
