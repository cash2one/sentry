# QA

## Q: why we need StatsD?

A: we want to measure lots of stuff about OpenStack, like response time of
API, RPC, database, error-rates. The normal way in OpenStack is send
notification to message bus, then a consumer (maybe stacktach) drain out
these event to measure things. This way have some cons.

First, notification is something important, OpenStack will do retry to sent
them forever. It is too much to measure, losting some metric data do little
harm. and retrying forever may block the normal service which is unexpected.

Second, putting lots of metric data take make much load on MQ, in designment
 MQ is just used for communication message bus for OpenStack, rather than a
data message bus.

On the contrary, StatsD is based on UDP, and dead simple to use. Losting some
metric data only make measure not that precise, which is acceptable to us.

## Q: Why we reinvent the wheel?

A: Because all the supported project was based on python, like CI, packaging,
And all our developers are all family with python. Another reason is that
StatsD is easy to reimplentment, so I recreate it without any hestitation.


# Designment

## Metrics
Get insight from [datadog](http://docs.datadoghq.com/guides/dogstatsd/).

If you want to send metrics to DogStatsD in your own way, here is the format of
the packets:

```
ns.dimension_name.dimension_value.name:value|type|@sample_rate|#tag1:value,tag2
```
Here’s breakdown of the fields:

`ns` should be a String that specified the namespace.
`dimension_name` should be String specified the dimension name of the metric.
`dimension_value` should be a String specified the dimension value of the
metric.
`name` should be a String with no colons, bars or @ characters.
`value` should be a number
`type` should be c for Counter, g for Gauge, h for Histogram, ms for Timer or s
for Set. Full explanation of type
[here](https://github.com/etsy/statsd/blob/master/docs/metric_types.md).
`sample rate` is optional and should be a float between 0 and 1 inclusive.
`tags` are optional, and should be a comma seperated list of tags. colons are
used for key value tags. The first item of tags will be dimension, the other of
tags will be aggregation_dimension.

Here are some example datagrams and comments explaining them:


```
# Increment the page.views counter.
page.views:1|c

# Record the fuel tank is half-empty
fuel.level:0.5|g

# Sample a the song length histogram half of the time.
song.length:240|h|@0.5

# Track a unique visitor to the site.
users.uniques:1234|s

# Increment the users online counter tagged by country of origin.
users.online:1|c|#country:china

# An example putting it all together.
users.online:1|c|@0.5|#country:china
````` ``

# Examples

## Timer
```
openstack.service.10-120-12-12@cinder-api.rpc_rt:1|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:2|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:3|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:4|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:5|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:6|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:7|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:8|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:9|ms
openstack.service.10-120-12-12@cinder-api.rpc_rt:10|ms
```

will result in NCM metric:

rpc_rt_sum
rpc_rt_mean
rpc_rt_count
rpc_rt_lower
rpc_rt_upper
rpc_rt_sum_90
rpc_rt_upper_90
rpc_rt_mean_90
