class TwitterException(Exception):
    ...


class NotAuthenticated(TwitterException, PermissionError):
    ...


class TweetUnavailable(TwitterException, PermissionError):
    ...
