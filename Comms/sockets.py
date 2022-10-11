import zmq

from ports import SUB_PREFIX, PUB_PREFIX


def create_subscriber(context, sub_port, topic, queue_messages=True, connect=True):
    """
    utility function to produce a socket subscribed to a
    specified port and topic.
    :param context a zmq context
    :param sub_port the port to connect topic
    :param topic the topic to subscribe topic
    :param queue_messages set to 'true' to hold messages in the queue,
                          set to 'false' to use only the most recent message
    :param connect set to 'true' to have the socket connect to the address
                   set to 'false' to have the socket bind to the address
    :return the configured subscriber socket
    """
    sock = context.socket(zmq.SUB)

    if not queue_messages:
        sock.setsockopt(zmq.CONFLATE, 1)

    address = SUB_PREFIX if connect else PUB_PREFIX
    address += sub_port

    if connect:
        sock.connect(address)
    else:
        sock.bind(address)

    sock.setsockopt(zmq.SUBSCRIBE, topic)
    return sock


def create_publisher(context, publish_port, bind=True):
    """
    takes in a zmq context and a port to publish on, returns a
    zmq socket bound to publish on the specified port.
    :param context a zmq context
    :param publish_port a port to bind the socket to
    :param bind set to 'true' to have the socket bind to the address
                set to 'false' to have the socket connect to the address
    :return the configured publisher socket
    """
    sock = context.socket(zmq.PUB)
    address = PUB_PREFIX + publish_port
    if bind:
        sock.bind(address)
    else:
        sock.connect(address)
    return sock

