import dagster as dg


@dg.asset
def assetsR(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

@dg.asset
def assetsRaw(context: dg.AssetExecutionContext) -> str:
  print('materializing assetsRaw')
  return 'raw'

@dg.asset
def assetsCanonical(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

@dg.asset
def assetsChunks(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...

@dg.asset
def assetsEmbeddings(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
