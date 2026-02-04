"""VCR helpers for recording and replaying Auto step results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mekara.vcr.events import (
    AutoExceptionData,
    AutoStepEvent,
    AutoStepInputs,
    CallResultData,
    ShellResultData,
)


def build_recorded_auto_step_event(*, step: Any, result: Any, working_dir: Path) -> AutoStepEvent:
    """Serialize an Auto step result to a typed AutoStepEvent."""
    from mekara.scripting.runtime import AutoException, ShellResult

    if isinstance(result, ShellResult):
        result_data: ShellResultData | CallResultData | AutoExceptionData = ShellResultData(
            success=result.success,
            exit_code=result.exit_code,
            output=result.output,
        )
    elif isinstance(result, AutoException):
        result_data = AutoExceptionData(
            success=result.success,
            exception=str(result.exception),
            step_description=result.step_description,
            output=result.output,
        )
    else:
        result_data = CallResultData(
            success=result.success,
            value=result.value,
            error=result.error,
            output=result.output,
        )

    return AutoStepEvent(
        working_dir=str(working_dir),
        inputs=AutoStepInputs.from_step(step),
        result=result_data,
    )


def reconstruct_auto_step_result(*, recorded_event: AutoStepEvent) -> Any:
    """Reconstruct an AutoResult for the given step from a typed AutoStepEvent."""

    from mekara.scripting.runtime import AutoException, CallResult, ShellResult

    result_data = recorded_event.result

    if isinstance(result_data, ShellResultData):
        return ShellResult(
            success=result_data.success,
            exit_code=result_data.exit_code,
            output=result_data.output,
        )

    if isinstance(result_data, AutoExceptionData):
        return AutoException(
            success=result_data.success,
            exception=Exception(result_data.exception),
            step_description=result_data.step_description,
            output=result_data.output,
        )

    return CallResult(
        success=result_data.success,
        value=result_data.value,
        error=result_data.error,
        output=result_data.output,
    )
