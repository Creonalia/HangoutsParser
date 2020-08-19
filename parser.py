import json
from datetime import datetime
from pytz import timezone
from collections import defaultdict

output_file_name = "Hangouts.txt"

def format_datetime(datetime_):
    return datetime_.astimezone(timezone("US/Pacific")).strftime('%b %d, %Y %H:%M')


def get_text(event):
    sender = participants[event["sender_id"]["gaia_id"]]
    # hangouts timestamp is in microseconds
    timestamp = format_datetime(datetime.fromtimestamp(int(event["timestamp"])//1000000))

    # messages
    if event["event_type"] == "REGULAR_CHAT_MESSAGE":
        message = ""
        for content_type, content in event["chat_message"]["message_content"].items():
            if content_type == "segment":
                for segment in content:
                    if segment["type"] == "TEXT":
                        message += segment["text"]
                    elif segment["type"] == "LINE_BREAK":
                        message += segment.get("text", "\n")
                    elif segment["type"] == "LINK":
                        message += segment["text"]
                    else:
                        print(f"unrecognized segment type {i['type']}")
            elif content_type == "attachment":
                for i in content:
                    embed_item = i["embed_item"]
                    if embed_item["type"] == ["PLUS_PHOTO",]:
                        message += embed_item["plus_photo"]["url"]

        return f"{timestamp} {sender}: {message}"

    elif event["event_type"] == "RENAME_CONVERSATION":
        return f"{timestamp} {sender} renamed {event['conversation_rename']['old_name']} to {event['conversation_rename']['new_name']}"

    # calls
    elif event["event_type"] == "HANGOUT_EVENT":
        if event["hangout_event"]["event_type"] == "START_HANGOUT":
            return f"{timestamp} {sender} started a call"

        elif event["hangout_event"]["event_type"] == "END_HANGOUT":
            hangout_participants = [
                participants[participant["gaia_id"]]
                for participant in event["hangout_event"]["participant_id"]
            ]
            return f"{timestamp} {event['hangout_event']['hangout_duration_secs']} second call with {', '.join(hangout_participants)} ended"

    # people joining/leaving
    elif event["event_type"] in ("REMOVE_USER", "ADD_USER"):
        event_participants = [
            participants[participant["gaia_id"]]
            for participant in event["membership_change"]["participant_id"]
        ]
        return f"{timestamp} {', '.join(event_participants)} {'left' if event['event_type'] == 'REMOVE_USER' else 'joined'}"


if __name__ == "__main__":
    with open("Hangouts.json", "r") as hangouts_json:
        hangouts_data = json.load(hangouts_json)

    with open(output_file_name, "w") as output_file:
        output_file.write("")

    for conv in hangouts_data["conversations"]:
        participants = defaultdict(lambda: "Unknown", **{
            participant["id"]["gaia_id"]: participant.get("fallback_name", "Unknown")
            for participant in conv["conversation"]["conversation"]["participant_data"]
        })
        conv_name = conv["conversation"]["conversation"].get("name", ", ".join(participants.values()))

        messages = [get_text(event) for event in conv["events"]]
        with open(output_file_name, "a") as output_file:
            output_file.write(f"{conv_name}\n" + "\n".join(messages) + "\n\n")
