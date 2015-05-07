import eventlet


def retry_do(retry_times, method, *args, **kwargs):
    """Common code to retry some method

    :param retry_times: int, the max retry number. If retry_times is 3, the
                        total invoking number is 4, cause first invoking is
                        not retrying.
    :param method: the method to retry.
    :param *args: the position argument passin method.
    :param **kwargs: the key word argument passin method.
    """
    assert callable(method)

    times = 0

    while True:
        try:
            times += 1
            return method(*args, **kwargs)
        except Exception as ex:
            if times > retry_times:
                raise ex
            eventlet.sleep(times * 2)
