import csv
import json
import os
import tempfile
from datetime import datetime
from typing import List
from models import Message

async def generate_csv(messages: List[Message], chat_id: int, start: datetime, end: datetime) -> str:
    fd, path = tempfile.mkstemp(suffix='.csv', prefix=f'export_{chat_id}_')
    os.close(fd)

    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['message_id', 'date', 'user_id', 'username', 'text', 'reactions', 'media']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for msg in messages:
            reactions_str = ';'.join([f"{r.user_id}:{r.reaction}" for r in msg.reactions])
            media_str = json.dumps(msg.media, ensure_ascii=False) if msg.media else ''
            writer.writerow({
                'message_id': msg.id,
                'date': msg.date.isoformat(),
                'user_id': msg.user_id or '',
                'username': msg.user.username if msg.user else '',
                'text': msg.text or '',
                'reactions': reactions_str,
                'media': media_str
            })
    return path

async def generate_json(messages: List[Message], chat_id: int, start: datetime, end: datetime) -> str:
    data = []
    for msg in messages:
        msg_dict = {
            'id': msg.id,
            'date': msg.date.isoformat(),
            'user': {
                'id': msg.user_id,
                'username': msg.user.username if msg.user else None,
                'first_name': msg.user.first_name if msg.user else None,
                'last_name': msg.user.last_name if msg.user else None
            } if msg.user else None,
            'text': msg.text,
            'reactions': [
                {'user_id': r.user_id, 'reaction': r.reaction, 'date': r.date.isoformat()}
                for r in msg.reactions
            ],
            'media': msg.media
        }
        data.append(msg_dict)

    fd, path = tempfile.mkstemp(suffix='.json', prefix=f'export_{chat_id}_')
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path