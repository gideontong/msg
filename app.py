from collections import Counter
from datetime import timedelta
from humanize import naturaldelta
from json import load
from sys import argv
from os import listdir


NAME = argv[1]
folders = [
    'archived_threads',
    'filtered_threads',
    'inbox'
]

files = list()
for folder in folders:
    for conversation in listdir(folder):
        for file in listdir(f'{folder}/{conversation}'):
            if '.json' in file:
                files.append(f'{folder}/{conversation}/{file}')

message_types = list()
senders = list()
to_process = list()
for file in files:
    with open(file) as fp:
        dumped = load(fp)
        participants = [participant['name'] for participant in dumped['participants']]
        if len(participants) != 2 or NAME not in participants:
            continue

        for message in dumped['messages']:
            message_types.append(message['type'])
            senders.append(message['sender_name'])

message_types = Counter(message_types)
senders = Counter(senders)

print(message_types)
top_senders = [group[0] for group in senders.most_common(50)][1:]

messages = dict()
for file in files:
    with open(file) as fp:
        dumped = load(fp)
        participants = [participant['name'] for participant in dumped['participants']]
        if len(participants) != 2 or NAME not in participants:
            continue
        
        for sender in top_senders:
            if sender in participants:
                messages[sender] = dumped['messages']

allowed_types = [
    'Generic',
    'Share'
]

# limit = 2 days
limit = 2 * 24 * 60 * 60 * 1000
stats = dict()
for person in messages:
    interactions = [i for i in messages[person] if i['type'] in allowed_types][::-1]
    last_ms = 0
    last_person = None
    started_by_me = 0
    started_by_you = 0
    reply_times = list()
    their_reply_times = list()
    my_reply_times = list()
    for interaction in interactions:
        ts = interaction['timestamp_ms']
        sender = interaction['sender_name']

        # New conversation
        if ts - last_ms > limit:
            if sender == person:
                started_by_you += 1
            else:
                started_by_me += 1
        
        # Reply
        elif sender != last_person:
            td = ts - last_ms
            reply_times.append(td)

            if sender == person:
                their_reply_times.append(td)
            else:
                my_reply_times.append(td)

        last_ms = ts
        last_person = sender
    
    stats[person] = {
        'count': len(interactions),
        'first': interactions[0]['sender_name'],
        'started': {
            'me': started_by_me,
            'you': started_by_you
        },
        'times': {
            'total': reply_times,
            'me': my_reply_times,
            'you': their_reply_times
        }
    }

print(stats.keys())

person = input('Pick a person> ')

data = stats[person]
print(f'Now showing stats for you and: {person}')

print(f'Exchanged messages: {data["count"]}')

if person == data['first']:
    print(f'{person} slid into your DMs. I guess you are cool?')
else:
    print(f'You slid into their DMs. As usual.')

if data['started']['me'] > data['started']['you']:
    print('You start most of the conversations. Of course you do.')
elif data['started']['you'] > data['started']['me']:
    print(f'{person} starts more conversations with you. Keep replying I guess?')

times = data['times']['total']
avg_time = naturaldelta(timedelta(milliseconds=sum(times) / len(times)), minimum_unit="microseconds")
print(f'On average, it takes {avg_time} for anyone to get a reply here.')

times = data['times']['me']
min_time = naturaldelta(timedelta(milliseconds=min(times)), minimum_unit="microseconds")
max_time = naturaldelta(timedelta(milliseconds=max(times)), minimum_unit="microseconds")
avg_time = naturaldelta(timedelta(milliseconds=sum(times) / len(times)), minimum_unit="microseconds")
print(f'My fastest reply to {person} was {min_time}')
print(f'My slowest reply to them was {max_time}')
print(f'On average, it takes me {avg_time} to reply to them')

times = data['times']['you']
min_time = naturaldelta(timedelta(milliseconds=min(times)), minimum_unit="microseconds")
max_time = naturaldelta(timedelta(milliseconds=max(times)), minimum_unit="microseconds")
avg_time = naturaldelta(timedelta(milliseconds=sum(times) / len(times)), minimum_unit="microseconds")
print(f'{person}\'s fastest reply to me only took {min_time}')
print(f'However, one time they took {max_time} to reply to me')
print(f'Yet on average, it takes them {avg_time} to reply\n')
