import docker
import subprocess

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerClient(object):

    def __init__(self):
        self.client = docker.from_env()

    def container_is_built(self, name):
        try:
            self.client.containers.get(name)
        except docker.errors.NotFound:
            return False
        return True

    @staticmethod
    def container_is_running(container):
        return container.status in ["restarting", "running"]
        # restarting, running, paused, exited

    def container_remove(self, name, force=True):
        if self.container_is_built(name):
            container = self.client.containers.get(name)
            container.remove(force=force)

    def container_stop(self, name, not_exist_ok=False, wait=True):
        if self.container_is_built(name):
            container = self.client.containers.get(name)
            if DockerClient.container_is_running(container):
                container.stop()
                logger.info(f"stopping (about 30 seconds){' and waiting' if wait else ''} docker {name}")
                if wait:
                    container.wait()
        else:
            if not not_exist_ok:
                raise RuntimeError(f"docker container does not exist {name}")

    def container_start(self, name, not_exist_ok=False):
        if self.container_is_built(name):
            container = self.client.containers.get(name)
            if not DockerClient.container_is_running(container):
                logger.info(f"starting (about 30 seconds) docker {name}")
                container.start()
        else:
            if not not_exist_ok:
                raise RuntimeError(f"docker container does not exist {name}")

    def container_build(self, image, ports, name=None, environment=None, detach=False, mounts=None, censor=None):

        # create and run
        logger.info(f"ElasticSearch server creation and startup procedure (about 30 seconds): {name}")
        if not isinstance(ports, dict): ports = {ports: ports for port in ports}
        if environment is None: environment = dict()
        if mounts is None: mounts = []
        as_mounts = [docker.types.Mount(**mount) for mount in mounts]

        # to help users unsure what is happening in the background
        s_env_log = " ".join([f"-e {k}={'<hidden>' if k in censor else v}" for k,v in environment.items()])
        s_env = " ".join([f"-e {k}={v}" for k,v in environment.items()])
        s_mount = " ".join([f"--mount type={m['type']},source={m['source']},target={m['target']}" for m in mounts])
        s_ports = " ".join(f"-p {_from}:{_to}" for _from, _to in ports.items())
        s_detact = " -d" if detach else ""
        s_name = f" --name {name}" if name is not None else ""
        as_cmd_log = f"docker run {s_ports}{s_detact}{s_name} {s_mount} {s_env_log} {image}"
        as_cmd = f"docker run {s_ports}{s_detact}{s_name} {s_mount} {s_env} {image}"
        logger.info(f"running docker equivalent to: {as_cmd_log}")

        # try using the docker python sdk then the command line as fallback
        try:
            logger.info("trying docker python sdk")
            self.client.containers.run(image=image, ports=ports, name=name, mounts=as_mounts,
                                       # volumes={directory: {"bind": directory, "mode": "rw"}},
                                       environment=[environment], detach=detach)

        except docker.errors.APIError as e:
            logger.warning("docker python sdk client build error")
            logger.info("trying docker command subprocess")
            subprocess.run([p.strip() for p in as_cmd.split() if len(p.strip()) != 0])

    @staticmethod
    def copy_from_container(name, source, target):
        # NOTE: for large file transfers use client.put_archive (not implemented)
        cmd = f"docker container cp {name}:{source} {target}"
        logger.info(f"trying docker command: {cmd}")
        subprocess.run([p.strip() for p in cmd.split() if len(p.strip()) != 0])

    @staticmethod
    def copy_to_container(name, source, target):
        # NOTE: for large file transfers use client.get_archive (not implemented)
        cmd = f"docker container cp {source} {name}:{target}"
        logger.info(f"trying docker command: {cmd}")
        subprocess.run([p.strip() for p in cmd.split() if len(p.strip()) != 0])

