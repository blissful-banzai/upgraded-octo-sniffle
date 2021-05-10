# %%
import datetime
import tweepy as tw
from pathlib import Path

# %%
consumer_key = "bJGqgOc9f8aiSKmUnehRRM8Ed"
consumer_secret_key = "9ouo8JF9D7gi8GBjCV7nv1Z98NtorfZDyT2201euzCJZIr7MHH"
access_token = "1391766462084288514-t8uM73BxxENk3hka81Fg9wIWg4GaK3"
access_token_secret = "vYROIptwYXOgZGVwn7KEDW2AdKtm0GuENMpslcluGx899"
# %%


def search_tweets(search_query, time_frame=datetime.timedelta(hours=1), granularity=10):
    """
    This function queries twitter and counts the number of tweets in a specific time interval
    relative to now. There seems to be always a 2 hour shift, but I guess that is not problematic
    The granularity is the maximum precision with which tweets are counted. Smaller takes longer but
    is more accurate.
    """
    # Initially search for most recent tweet
    newest_tweet = tw.Cursor(
        api.search,
        q=search_query,
        lang="en",
    ).items(1)
    newest_tweet = list(newest_tweet)[0]
    print(f"newest tweet for {search_query} was created at {newest_tweet.created_at}")
    now = newest_tweet.created_at
    max_id = newest_tweet.id
    count = 0
    searching_timeframe = True
    while searching_timeframe:
        found_tweets = tw.Cursor(
            api.search,
            q=search_query,
            lang="en",
            max_id=max_id,
        ).items(granularity)
        last_tweet = list(found_tweets)[-1]
        max_id = last_tweet.id
        if last_tweet.created_at < now - time_frame:
            searching_timeframe = False
        else:
            count += granularity
    return count, now


if __name__ == "__main__":

    auth = tw.OAuthHandler(consumer_key, consumer_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)

    # Get the counts
    count_long, latest_long = search_tweets("$BTC Long")
    count_short, latest_short = search_tweets("$BTC Short")
    date_str = latest_long.strftime("%m%d%Y_%H00")

    # Save if it has not been saved before
    results_path = Path(f"queries/")
    filename = Path(f"{date_str}_query.txt")
    file_path = results_path / filename

    if file_path.exists():
        print(
            f"already collected data for {latest_long.strftime('%m-%d-%Y at %H:00')}, skipping save."
        )
    else:
        results_path.mkdir(parents=True, exist_ok=True)
        with open(str(file_path), "w") as f:
            f.write(f"{count_long}, {count_short}")
