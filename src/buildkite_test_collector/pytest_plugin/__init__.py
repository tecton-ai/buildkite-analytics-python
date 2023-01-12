"""Buildkite test collector for Pytest."""

import json
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


@pytest.hookimpl
def pytest_addoption(parser, pluginmanager):
    group = parser.getgroup("buildkite-test-collector")
    group.addoption(
        "--buildkite-analytics-json-out", action="store", help="JSON file to write analytics payload to"
    )


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

        if config.getoption("--buildkite-analytics-json-out"):
            with open(config.getoption("--buildkite-analytics-json-out"), mode="w") as f:
                f.write(json.dumps(plugin.payload.as_json()))
        config.pluginmanager.unregister(plugin)
