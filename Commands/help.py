import discord
from util.exception import NotFound

from discord import TextChannel

helper = {
    "MithJDR": {
        "/mithroll ou /mr": "``{compétence} [+/-][bonus/malus]`` Lance un dé pour la compétence donnée",
        "/gmroll ou /gr": "Comme le /roll mais envoie une copie du lancé au MJ (voir /help Roll)",
        "/xproll": "Effectue tout les jets d'XP du personnage",
        "/takedamage ou /td": "``[joueur] {Roll expr.}`` Fait perdre le résultat de l'expression au joueur",
        "/healdamage ou /hd": "``[joueur] {Roll expr.}`` Comme /takedamage mais soigne à la place",
        "/mithcfg": "Ouvre le panneau de config pour le module"
    },
    "Moderation": {
        "/mdelete": "``{message_id} [!][raison]`` Supprime le message, si un ! est donné avant la raison, une notification est envoyé à la personne",
        "/mmove": "``{message_id} {channel_id} [!][raison]`` Déplace le message donné vers le channel donné, si un ! est donné avant la raison, une notification est envoyé à la personne",
        "/mmoveafter": "``{message_id} {channel_id} [!][raison]`` Déplace tout les message après celui donné (inclu) dans le channel x, si un ! est donné avant la raison, une (et une seule) notification est envoyé à la personne",
    },
#    "Money": {
#        "/coin": "``[member]`` Affiche le nombre de compte de `member`, si `member` n'est pas donné, affiche votre compte",
#        "/daily": "Récupère votre somme quotidienne",
#        "/pay": "``{value} {member}`` Envoie `valeur` coins à `member`",
#    },
    "Music": {
        "/music {lien Youtube}" : "Ajoute la musique à la queue",
        "/music search": "``{query}`` Checrche sur Youtube et joue le premier résultat trouvé",
        "/music skip" : "Passe à la musique suivante",
        "/music pause" : "met en pause la musique",
        "/music resume" : "enlève la pause de la musique",
        "/music disconnect" : "déconnecte le bot du canal",
    },
    "OpenRole": {
        "/roleadd": "``{role}`` Ajoute le role dans la liste des roles joinable",
        "/roledel": "``{role}`` Supprime le role de la liste des roles joinable",
        "/rolelist": "Affiche la liste des roles joinable",
    },
    "Quizz": {
        "/lolquizz": "Retrouvez à quel champion de LoL le sort donné appartient"
    },
    "RiotAPI (claqué au sol)": {
        '/verif' : "Affiche les informations pour la vérification (nécessaire pour certaines commandes)",
        '/afkmeter' : "Affiche le nombre d'AFK de l'invocateur sur les 100 dernières games.",
        '/kikimeter' : "Permet de savoir .... bref le nom de la commande quoi.",
        '/premade' : "Affiche le nombre de partie jouer avec chaque joueurs",
        '/info' : "Affiche le rank de l'invocateur et son classement sur le serveur.",
        '/ladder': "``SoloQ / FlexQ / 3v3TT`` Affiche les meilleurs invocateur du serveur dans la queue sélectionnée",
    },
    "Roll": {
        '/r ou /roll' : "``[x]d[y][+ ou -][b]`` Lance x dé(s) y avec un bonus/malus de b.",
        '/br ou /rb' : "``x[+r]`` Lancer de dé de bloodlust, lance x dé(s) 6 avec r risque.",
    },
    "SuperAdmin": {
        "/sleep": "Empeche le bot de réagir aux commandes jusqu'au prochain /sleep",
        "/kill": "Envoie un SIGKILL au bot (j'aime pas trop ce moment là)",
        "/refreshallscore": "Refresh tout les scores pour le /info et /ladder de la RGAPI",
        "/force": "``commande`` permet de bypass les check de permission",
        "/python": "``code`` éxecute le code python donné dans le bot",
        "/bash": "``bash`` éxecute le code donné dans bash",
        "/importverif": "Importe les comptes vérifié sur un serveur officiel"
    },
    "TFT": {
         "/tftteam": "Affiche les champions que vous possédez",
        "/tftsell": "``{champion_name} {level}`` vend un champion"
    },
    "Useless": {
        '/thanossnap': "Affiche un simulateur de thanos snap sur le serveur",
        "/latex": "``{commande latex}`` affiche une image formaté par LaTeX",
        "/memberinfo": "``[member]`` affiche les informations d'un membre",
        "/getroleid": "``{role name}``Renvoie l'id du role"
    },
}



class CmdHelp:
    async def cmd_help(self, *args, channel, **_):
        if not args:
            em = discord.Embed(title="Help")
            em.set_footer(text="Entrez /help {module} pour plus de détail")
            for k, v in helper.items():
                em.add_field(name=f"**{k}**",
                             value=',    '.join([f"``{i}``" for i in v.keys()]), inline=False)
            await channel.send(embed=em)
        elif args[0] in helper:
            d = helper[args[0]]
            em = discord.Embed(title=f"Help {args[0]}")
            for k, v in d.items():
                if v.startswith('``'):
                    a, t = v.split('``')[1], '``'.join(v.split('``')[2:])
                    em.add_field(name=f"**{k}** ``{a}``", value=t, inline=False)
                else:
                    em.add_field(name=f"**{k}**", value=v, inline=False)
            await channel.send(embed=em)
        else:
            raise NotFound("Erreur: J'ai pas trouvé le module dans mon manuel :(")
            
