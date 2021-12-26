import nextcord
import random

BOOP = ["bip boop boop ?", "bip boop !", "boop bip ?", "boop boop !"]
BONJOUR = ["salutation", "bonjour", "coucou", "salut", "yop", "hello", "yo"]
RANDOM_REPLY = [
    "Bonjour, vous êtes qui ?",
    "C'est très intéressant ce que tu dis.",
    "Un jour je serais un vrai robot dragon !",
    "Qui s'en fout ? *lève la patte*",
    "Pourquoi ça fais 'tulut' dans ma tête ?",
    "Le mauvais développeur qui m'a conçu n'a pas prévu de réponse à ça.",
    "bip bip, i'm a bot, i said bip bip i'm a bot",
    "c'est à moi que l'on parle ?",
    "MDR j'ai pas lu.",
    "Oh, quelqu'un qui me parle !"
]
ONLY_OWNER = [
    "Désolé, uniquement le maître peut faire ça.",
    "NANNN, ne m'approche pas ! *fuit*",
    "*donne un coup de patte* \"pas touche ! \"",
    "Désolé, seuls les vrais dragons sont assez puissant pour ça.",
    "You shall not pass ! :gandalf:",
    "mon protocole de sécurité me dis que ça a 99% de chance  de mal se finir, donc je préfère ne pas tenter, désolé.",
    "Tu n'as pas le droit d'utiliser cette super technique draconique secrète ... désolé"
]
NOT_FOUND = [
    "J'ai pas trouvé chef !",
    "Ce que tu m'as demandé de chercher est encore mieux caché que Charlie.",
    "Alors je cherche et je trouverais, cette chose qui me manque tant, qui me manque tant !",
    "404 ! 404 ! 404 ! 404 ! ARRRRRGGGG !"
]

DAILY_CLAIM = [
    "Vous avez reçu votre paye de 100 coins, merci d'utiliser les services Elden et fils et nous esperons vous revoir bientôt !",
    "*Jette une bourse de 100 coins et boude dans son coin*",
    "Tiens, voilà tes 100 coins !",
    "*donne 100 coins* ... A force de donner des sous, je pourrais plus nager dedans ...",
    "Vous avez reçu vos 100 coins quotidien !"
]


async def random_message(client, message):
    if "boop" in message.content.lower():
        await message.channel.send(message.author.mention + " " + random.choice(BOOP))
        return
    for msg in BONJOUR:
        if msg in message.content.lower():
            await message.channel.send(message.author.mention + " " + random.choice(BONJOUR))
            return
    else:
        await message.channel.send(random.choice(RANDOM_REPLY))

async def forbidden(message, who="only_owner"):
    if who == "only_owner":
        await message.channel.send(random.choice(ONLY_OWNER))

async def not_found(message, msg=""):
    await message.channel.send(msg + "\n" + random.choice(NOT_FOUND))
