from sqlalchemy import create_engine, ForeignKey, Column, BigInteger, String, Sequence, Boolean, ARRAY, Enum, DateTime, JSON, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy_utils import StringEncryptedType
from discord import Locale
from cryptography.fernet import Fernet
import os
import secrets
import logging
import datetime
import enum
import base64
import exceptions

class Base(DeclarativeBase):
    pass

class Y2dlKeyHandler:
    def get_key():
        key = os.environ.get('Y2DL_TK_KEY')
        if not key:
            key = Fernet.generate_key()
            os.environ['Y2DL_TK_KEY'] = key.decode()
            return key
        else:
            return key.encode()

class NotifType(enum.Enum):
    YOUTUBE = 'youtube'
    TWITCH = 'twitch'
    MASTODON = 'mastodon'
    FEEDS = 'feeds'

class FeatureType(enum.Enum):
    DYNAMIC_INFO_TEXT = 'dynamic_info_text'
    DYNAMIC_INFO_VOICE = 'dynamic_info_voice'
    RELEASE_NOTIF = 'release_notifications'

class GuildConfig(Base):
    __tablename__ = 'guild_cfg'
    id = Column(BigInteger, primary_key=True)
    manager_roles = Column(ARRAY(BigInteger))
    last_modified = Column(DateTime)
    notifications = relationship('NotificationConfig', backref='guild', cascade="all, delete-orphan")

class NotificationConfig(Base):
    __tablename__ = 'notif_cfg'
    id = Column(Integer, autoincrement=True, primary_key=True)
    type = Column(Enum(FeatureType))
    source_type = Column(Enum(NotifType))
    guild_id = Column(BigInteger, ForeignKey('guild_cfg.id'))
    source_id = Column(String)
    channel_id = Column(BigInteger)
    ping_roles = Column(ARRAY(BigInteger), nullable=True)
    notif_content = Column(String, nullable=True)
    notif_embed = Column(JSON(True), nullable=True)

    __table_args__ = (
        UniqueConstraint('source_id', 'channel_id', 'guild_id', name='uq_all_columns'),
    )
    def __eq__(self, other):
        if isinstance(other, MyClass):
            return (
                self.guild_id == other.guild_id and
                self.source_id == other.source_id and
                self.channel_id == other.channel_id
            )
        return False
    def __hash__(self):
        return hash((self.guild_id, self.source_id, self.channel_id))

class UserConfig(Base):
    __tablename__ = 'user_cfg'
    id = Column(BigInteger, primary_key=True) # discord user id
    language = Column(Enum(Locale))
    ephemeral = Column(Boolean, default=False)
    
class DashAuthentication(Base):
    __tablename__ = 'dash_auth'
    id = Column(BigInteger, ForeignKey('user_cfg.id'), primary_key=True)
    refresh_token = Column(StringEncryptedType(key=Y2dlKeyHandler.get_key), unique=True)
    access_token = Column(StringEncryptedType(key=Y2dlKeyHandler.get_key), unique=True)
    backup_key = Column(StringEncryptedType(key=Y2dlKeyHandler.get_key), unique=True)

    def __init__(self, id, refresh, access):
        cipher_suite = Fernet(Y2dlKeyHandler.get_key())
        self.id = id
        self.refresh_token = cipher_suite.encrypt(bytes(refresh, 'utf8'))
        self.access_token = cipher_suite.encrypt(bytes(access, 'utf8'))
        self.backup_key = cipher_suite.encrypt(Fernet.generate_key())

    def get_data(self):
        cipher_suite = Fernet(Y2dlKeyHandler.get_key())
        refresh_token = cipher_suite.decrypt(self.refresh_token).decode('utf-8')
        access_token = cipher_suite.decrypt(self.access_token).decode('utf-8')
        backup_key = cipher_suite.decrypt(self.backup_key)
        return {
            'id': self.id,
            'refresh_token': refresh_token,
            'access_token': access_token,
            'backup_key': backup_key
        }
    
class Y2dlDatabase:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def init_guild_cfg(self, guild_id):
        gcfg = GuildConfig(
            id=guild_id,
            manager_roles=[],
            last_modified=datetime.datetime.now(datetime.timezone.utc)
        )
        self.session.add(gcfg)
        self.session.commit()

    def modify_guild_cfg(self, guild_id, *, manager_roles = None):
        gcfg = self.session.query(GuildConfig).filter_by(id=guild_id).first()
        if gcfg is None:
            raise exceptions.InvalidGuildException(f"Invalid guild: {guild_id}")
        if manager_roles is not None:
            gcfg.manager_roles = manager_roles
        self.session.commit()

    def delete_guild_cfg(self, guild_id):
        gcfg = self.session.query(GuildConfig).filter_by(id=guild_id).first()
        if gcfg is None:
            raise exceptions.InvalidGuildException(f"Invalid guild: {guild_id}")
        self.session.delete(gcfg)
        self.session.commit()

    def add_notif(self, guild_id, notif: NotificationConfig):
        gcfg = self.session.query(GuildConfig).filter_by(id=guild_id).first()
        if gcfg is None:
            raise exceptions.InvalidGuildException(f"Invalid guild: {guild_id}")
        gcfg.notifications.append(notif)
        self.session.commit()

    def modify_notif(self, guild_id, channel_id, dsource_id, *, source_id = None, ping_roles = None, notif_content = None, notif_embed = None):
        gcfg = self.session.query(GuildConfig).filter_by(id=guild_id).first()
        if gcfg is None:
            raise exceptions.InvalidGuildException(f"Invalid guild: {guild_id}")
        ncfg = gcfg.notifications.filter_by(channel_id=channel_id, source_id=dsource_id)
        if ncfg is None:
            raise exceptions.InvalidNotifException(f"Invalid notification config: {ch_id}, {so_id}")
        if bso_id is not None:
            ncfg.source_id = bso_id
        if ping_roles is not None:
            ncfg.ping_roles = ping_roles
        if notif_content is not None:
            ncfg.notif_content = notif_content
        if notif_embed is not None:
            ncfg.notif_embed = notif_embed
        self.session.commit()

    def del_notif(self, guild_id, channel_id, source_id):
        gcfg = self.session.query(GuildConfig).filter_by(id==guild_id).first()
        if gcfg is None:
            raise exceptions.InvalidGuildException(f"Invalid guild: {guild_id}")
        ncfg = gcfg.notifications.filter_by(channel_id=channel_id, source_id=source_id)
        if ncfg is None:
            raise exceptions.InvalidNotifException(f"Invalid notification config: {ch_id}, {so_id}")
        ncfg.delete()
        self.session.commit()

    def get_all_notifs(self, type: NotifType):
        ncfgs = self.session.query(NotificationConfig).filter_by(type=type)
        return ncfgs.all()