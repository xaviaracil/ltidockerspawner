import os

from dockerspawner.dockerspawner import DockerSpawner
from ltiauthenticator.lti_aware import LTIAwareMixin
from tornado import gen
from traitlets import Unicode


class LTIDockerSpawner(DockerSpawner, LTIAwareMixin):
    """
    DockerSpawner that defines notebook_dir and container_image
    from LTI (http://www.imsglobal.org/activity/learning-tools-interoperability) context
    """

    notebook_root_dir = Unicode(
        '',
        config=True,
        allow_none=True,
        help="""Path where find notebooks for every context. If not found, notebook_dir is used as default"""
    )

    container_image_param_name = Unicode(
        os.getenv('LTI_SPAWNER_CONTAINER_IMAGE_PARAM_NAME'),
        config=True,
        allow_none=True,
        help=("Param name in LTI context defining the container image to spawn. \n"
              "                If not found, container_image is used as default")
    )

    def _fmt(self, v):
        return v.format(context_id=self.provider.context_id)

    def get_env(self):
        env = super().get_env()
        if self.notebook_root_dir:
            volume_dir = self._fmt(self.notebook_root_dir)
            env["NOTEBOOK_DIR"] = volume_dir

        return env

    @gen.coroutine
    def start(self, image=None, extra_create_kwargs=None, extra_start_kwargs=None, extra_host_config=None):

        """Get image name from LTI context"""
        if self.container_image_param_name:
            image = self.provider.get_custom_param(self.container_image_param_name)

        """Get notebook dir from LTI context"""
        if self.notebook_root_dir:
            volume_dir = self._fmt(self.notebook_root_dir)
            context_volume = {self.provider.context_label: volume_dir}
            if not extra_host_config:
                extra_host_config = dict(binds=self._volumes_to_binds(context_volume, {}))
            else:
                extra_host_config['binds'] = self._volumes_to_binds(context_volume, extra_host_config['binds'])

        """Start the server"""
        yield super().start(image, extra_create_kwargs, extra_start_kwargs, extra_host_config)
