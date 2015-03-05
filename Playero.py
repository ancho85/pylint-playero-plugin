from astroid import MANAGER, node_classes
from astroid import scoped_nodes
from transforms.execs import exec_transform
from transforms.classes import classes_transform
from transforms.modules import modules_transform
from transforms.functions import function_transform
from funcs import *

def register(linter):
    """required method to auto register this checker"""
    from playero_checkers.query_checker import QueryChecker
    linter.register_checker(QueryChecker(linter))

    if int(getConfig().get("optionals", "collect_cache_stats")):
        cache.collectStats = True
        from playero_checkers.cache_statistics_writer import CacheStatisticWriter
        linter.register_checker(CacheStatisticWriter(linter, cache))


MANAGER.register_transform(scoped_nodes.Module, modules_transform)
MANAGER.register_transform(scoped_nodes.Class, classes_transform)
MANAGER.register_transform(node_classes.CallFunc, function_transform)
MANAGER.register_transform(node_classes.Exec, exec_transform)
