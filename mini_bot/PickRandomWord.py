#!/usr/bin/python3
import sys
import os
import nextcord
import asyncio
import random
import logging
import json

logging.basicConfig(level=logging.INFO)
client = nextcord.Client()
#wb = gspread.authorize("token_google").open_by_key('1v-MzfsOmmCQNwWFHl86UVrf3lIm5QPitRiJeA4ISIPw')
#wb = wb.get_worksheet(0)

global word
word = []

@client.event
async def on_ready():
    print("Connected")


@client.event
async def on_message(m):
    global word
    av = m.content.split(' ')
    if av[0] == "/add" :
        word.append(" ".join(av[1:]))
    if av[0] == "/pick" :
        mot = random.choice(word)
        word.remove(mot)
        await m.channel.send(mot)

fd = open("private/token")
client.run(json.load(fd))
fd.close()
