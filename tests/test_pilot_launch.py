"""Bootstrap contracts; these mocks do not replace the retained native process probe."""
import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.pilot import launch


def test_windows_selector_policy_is_explicit_and_other_platforms_unchanged(monkeypatch):
    policy = object()
    setter = Mock()
    monkeypatch.setattr(asyncio, "set_event_loop_policy", setter)
    monkeypatch.setattr(asyncio, "WindowsSelectorEventLoopPolicy", lambda: policy, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    assert launch.configure_event_loop() == "windows-selector"
    setter.assert_called_once_with(policy)
    setter.reset_mock()
    monkeypatch.setattr(sys, "platform", "linux")
    assert launch.configure_event_loop() == "platform-default"
    setter.assert_not_called()


def test_launcher_configures_policy_before_importing_application_and_has_one_worker(monkeypatch):
    events = []
    monkeypatch.setattr(launch, "configure_event_loop", lambda: events.append("policy"))
    invoke = Mock(side_effect=lambda *args, **kwargs: events.append("server"))
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=invoke))
    launch.main([])
    assert events == ["policy", "server"]
    invoke.assert_called_once_with("src.pilot.api:create_app", factory=True, host="127.0.0.1", port=8000,
                                   workers=1, access_log=False, loop="asyncio")


@pytest.mark.parametrize("args", [["--port", "0"], ["--port", "65536"], ["--host", "public.example"]])
def test_invalid_launch_settings_fail_before_starting_application(monkeypatch, args):
    configure = Mock()
    monkeypatch.setattr(launch, "configure_event_loop", configure)
    with pytest.raises(SystemExit):
        launch.main(args)
    configure.assert_not_called()
