import requests


def user_id(anilist):
    viewer = requests.post(
        "https://graphql.anilist.co",
        json={"query": "{ Viewer { id } }"},
        headers={
            "Authorization": anilist["token_type"] + " " + anilist["access_token"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    ).json()["data"]["Viewer"]

    if viewer is None:
        return -1

    return int(viewer["id"])


def last_activity(id):
    return int(
        requests.post(
            "https://graphql.anilist.co",
            json={
                "query": f"""{{ Activity(userId: {id}, type: MEDIA_LIST, sort: ID_DESC) {{
                    __typename ... on ListActivity {{ createdAt }}
                }} }}"""
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        ).json()["data"]["Activity"]["createdAt"]
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
