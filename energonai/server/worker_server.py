import uvicorn
from fastapi import FastAPI
import torch.distributed.rpc as rpc
from energonai.initialize import launch_from_multiprocess
from colossalai.logging import get_dist_logger
from energonai.context import MEATCONFIG

logger = get_dist_logger('energonai')

app = FastAPI()


@app.get("/")
def root():
    return {"200"}


@app.on_event("shutdown")
async def shutdown():
    rpc.shutdown()
    server.should_exit = True
    server.force_exit = True
    await server.shutdown()


def launch_worker(config_file,
                  rank=0,
                  local_rank=0,
                  server_host="127.0.0.1",
                  server_port=8005):

    MEATCONFIG.load_config(config_file)

    world_size = MEATCONFIG['tp_init_size'] * MEATCONFIG['pp_init_size']

    launch_from_multiprocess(MEATCONFIG['tp_init_size'], MEATCONFIG['pp_init_size'], MEATCONFIG['backend'],
                             MEATCONFIG['seed'], MEATCONFIG['verbose'], rank, local_rank, world_size,
                             MEATCONFIG['host'], MEATCONFIG['port'])

    WORKER_NAME = "wok{}"
    # _transports=["uv"] TODO: potentially a bug
    rpc_backend_options = rpc.TensorPipeRpcBackendOptions(num_worker_threads=16, rpc_timeout=6000)
    rpc.init_rpc(WORKER_NAME.format(rank), rank=rank, world_size=world_size, rpc_backend_options=rpc_backend_options)

    logger.info(f'RPC STATUS: RPC of Rank: {rank} is initialized.')

    global server
    config = uvicorn.Config(app, host=server_host, port=server_port, log_level=MEATCONFIG['log_level'])
    server = uvicorn.Server(config=config)
    server.run()
