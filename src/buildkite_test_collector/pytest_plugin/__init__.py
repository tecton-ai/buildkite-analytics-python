"""Buildkite test collector for Pytest."""

from logging import warning

import pytest

from ..collector.payload import Payload
from ..collector.run_env import detect_env
from ..collector.api import submit
from .span_collector import SpanCollector
from .buildkite_plugin import BuildkitePlugin


@pytest.fixture
def spans(request):
    """A pytest fixture which returns an instance of SpanCollector"""
    nodeid = request.node.nodeid
    plugin = getattr(request.config, '_buildkite', None)

    return SpanCollector(plugin=plugin, nodeid=nodeid)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """pytest_configure hook callback"""
    env = detect_env()

    if env:
        plugin = BuildkitePlugin(Payload.init(env))
        config.pluginmanager.register(plugin, name="_buildkite")
    else:
        warning("Unable to detect CI environment.  No test analytics will be sent.")


@pytest.hookimpl
def pytest_unconfigure(config):
    """pytest_unconfigure hook callback"""
    plugin = config.pluginmanager.get_plugin("_buildkite")
    if plugin:
        submit(plugin.payload)
        config.pluginmanager.unregister(plugin)
