import requests
from .utilities import user_id


def create_collection(anilist, type, username=None):
    current_collection = media_list_collection(anilist, type, username)
    current = []

    for list in current_collection["MediaListCollection"]["lists"]:
        current += list["entries"]

    return (current, current_collection["MediaListCollection"]["user"]["name"])


def media_list_collection(anilist, type, username=None):
    return requests.post(
        "https://graphql.anilist.co",
        json={
            "query": media_list_collection_query(
                user_id(anilist) if username is None else user_name_to_id(username),
                type,
            )
        },
        headers={
            "Authorization": anilist["token_type"] + " " + anilist["access_token"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    ).json()["data"]


def media_list_collection_query(user_id: int, type) -> str:
    return f"""{{
        MediaListCollection(userId: {user_id}, type: {"ANIME" if type == "ANIME" else "MANGA"}, status_not_in: [COMPLETED]) {{
            hasNextChunk
            lists {{
                entries {{
                    media {{
                        id
                        status
                        type
                        episodes
                        title {{ romaji english native }}
                        nextAiringEpisode {{ episode }}
                        mediaListEntry {{ progress }}
                        startDate {{ year }}
                    }}
                }}
            }}
            user {{ name }}
        }}
    }}"""
