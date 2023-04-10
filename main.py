from datetime import datetime, timedelta
import os

import modal
import requests

stub = modal.Stub(
    "bsky-autodelete",
    image=modal.Image.debian_slim().pip_install(
        "requests",
    ),
)


@stub.function(
    secret=modal.Secret.from_name("bsky"),
    schedule=modal.Cron("*/5 * * * *"),
)
def delete_tmp_posts(delete_after=timedelta(hours=24)):
    handle = os.environ.get("BSKY_HANDLE")
    data = {"identifier": handle, "password": os.environ.get("BSKY_PASS")}
    resp = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession", json=data
    )

    auth_token = resp.json().get("accessJwt")
    did = resp.json().get("did")
    if auth_token is None or did is None:
        raise ValueError(
            "incorrect handle or pass? check BLUESKY_HANDLE and BLUESKY_PASS env vars"
        )

    headers = {"Authorization": f"Bearer {auth_token}"}
    rkeys_to_delete = []

    current_datetime = datetime.utcnow()

    cursor = None
    while True:
        if cursor is None:
            resp_json = requests.get(
                f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={handle}",
                headers=headers,
            ).json()
        else:
            resp_json = requests.get(
                f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={handle}&cursor={cursor}",
                headers=headers,
            ).json()

        rkeys_to_delete.extend(
            [
                j["post"]["uri"].split("/")[-1]
                for j in resp_json["feed"]
                if j["post"]["record"]["text"].startswith("!tmp")
                and current_datetime
                - datetime.strptime(
                    j["post"]["record"]["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                >= delete_after
            ]
        )

        if "cursor" in resp_json and resp_json["cursor"]:
            cursor = resp_json["cursor"]
        else:
            break

    deleted_count = 0
    for rkey in rkeys_to_delete:
        data = {"collection": "app.bsky.feed.post", "repo": did, "rkey": rkey}
        resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.deleteRecord",
            json=data,
            headers=headers,
        )
        if resp.status_code == 200:
            print(f"deleted post with rkey {rkey}")
            deleted_count += 1
        else:
            print(f"failed to delete post with rkey {rkey}")

    print(f"deleted {deleted_count} posts")


@stub.local_entrypoint()
def main():
    delete_tmp_posts.call()

