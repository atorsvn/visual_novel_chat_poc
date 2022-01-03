
import discord
from discord.ui import Button, View
from discord.ext import commands
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import textwrap 
import os
import json
import requests
import re
import nltk


nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

import text2emotions as emo

f = open('waifu_config.json')
WAIFU_CONFIG = json.load(f)
f.close()

CONST_POSITION = {
    "left" : (-115,0),
    "center" : (108, 0),
    "right" : (300, 0)
}

def waifu_ai_query(query, user_id, user_name):
    global WAIFU_CONFIG
    url = "https://waifu.p.rapidapi.com/path"

    querystring = {"user_id":user_id,"message":query,"from_name": user_name, "to_name" : WAIFU_CONFIG['BOT-NAME'],"situation": WAIFU_CONFIG['SITUATION'],"translate_from":"auto","translate_to":"auto"}
    my_obj = {
        "key1": "value",
        "key2": "value"
    }
    
    payload = json.dumps(my_obj)

    headers = {
    'content-type': "application/json",
    'x-rapidapi-host': "waifu.p.rapidapi.com",
    'x-rapidapi-key': WAIFU_CONFIG['RAPID-API-KEY']
    }
    
    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    
    reply = response.text

    if reply == """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>500 Internal Server Error</title>
<h1>Internal Server Error</h1>
<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>
    """:
        reply = "There was some sort of error."

    return reply

def waifu_text_wrap(text_string):
    wrapper = textwrap.TextWrapper(width=30) 
    word_list = wrapper.wrap(text=text_string) 
    text_new = ''
    for ii in word_list[:-1]:
        text_new = text_new + ii + '\n'
    text_new += word_list[-1]

    return text_new

def get_text_dimensions(text_string, font):
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return (text_width, text_height)

async def vn_render_menu(interaction):
    VN_CONFIG['last-interaction'] = interaction
    W, H = (720,540)
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['current-location']], (0,0), VN_CONFIG['images'][VN_CONFIG['current-location']])    
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['waifu-mood']], VN_CONFIG['waifu-position'], VN_CONFIG['images'][VN_CONFIG['waifu-mood']]) 
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images']['menu'], (0,0), VN_CONFIG['images']['menu'])

    draw = ImageDraw.Draw(VN_CONFIG['images']['empty'])
    font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
    w, h = get_text_dimensions(VN_CONFIG["waifu-stats"], font)
    draw.text((0.5*(W-w),18),VN_CONFIG["waifu-stats"],(255,255,255),font=font)
    draw.text((27,91),VN_CONFIG["menu"][VN_CONFIG['menu-position']],(255,255,255),font=font)

    rgb_im = VN_CONFIG['images']['empty'].convert('RGB')
    rgb_im.save('output/screen.jpg')

    await interaction.message.delete()
    await interaction.message.channel.send(file=discord.File(r'output/screen.jpg'), view=VN_CONFIG['view'][VN_CONFIG['state']])
 
async def vn_render_chat(interaction):
    global current_interaction
    current_interaction = interaction
    VN_CONFIG['last-interaction'] = interaction
    W, H = (720,540)
    tb_center = 416
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['current-location']], (0,0), VN_CONFIG['images'][VN_CONFIG['current-location']])
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['waifu-mood']], VN_CONFIG['waifu-position'], VN_CONFIG['images'][VN_CONFIG['waifu-mood']]) 
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images']['chat'], (0,0), VN_CONFIG['images']['chat'])

    draw = ImageDraw.Draw(VN_CONFIG['images']['empty'])
    font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
    w, h = get_text_dimensions(VN_CONFIG["waifu-stats"], font)
    draw.text((0.5*(W-w),18),VN_CONFIG["waifu-stats"],(255,255,255),font=font)
    w, h = draw.textsize(VN_CONFIG["waifu-chat"], font)
    draw.text((0.5*(W-w),tb_center-(h/2)),VN_CONFIG["waifu-chat"],(255,255,255),font=font)

    rgb_im = VN_CONFIG['images']['empty'].convert('RGB')
    rgb_im.save('output/screen.jpg')

    await interaction.message.delete()
    await interaction.message.channel.send(file=discord.File(r'output/screen.jpg'), view=VN_CONFIG['view'][VN_CONFIG['state']])

async def vn_render_waifu_chat():
    W, H = (720,540)
    tb_center = 416
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['current-location']], (0,0), VN_CONFIG['images'][VN_CONFIG['current-location']])
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['waifu-mood']], VN_CONFIG['waifu-position'], VN_CONFIG['images'][VN_CONFIG['waifu-mood']]) 
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images']['chat'], (0,0), VN_CONFIG['images']['chat'])

    draw = ImageDraw.Draw(VN_CONFIG['images']['empty'])
    font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
    w, h = get_text_dimensions(VN_CONFIG["waifu-stats"], font)
    draw.text((0.5*(W-w),18),VN_CONFIG["waifu-stats"],(255,255,255),font=font)
    waifu_text = waifu_text_wrap(VN_CONFIG["waifu-chat"])
    w, h = draw.textsize(waifu_text, font)
    draw.text((0.5*(W-w),tb_center-(h/2)),waifu_text,(255,255,255),font=font)

    rgb_im = VN_CONFIG['images']['empty'].convert('RGB')
    rgb_im.save('output/screen.jpg')

async def vn_render_about(interaction):
    VN_CONFIG['state'] = 3
    W, H = (720,540)
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['current-location']], (0,0), VN_CONFIG['images'][VN_CONFIG['current-location']])    
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['waifu-mood']], VN_CONFIG['waifu-position'], VN_CONFIG['images'][VN_CONFIG['waifu-mood']]) 
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images']['about'], (0,0), VN_CONFIG['images']['about'])

    draw = ImageDraw.Draw(VN_CONFIG['images']['empty'])
    font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
    w, h = get_text_dimensions(VN_CONFIG["waifu-stats"], font)
    draw.text((0.5*(W-w),18),VN_CONFIG["waifu-stats"],(255,255,255),font=font)
    rgb_im = VN_CONFIG['images']['empty'].convert('RGB')
    rgb_im.save('output/screen.jpg')

    await interaction.message.delete()
    await interaction.message.channel.send(file=discord.File(r'output/screen.jpg'), view=VN_CONFIG['view'][VN_CONFIG['state']])
 

async def  vn_render_map(interaction):
    VN_CONFIG['last-interaction'] = interaction
    VN_CONFIG['state'] = 2
    W, H = (720,540)
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['current-location']], (0,0), VN_CONFIG['images'][VN_CONFIG['current-location']])    
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['waifu-mood']], VN_CONFIG['waifu-position'], VN_CONFIG['images'][VN_CONFIG['waifu-mood']]) 
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images']['map'], (0,0), VN_CONFIG['images']['map'])

    draw = ImageDraw.Draw(VN_CONFIG['images']['empty'])
    font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
    w, h = get_text_dimensions(VN_CONFIG["waifu-stats"], font)
    draw.text((0.5*(W-w),18),VN_CONFIG["waifu-stats"],(255,255,255),font=font)
    rgb_im = VN_CONFIG['images']['empty'].convert('RGB')
    rgb_im.save('output/screen.jpg')

    await interaction.message.delete()
    await interaction.message.channel.send(file=discord.File(r'output/screen.jpg'), view=VN_CONFIG['view'][VN_CONFIG['state']])
 

async def vn_render_quit(interaction):
    await interaction.message.delete()
    await interaction.message.channel.send("Thanks for trying out the demo!")
 

async def vn_start():
    W, H = (720,540)
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['current-location']], (0,0), VN_CONFIG['images'][VN_CONFIG['current-location']])
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images'][VN_CONFIG['waifu-mood']], VN_CONFIG['waifu-position'], VN_CONFIG['images'][VN_CONFIG['waifu-mood']])   
    VN_CONFIG['images']['empty'].paste(VN_CONFIG['images']['chat'], (0,0), VN_CONFIG['images']['chat'])

    draw = ImageDraw.Draw(VN_CONFIG['images']['empty'])
    font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
    w, h = get_text_dimensions(VN_CONFIG["waifu-stats"], font)
    draw.text((0.5*(W-w),18),VN_CONFIG["waifu-stats"],(255,255,255),font=font)

    rgb_im = VN_CONFIG['images']['empty'].convert('RGB')
    rgb_im.save('output/screen.jpg')


async def vn_button_menu_callback(interaction): 
    VN_CONFIG['state'] = 1
    VN_CONFIG['menu-position'] = 0

    await vn_render_menu(interaction)

async def vn_button_up_callback(interaction):
    if VN_CONFIG['menu-position'] > 0:
        VN_CONFIG['menu-position'] = VN_CONFIG['menu-position'] - 1
    
    await vn_render_menu(interaction)

async def vn_button_down_callback(interaction):
    if VN_CONFIG['menu-position'] < 3:
        VN_CONFIG['menu-position'] = VN_CONFIG['menu-position'] + 1

    await vn_render_menu(interaction)

async def vn_button_menu_ok_callback(interaction):
    VN_CONFIG['state'] = VN_CONFIG['menu-position']

    await VN_CONFIG['render'][VN_CONFIG['state']](interaction)

async def vn_button_map_1_callback(interaction):
    VN_CONFIG['state'] = 0
    VN_CONFIG['current-location'] = 'bridge'
    WAIFU_CONFIG['situation'] = "Waifu loves her Senpai. They are having a conversation in a park at the bridge",

    await VN_CONFIG['render'][VN_CONFIG['state']](interaction)


async def vn_button_map_2_callback(interaction):
    VN_CONFIG['state'] = 0
    VN_CONFIG['current-location'] = 'swing'
    WAIFU_CONFIG['situation'] = "Waifu loves her Senpai. They are having a conversation in a park at the swing",

    await VN_CONFIG['render'][VN_CONFIG['state']](interaction)


async def vn_button_map_3_callback(interaction):
    VN_CONFIG['state'] = 0
    VN_CONFIG['current-location'] = 'grove'
    WAIFU_CONFIG['situation'] = "Waifu loves her Senpai. They are having a conversation in a park at the grove",

    await VN_CONFIG['render'][VN_CONFIG['state']](interaction)


async def vn_button_map_4_callback(interaction):
    VN_CONFIG['state'] = 0
    VN_CONFIG['current-location'] = 'path'
    WAIFU_CONFIG['situation'] = "Waifu loves her Senpai. They are having a conversation in a park at a path leading to woods",

    await VN_CONFIG['render'][VN_CONFIG['state']](interaction)

async def vn_about_ok_callback(interaction):
    VN_CONFIG['state'] = 0

    await VN_CONFIG['render'][VN_CONFIG['state']](interaction)

VN_CONFIG = {
    "prefix" : "!",
    "token" : "ODQ1NDIxMzEwNDQwMTEyMjA4.YKgt8w.yx_ZtzmWyIg9CWTuDRt991OuSHU",
    "last-interaction" : 0,
    "state" : 0,
    "menu" : [
        "👉 CHAT\n      MAP\n      ABOUT\n      QUIT",
        "      CHAT\n👉 MAP\n      ABOUT\n      QUIT",
        "      CHAT\n      MAP\n👉 ABOUT\n      QUIT",
        "      CHAT\n      MAP\n      ABOUT\n👉 QUIT"
    ],
    "menu-position" : 0,
    "images" : {
        "empty" : 0,
        "background" : 0,
        "menu" : 0
    },
    "render" : [
        vn_render_chat, 
        vn_render_map,
        vn_render_about,
        vn_render_quit,
    ],
    "waifu-mood" : "Normal",
    "waifu-chat" : "Hello!",
    "waifu-name" : "",
    "waifu-stats" : "",
    "waifu-position" : CONST_POSITION['center'],
    "current-location" : "bridge",
    "view" : 0,
    "views" : 
        [
            [
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:menu_w:925958797145554994>",
                    "callback" : vn_button_menu_callback
                }            
            ],
            [
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:menu_w:925958797145554994>",
                    "callback" : vn_button_menu_callback
                },
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:up_w:925955838424809552>",
                    "callback" : vn_button_up_callback
                },
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:down_w:925955926878466099>",
                    "callback" : vn_button_down_callback
                },
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:ok_w:925959646114631711>", 
                    "callback" : vn_button_menu_ok_callback
                }                
            ],
            [
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:menu_w:925958797145554994>",
                    "callback" : vn_button_menu_callback
                },
                {
                    "label" : "1",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "",
                    "callback" : vn_button_map_1_callback
                },
                {
                    "label" : "2",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "",
                    "callback" : vn_button_map_2_callback
                },
                {
                    "label" : "3",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "",
                    "callback" : vn_button_map_3_callback
                },
                {
                    "label" : "4",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "",
                    "callback" : vn_button_map_4_callback
                }
            ],
            [
                {
                    "label" : "",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "<:menu_w:925958797145554994>",
                    "callback" : vn_button_menu_callback
                },
                {
                    "label" : "So Cool! Sonuvabitch.",
                    "style" : discord.ButtonStyle.blurple,
                    "emoji" : "",
                    "callback" : vn_button_map_1_callback
                }
       
            ]
        ]
}

async def vn_update_waifu_stats():
    VN_CONFIG['waifu-stats'] = "👰 "+ WAIFU_CONFIG['BOT-NAME'] + " ♥ " + VN_CONFIG['waifu-mood'] +  " 📍 " + VN_CONFIG['current-location']

async def vn_load_view(x):
    view = View()
    for i in range(len(VN_CONFIG['views'][x])):
        if VN_CONFIG['views'][x][i]['emoji'] == "":
            button_item = Button(label=VN_CONFIG['views'][x][i]['label'], style=VN_CONFIG['views'][x][i]['style'])
            view.add_item(button_item)
            button_item.callback = VN_CONFIG['views'][x][i]['callback']
        else:
            button_item = Button(label=VN_CONFIG['views'][x][i]['label'], style=VN_CONFIG['views'][x][i]['style'], emoji=VN_CONFIG['views'][x][i]['emoji'])
            view.add_item(button_item)
            button_item.callback = VN_CONFIG['views'][x][i]['callback']
    return view

async def vn_load_views():
    da_size = len(VN_CONFIG['views'])
    views = []

    if da_size > 1 :
        for i in range(da_size):
            views.append(await vn_load_view(i))
    else:
        views.append(await vn_load_view(0))

    return views

def load_layer_images():
    VN_CONFIG['images']['empty'] = Image.open('ui_elements/blank.png')
    VN_CONFIG['images']['Normal'] = Image.open('sprites/normal.png')
    VN_CONFIG['images']['Happy'] = Image.open('sprites/delighted.png')
    VN_CONFIG['images']['Angry'] = Image.open('sprites/angry.png')
    VN_CONFIG['images']['Surprise'] = Image.open('sprites/shocked.png')
    VN_CONFIG['images']['Sad'] = Image.open('sprites/sad.png')
    VN_CONFIG['images']['Fear'] = Image.open('sprites/shocked.png')
    VN_CONFIG['images']['menu'] = Image.open('ui_elements/overlay_menu.png')
    VN_CONFIG['images']['map'] = Image.open('ui_elements/overlay_map.png')
    VN_CONFIG['images']['about'] = Image.open('ui_elements/overlay_about.png')
    VN_CONFIG['images']['chat'] = Image.open('ui_elements/overlay_chat.png')
    VN_CONFIG['images']['bridge'] = Image.open('backgrounds/bridge.png')
    VN_CONFIG['images']['swing'] = Image.open('backgrounds/swing.png')
    VN_CONFIG['images']['grove'] = Image.open('backgrounds/grove.png')
    VN_CONFIG['images']['path'] = Image.open('backgrounds/path.png')

load_layer_images()

bot = commands.Bot(command_prefix = VN_CONFIG['prefix'])

@bot.command()
async def vnc_start(ctx):
    VN_CONFIG['view'] =await vn_load_views()
    await vn_update_waifu_stats()
    await vn_start()
    msg = await ctx.send(file=discord.File(r'video/splash.mp4'), view=VN_CONFIG['view'][VN_CONFIG['state']])

@bot.command()
async def gwen(ctx):
    VN_CONFIG['state'] = 0
    query = re.sub("!gwen" + " ", '', ctx.message.content)
    response = waifu_ai_query(query, ctx.message.author.id, ctx.message.author.name)
    emotions = emo.get_emotion(response)
    emotion = max(emotions, key=emotions.get)
    if(emotions[emotion] > 0.0):
        VN_CONFIG['waifu-mood'] = emotion
    else:
        VN_CONFIG['waifu-mood'] = "Normal"

    await vn_update_waifu_stats()
    waifu_text = waifu_text_wrap(response)
    waifu_text= "\n".join(waifu_text.splitlines()[:5])
    VN_CONFIG['waifu-chat'] = waifu_text
    await vn_render_waifu_chat()
    await ctx.send(file=discord.File(r'output/screen.jpg'), view=VN_CONFIG['view'][VN_CONFIG['state']])

bot.run(VN_CONFIG['token'])

