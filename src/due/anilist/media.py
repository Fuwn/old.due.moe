# import requests

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
