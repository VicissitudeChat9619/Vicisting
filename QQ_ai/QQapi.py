import http.client
import json


class QQapi:
    def __init__(self, ip: str, port: int, token: str):
        self.ip = ip
        self.port = port
        self.token = token

    def send_friend_message(self, message: str, user_id: str):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps(
            {
                "user_id": user_id,
                "message": [
                    {
                        "type": "text",
                        "data": {"text": message},
                    },
                    # {
                    #     "type": "text",
                    #     "data": {"text": "知几验美经和通圆。究其又是。技才何林按。"},
                    # },
                ],
            }
        )
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/send_private_msg", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))

    def send_group_message(self, message: str, group_id: str):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps(
            {
                "group_id": group_id,
                "message": [
                    {
                        "type": "text",
                        "data": {"text": message},
                    },
                ],
            }
        )
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/send_group_msg", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))

    def get_message_detail(self, user_id: str, message_id: str):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps({"message_id": message_id})
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/get_msg", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))

    def get_friend_message(self, user_id: str):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps(
            {
                "user_id": user_id,
                "message_seq": 0,
                "count": 20,
            }
        )
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/get_friend_msg_history", payload, headers)
        res = conn.getresponse()
        data = res.read()
        r_data = json.loads(data.decode("utf-8"))
        message_list = [
            r_data["data"]["messages"][i]["message"][0]["data"]
            for i in range(len(r_data["data"]["messages"]))
        ]
        return message_list

    def send_friend_audio(self, user_id: str, audio_path: str):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps(
            {
                "user_id": user_id,
                "message": [
                    {
                        "type": "record",
                        "data": {
                            "path": audio_path,
                            "thumb": "string",
                            "name": "audio",
                            "file": audio_path,
                            "url": audio_path,
                        },
                    }
                ],
            }
        )
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/send_private_msg", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))

    def get_recent_contact(self, count: int):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps({"count": count})
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/get_recent_contact", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        rdata = json.loads(data.decode("utf-8"))
        # recent_message_list=rdata
        recent_message_list = [
            rdata["data"][i]["lastestMsg"] for i in range(len(rdata["data"]) - 1)
        ]
        return recent_message_list

    def mark_group_msg_as_read(self, group_id):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps({"group_id": group_id})
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/mark_msg_as_read", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))

    def mark_private_msg_as_read(self, user_id: str):
        ip = self.ip
        port = self.port
        token = self.token
        conn = http.client.HTTPConnection(ip, port)
        payload = json.dumps({"user_id": user_id})
        headers = {"Authorization": token, "Content-Type": "application/json"}
        conn.request("POST", "/mark_msg_as_read", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))


if __name__ == "__main__":
    user_id = "2223028651"
    group_id = "588982870"
    ip = "127.0.0.1"
    port = 3000
    token = "E75-1Udr6IgoeYWQ"
    count = 50
    audio_path = "E:\\Vicisting\\output.mp3"
    api = QQapi(ip, port, token)
    # message_list = get_friend_message(user_id, ip, port, token)   pass
    # print(recent_message_list)
    api.send_friend_audio(user_id, audio_path)
    # send_friend_message(user_id)  pass
    # send_group_message("",group_id, ip, port, token)  pass
