import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME")
STAFF_ROLE_NAME = os.getenv("STAFF_ROLE_NAME")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

REACTION_EMOJIS = {
    "INSCRIPTION": "✅",
    "PRET": "🟢",
    "RECHERCHE_EQUIPE": "🔍",
    "SCORES":
    ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
}


def has_role(member: discord.Member, role_name: str):
    return any(role.name.lower() == role_name.lower() for role in member.roles)


async def generer_classement(interaction: discord.Interaction, channel_id: int,
                             message_id: int, ephemeral: bool):
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            await interaction.followup.send("❌ Salon introuvable.",
                                            ephemeral=ephemeral)
            return

        message = await channel.fetch_message(message_id)
    except Exception:
        await interaction.followup.send("❌ Message introuvable.",
                                        ephemeral=ephemeral)
        return

    if not message.embeds:
        await interaction.followup.send(
            "❌ Ce message ne contient pas d’embed.", ephemeral=ephemeral)
        return

    embed = message.embeds[0]

    emoji_scores = {
        emoji: i + 1
        for i, emoji in enumerate(REACTION_EMOJIS["SCORES"])
    }

    # Gestion des réactions
    inscrits = set()
    equipes_pretes = set()
    chercheurs_equipe = set()
    user_vote_counts = defaultdict(int)
    reaction_users_by_score = defaultdict(list)

    for reaction in message.reactions:
        emoji = str(reaction.emoji)
        async for user in reaction.users():
            if user.bot:
                continue
            if emoji == REACTION_EMOJIS["INSCRIPTION"]:
                inscrits.add(user.id)
            elif emoji == REACTION_EMOJIS["PRET"]:
                equipes_pretes.add(user.id)
            elif emoji == REACTION_EMOJIS["RECHERCHE_EQUIPE"]:
                chercheurs_equipe.add(user.id)

    for reaction in message.reactions:
        emoji = str(reaction.emoji)
        if emoji not in emoji_scores:
            continue
        score = emoji_scores[emoji]
        async for user in reaction.users():
            if user.bot or user.id not in inscrits:
                continue
            member = interaction.guild.get_member(user.id)
            if member:
                user_vote_counts[user.id] += 1
                reaction_users_by_score[score].append(member)

    # Extraire le nombre de joueurs par équipe
    try:
        joueurs_par_equipe_str = field_dict.get("👥 Joueurs/équipe", "0")
        joueurs_par_equipe_int = int(joueurs_par_equipe_str.strip())
    except ValueError:
        joueurs_par_equipe_int = 0  # fallback si champ mal rempli

    classement_lines = []
    for score in range(1, 11):
        members = reaction_users_by_score.get(score, [])
        unique_members = {m.id: m for m in members if m.id in inscrits}

        if not unique_members:
            classement_lines.append(f"{score}. —")
            continue

        mentions = []
        nb_members = len(unique_members)
        has_conflict = nb_members > joueurs_par_equipe_int > 0
        for uid, member in unique_members.items():
            multivote = user_vote_counts[uid] > 1
            warnings = []
            if has_conflict:
                warnings.append("⚠️ Équipe trop nombreuse")
            if multivote:
                warnings.append("⚠️ Vote multiple")
            warning_str = " ".join(warnings)
            mention = f"{warning_str} {member.mention}".strip()
            mentions.append(mention)

        joined_mentions = ", ".join(mentions)
        classement_lines.append(f"{score}. {joined_mentions}")

    # Trouve les champs nécessaires uniquement
    field_dict = {f.name: f.value for f in embed.fields}
    organisateur = field_dict.get("👤 Organisateur", "-")
    jeu = field_dict.get("🕹️ Jeu", "-")
    url = field_dict.get("🔗 URL", "-")

    # Crée un embed résumé stylé
    rank_embed = discord.Embed(title=embed.title, color=discord.Color.gold())

    rank_embed.add_field(name="👤 Organisateur",
                         value=organisateur,
                         inline=False)
    rank_embed.add_field(name="🕹️ Jeu", value=jeu, inline=False)
    rank_embed.add_field(name="🔗 URL", value=url, inline=False)
    rank_embed.add_field(
        name="🧾 Détails complets de l'animation",
        value=
        f"[Voir le message original dans Discord](https://discord.com/channels/{interaction.guild_id}/{channel_id}/{message_id})",
        inline=False)

    rank_embed.add_field(name="✅ Inscrits",
                         value=str(len(inscrits)),
                         inline=True)
    rank_embed.add_field(name="🟢 Équipes prêtes",
                         value=str(len(equipes_pretes)),
                         inline=True)
    rank_embed.add_field(name="🔍 Cherche équipe",
                         value=str(len(chercheurs_equipe)),
                         inline=True)

    classement_texte = "\n".join(classement_lines) or "—"
    rank_embed.add_field(name="🏆 Classement",
                         value=classement_texte,
                         inline=False)

    await interaction.followup.send(embed=rank_embed, ephemeral=ephemeral)


def build_anim_embed(nom: str,
                     organisateur: str,
                     jeu: str,
                     url: str,
                     prix: str,
                     plateforme: str,
                     joueurs_par_equipe: str,
                     duree: str,
                     min_joueurs: str,
                     max_joueurs: str,
                     logiciels_autorises: str,
                     deroulement: str,
                     briefing: str,
                     autre_infos: str,
                     footer: str = None):
    embed = discord.Embed(title=f"🎮 {nom}", color=discord.Color.blue())
    embed.add_field(name="👤 Organisateur", value=organisateur, inline=False)
    embed.add_field(name="🕹️ Jeu", value=jeu, inline=False)
    embed.add_field(name="🔗 URL", value=url or "-", inline=False)
    embed.add_field(name="💰 Prix d’achat", value=prix, inline=True)
    embed.add_field(name="🖥️ Plateforme", value=plateforme, inline=True)
    embed.add_field(name="👥 Joueurs/équipe",
                    value=joueurs_par_equipe,
                    inline=True)
    embed.add_field(name="⏱️ Durée (en heure)", value=duree, inline=True)
    embed.add_field(name="👤 Joueurs min", value=min_joueurs, inline=True)
    embed.add_field(name="👥 Joueurs max", value=max_joueurs, inline=True)
    embed.add_field(name="🛠️ Logiciels autorisés",
                    value=logiciels_autorises or "-",
                    inline=False)
    embed.add_field(name="📋 Déroulement", value=deroulement, inline=False)
    embed.add_field(name="📣 Briefing", value=briefing or "-", inline=False)
    embed.add_field(name="ℹ️ Autres informations utiles",
                    value=autre_infos or "-",
                    inline=False)
    embed.add_field(
        name="ℹ️ Réactions",
        value=
        ("▪ ✅ **S’inscrire à l’animation** – obligatoire pour participer\n"
         "▪ 🟢 **Mon équipe est prête** – à cocher si l’animation se joue en équipe et que la vôtre est complète\n"
         "▪ 🔍 **Je cherche une équipe / des coéquipiers** – si vous êtes seul ou votre équipe est incomplète (animations en équipe uniquement)\n"
         "▪ 1️⃣ à 🔟 **Indiquer le classement** – si l’animation se joue en équipe, chaque membre de l’équipe doit voter"
         ),
        inline=False)

    if footer:
        embed.add_field(name="🆔 Commande classement",
                        value=footer,
                        inline=False)
    return embed


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            print(f"🏠 Connecté au serveur : {guild.name} (ID: {guild.id})")
        else:
            print("❌ Erreur : serveur non trouvé avec GUILD_ID")

        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🔁 Synced {len(synced)} command(s) in guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Sync error: {e}")


@bot.tree.command(name="newanim",
                  description="Créer une animation",
                  guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    organisateur="Mentionne le responsable de l’animation",
    nom="Nom de l'animation",
    jeu="Nom du jeu",
    url="URL du jeu ou du tournoi (si applicable)",
    prix="Prix d'achat du jeu",
    plateforme="Plateforme utilisée",
    joueurs_par_equipe="Nombre de joueurs par équipe",
    duree="Durée de l'animation (en heure)",
    min_joueurs="Nombre minimum de joueurs",
    max_joueurs="Nombre maximum de joueurs",
    logiciels_autorises=
    "Logiciels autorisés (mettre - si seulement le jeu de base)",
    deroulement=
    "Déroulement de l'animation (tournoi, conditions de victoire, etc.)",
    briefing="Briefing (lieu ou - s'il n'y en a pas)",
    autre_infos="Autres informations utiles")
async def newanim(interaction: discord.Interaction,
                  organisateur: discord.Member, nom: str, jeu: str, url: str,
                  prix: str, plateforme: str, joueurs_par_equipe: str,
                  duree: str, min_joueurs: str, max_joueurs: str,
                  logiciels_autorises: str, deroulement: str, briefing: str,
                  autre_infos: str):
    if not has_role(interaction.user, ADMIN_ROLE_NAME):
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True)
        return

    embed = build_anim_embed(nom, organisateur.mention, jeu, url, prix,
                             plateforme, joueurs_par_equipe, duree,
                             min_joueurs, max_joueurs, logiciels_autorises,
                             deroulement, briefing, autre_infos)

    await interaction.response.send_message(embed=embed)
    sent_message = await interaction.original_response()

    # Modifier l’embed pour inclure les bons IDs
    embed.add_field(
        name="🆔 Commande classement",
        value=
        f"`/getrank channel_id:{interaction.channel.id} message_id:{sent_message.id}`",
        inline=False)

    # Ajoute les emojis par défaut
    for emoji in [
            REACTION_EMOJIS["INSCRIPTION"], REACTION_EMOJIS["PRET"],
            REACTION_EMOJIS["RECHERCHE_EQUIPE"], *REACTION_EMOJIS["SCORES"]
    ]:
        await sent_message.add_reaction(emoji)

    # Mettre à jour le message avec le nouvel embed
    await sent_message.edit(embed=embed)


@bot.tree.command(
    name="editanim",
    description="Modifier partiellement les infos d'une animation existante",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    channel_id="ID du salon contenant le message",
    message_id="ID du message à modifier",
    organisateur="Nouvel organisateur de l'animation",
    nom="Nouveau nom de l'animation (sera affiché comme titre)",
    jeu="Nouveau nom du jeu",
    url="Nouvelle URL",
    prix="Nouveau prix",
    plateforme="Nouvelle plateforme",
    joueurs_par_equipe="Nouveau nombre de joueurs par équipe",
    duree="Nouvelle durée",
    min_joueurs="Nouveau nombre minimum de joueurs",
    max_joueurs="Nouveau nombre maximum de joueurs",
    logiciels_autorises="Nouveaux logiciels autorisés",
    deroulement="Nouveau déroulement",
    briefing="Nouveau briefing",
    autre_infos="Nouvelles infos utiles",
)
async def editanim(
    interaction: discord.Interaction,
    channel_id: str,
    message_id: str,
    organisateur: discord.Member = None,
    nom: str = None,
    jeu: str = None,
    url: str = None,
    prix: str = None,
    plateforme: str = None,
    joueurs_par_equipe: str = None,
    duree: str = None,
    min_joueurs: str = None,
    max_joueurs: str = None,
    logiciels_autorises: str = None,
    deroulement: str = None,
    briefing: str = None,
    autre_infos: str = None,
):
    if not has_role(interaction.user, ADMIN_ROLE_NAME):
        await interaction.response.send_message("❌ Tu n'as pas la permission.",
                                                ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        channel = bot.get_channel(int(channel_id))
        message = await channel.fetch_message(int(message_id))
    except Exception:
        await interaction.followup.send(
            "❌ Impossible de retrouver le message.", ephemeral=True)
        return

    if not message.embeds:
        await interaction.followup.send(
            "❌ Le message ne contient pas d'embed.", ephemeral=True)
        return

    embed = message.embeds[0]
    old_fields = {f.name: f.value for f in embed.fields}

    def get(name, default):
        return old_fields.get(name, default)

    # Récupère les anciennes valeurs si pas modifiées
    data = {
        "nom": (nom.removeprefix("🎮 ").strip()
                if nom else embed.title.removeprefix("🎮 ").strip()),
        "organisateur":
        organisateur.mention if organisateur else get("👤 Organisateur", "-"),
        "jeu":
        jeu or get("🕹️ Jeu", "-"),
        "url":
        url if url is not None else get("🔗 URL", "-"),
        "prix":
        prix or get("💰 Prix d’achat", "-"),
        "plateforme":
        plateforme or get("🖥️ Plateforme", "-"),
        "joueurs_par_equipe":
        joueurs_par_equipe or get("👥 Joueurs/équipe", "-"),
        "duree":
        duree or get("⏱️ Durée (en heure)", "-"),
        "min_joueurs":
        min_joueurs or get("👤 Joueurs min", "-"),
        "max_joueurs":
        max_joueurs or get("👥 Joueurs max", "-"),
        "logiciels_autorises":
        logiciels_autorises if logiciels_autorises is not None else get(
            "🛠️ Logiciels autorisés", "-"),
        "deroulement":
        deroulement or get("📋 Déroulement", "-"),
        "briefing":
        briefing if briefing is not None else get("📣 Briefing", "-"),
        "autre_infos":
        autre_infos if autre_infos is not None else get(
            "ℹ️ Autres informations utiles", "-"),
        "footer":
        get("🆔 Commande classement", None)
    }

    # Construit un nouvel embed identique
    new_embed = build_anim_embed(
        data["nom"], data["organisateur"], data["jeu"], data["url"],
        data["prix"], data["plateforme"], data["joueurs_par_equipe"],
        data["duree"], data["min_joueurs"], data["max_joueurs"],
        data["logiciels_autorises"], data["deroulement"], data["briefing"],
        data["autre_infos"], data["footer"])

    try:
        await message.edit(embed=new_embed)
        await interaction.followup.send(
            "✅ Le message a été mis à jour avec succès.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(
            f"❌ Erreur lors de la mise à jour : {e}", ephemeral=True)


@bot.tree.command(
    name="getrank",
    description=
    "Afficher juste pour moi les infos et le classement d'une animation",
    guild=discord.Object(id=GUILD_ID))
async def getmsginfo(interaction: discord.Interaction, channel_id: str,
                     message_id: str):

    await interaction.response.defer(ephemeral=True)

    try:
        cid = int(channel_id)
        mid = int(message_id)
    except ValueError:
        await interaction.followup.send("❌ ID(s) invalide(s).", ephemeral=True)
        return

    await generer_classement(interaction, cid, mid, ephemeral=True)


@bot.tree.command(
    name="postrank",
    description=
    "Publier pour tout le monde les infos et le classement d'une animation",
    guild=discord.Object(id=GUILD_ID))
async def postrank(interaction: discord.Interaction, channel_id: str,
                   message_id: str):
    if not has_role(interaction.user, ADMIN_ROLE_NAME):
        await interaction.response.send_message("❌ Tu n'as pas la permission.",
                                                ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    try:
        cid = int(channel_id)
        mid = int(message_id)
    except ValueError:
        await interaction.followup.send("❌ ID(s) invalide(s).")
        return

    await generer_classement(interaction, cid, mid, ephemeral=False)


bot.run(TOKEN)
