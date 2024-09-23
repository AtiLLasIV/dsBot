import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle
from config import settings
from Cybernator import Paginator as pag
import json
import requests
import random
import time
import sqlite3
import pyowm
from datetime import datetime
from discord.utils import get



bot = commands.Bot(command_prefix = settings['prefix'], intents = discord.Intents.all())
bot.remove_command ('help')

connection = sqlite3.connect('SERVER_economic.db')
cursor = connection.cursor()


@bot.event
async def on_ready():
    DiscordComponents(bot)
    print ('..Внедрение на сервер бота-картошки...')
    await bot.change_presence (activity = discord.Activity (type = discord.ActivityType.watching, name = 'в пустоту, осозновая бессмысленность своего бытия...'))
     
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    name TEXT,
    id INT,
    cash BIGINT,
    rep INT,
    lvl INT,
    xp BIGINT,
    allxp BIGINT,
    server_id INT
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS shop(
    role_id INT,
    id INT,
    cost BIGINT
    )""")

    connection.commit()
    for guild in bot.guilds:
        for member in guild.members:
            if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', '{member.id}', 0, 0, 1, 0, 0, {guild.id})")
            else:
                pass
    connection.commit()

@bot.event
async def on_member_join(member):
    if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                cursor.execute(f"INSERT INTO users VALUES ('{member}', '{member.id}', 0, 0, 1, 0, 0, {member.guild.id})")
                connection.commit()
    else:
        pass

 #уровни:
@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return
        elif message.guild.id == cursor.execute("SELECT server_id FROM users WHERE id = {}".format(message.author.id)).fetchone()[0]:
            if len(message.content) > 8:
                cursor.execute("UPDATE users SET xp = xp + 25 WHERE id = {}".format(message.author.id))
                cursor.execute("UPDATE users SET allxp = allxp + 25 WHERE id = {}".format(message.author.id))
                cursor.execute("UPDATE users SET cash = cash + 5 WHERE id = {}".format(message.author.id))
                connection.commit()
                if cursor.execute("SELECT xp FROM users WHERE id = {}".format(message.author.id)).fetchone()[0] >= 500 + 150 * cursor.execute("SELECT lvl FROM users WHERE id = {}".format(message.author.id)).fetchone()[0]:
                    delta = cursor.execute("SELECT xp FROM users WHERE id = {}".format(message.author.id)).fetchone()[0] - (500 + 150 * cursor.execute("SELECT lvl FROM users WHERE id = {}".format(message.author.id)).fetchone()[0])
                    cursor.execute("UPDATE users SET lvl = lvl + 1 WHERE id = {}".format(message.author.id))
                    cursor.execute("UPDATE users SET xp = {} WHERE id = {}".format(delta, message.author.id))
                    cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(100 * cursor.execute("SELECT lvl FROM users WHERE id = {}".format(message.author.id)).fetchone()[0], message.author.id))
                    cursor.execute("UPDATE users SET xp = xp + 25 WHERE id = {}".format(message.author.id))
                    cursor.execute("UPDATE users SET allxp = allxp + 25 WHERE id = {}".format(message.author.id))
                    await message.channel.send(embed = discord.Embed(
                    description = f"""**{message.author}**, теперь ваш уровень составляет **{cursor.execute("SELECT lvl FROM users WHERE id = {}".format(message.author.id)).fetchone()[0]} :mechanical_arm: ** """
                    ))
                    connection.commit() 
    except:
        tm = datetime.now().time()
        print()
        print(tm)
        print(f"{message.author} написал боту в ЛС")
    await bot.process_commands(message)


@bot.command()
@commands.guild_only()
async def lvl(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(embed = discord.Embed(
            description = f"""У **{ctx.author}** уровень **{cursor.execute("SELECT lvl FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}** и **{cursor.execute("SELECT xp FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}** опыта"""
            ))
    else:
        await ctx.send(embed = discord.Embed(
            description = f"""У **{member}** уровень **{cursor.execute("SELECT lvl FROM users WHERE id = {}".format(member.id)).fetchone()[0]}** и **{cursor.execute("SELECT xp FROM users WHERE id = {}".format(member.id)).fetchone()[0]}** опыта"""
            ))

@bot.command(aliases = ['lb'])
@commands.guild_only()
async def leaderboard(ctx):
    embed1 = discord.Embed(color = 0x008B8B, title = 'Топ игроков по уровню')
    counter = 0
    for row in cursor.execute("SELECT name, lvl, xp, allxp FROM users WHERE server_id = {} ORDER BY allxp DESC LIMIT 5".format(ctx.guild.id)):
        counter+=1
        embed1.add_field(name = f'# {counter} | **{row[0]}**', value = f'Уровень: **{row[1]}**, Опыт: **{row[2]}**', inline = False)
    #------------------------------------------------------------------------------------------------------------------
    embed2 = discord.Embed(color = 0x52cc00, title = 'Топ игроков по богатству')
    counter = 0
    for row in cursor.execute("SELECT name, cash FROM users WHERE server_id = {} ORDER BY cash DESC LIMIT 5".format(ctx.guild.id)):
        counter+=1
        embed2.add_field(name = f'# {counter} | **{row[0]}**', value = f'Количество денег: **{row[1]}**', inline = False)     

    embeds = [embed1, embed2]
    message = await ctx.send(embed = embed1)
    page = pag(bot, message, use_more=False, embeds=embeds)  
    
    try:
        await page.start()
    except:
        print()
        print('Ошибка (leaderboard)')
        pass

 #экономика, команды:

@bot.command(aliases = ['cash'])
@commands.guild_only()
async def balance(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send(embed = discord.Embed(
            description = f"""Баланс игрока **{ctx.author.mention}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :dollar:** """
            ))
    else:
        await ctx.send(embed = discord.Embed(
            description = f"""Баланс игрока **{member.mention}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]}:dollar:**  """
            ))
 
@bot.command()
@commands.guild_only()
#@commands.has_role(781116154219200533)
@commands.has_permissions (administrator = True)
async def award(ctx, member: discord.Member = None, amount: int = None):
    if member is None:
        await ctx.send(f"**{ctx.author.mention}**, укажите игрока, которого хотите одарить деньгами")
    else:
        if amount is None:
            await ctx.send(f"**{ctx.author.mention}**, укажите сумму денег, которой хочешь одарить игрока")
        elif amount < 1:
            await ctx.send(f"**{ctx.author.mention}**, укажите корректную сумму денег")
        else:

            tm = datetime.now().time()
            print()
            print(tm)
            print(f'{ctx.author} выдал {member} ' + str(amount) + ' денег')
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
            connection.commit()
            await ctx.message.add_reaction('👌')
            
            

@bot.command()
@commands.guild_only()
#@commands.has_role(781116154219200533)
@commands.has_permissions (administrator = True)
async def take(ctx, member: discord.Member = None, amount = None):
    cash = cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0]
    #print(cash) 
    if member is None:
        await ctx.send(f"**{ctx.author.mention}**, укажите игрока, у которого хотешь забрать деньги")
    else:
        if amount is None:
            await ctx.send(f"**{ctx.author.mention}**, укажите сумму денег, которую хотешь забрать")
        elif amount == 'all':
            cursor.execute("UPDATE users SET cash = {} WHERE id = {}".format(0, member.id))
            connection.commit()
        elif int(amount) < 1:
            await ctx.send(f"**{ctx.author.mention}**, укажите корректную сумму денег")
        elif int(amount) > cash:
            await ctx.send(f"**{ctx.author.mention}**, у пользователя нет столько денег")
        else:
            tm = datetime.now().time()
            print()
            print(tm)
            print(f'{ctx.author} забрал у {member} ' + str(amount) + ' денег')

            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(amount), member.id))
            connection.commit()
            await ctx.message.add_reaction('👌')
            


@bot.command()
@commands.guild_only()
async def pay(ctx, member: discord.Member = None, amount: int = None):
    for a in cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)):
        cash = a[0]
    print ('Кол-во денег: ')
    print (cash)
    if member is None:
        await ctx.send(f"**{ctx.author}**, укажи человека, которому хотешь заплатить")
    else:
        if amount is None:
            await ctx.send(f"**{ctx.author}**, укажи сумму денег, которую хотите заплатить")
        elif amount < 1:
            await ctx.send(f"**{ctx.author}**, укажи корректную сумму денег")
        elif amount > cash:
            await ctx.send(f"**{ctx.author}**, у Вас нет столько денег")
        else:
            cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, ctx.author.id))
            connection.commit()

            await ctx.message.add_reaction('👌')
 
@bot.command(aliases = ['add'])
@commands.has_permissions (administrator = True)
@commands.guild_only()
async def add_shop(ctx, role: discord.Role = None, cost: int = None):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую Вы хотите добавить в магазин")
    elif role in ctx.author.roles:
        await ctx.send(f"**{ctx.author}**, такая роль уже есть в магазине")
    elif cost is None:
        await ctx.send(f"**{ctx.author}**, укажите стоимость роли, которую Вы хотите добавить в магазин")
    elif cost < 1:
        await ctx.send(f"**{ctx.author}**, укажите корректную стоимость роли")
    else:
        flag = 0
        for row in cursor.execute("SELECT role_id FROM shop WHERE id = {}".format(ctx.guild.id)):
            if ctx.guild.get_role(row[0]) != None:
                if role == ctx.guild.get_role(row[0]):
                    flag = 1
        if flag == 0:
            cursor.execute("INSERT INTO shop VALUES({}, {}, {})".format(role.id, ctx.guild.id, cost))
            connection.commit()
            await ctx.message.add_reaction('👌')
        else:
            await ctx.send(f"**{ctx.author}**, такая роль уже есть в магазине")


@bot.command(aliases = ['remove'])
@commands.has_permissions (administrator = True)
async def remove_shop(ctx, role: discord.Role = None):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую Вы хотите убрать из магазина")
    else:
        cursor.execute("DELETE FROM shop WHERE role_id = {}".format(role.id))
        connection.commit()
        await ctx.message.add_reaction('👌')

@bot.command()
@commands.guild_only()
async def shop(ctx):
    embed = discord.Embed(title = 'Магазин ролей')

    for row in cursor.execute("SELECT role_id, cost FROM shop WHERE id = {} ORDER BY cost DESC".format(ctx.guild.id)):
        if ctx.guild.get_role(row[0]) != None:
            embed.add_field(
                name = f"Стоимость {row[1]} :dollar:",
                value = f"Роль {ctx.guild.get_role(row[0]).mention}",
                inline = False
                )
        else: 
            pass
    await ctx.send(embed = embed) 

@bot.command(aliases = ['buy'])
@commands.guild_only()
async def buy_role(ctx, role: discord.Role = None):
    if role is None:
        await ctx.send(f"**{ctx.author}**, укажите роль, которую Вы хотите купить в магазине")
    elif role in ctx.author.roles:
        await ctx.send(f"**{ctx.author}**, зачем Вам 2 одинаковые роли? Одумайтесь")
    elif cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0] > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
        await ctx.send(f"**{ctx.author}**, у Вас недостаточно денег")
    else:
        await ctx.author.add_roles(role)
        cursor.execute("UPDATE users SET cash = cash - {0} WHERE id = {1}".format(cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0], ctx.author.id))
        connection.commit()
        await ctx.message.add_reaction('👌')


#обычные команды для бота:

@bot.command()
@commands.guild_only()
async def help(ctx):
    embed1 = discord.Embed(color = 0x008B8B, title = 'Обычные команды')
    embed1.set_author(name = bot.user.name, icon_url = bot.user.avatar_url)
    embed1.set_thumbnail(url = 'http://s1.iconbird.com/ico/1012/SimplifiedApp/w513h5131350915237appicnsTerminal.png')
    embed1.add_field (name = '`&hi`', value = 'Приветствие', inline = False)
    embed1.add_field (name = '`&b`', value = 'Бадум-тсс', inline = False)
    embed1.add_field (name = '`&fox`', value = 'Картинка лисы', inline = False)
    embed1.add_field (name = '`&leaderboard`', value = 'Таблица лидеров', inline = False)
    embed1.add_field (name = '`&clear (кол-во)`', value = 'Очистка чата', inline = False)
    embed1.set_footer(text = 'Список команд будет пополняться')
    #------------------------------------------------------------------
    embed2 = discord.Embed(color = 0x52cc00, title = '"Денежные" команды')
    embed2.set_author(name = bot.user.name, icon_url = bot.user.avatar_url)
    embed2.set_thumbnail(url = 'https://mql.su/wp-content/uploads/2019/07/123-55-750x410.png')
    embed2.add_field (name = '`&balance`', value = 'Баланс', inline = False)
    embed2.add_field (name = '`&pay`', value = 'Заплатить', inline = False)
    embed2.add_field (name = '`&shop`', value = 'Магазин ролей', inline = False)
    embed2.add_field (name = '`&buy (роль)`', value = 'Купить роль', inline = False)
    embed2.set_footer(text = 'Список команд будет пополняться')
    #------------------------------------------------------------------
    embed3 = discord.Embed(color = 0xFFD700, title = 'Админские команды')
    embed3.set_author(name = bot.user.name, icon_url = bot.user.avatar_url)
    embed3.add_field (name = '`&award`', value = 'Одарить', inline = False)
    embed3.add_field (name = '`&take`', value = 'Штраф', inline = False)
    embed3.add_field (name = '`&add (роль)`', value = 'Добавить роль в магазин', inline = False)
    embed3.add_field (name = '`&remove (роль)`', value = 'Убрать роль из магазина', inline = False)

    embeds = [embed1, embed2, embed3]
    message = await ctx.send(embed = embed1)
    page = pag(bot, message, use_more=False, embeds=embeds)
    
    try:
        await page.start()
    except:
        print()
        print('Ошибка (help)')
        pass
    
@bot.command()
async def hi(ctx):
    author = ctx.message.author
    n = random.randint(1, 3)
    if n == 1:
        await ctx.send(f'Привет, {author.mention}!') 
    if n == 2:
        await ctx.send(f'Добрый день, {author.mention}!')
    if n == 3:
        await ctx.send(f'Доброго времени суток, {author.mention}!') 

@bot.command() 
async def b(ctx):
    n = random.randint(1, 7) 
    if n == 1:
        await ctx.send(f'https://tenor.com/view/ba-dum-tsss-drum-band-gif-7320811') 
    if n == 2:
        await ctx.send(f'https://tenor.com/view/brian-baumgartner-badumtss-the-office-kevin-joke-gif-15818642') 
    if n == 3:
        await ctx.send(f'https://tenor.com/view/punchline-badumtss-the-pirates-bandof-misfits-gif-5556409') 
    if n == 4:
        await ctx.send(f'https://tenor.com/view/badumtss-badjoke-gif-5348673')
    if n == 5:
        await ctx.send(f'https://tenor.com/view/sigrid-ba-dum-tss-joke-gif-15138926')
    if n == 6:
        await ctx.send(f'https://tenor.com/view/badumtss-baxmusic-bax-shop-bax-it-gif-14812059')
    if n == 7:
        await ctx.send(f'https://tenor.com/view/drums-troll-badumtss-badaboom-snare-gif-7191319')

@bot.command() 
async def upd(ctx):
    embed = discord.Embed(color = 0x008B8B, title = 'Что Артём прикрутил ко мне из новых функций за последнее время: ')
    embed.add_field (name = '1)', value = 'Он на меня забил 😢', inline = False)
    await ctx.send(embed = embed)


@bot.command()
#@commands.has_permissions (administrator = True)
async def sogl(ctx):
    author = ctx.message.author
    await ctx.channel.purge (limit = 1)
    await ctx.send(f'{author.mention} Согласен') 
    

@bot.command() 
@commands.has_permissions (administrator = True)
async def ai(ctx, member: discord.Member = None): 
    await ctx.channel.purge (limit = 1)
    await ctx.send(f'Ай-ай-ай, как так можно, {member.mention}') 


@bot.command()
#@commands.has_permissions (administrator = True)
#@commands.has_role(781116154219200533)
#@commands.has_role()
@commands.guild_only()
async def clear(ctx, amount: int):
    await ctx.channel.purge (limit = 1)
    deleted = await ctx.channel.purge(limit = amount)
    await ctx.channel.send(':detective: Удалено {} сообщения'.format(len(deleted)))
    time.sleep(3)
    await ctx.channel.purge (limit = 1)
    tm = datetime.now().time()
    print()
    print(tm)
    print(f'{ctx.author} удалил ' + str(amount) + ' сообщения с помощью бота')

@bot.command()
@commands.has_permissions (administrator = True)
async def ping(ctx, member: discord.Member = None, amount: int = None):
    i = 0
    while i < amount: 
        await ctx.channel.send(f'{member.mention}')
        time.sleep(0.1)
        await ctx.channel.purge (limit = 1)
        time.sleep(0.1)
        i = i + 1
    print()
    print(f'{ctx.author} пинганул {member}')

@bot.command()
async def jpg(ctx, text):
    response = requests.get('https://some-random-api.ml/img/' + text)
    try: 
        json_data = json.loads(response.text)
        embed = discord.Embed(color = 0xff9900, title = text)
        embed.set_image(url = json_data['link'])
        await ctx.send(embed = embed)
    except:
        await ctx.send('Картинка не найдена (можете попробовать еще раз(а можете и не пробовать) )')
@bot.command()
async def jpg2(ctx, text):
    response = requests.get('https://www.googleapis.com/customsearch/v1?q='+ text + '&cx=d0c3a1f05db472102&key=AIzaSyD5lSNWFlZXAZOIYhfgl_qbSA1a75CYNAQ&searchType=image&alt=json') # Get-запрос
    try: 
        json_data = json.loads(response.text)
        embed = discord.Embed(color = 0xff9900, title = text)
        embed.set_image(url = json_data['link'])
        embed.set_footer(text = response.text)
        await ctx.send(embed = embed)
    except:
        await ctx.send('Картинка не найдена (можете попробовать еще раз(а можете и не пробовать) )') 

#погода:
@bot.command()
async def temp(ctx):
    tkn = 'd9957c4e14de3614258de9711985e9c8'
    owm = pyowm.OWM(tkn)
    w = owm.weather_manager()
    call = w.one_call(lat=54, lon=28)
    temperature = call.current.temperature('celsius')
    temp = temperature ['temp']
    await ctx.send('Сейчас температура в Минске: **{}**'.format(temp))


#---------------------------------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------Кнопочки--------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------#

@bot.command()
async def knopochka(ctx):
    await ctx.send(
        embed=discord.Embed(title = "Наконец-тоооо"),
        components=[
            Button(style=ButtonStyle.red, label="Кнопки в дискорде!!!", emoji="🥳"),
            Button(style=ButtonStyle.blue, label="*кнопка*"),
            ]
        )

    response=await bot.wait_for("button_click")
    if response.channel == ctx.channel:
        if response.component.label == "Кнопки в дискорде!!!":
            await response.respond(content="Балдеж, просто")
        if response.component.label == "*кнопка*":
            await response.respond(content="*Ответ*")


#---------------------------------------------------------------------------------------------------------------------------------#
#---------------------------------------Возможные-ошибки--------------------------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------------------#

@award.error
async def net_prav30(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'{ctx.author.mention}, лол, у Вас нет прав')

@take.error
async def net_prav3(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'{ctx.author.mention}, лол, у Вас нет прав')

@add_shop.error
async def net_prav1(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'{ctx.author.mention}, лол, у Вас нет прав')

@remove_shop.error
async def net_prav2(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'{ctx.author.mention}, лол, у Вас нет прав')

@clear.error
async def clear_error1(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'{ctx.author.mention}, лол, у Вас нет прав')

@ai.error
async def clear_error1(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'{ctx.author.mention}, ай-ай-айкать могут только избранные')

@clear.error
async def clear_error2(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'{ctx.author.mention}, укажите, сколько сообщений надо удалить')

@bot.event
async def on_command_error(ctx, error):
    pass


bot.run(settings['token'])


