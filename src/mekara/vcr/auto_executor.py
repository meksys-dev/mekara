"""VCR auto step executor.

This module contains the VCR implementation of the `AutoExecutorProtocol` boundary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator

from mekara.scripting.auto import (
    AutoExecutionError,
    AutoExecutionResult,
    RealAutoExecutor,
    ScriptExecutionError,
)
from mekara.scripting.runtime import Auto, AutoResult
from mekara.vcr.events import AutoStepEvent


class VcrAutoExecutor:
    """Auto executor that records/replays via a VCR cassette.

    Record mode: wraps a RealAutoExecutor, delegates execution, records results.
    Replay mode: NO inner executor - returns everything from cassette.

    Stateless: all context (including working_dir) passed per method call.
    """

    def __init__(
        self,
        *,
        cassette: Any,
        inner: RealAutoExecutor | None = None,
    ) -> None:
        from mekara.vcr.cassette import VCRCassette

        if not isinstance(cassette, VCRCassette):
            raise TypeError(f"cassette must be a VCRCassette, got {type(cassette)!r}")

        if cassette.mode == "record" and inner is None:
            raise ValueError("Record mode requires an inner executor")
        if cassette.mode == "replay" and inner is not None:
            raise ValueError("Replay mode must not have an inner executor")

        self._cassette = cassette
        self._inner = inner

    async def execute(self, step: Auto, *, working_dir: Path) -> AsyncIterator[AutoExecutionResult]:
        mode = self._cassette.mode

        if mode == "replay":
            from mekara.vcr.auto_steps import reconstruct_auto_step_result
            from mekara.vcr.events import AutoStepInputs

            recorded_event = self._cassette.consume_event(AutoStepEvent)
            expected_inputs = AutoStepInputs.from_step(step)

            # Verify inputs match
            if recorded_event.inputs != expected_inputs:
                raise ScriptExecutionError(
                    f"VCR replay error: auto_step inputs mismatch.\n"
                    f"Expected: {expected_inputs!r}\n"
                    f"Got: {recorded_event.inputs!r}\n"
                    "Re-record the cassette to capture events in order."
                )

            # Assert working_dir matches
            current_working_dir = str(working_dir)
            if current_working_dir != recorded_event.working_dir:
                raise ScriptExecutionError(
                    f"VCR replay error: working_dir mismatch.\n"
                    f"Expected: {recorded_event.working_dir!r}\n"
                    f"Got: {current_working_dir!r}\n"
                    "Re-record the cassette to capture events in order."
                )

            recorded = reconstruct_auto_step_result(recorded_event=recorded_event)
            yield AutoExecutionResult(result=recorded)
            return

        # Record mode - delegate to inner executor
        assert self._inner is not None
        final_result: AutoResult | None = None
        output: str = ""
        try:
            async for event in self._inner.execute(step, working_dir=working_dir):
                if isinstance(event, AutoExecutionResult):
                    final_result = event.result
                yield event
        except AutoExecutionError as exc:
            from mekara.scripting.runtime import AutoException

            auto_exception = AutoException(
                exception=exc.original_exception,
                step_description=step.description,
                output=exc.output,
            )
            final_result = auto_exception
            yield AutoExecutionResult(result=auto_exception)
        except ScriptExecutionError:
            raise
        except Exception as exc:
            from mekara.scripting.runtime import AutoException

            auto_exception = AutoException(
                exception=exc,
                step_description=step.description,
                output=output,
            )
            final_result = auto_exception
            yield AutoExecutionResult(result=auto_exception)

        if mode == "record" and final_result is not None:
            from mekara.vcr.auto_steps import build_recorded_auto_step_event

            self._cassette.record_event(
                build_recorded_auto_step_event(
                    step=step,
                    result=final_result,
                    working_dir=working_dir,
                )
            )
            self._cassette.save()
