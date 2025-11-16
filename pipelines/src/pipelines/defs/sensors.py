import dagster as dg

from .assets import assetsRaw


@dg.sensor(
    target=None,
    asset_selection=[assetsRaw]
)
def sensors(context: dg.SensorEvaluationContext) -> dg.SensorResult:
    context.log.info('sensors running')
    return dg.RunRequest()
