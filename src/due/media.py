import requests


def user_id(anilist):
    return int(
        requests.post(
            "https://graphql.anilist.co",
            json={"query": "{ Viewer { id } }"},
            headers={
                "Authorization": anilist["token_type"] + " " + anilist["access_token"],
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        ).json()["data"]["Viewer"]["id"]
    )


def user_name_to_id(name):
    return int(
        requests.post(
            "https://graphql.anilist.co",
            json={"query": f'{{ User(name: "{name}") {{ id }} }}'},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        ).json()["data"]["User"]["id"]
    )


def create_collection(anilist, type, username=None):
    current_collection = media_list_collection(anilist, type, username)
    current = []

    for list in current_collection["MediaListCollection"]["lists"]:
        current += list["entries"]

    return (current, current_collection["MediaListCollection"]["user"]["name"])


# def media_list(anilist, pageNumber):
#     return requests.post(
#         "https://graphql.anilist.co",
#         json={"query": media_list_query(user_id(anilist), pageNumber)},
#         headers={
#             "Authorization": anilist["token_type"] + " " + anilist["access_token"],
#             "Content-Type": "application/json",
#             "Accept": "application/json",
#         },
#     ).json()["data"]


# def media_list_query(user_id: int, page_number: int) -> str:
#     return f"""{{
#         Page(page: {page_number}) {{
#             mediaList(userId: {user_id}, status_not_in: [COMPLETED]) {{
#                 media {{
#                     id
#                     status
#                     type
#                     title {{ romaji english }}
#                     nextAiringEpisode {{ episode }}
#                     mediaListEntry {{ progress }}
#                     startDate {{ year }}
#                 }}
#             }}
#             pageInfo {{ hasNextPage }}
#         }}
#     }}"""


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
                        title {{ romaji english }}
                        nextAiringEpisode {{ episode }}
                        mediaListEntry {{ progress }}
                        startDate {{ year }}
                    }}
                }}
            }}
            user {{ name }}
        }}
    }}"""
