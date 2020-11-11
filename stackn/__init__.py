# Maybe create a module API like the mlflow API? E.g. allow for logging of metrics using stackn.log_metric(key, value)


import stackn.tracking.fluent
print("hello")
import stackn.tracking as tracking

log_param = stackn.tracking.fluent.log_param
log_metric = stackn.tracking.fluent.log_metric

__all__ = [
    "log_param",
    "log_metric" 
]