# %%
import json
import datetime
import numpy as np
import tweepy as tw
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging

logging.basicConfig(level=logging.INFO)

# %%
consumer_key = "bJGqgOc9f8aiSKmUnehRRM8Ed"
consumer_secret_key = "9ouo8JF9D7gi8GBjCV7nv1Z98NtorfZDyT2201euzCJZIr7MHH"
access_token = "1391766462084288514-t8uM73BxxENk3hka81Fg9wIWg4GaK3"
access_token_secret = "vYROIptwYXOgZGVwn7KEDW2AdKtm0GuENMpslcluGx899"
# %%


def save_query(timepoint, count, search_query, save_dir):
    date_str = timepoint.strftime("%m%d%Y_%H00")
    # Save if it has not been saved before
    results_path = Path(save_dir) / Path(search_query)
    filename = Path(f"{date_str}_count.txt")
    file_path = results_path / filename
    results_path.mkdir(parents=True, exist_ok=True)
    with open(str(file_path), "w") as f:
        f.write(f"{count}")


def query_exists(timepoint, search_query, save_dir):
    date_str = timepoint.strftime("%m%d%Y_%H00")
    # Save if it has not been saved before
    results_path = Path(save_dir) / Path(search_query)
    filename = Path(f"{date_str}_count.txt")
    file_path = results_path / filename
    return file_path.exists()


def search_tweets(
    search_query,
    time_frame=datetime.timedelta(hours=1),
    granularity=10,
    go_back_until=3,  # in hours
    save_dir="queries/",
    search_kwargs=None,
):
    """
    This function queries twitter and counts the number of tweets in a specific time interval
    relative to now. There seems to be always a 2 hour shift, but I guess that is not problematic
    The granularity is the maximum precision with which tweets are counted. Smaller takes longer but
    is more accurate.
    """
    go_back_until = datetime.timedelta(hours=go_back_until)
    # Initially search for most recent tweet
    newest_tweet = tw.Cursor(
        api.search,
        q=search_query,
        **search_kwargs,
    ).items(1)
    list_of_tweets = list(newest_tweet)
    if len(list_of_tweets) == 0:
        logging.warning(f"Did not find any tweets.")
        return
    newest_tweet = list_of_tweets[0]
    now = newest_tweet.created_at
    logging.info(
        f"newest tweet for {search_query} was created at {now}. Going back {go_back_until}"
    )
    max_id = newest_tweet.id

    searching_history = True
    n_inc = 1
    while searching_history == True:
        searching_timeframe = True
        count = 0
        while searching_timeframe:
            found_tweets = tw.Cursor(
                api.search,
                q=search_query,
                lang="en",
                max_id=max_id,
            ).items(granularity)
            last_tweet = list(found_tweets)[-1]
            max_id = last_tweet.id
            if last_tweet.created_at < now - n_inc * time_frame:
                count += granularity
                searching_timeframe = False
                if query_exists(now - n_inc * time_frame, search_query, save_dir):
                    logging.warning(
                        f"file already exists for query {search_query} and time {(now - n_inc * time_frame).strftime('%m%d%Y_%H00')}."
                    )
                else:
                    save_query(now - n_inc * time_frame, count, search_query, save_dir)
                n_inc += 1
            else:
                count += granularity
                logging.info(
                    f"count for {search_query} and time {(now - n_inc * time_frame).strftime('%m%d%Y_%H00')} = {count}. Sill counting."
                )
        if last_tweet.created_at <= now - go_back_until:
            searching_history = False

    return count, now


def plot_queries(list_of_queries, save_dir):

    for query in list_of_queries:
        dates = []
        counts = []
        results_directory = Path(save_dir) / Path(query)
        for result in results_directory.rglob("*.txt"):
            date = "".join(result.name.split("_")[0:2])
            date = datetime.datetime.strptime(date, "%m%d%Y%H00")
            count = np.loadtxt(result)

            dates.append(date)
            counts.append(count)
        df = pd.DataFrame({"query": counts, "time": dates})
        df.sort_values("time", ascending=True, inplace=True)
        plt.plot(df["time"], df["query"], "-o", label=query)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d-%H:00"))
    fig = plt.gcf()
    fig.autofmt_xdate()
    plt.xlabel("time")
    plt.ylabel("counts")
    plt.grid()
    plt.legend()
    plt.savefig(Path(save_dir) / Path("query_timeline.png"))
    plt.close()


if __name__ == "__main__":

    auth = tw.OAuthHandler(consumer_key, consumer_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)

    config_path = Path(__file__).parents[0] / Path("config.json")
    with open(str(config_path)) as json_file:
        config = json.load(json_file)
    # Get the counts
    for query, search_kwargs in zip(config["search_queries"], config["search_kwargs"]):
        logging.info(f"searching {query} with the following setting: {search_kwargs}")
        search_tweets(
            query,
            granularity=config["granularity"],
            go_back_until=config["go_back_until"],
            save_dir=config["save_directory"],
            search_kwargs=search_kwargs,
        )

    plot_queries(config["search_queries"], config["save_directory"])
