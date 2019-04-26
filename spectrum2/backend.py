# pylint: disable=no-member

import socket
import struct
import sys
import os
import logging
import google.protobuf
import resource

from . import protocol_pb2 as pb2


class Backend:
    """
    Creates new NetworkPlugin and connects the Spectrum2 NetworkPluginServer.
    @param loop: Event loop.
    @param host: Host where Spectrum2 NetworkPluginServer runs.
    @param port: Port.
    """

    def __init__(self):
        self._ping_received = False
        self._data = bytes()
        self._init_res = 0
        self.logger = logging.getLogger(self._class_._name_)

    def handle_message(self, user, legacy_name, msg, nickname="", xhtml="",
                       timestamp=""):
        m = pb2.ConversationMessage()
        m.userName = user
        m.buddy_name = legacy_name
        m.message = msg
        m.nickname = nickname
        m.xhtml = xhtml
        m.timestamp = str(timestamp)

        self.send_wrapped(m.SerializeToString(),
                          pb2.WrapperMessage.TYPE_CONV_MESSAGE)

    def handle_message_ack(self, user, legacy_name, id):
        m = pb2.ConversationMessage()
        m.userName = user
        m.buddyName = legacy_name
        m.message = ""
        m.id = id

        self.send_wrapped(m.SerializeToString(),
                          pb2.WrapperMessage.TYPE_CONV_MESSAGE_ACK)

    def handle_attention(self, user, buddy_name, msg):
        m = pb2.ConversationMessage()
        m.userName = user
        m.buddyName = buddy_name
        m.message = msg

        self.send_wrapped(m.SerializeToString(),
                          pb2.WrapperMessage.TYPE_ATTENTION)

    def handle_vcard(self, user, id, legacy_name, fullName, nickname, photo):
        vcard = pb2.VCard()
        vcard.userName = user
        vcard.buddyName = legacy_name
        vcard.id = id
        vcard.fullname = fullName
        vcard.nickname = nickname
        vcard.photo = bytes(photo)

        self.send_wrapped(vcard.SerializeToString(),
                          pb2.WrapperMessage.TYPE_VCARD)

    def handle_subject(self, user, legacy_name, msg, nickname=""):
        m = pb2.ConversationMessage()
        m.userName = user
        m.buddyName = legacy_name
        m.message = msg
        m.nickname = nickname

        self.send_wrapped(m.SerializeToString(),
                          pb2.WrapperMessage.TYPE_ROOM_SUBJECT_CHANGED)

    def handle_buddy_changed(self, user, buddy_name, alias, groups, status,
                             status_message="", icon_hash="", blocked=False):
        buddy = pb2.Buddy()
        buddy.userName = user
        buddy.buddyName = buddy_name
        buddy.alias = alias
        buddy.group.extend(groups)
        buddy.status = status
        buddy.statusMessage = status_message
        buddy.iconHash = icon_hash
        buddy.blocked = blocked

        self.send_wrapped(buddy.SerializeToString(),
                          pb2.WrapperMessage.TYPE_BUDDY_CHANGED)

    def handle_buddy_removed(self, user, buddy_name):
        buddy = pb2.Buddy()
        buddy.userName = user
        buddy.buddyName = buddy_name

        self.send_wrapped(buddy.SerializeToString(),
                          pb2.WrapperMessage.TYPE_BUDDY_REMOVED)

    def handle_buddy_typing(self, user, buddy_name):
        buddy = pb2.Buddy()
        buddy.userName = user
        buddy.buddyName = buddy_name

        self.send_wrapped(buddy.SerializeToString(),
                          pb2.WrapperMessage.TYPE_BUDDY_TYPING)

    def handle_buddy_typed(self, user, buddy_name):
        buddy = pb2.Buddy()
        buddy.userName = user
        buddy.buddyName = buddy_name

        self.send_wrapped(buddy.SerializeToString(),
                          pb2.WrapperMessage.TYPE_BUDDY_TYPED)

    def handle_buddy_stopped_typing(self, user, buddy_name):
        buddy = pb2.Buddy()
        buddy.userName = user
        buddy.buddyName = buddy_name

        self.send_wrapped(buddy.SerializeToString(),
                          pb2.WrapperMessage.TYPE_BUDDY_STOPPED_TYPING)

    def handle_authorization(self, user, buddy_name):
        buddy = pb2.Buddy()
        buddy.userName = user
        buddy.buddyName = buddy_name

        self.send_wrapped(buddy.SerializeToString(),
                          pb2.WrapperMessage.TYPE_AUTH_REQUEST)

    def handle_connected(self, user):
        d = pb2.Connected()
        d.user = user

        self.send_wrapped(d.SerializeToString(),
                          pb2.WrapperMessage.TYPE_CONNECTED)

    def handle_disconnected(self, user, error=0, msg=""):
        d = pb2.Disconnected()
        d.user = user
        d.error = error
        d.message = msg

        self.send_wrapped(d.SerializeToString(),
                          pb2.WrapperMessage.TYPE_DISCONNECTED)

    def handle_participant_changed(self, user, nickname, room, flags, status,
                                   status_message="", newname="",
                                   icon_hash=""):
        d = pb2.Participant()
        d.userName = user
        d.nickname = nickname
        d.room = room
        d.flag = flags
        d.newname = newname
        d.iconHash = icon_hash
        d.status = status
        d.statusMessage = status_message

        self.send_wrapped(d.SerializeToString(),
                          pb2.WrapperMessage.TYPE_PARTICIPANT_CHANGED)

    def handle_room_nickname_changed(self, user, r, nickname):
        room = pb2.Room()
        room.userName = user
        room.nickname = nickname
        room.room = r
        room.password = ""

        self.send_wrapped(room.SerializeToString(),
                          pb2.WrapperMessage.TYPE_ROOM_NICKNAME_CHANGED)

    def handle_room_list(self, rooms):
        room_list = pb2.RoomList()

        for room in rooms:
            room_list.room.append(room[0])
            room_list.name.append(room[1])

        self.send_wrapped(room_list.SerializeToString(),
                          pb2.WrapperMessage.TYPE_ROOM_LIST)

    def handle_ft_start(self, user, buddy_name, fileName, size):
        room = pb2.File()
        room.userName = user
        room.buddyName = buddy_name
        room.fileName = fileName
        room.size = size

        self.send_wrapped(room.SerializeToString(),
                          pb2.WrapperMessage.TYPE_FT_START)

    def handle_ft_finish(self, user, buddy_name, fileName, size, ftid):
        room = pb2.File()
        room.userName = user
        room.buddyName = buddy_name
        room.fileName = fileName
        room.size = size

        # Check later
        if ftid != 0:
            room.ft_id = ftid

        self.send_wrapped(room.SerializeToString(),
                          pb2.WrapperMessage.TYPE_FT_FINISH)

    def handle_ft_data(self, ft_id, data):
        d = pb2.FileTransferData()
        d.ftid = ft_id
        d.data = bytes(data)

        self.send_wrapped(d.SerializeToString(),
                          pb2.WrapperMessage.TYPE_FT_DATA)

    def handle_backend_config(self, data):
        """
        data is a dictionary, whose keys are sections and values are a list of
        tuples of configuration key and configuration value.
        """
        c = pb2.BackendConfig()
        config = []
        for section, rest in data.items():
            config.append('[%s]' % section)
            for key, value in rest:
                config.append('%s = %s' % (key, value))

        c.config = '\n'.join(config)

        self.send_wrapped(c.SerializeToString(),
                          pb2.WrapperMessage.TYPE_BACKEND_CONFIG)

    def handle_query(self, command):
        c = pb2.BackendConfig()
        c.config = command

        self.send_wrapped(c.SerializeToString(),
                          pb2.WrapperMessage.TYPE_QUERY)

    def handle_login_payload(self, data):
        payload = pb2.Login()
        payload.ParseFromString(data)

        self.handle_login_request(payload.user,
                                  payload.legacyName,
                                  payload.password,
                                  payload.extraFields)

    def handle_logout_payload(self, data):
        payload = pb2.Logout()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_logout_request(payload.user,
                                   payload.legacyName)

    def handle_status_changed_payload(self, data):
        payload = pb2.Status()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_status_change_request(payload.userName,
                                          payload.status,
                                          payload.statusMessage)

    def handle_conv_message_payload(self, data):
        payload = pb2.ConversationMessage()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_message_send_request(payload.userName,
                                         payload.buddyName,
                                         payload.message,
                                         payload.xhtml,
                                         payload.id)

    def handle_conv_message_ack_payload(self, data):
        payload = pb2.ConversationMessage()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_message_ack_request(payload.userName,
                                        payload.buddyName,
                                        payload.id)

    def handle_attention_payload(self, data):
        payload = pb2.ConversationMessage()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error
        
        self.handle_attention_request(payload.userName,
                                      payload.buddyName,
                                      payload.message)

    def handle_ft_start_payload(self, data):
        payload = pb2.File()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_ft_start_request(payload.userName,
                                     payload.buddyName,
                                     payload.fileName,
                                     payload.size,
                                     payload.ftId)

    def handle_ft_finish_payload(self, data):
        payload = pb2.File()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_ft_finish_request(payload.userName,
                                     payload.buddyName,
                                     payload.fileName,
                                     payload.size,
                                     payload.ftId)

    def handle_ft_pause_payload(self, data):
        payload = pb2.FileTransferData()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_ft_pause_request(payload.ftId)

    def handle_ft_continue_payload(self, data):
        payload = pb2.FileTransferData()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_ft_continue_request(payload.ftId)

    def handle_join_room_payload(self, data):
        payload = pb2.Room()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_join_room_request(payload.userName,
                                      payload.room,
                                      payload.nickname,
                                      payload.password)

    def handle_leave_room_payload(self, data):
        payload = pb2.Room()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_leave_room_request(payload.userName,
                                       payload.room)

    def handle_vcard_payload(self, data):
        payload = pb2.VCard()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        if payload.HasField('photo'):
            self.handle_vcard_updated_request(payload.userName,
                                              payload.photo,
                                              payload.nickname)
        elif len(payload.buddyName) > 0:
            self.handle_vcard_request(payload.userName, payload.buddyName,
                                      payload.id)

    def handle_buddy_changed_payload(self, data):
        payload = pb2.Buddy()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        if payload.HasField('blocked'):
            self.handle_buddy_block_toggled(payload.userName,
                                            payload.buddyName,
                                            payload.blocked)
        else:
            groups = [g for g in payload.group]
            self.handle_buddy_updated_request(payload.userName,
                                              payload.buddyName,
                                              payload.alias, groups)

    def handle_buddy_removed_payload(self, data):
        payload = pb2.Buddy()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        groups = [g for g in payload.group]
        self.handle_buddy_removed_request(payload.userName,
                                          payload.buddyName,
                                          groups)

    def handle_buddies_payload(self, data):
        payload = pb2.Buddies()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        self.handle_buddies(payload)

    def handle_chat_state_payload(self, data, msg_type):
        payload = pb2.Buddy()
        if payload.ParseFromString(data) is False:
            return  # TODO: Handle error

        if msg_type == pb2.WrapperMessage.TYPE_BUDDY_TYPING:
                self.handle_typing_request(payload.userName,
                                           payload.buddyName)
        elif msg_type == pb2.WrapperMessage.TYPE_BUDDY_TYPED:
                self.handle_typed_request(payload.userName,
                                          payload.buddyName)
        elif msg_type == pb2.WrapperMessage.TYPE_BUDDY_STOPPED_TYPING:
                self.handle_stopped_typing_request(payload.userName,
                                                   payload.buddyName)

    def handle_data_read(self, data):
        self._data += data
        while len(self._data) != 0:
            expected_size = 0
            if len(self._data) >= 4:
                expected_size = struct.unpack('!I', self._data[0:4])[0]
                if len(self._data) - 4 < expected_size:
                    self.logger.debug("Data packet incomplete")
                    return
            else:
                self.logger.debug("Data packet incomplete")
                return

            packet = self._data[4:4+expected_size]
            wrapper = pb2.WrapperMessage()
            try:
                parseFromString = wrapper.ParseFromString(packet)
            except:
                self._data = self._data[expected_size+4:]
                self.logger.error("Parse from String exception. Skipping packet.")
                return

            if parseFromString is False:
                self._data = self._data[expected_size+4:]
                self.logger.error("Parse from String failed. Skipping packet.")
                return

            self._data = self._data[4+expected_size:]

            if wrapper.type == pb2.WrapperMessage.TYPE_LOGIN:
                self.handle_login_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_LOGOUT:
                self.handle_logout_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_PING:
                self.send_pong()
            elif wrapper.type == pb2.WrapperMessage.TYPE_CONV_MESSAGE:
                self.handle_conv_message_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_JOIN_ROOM:
                self.handle_join_room_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_LEAVE_ROOM:
                self.handle_leave_room_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_VCARD:
                self.handle_vcard_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_BUDDY_CHANGED:
                self.handle_buddy_changed_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_BUDDY_REMOVED:
                self.handle_buddy_removed_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_STATUS_CHANGED:
                self.handle_status_changed_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_BUDDY_TYPING:
                self.handle_chat_state_ayload(wrapper.payload, pb2.WrapperMessage.TYPE_BUDDY_TYPING)
            elif wrapper.type == pb2.WrapperMessage.TYPE_BUDDY_TYPED:
                self.handle_chat_state_payload(wrapper.payload, pb2.WrapperMessage.TYPE_BUDDY_TYPED)
            elif wrapper.type == pb2.WrapperMessage.TYPE_BUDDY_STOPPED_TYPING:
                self.handle_chat_state_payload(wrapper.payload, pb2.WrapperMessage.TYPE_BUDDY_STOPPED_TYPING)
            elif wrapper.type == pb2.WrapperMessage.TYPE_ATTENTION:
                self.handle_attention_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_FT_START:
                self.handle_ft_start_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_FT_FINISH:
                self.handle_ft_finish_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_FT_PAUSE:
                self.handle_ft_pause_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_FT_CONTINUE:
                self.handle_ft_continue_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_EXIT:
                self.handle_exit_request()
            elif wrapper.type == pb2.WrapperMessage.TYPE_CONV_MESSAGE_ACK:
                self.handle_conv_message_ack_payload(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_RAW_XML:
                self.handle_raw_xml_request(wrapper.payload)
            elif wrapper.type == pb2.WrapperMessage.TYPE_BUDDIES:
                    self.handle_buddies_payload(wrapper.payload)

    def send(self, data):
        header = struct.pack('!I',len(data))
        self.send_data(header + data)

    def send_wrapped(self, msg, type):
        wrap = pb2.WrapperMessage()
        wrap.type = TYPE
        wrap.payload = bytes(MESSAGE)

        self.send(wrap.SerializeToString())

    def check_ping(self):
        if self._ping_received is False:
            self.handle_exit_request()
        self._ping_received = False

    def send_pong(self):
        self._ping_received = True
        wrap = pb2.WrapperMessage()
        wrap.type = pb2.WrapperMessage.TYPE_PONG
        message = wrap.SerializeToString()
        self.send(message)
        self.sendMemoryUsage()

    def send_memory_usage(self):
        stats = pb2.Stats()

        stats.init_res = self._init_res
        res = 0
        shared = 0

        e_res, e_shared = self.handle_memory_usage()

        stats.res = res + e_res
        stats.shared = shared + e_shared
        stats.id = str(os.getpid())

        self.send_wrapped(stats.SerializeToString(),
                          pb2.WrapperMessage.TYPE_STATS)

    def handle_login_request(self, user, legacy_name, password, extra):
        """
        Called when XMPP user wants to connect legacy network.
        You should connect him to legacy network and call handle_connected or handle_disconnected function later.
        @param user: XMPP JID of user for which this event occurs.
        @param legacy_name: Legacy network name of this user used for login.
        @param password: Legacy network password of this user.
        """

        #\msc
        #NetworkPlugin,YourNetworkPlugin,LegacyNetwork;
        #NetworkPlugin->YourNetworkPlugin [label="handle_loginRequest(...)", URL="\ref NetworkPlugin::handle_loginRequest()"];
        #YourNetworkPlugin->LegacyNetwork [label="connect the legacy network"];
        #--- [label="If password was valid and user is connected and logged in"];
        #YourNetworkPlugin<-LegacyNetwork [label="connected"];
        #YourNetworkPlugin->NetworkPlugin [label="handle_connected()", URL="\ref NetworkPlugin::handle_connected()"];
        #--- [label="else"];
        #YourNetworkPlugin<-LegacyNetwork [label="disconnected"];
        #YourNetworkPlugin->NetworkPlugin [label="handle_disconnected()", URL="\ref NetworkPlugin::handle_disconnected()"];
        #\endmsc

        raise NotImplementedError()

    def handle_buddies(self, buddies):
        pass

    def handle_logout_request(self, user, legacy_name):
        """
        Called when XMPP user wants to disconnect legacy network.
        You should disconnect him from legacy network.
        @param user: XMPP JID of user for which this event occurs.
        @param legacy_name: Legacy network name of this user used for login.
        """

        raise NotImplementedError()

    def handle_message_send_request(self, user, legacy_name, message, xhtml="", id=0):
        """
        Called when XMPP user sends message to legacy network.
        @param user: XMPP JID of user for which this event occurs.
        @param legacy_name: Legacy network name of buddy or room.
        @param message: Plain text message.
        @param xhtml: XHTML message.
        @param id: message ID
        """

        raise NotImplementedError()

    def handle_message_ack_request(self, user, legacy_name, id=0):
        """
        Called when XMPP user sends message to legacy network.
        @param user: XMPP JID of user for which this event occurs.
        @param legacy_name: Legacy network name of buddy or room.
        @param id: message ID
        """

        #raise NotImplementedError()
        pass

    def handle_vcard_request(self, user, legacy_name, id):
        """ Called when XMPP user requests VCard of buddy.
        @param user: XMPP JID of user for which this event occurs.
        @param legacy_name: Legacy network name of buddy whose VCard is requested.
        @param id: ID which is associated with this request. You have to pass it to handle_vcard function when you receive VCard."""

        #\msc
        #NetworkPlugin,YourNetworkPlugin,LegacyNetwork;
        #NetworkPlugin->YourNetworkPlugin [label="handle_vcard_request(...)", URL="\ref NetworkPlugin::handle_vcard_request()"];
        #YourNetworkPlugin->LegacyNetwork [label="start VCard fetching"];
        #YourNetworkPlugin<-LegacyNetwork [label="VCard fetched"];
        #YourNetworkPlugin->NetworkPlugin [label="handle_vcard()", URL="\ref NetworkPlugin::handle_vcard()"];
        #\endmsc

        pass

    def handle_vcard_updated_request(self, user, photo, nickname):
        """
        Called when XMPP user updates his own VCard.
        You should update the VCard in legacy network too.
        @param user: XMPP JID of user for which this event occurs.
        @param photo: Raw photo data.
        """
        pass

    def handle_join_room_request(self, user, room, nickname, pasword):
        pass

    def handle_leave_room_request(self, user, room):
        pass

    def handle_status_change_request(self, user, status, status_message):
        pass

    def handle_buddy_updated_request(self, user,  buddy_name, alias, groups):
        pass

    def handle_buddy_removed_request(self, user, buddy_name, groups):
        pass

    def handle_buddy_block_toggled(self, user, buddy_name, blocked):
        pass

    def handle_typing_request(self, user, buddy_name):
        pass

    def handle_typed_request(self, user, buddy_name):
        pass

    def handle_stopped_typing_request(self, user, buddy_name):
        pass

    def handle_attention_request(self, user, buddy_name, message):
        pass

    def handle_ft_start_request(self, user, buddy_name, fileName, size, ft_id):
        pass

    def handle_ft_finish_request(self, user, buddy_name, fileName, size, ft_id):
        pass

    def handle_ft_pause_request(self, ft_id):
        pass

    def handle_ft_continue_request(self, ft_id):
        pass

    def handle_memory_usage(self):
        return (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 0)

    def handle_exit_request(self):
        sys.exit(1)

    def handle_raw_xml_request(self, xml):
        pass

    def send_data(self, data):
        pass