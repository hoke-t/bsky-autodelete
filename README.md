# bsky-autodelete

Uses Modal (https://modal.com) to run a function that deletes all bluesky posts starting with "!tmp" after 24 hours.

## Installation

1. Sign in or create an account at https://modal.com with GitHub
2. Navigate to "Secrets > New Secret > Custom"
3. Create key "BSKY_HANDLE" with value your bluesky handle, and "BSKY_PASS" with value your bluesky password
4. Name the secret "bsky"
5. Run `pip install modal-client`, then go through `modal token new`, then `modal deploy main.py`. You should get a link at which you can see script runs and outputs. The default is that every 5 minutes it will run and delete "!tmp" posts older than 24 hours.
