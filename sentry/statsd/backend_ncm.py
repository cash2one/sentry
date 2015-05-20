from sentry import ncm


class NCMBackend(object):

    def __init__(self):
        self.client = ncm.get_client()

    def push_metric(self, metric_info, metric_values):
        if not self.client:
            return

        metric_name = metric_info['metric_name']
        dimens_name = metric_info['dimension_name']
        dimens_value = metric_info['dimension_value']
        namespace = metric_info['namespace']
        agg_dimens = metric_info['tags']

        self.client.set_namespace(namespace)

        if isinstance(metric_values, dict):
            # Timer goes here
            for name, value in metric_values.iteritems():
                full_name = '%s_%s' % (metric_name, name)
                self.client.post_metric(full_name, value, dimens_name,
                                        dimens_value, agg_dimens)

        elif (isinstance(metric_values, float) or
                                        isinstance(metric_values, int)):
            self.client.post_metric(metric_name, metric_values, dimens_name,
                                    dimens_value, agg_dimens)
